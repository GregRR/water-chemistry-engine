"""Forward application of simple mineral additions to a derived water state.

This layer combines the fixed stoichiometric contributions calculated by
``treatment_stoichiometry`` with an existing exact derived ion inventory.  It
is still a formal mass-balance model rather than an aqueous-equilibrium model.
In particular, it does not consume ions through reactions, enforce solubility,
model precipitation, or redistribute carbonate species.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import fsum, isfinite
from typing import TypeAlias

from fermunits import Q_, Quantity

from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.treatment_ingredients import TreatmentIngredient
from water_chemistry_engine.treatment_stoichiometry import (
    IonContribution,
    calculate_ion_contributions,
)


@dataclass(frozen=True, slots=True)
class TreatmentAddition:
    """One requested mass addition of a specific treatment ingredient."""

    ingredient: TreatmentIngredient
    mass: ScalarQuantity

    def __post_init__(self) -> None:
        try:
            normalized = self.mass.to("gram")
        except Exception as exc:
            raise ValueError(
                "Treatment addition mass must be convertible to mass."
            ) from exc

        magnitude = float(normalized.magnitude)
        if not isfinite(magnitude):
            raise ValueError("Treatment addition mass must be finite.")
        if magnitude < 0:
            raise ValueError("Treatment addition mass cannot be negative.")


@dataclass(frozen=True, slots=True)
class AppliedTreatment:
    """One treatment addition together with its derived ion contributions."""

    addition: TreatmentAddition
    ion_contributions: tuple[IonContribution, ...]


@dataclass(frozen=True, slots=True)
class TreatmentIonContribution:
    """One treatment's known contribution to one ion in the result."""

    treatment_index: int
    addition: TreatmentAddition
    contribution: IonContribution

    @property
    def ion(self) -> Ion:
        return self.contribution.ion


@dataclass(frozen=True, slots=True)
class ResolvedTreatmentIon:
    """One ion whose treated-water total is fully known."""

    concentration: DerivedIonConcentration
    initial_concentration: DerivedIonConcentration
    treatment_contributions: tuple[TreatmentIonContribution, ...]

    @property
    def ion(self) -> Ion:
        return self.concentration.ion


class UnresolvedTreatmentIonReason(StrEnum):
    """Why one treated-water ion could not be assigned a final total."""

    MISSING_INITIAL_CONCENTRATION = "missing_initial_concentration"


@dataclass(frozen=True, slots=True)
class UnresolvedTreatmentIon:
    """One ion whose final total is unknown despite any known additions."""

    ion: Ion
    reason: UnresolvedTreatmentIonReason
    known_treatment_contributions: tuple[TreatmentIonContribution, ...]


TreatmentIonResolution: TypeAlias = ResolvedTreatmentIon | UnresolvedTreatmentIon


@dataclass(frozen=True, slots=True)
class TreatmentApplicationResult:
    """Derived final state and auditable contribution detail for a treatment set."""

    initial_state: AqueousChemicalState
    water_volume: Quantity[float]
    applied_treatments: tuple[AppliedTreatment, ...]
    final_state: AqueousChemicalState
    ion_resolutions: tuple[TreatmentIonResolution, ...]

    def resolution_for(self, ion: Ion) -> TreatmentIonResolution:
        """Return one ion outcome; normal treatment results contain every canonical ion."""
        for resolution in self.ion_resolutions:
            if resolution.ion is ion:
                return resolution

        raise ValueError(f"Unsupported treatment ion: {ion!r}")


def _normalize_water_volume(water_volume: ScalarQuantity) -> Quantity[float]:
    try:
        normalized = water_volume.to("liter")
    except Exception as exc:
        raise ValueError(
            "Treatment water volume must be convertible to volume."
        ) from exc

    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude):
        raise ValueError("Treatment water volume must be finite.")
    if magnitude <= 0:
        raise ValueError("Treatment water volume must be greater than zero.")

    return Q_(magnitude, "liter")


def apply_treatment_additions(
    initial_state: AqueousChemicalState,
    water_volume: ScalarQuantity,
    additions: tuple[TreatmentAddition, ...],
) -> TreatmentApplicationResult:
    """Apply zero or more simple mineral additions to an exact water state.

    Existing known state concentrations and each treatment contribution are
    summed in canonical mg/L units.  A missing ion in ``initial_state`` remains
    unknown: treatment contribution to that ion is recorded, but it is not
    silently promoted to a final total by assuming the unknown starting value
    was zero.  Callers that genuinely know a starting concentration is zero
    should represent that zero explicitly in the derived state.

    The returned per-treatment records preserve how much each requested
    addition contributed.  Per-ion resolution records additionally state
    whether the final total is known and retain the treatment contributions
    even when a missing initial concentration keeps that total unknown.
    """
    normalized_volume = _normalize_water_volume(water_volume)

    initial_concentrations = {
        concentration.ion: concentration
        for concentration in initial_state.concentrations
    }
    concentration_terms_mg_per_liter = {
        ion: [float(concentration.concentration.magnitude)]
        for ion, concentration in initial_concentrations.items()
    }
    contributions_by_ion: dict[Ion, list[TreatmentIonContribution]] = {
        ion: [] for ion in Ion
    }

    applied_treatments: list[AppliedTreatment] = []
    for treatment_index, addition in enumerate(additions):
        contributions = calculate_ion_contributions(
            addition.ingredient,
            addition.mass,
            normalized_volume,
        )
        applied_treatments.append(
            AppliedTreatment(
                addition=addition,
                ion_contributions=contributions,
            )
        )

        for contribution in contributions:
            contributions_by_ion[contribution.ion].append(
                TreatmentIonContribution(
                    treatment_index=treatment_index,
                    addition=addition,
                    contribution=contribution,
                )
            )
            if contribution.ion in concentration_terms_mg_per_liter:
                concentration_terms_mg_per_liter[contribution.ion].append(
                    float(contribution.concentration.magnitude)
                )

    resolutions: list[TreatmentIonResolution] = []
    for ion in Ion:
        treatment_contributions = tuple(contributions_by_ion[ion])
        initial_concentration = initial_concentrations.get(ion)
        if initial_concentration is None:
            resolutions.append(
                UnresolvedTreatmentIon(
                    ion=ion,
                    reason=UnresolvedTreatmentIonReason.MISSING_INITIAL_CONCENTRATION,
                    known_treatment_contributions=treatment_contributions,
                )
            )
            continue

        resolutions.append(
            ResolvedTreatmentIon(
                concentration=DerivedIonConcentration.mg_per_liter(
                    ion,
                    fsum(concentration_terms_mg_per_liter[ion]),
                ),
                initial_concentration=initial_concentration,
                treatment_contributions=treatment_contributions,
            )
        )

    # Enum declaration order gives the derived state a stable ordering that is
    # independent of dict insertion details or the order in which treatments
    # happened to be supplied.
    final_concentrations = tuple(
        resolution.concentration
        for resolution in resolutions
        if isinstance(resolution, ResolvedTreatmentIon)
    )

    return TreatmentApplicationResult(
        initial_state=initial_state,
        water_volume=normalized_volume,
        applied_treatments=tuple(applied_treatments),
        final_state=AqueousChemicalState(concentrations=final_concentrations),
        ion_resolutions=tuple(resolutions),
    )
