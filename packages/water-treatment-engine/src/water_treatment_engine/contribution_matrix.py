"""Combined source-water and treatment contribution presentation.

This module reshapes the audit records already produced by fixed blending and
forward treatment application into one row-per-ion matrix suitable for UIs and
other presentation layers.  It does not perform a second chemistry calculation.

A source contribution can be unknown when a positive-volume source lacks a
resolved concentration for that ion.  A zero-volume source is instead marked as
having no chemical effect.  Treatment contributions are always known under the
current fixed-stoichiometry model; ingredients that do not contain an ion are
marked as not contributing rather than being confused with unknown data.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import fsum

from fermunits import Q_
from pint import Quantity

from water_treatment_engine._workflow_validation import (
    require_treatment_matches_blend,
)
from water_treatment_engine.blending import (
    BlendIonContribution,
    ResolvedBlendIon,
    UnresolvedBlendIon,
    WaterBlendResult,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.treatment_application import (
    ResolvedTreatmentIon,
    TreatmentAddition,
    TreatmentApplicationResult,
    TreatmentIonContribution,
    UnresolvedTreatmentIon,
)


@dataclass(frozen=True, slots=True)
class SourceContributionColumn:
    """Display metadata for one fixed-blend source column."""

    source_index: int
    source_name: str
    volume: Quantity[float]
    fraction: float


class SourceContributionCellStatus(StrEnum):
    """How one source participates in one ion row."""

    KNOWN = "known"
    SOURCE_CONCENTRATION_UNKNOWN = "source_concentration_unknown"
    ZERO_VOLUME = "zero_volume"


@dataclass(frozen=True, slots=True)
class SourceContributionCell:
    """One source-water cell in an ion contribution row."""

    source_index: int
    source_name: str
    status: SourceContributionCellStatus
    source_concentration: Quantity[float] | None
    weighted_contribution: Quantity[float] | None


@dataclass(frozen=True, slots=True)
class TreatmentContributionColumn:
    """Display metadata for one requested treatment-addition column."""

    treatment_index: int
    addition: TreatmentAddition


class TreatmentContributionCellStatus(StrEnum):
    """How one treatment addition participates in one ion row."""

    CONTRIBUTES = "contributes"
    DOES_NOT_CONTRIBUTE = "does_not_contribute"


@dataclass(frozen=True, slots=True)
class TreatmentContributionCell:
    """One treatment-addition cell in an ion contribution row."""

    treatment_index: int
    addition: TreatmentAddition
    status: TreatmentContributionCellStatus
    contribution: Quantity[float] | None


@dataclass(frozen=True, slots=True)
class IonContributionMatrixRow:
    """Combined source and treatment contribution detail for one modeled ion."""

    ion: Ion
    source_contributions: tuple[SourceContributionCell, ...]
    treatment_contributions: tuple[TreatmentContributionCell, ...]
    blend_concentration: Quantity[float] | None
    final_concentration: Quantity[float] | None

    @property
    def blend_is_known(self) -> bool:
        """Return whether the complete fixed-blend concentration is known."""
        return self.blend_concentration is not None

    @property
    def final_is_known(self) -> bool:
        """Return whether the complete final treated concentration is known."""
        return self.final_concentration is not None

    @property
    def known_source_contribution_sum(self) -> Quantity[float]:
        """Sum only source contributions that are actually known.

        This is intentionally named a *known contribution sum*.  When one or
        more positive-volume source concentrations are unknown, it is only a
        partial subtotal and must not be presented as the full blend total.
        """
        return Q_(
            fsum(
                float(cell.weighted_contribution.magnitude)
                for cell in self.source_contributions
                if cell.weighted_contribution is not None
            ),
            "milligram / liter",
        )

    @property
    def known_treatment_contribution_sum(self) -> Quantity[float]:
        """Return the complete known treatment contribution for this ion."""
        return Q_(
            fsum(
                float(cell.contribution.magnitude)
                for cell in self.treatment_contributions
                if cell.contribution is not None
            ),
            "milligram / liter",
        )


@dataclass(frozen=True, slots=True)
class WaterContributionMatrix:
    """One matrix spanning every source, treatment, and canonical ion."""

    source_columns: tuple[SourceContributionColumn, ...]
    treatment_columns: tuple[TreatmentContributionColumn, ...]
    rows: tuple[IonContributionMatrixRow, ...]

    def row_for(self, ion: Ion) -> IonContributionMatrixRow:
        """Return the matrix row for one canonical ion."""
        for row in self.rows:
            if row.ion is ion:
                return row

        raise ValueError(f"Unsupported contribution-matrix ion: {ion!r}")


def _source_cells(
    blend_result: WaterBlendResult,
    resolution: ResolvedBlendIon | UnresolvedBlendIon,
) -> tuple[SourceContributionCell, ...]:
    if isinstance(resolution, ResolvedBlendIon):
        known_contributions = resolution.source_contributions
        missing_source_indices: frozenset[int] = frozenset()
    else:
        known_contributions = resolution.known_source_contributions
        missing_source_indices = frozenset(resolution.missing_source_indices)

    contributions_by_source: dict[int, BlendIonContribution] = {
        contribution.source_index: contribution for contribution in known_contributions
    }

    cells: list[SourceContributionCell] = []
    for source_index, source in enumerate(blend_result.sources):
        if source.fraction == 0.0:
            cells.append(
                SourceContributionCell(
                    source_index=source_index,
                    source_name=source.name,
                    status=SourceContributionCellStatus.ZERO_VOLUME,
                    source_concentration=None,
                    weighted_contribution=None,
                )
            )
            continue

        contribution = contributions_by_source.get(source_index)
        if contribution is not None:
            cells.append(
                SourceContributionCell(
                    source_index=source_index,
                    source_name=source.name,
                    status=SourceContributionCellStatus.KNOWN,
                    source_concentration=contribution.source_concentration,
                    weighted_contribution=contribution.weighted_contribution,
                )
            )
            continue

        if source_index not in missing_source_indices:
            raise ValueError(
                "Blend ion-resolution audit does not account for every "
                "positive-volume source."
            )

        cells.append(
            SourceContributionCell(
                source_index=source_index,
                source_name=source.name,
                status=SourceContributionCellStatus.SOURCE_CONCENTRATION_UNKNOWN,
                source_concentration=None,
                weighted_contribution=None,
            )
        )

    return tuple(cells)


def _treatment_contributions_for(
    resolution: ResolvedTreatmentIon | UnresolvedTreatmentIon,
) -> tuple[TreatmentIonContribution, ...]:
    if isinstance(resolution, ResolvedTreatmentIon):
        return resolution.treatment_contributions
    return resolution.known_treatment_contributions


def _treatment_cells(
    treatment_result: TreatmentApplicationResult,
    resolution: ResolvedTreatmentIon | UnresolvedTreatmentIon,
) -> tuple[TreatmentContributionCell, ...]:
    contributions_by_treatment = {
        contribution.treatment_index: contribution
        for contribution in _treatment_contributions_for(resolution)
    }

    cells: list[TreatmentContributionCell] = []
    for treatment_index, applied in enumerate(treatment_result.applied_treatments):
        contribution = contributions_by_treatment.get(treatment_index)
        if contribution is None:
            cells.append(
                TreatmentContributionCell(
                    treatment_index=treatment_index,
                    addition=applied.addition,
                    status=TreatmentContributionCellStatus.DOES_NOT_CONTRIBUTE,
                    contribution=None,
                )
            )
            continue

        cells.append(
            TreatmentContributionCell(
                treatment_index=treatment_index,
                addition=applied.addition,
                status=TreatmentContributionCellStatus.CONTRIBUTES,
                contribution=contribution.contribution.concentration,
            )
        )

    return tuple(cells)


def build_contribution_matrix(
    blend_result: WaterBlendResult,
    treatment_result: TreatmentApplicationResult,
) -> WaterContributionMatrix:
    """Build a presentation matrix from one linked blend/treatment workflow.

    The function consumes the existing per-ion audit records rather than
    recalculating weighted source chemistry or treatment stoichiometry.  The
    treatment stage must therefore start from the supplied blend state and use
    the supplied blend volume.
    """
    require_treatment_matches_blend(blend_result, treatment_result)

    rows: list[IonContributionMatrixRow] = []
    for ion in Ion:
        blend_resolution = blend_result.resolution_for(ion)
        treatment_resolution = treatment_result.resolution_for(ion)

        blend_concentration = (
            blend_resolution.concentration.concentration
            if isinstance(blend_resolution, ResolvedBlendIon)
            else None
        )
        final_concentration = (
            treatment_resolution.concentration.concentration
            if isinstance(treatment_resolution, ResolvedTreatmentIon)
            else None
        )

        rows.append(
            IonContributionMatrixRow(
                ion=ion,
                source_contributions=_source_cells(
                    blend_result,
                    blend_resolution,
                ),
                treatment_contributions=_treatment_cells(
                    treatment_result,
                    treatment_resolution,
                ),
                blend_concentration=blend_concentration,
                final_concentration=final_concentration,
            )
        )

    return WaterContributionMatrix(
        source_columns=tuple(
            SourceContributionColumn(
                source_index=source_index,
                source_name=source.name,
                volume=source.volume,
                fraction=source.fraction,
            )
            for source_index, source in enumerate(blend_result.sources)
        ),
        treatment_columns=tuple(
            TreatmentContributionColumn(
                treatment_index=treatment_index,
                addition=treatment.addition,
            )
            for treatment_index, treatment in enumerate(
                treatment_result.applied_treatments
            )
        ),
        rows=tuple(rows),
    )
