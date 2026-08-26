"""Fixed-volume and fixed-fraction blending of derived water states.

Blending operates only on exact derived ``AqueousChemicalState`` inputs.  Source
report interpretation belongs at the earlier source-resolution boundary.
Conservative ion concentrations are combined by volume-weighted mass balance.

Unknown source concentrations remain unknown.  If any positive-volume source
omits an ion, the final blend does not claim a total concentration for that ion,
although contributions from sources with known concentrations remain available
for audit and explanation.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction
from math import fsum, isclose, isfinite

from fermunits import Q_
from pint import Quantity

from water_treatment_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.quantity_types import ScalarQuantity

type ScalarBlendFraction = int | float | Decimal | Fraction


@dataclass(frozen=True, slots=True)
class BlendSource:
    """One named derived source state and its requested blend volume."""

    name: str
    state: AqueousChemicalState
    volume: ScalarQuantity

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Blend source name cannot be empty.")

        _normalize_nonnegative_volume(self.volume, context="Blend source")


@dataclass(frozen=True, slots=True)
class FractionalBlendSource:
    """One named derived source state and its requested fraction of a blend."""

    name: str
    state: AqueousChemicalState
    fraction: ScalarBlendFraction

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Blend source name cannot be empty.")

        value = _normalize_fraction(self.fraction)
        if value > 1.0:
            raise ValueError("Blend source fraction cannot be greater than one.")


@dataclass(frozen=True, slots=True)
class BlendedSource:
    """One source normalized to its actual volume and fraction in the blend."""

    name: str
    state: AqueousChemicalState
    volume: Quantity[float]
    fraction: float


@dataclass(frozen=True, slots=True)
class BlendIonContribution:
    """Known contribution from one source to one final blend concentration."""

    source_index: int
    source_name: str
    ion: Ion
    source_concentration: Quantity[float]
    weighted_contribution: Quantity[float]


@dataclass(frozen=True, slots=True)
class ResolvedBlendIon:
    """One ion whose final blend concentration is fully known."""

    concentration: DerivedIonConcentration
    source_contributions: tuple[BlendIonContribution, ...]

    @property
    def ion(self) -> Ion:
        return self.concentration.ion


class UnresolvedBlendIonReason(StrEnum):
    """Why one blend ion could not be assigned a final concentration."""

    MISSING_SOURCE_CONCENTRATION = "missing_source_concentration"


@dataclass(frozen=True, slots=True)
class UnresolvedBlendIon:
    """One ion whose total is unknown because a contributing source is unknown."""

    ion: Ion
    reason: UnresolvedBlendIonReason
    missing_source_indices: tuple[int, ...]
    missing_source_names: tuple[str, ...]
    known_source_contributions: tuple[BlendIonContribution, ...]


type BlendIonResolution = ResolvedBlendIon | UnresolvedBlendIon


@dataclass(frozen=True, slots=True)
class WaterBlendResult:
    """Fixed blend state with normalized source and per-ion audit detail."""

    sources: tuple[BlendedSource, ...]
    total_volume: Quantity[float]
    state: AqueousChemicalState
    ion_resolutions: tuple[BlendIonResolution, ...]

    def resolution_for(self, ion: Ion) -> BlendIonResolution:
        """Return the resolution outcome for one supported ion."""
        for resolution in self.ion_resolutions:
            if resolution.ion is ion:
                return resolution

        raise ValueError(f"Unsupported blend ion: {ion!r}")


def _normalize_nonnegative_volume(
    volume: ScalarQuantity,
    *,
    context: str,
) -> Quantity[float]:
    try:
        normalized = volume.to("liter")
    except Exception as exc:
        raise ValueError(f"{context} volume must be convertible to volume.") from exc

    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude):
        raise ValueError(f"{context} volume must be finite.")
    if magnitude < 0:
        raise ValueError(f"{context} volume cannot be negative.")

    return Q_(magnitude, "liter")


def _normalize_positive_total_volume(volume: ScalarQuantity) -> Quantity[float]:
    normalized = _normalize_nonnegative_volume(volume, context="Blend total")
    if normalized.magnitude <= 0:
        raise ValueError("Blend total volume must be greater than zero.")
    return normalized


def _normalize_fraction(fraction: ScalarBlendFraction) -> float:
    value = float(fraction)
    if not isfinite(value):
        raise ValueError("Blend source fraction must be finite.")
    if value < 0:
        raise ValueError("Blend source fraction cannot be negative.")
    return value


def _calculate_blend(
    sources: tuple[BlendedSource, ...],
    total_volume: Quantity[float],
) -> WaterBlendResult:
    resolutions: list[BlendIonResolution] = []

    for ion in Ion:
        known_contributions: list[BlendIonContribution] = []
        missing_source_indices: list[int] = []
        missing_source_names: list[str] = []

        for source_index, source in enumerate(sources):
            if source.fraction == 0.0:
                continue

            concentration = source.state.concentration_for(ion)
            if concentration is None:
                missing_source_indices.append(source_index)
                missing_source_names.append(source.name)
                continue

            source_mg_per_liter = float(concentration.to("milligram / liter").magnitude)
            weighted_mg_per_liter = source_mg_per_liter * source.fraction
            known_contributions.append(
                BlendIonContribution(
                    source_index=source_index,
                    source_name=source.name,
                    ion=ion,
                    source_concentration=Q_(
                        source_mg_per_liter,
                        "milligram / liter",
                    ),
                    weighted_contribution=Q_(
                        weighted_mg_per_liter,
                        "milligram / liter",
                    ),
                )
            )

        if missing_source_indices:
            resolutions.append(
                UnresolvedBlendIon(
                    ion=ion,
                    reason=UnresolvedBlendIonReason.MISSING_SOURCE_CONCENTRATION,
                    missing_source_indices=tuple(missing_source_indices),
                    missing_source_names=tuple(missing_source_names),
                    known_source_contributions=tuple(known_contributions),
                )
            )
            continue

        blended_value = fsum(
            float(contribution.weighted_contribution.magnitude)
            for contribution in known_contributions
        )
        resolutions.append(
            ResolvedBlendIon(
                concentration=DerivedIonConcentration.mg_per_liter(
                    ion,
                    blended_value,
                ),
                source_contributions=tuple(known_contributions),
            )
        )

    state = AqueousChemicalState(
        concentrations=tuple(
            resolution.concentration
            for resolution in resolutions
            if isinstance(resolution, ResolvedBlendIon)
        )
    )

    return WaterBlendResult(
        sources=sources,
        total_volume=total_volume,
        state=state,
        ion_resolutions=tuple(resolutions),
    )


def blend_waters(sources: tuple[BlendSource, ...]) -> WaterBlendResult:
    """Blend one or more exact source states using fixed source volumes.

    Zero-volume sources are retained in the normalized source list but have no
    effect on chemistry or unknown-value propagation.  The sum of source
    volumes must be greater than zero.
    """
    if not sources:
        raise ValueError("A water blend requires at least one source.")

    normalized_volumes = tuple(
        _normalize_nonnegative_volume(source.volume, context="Blend source")
        for source in sources
    )
    total_liters = fsum(float(volume.magnitude) for volume in normalized_volumes)
    total_volume = _normalize_positive_total_volume(Q_(total_liters, "liter"))

    normalized_sources = tuple(
        BlendedSource(
            name=source.name,
            state=source.state,
            volume=volume,
            fraction=float(volume.magnitude) / total_liters,
        )
        for source, volume in zip(sources, normalized_volumes, strict=True)
    )

    return _calculate_blend(normalized_sources, total_volume)


def blend_waters_by_fractions(
    sources: tuple[FractionalBlendSource, ...],
    *,
    total_volume: ScalarQuantity,
) -> WaterBlendResult:
    """Blend one or more exact source states using fractions of a total volume.

    Fractions are dimensionless values in the inclusive range 0..1 and must sum
    to one within a small floating-point tolerance.  ``total_volume`` preserves
    the physical batch size needed by later treatment-application calculations.
    """
    if not sources:
        raise ValueError("A water blend requires at least one source.")

    normalized_total_volume = _normalize_positive_total_volume(total_volume)
    fractions = tuple(_normalize_fraction(source.fraction) for source in sources)
    fraction_sum = fsum(fractions)
    if not isclose(fraction_sum, 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("Blend source fractions must sum to one.")

    normalized_fractions = tuple(fraction / fraction_sum for fraction in fractions)
    normalized_sources = tuple(
        BlendedSource(
            name=source.name,
            state=source.state,
            volume=Q_(
                float(normalized_total_volume.magnitude) * fraction,
                "liter",
            ),
            fraction=fraction,
        )
        for source, fraction in zip(sources, normalized_fractions, strict=True)
    )

    return _calculate_blend(normalized_sources, normalized_total_volume)
