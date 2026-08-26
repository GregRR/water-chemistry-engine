"""Resolve source-report ion results into deterministic calculation states.

Source-water reports preserve what the source actually said: exact values,
ranges, qualified bounds, not-detected results, named statistics, and reporting
context.  Deterministic calculations need exact numeric concentrations instead.

This module is the explicit boundary between those two representations.  It
resolves only source-result forms justified by the supplied policy and records
how each ion was handled so downstream calculations never have to guess.
"""

from dataclasses import dataclass
from enum import StrEnum

from water_treatment_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_treatment_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    IonConcentrationValue,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.profiles import SourceWaterProfile


@dataclass(frozen=True, slots=True)
class SourceResolutionPolicy:
    """Explicit rules for selecting representative linear source values."""

    allow_exact_range_midpoints: bool


class SourceIonResolutionMethod(StrEnum):
    """How one source-report result became a derived numeric concentration."""

    REPORTED_VALUE = "reported_value"
    REPORTED_AVERAGE = "reported_average"
    DERIVED_EXACT_RANGE_MIDPOINT = "derived_exact_range_midpoint"


class UnresolvedSourceIonReason(StrEnum):
    """Why one reported source ion was intentionally left unresolved."""

    EXACT_RANGE_MIDPOINT_NOT_PERMITTED = "exact_range_midpoint_not_permitted"
    QUALIFIED_RANGE = "qualified_range"
    UPPER_BOUND = "upper_bound"
    LOWER_BOUND = "lower_bound"
    NOT_DETECTED = "not_detected"


@dataclass(frozen=True, slots=True)
class ResolvedSourceIon:
    """One source ion that was resolved into an exact derived concentration."""

    source_result: IonConcentrationValue
    concentration: DerivedIonConcentration
    method: SourceIonResolutionMethod

    @property
    def ion(self) -> Ion:
        return self.source_result.ion


@dataclass(frozen=True, slots=True)
class UnresolvedSourceIon:
    """One source ion deliberately excluded from the derived calculation state."""

    source_result: IonConcentrationValue
    reason: UnresolvedSourceIonReason

    @property
    def ion(self) -> Ion:
        return self.source_result.ion


type SourceIonResolution = ResolvedSourceIon | UnresolvedSourceIon


@dataclass(frozen=True, slots=True)
class SourceProfileResolutionResult:
    """Derived state plus an auditable resolution outcome for each reported ion."""

    source_profile: SourceWaterProfile
    policy: SourceResolutionPolicy
    state: AqueousChemicalState
    ion_resolutions: tuple[SourceIonResolution, ...]

    def resolution_for(self, ion: Ion) -> SourceIonResolution | None:
        """Return the resolution outcome for one reported source ion, if present."""
        for resolution in self.ion_resolutions:
            if resolution.ion is ion:
                return resolution

        return None


def _resolve_concentration(
    result: IonConcentrationValue,
    policy: SourceResolutionPolicy,
) -> SourceIonResolution:
    if isinstance(result, IonConcentration):
        return ResolvedSourceIon(
            source_result=result,
            concentration=DerivedIonConcentration.from_quantity(
                result.ion,
                result.value,
            ),
            method=SourceIonResolutionMethod.REPORTED_VALUE,
        )

    if isinstance(result, IonConcentrationRange):
        if result.reported_average is not None:
            return ResolvedSourceIon(
                source_result=result,
                concentration=DerivedIonConcentration.from_quantity(
                    result.ion,
                    result.reported_average,
                ),
                method=SourceIonResolutionMethod.REPORTED_AVERAGE,
            )

        if isinstance(result.minimum, ExactConcentrationEndpoint) and isinstance(
            result.maximum,
            ExactConcentrationEndpoint,
        ):
            if not policy.allow_exact_range_midpoints:
                return UnresolvedSourceIon(
                    source_result=result,
                    reason=(
                        UnresolvedSourceIonReason.EXACT_RANGE_MIDPOINT_NOT_PERMITTED
                    ),
                )

            return ResolvedSourceIon(
                source_result=result,
                concentration=DerivedIonConcentration.from_quantity(
                    result.ion,
                    result.calculation_value,
                ),
                method=SourceIonResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT,
            )

        return UnresolvedSourceIon(
            source_result=result,
            reason=UnresolvedSourceIonReason.QUALIFIED_RANGE,
        )

    if isinstance(result, IonConcentrationUpperBound):
        return UnresolvedSourceIon(
            source_result=result,
            reason=UnresolvedSourceIonReason.UPPER_BOUND,
        )

    if isinstance(result, IonConcentrationLowerBound):
        return UnresolvedSourceIon(
            source_result=result,
            reason=UnresolvedSourceIonReason.LOWER_BOUND,
        )

    if isinstance(result, IonConcentrationNotDetected):
        return UnresolvedSourceIon(
            source_result=result,
            reason=UnresolvedSourceIonReason.NOT_DETECTED,
        )

    raise TypeError(f"Unsupported source ion concentration type: {type(result)!r}")


def resolve_source_profile(
    source_profile: SourceWaterProfile,
    *,
    policy: SourceResolutionPolicy,
) -> SourceProfileResolutionResult:
    """Resolve reported source ions into an exact calculation-ready state.

    Exact reported values and independently reported averages are usable without
    inventing new source data.  An exact-ended linear range may additionally be
    represented by its derived midpoint only when the caller explicitly allows
    that policy.  Bounds, not-detected results, and qualified ranges without an
    independently reported average remain unresolved.

    Missing and unresolved ions are omitted from the resulting state rather than
    treated as zero.  An explicitly reported zero remains a known zero.
    """
    resolutions = tuple(
        _resolve_concentration(result, policy)
        for result in source_profile.concentrations
    )

    resolved_by_ion = {
        resolution.ion: resolution.concentration
        for resolution in resolutions
        if isinstance(resolution, ResolvedSourceIon)
    }

    state = AqueousChemicalState(
        concentrations=tuple(
            resolved_by_ion[ion] for ion in Ion if ion in resolved_by_ion
        )
    )

    return SourceProfileResolutionResult(
        source_profile=source_profile,
        policy=policy,
        state=state,
        ion_resolutions=resolutions,
    )
