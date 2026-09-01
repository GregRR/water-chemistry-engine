"""Compare exact derived water states with target/reference profiles.

Target comparison is deliberately separate from source-report resolution.  The
state being compared already contains exact derived ion concentrations; missing
ions remain unknown.  Target/reference profiles may express exact values,
ordinary exact-ended ranges, or one-sided numeric bounds.

Qualified source-style ranges and not-detected results remain representable in a
``TargetWaterProfile`` for provenance, but this comparison layer does not invent
matching semantics for them.  Such criteria receive an explicit unsupported
outcome instead.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import isclose, isfinite

from fermunits import Q_, Quantity

from water_chemistry_engine.chemical_state import AqueousChemicalState
from water_chemistry_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    IonConcentrationValue,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.target_profiles import TargetWaterProfile

_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER = 1e-9


class TargetIonComparisonStatus(StrEnum):
    """Relationship between one known/unknown state ion and its target criterion."""

    WITHIN_TARGET = "within_target"
    BELOW_TARGET = "below_target"
    ABOVE_TARGET = "above_target"
    ACTUAL_UNKNOWN = "actual_unknown"
    TARGET_UNSUPPORTED = "target_unsupported"


class UnsupportedTargetIonReason(StrEnum):
    """Why a represented target criterion has no matching semantics yet."""

    QUALIFIED_RANGE = "qualified_range"
    NOT_DETECTED = "not_detected"


class TargetPHComparisonStatus(StrEnum):
    """Current status of a requested target-pH comparison."""

    NOT_CALCULATED = "not_calculated"


class TargetProfileComparisonStatus(StrEnum):
    """Summary of whether a state satisfies all currently comparable targets."""

    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"
    INDETERMINATE = "indeterminate"
    NO_CRITERIA = "no_criteria"


@dataclass(frozen=True, slots=True)
class TargetIonComparison:
    """Comparison outcome for one target ion.

    ``deviation`` is signed in mg/L.  It is negative below the accepted target,
    positive above it, and zero when an exact value or accepted range/bound is
    satisfied.  For an exact target outside the numerical-noise tolerance this
    is ``actual - target``.  Differences within that tolerance are reported as
    zero and do not change criterion status.
    """

    ion: Ion
    target: IonConcentrationValue
    actual_concentration: Quantity[float] | None
    target_minimum: Quantity[float] | None
    target_maximum: Quantity[float] | None
    status: TargetIonComparisonStatus
    deviation: Quantity[float] | None
    unsupported_reason: UnsupportedTargetIonReason | None = None


@dataclass(frozen=True, slots=True)
class TargetPHComparison:
    """Explicit placeholder for a target pH while derived pH is unsupported."""

    target_ph: float
    actual_ph: float | None
    status: TargetPHComparisonStatus


@dataclass(frozen=True, slots=True)
class TargetProfileComparison:
    """Structured state-versus-target/reference comparison result."""

    state: AqueousChemicalState
    target_profile: TargetWaterProfile
    ion_comparisons: tuple[TargetIonComparison, ...]
    ph_comparison: TargetPHComparison | None
    status: TargetProfileComparisonStatus

    def comparison_for(self, ion: Ion) -> TargetIonComparison | None:
        """Return one target-ion comparison, or ``None`` if no target was supplied."""
        for comparison in self.ion_comparisons:
            if comparison.ion is ion:
                return comparison

        return None


def _normalized_target_bounds(
    target: IonConcentrationValue,
) -> tuple[Quantity[float] | None, Quantity[float] | None] | None:
    if isinstance(target, IonConcentration):
        exact = Q_(
            float(target.value.to("milligram / liter").magnitude),
            "milligram / liter",
        )
        return exact, exact

    if isinstance(target, IonConcentrationRange):
        if not isinstance(target.minimum, ExactConcentrationEndpoint) or not isinstance(
            target.maximum,
            ExactConcentrationEndpoint,
        ):
            return None

        return (
            Q_(
                float(target.minimum.value.to("milligram / liter").magnitude),
                "milligram / liter",
            ),
            Q_(
                float(target.maximum.value.to("milligram / liter").magnitude),
                "milligram / liter",
            ),
        )

    if isinstance(target, IonConcentrationUpperBound):
        return (
            None,
            Q_(
                float(target.maximum.to("milligram / liter").magnitude),
                "milligram / liter",
            ),
        )

    if isinstance(target, IonConcentrationLowerBound):
        return (
            Q_(
                float(target.minimum.to("milligram / liter").magnitude),
                "milligram / liter",
            ),
            None,
        )

    return None


def _unsupported_reason(
    target: IonConcentrationValue,
) -> UnsupportedTargetIonReason | None:
    if isinstance(target, IonConcentrationRange):
        return UnsupportedTargetIonReason.QUALIFIED_RANGE
    if isinstance(target, IonConcentrationNotDetected):
        return UnsupportedTargetIonReason.NOT_DETECTED
    return None


def _compare_ion(
    state: AqueousChemicalState,
    target: IonConcentrationValue,
) -> TargetIonComparison:
    bounds = _normalized_target_bounds(target)
    if bounds is None:
        reason = _unsupported_reason(target)
        if reason is None:
            raise TypeError(
                f"Unsupported target ion concentration type: {type(target)!r}"
            )

        return TargetIonComparison(
            ion=target.ion,
            target=target,
            actual_concentration=state.concentration_for(target.ion),
            target_minimum=None,
            target_maximum=None,
            status=TargetIonComparisonStatus.TARGET_UNSUPPORTED,
            deviation=None,
            unsupported_reason=reason,
        )

    target_minimum, target_maximum = bounds
    minimum_mg_per_liter = (
        None if target_minimum is None else float(target_minimum.magnitude)
    )
    maximum_mg_per_liter = (
        None if target_maximum is None else float(target_maximum.magnitude)
    )
    if minimum_mg_per_liter is not None and not isfinite(minimum_mg_per_liter):
        raise ValueError("Target ion concentration must be finite for comparison.")
    if maximum_mg_per_liter is not None and not isfinite(maximum_mg_per_liter):
        raise ValueError("Target ion concentration must be finite for comparison.")

    actual = state.concentration_for(target.ion)
    if actual is None:
        return TargetIonComparison(
            ion=target.ion,
            target=target,
            actual_concentration=None,
            target_minimum=target_minimum,
            target_maximum=target_maximum,
            status=TargetIonComparisonStatus.ACTUAL_UNKNOWN,
            deviation=None,
        )

    actual_mg_per_liter = float(actual.to("milligram / liter").magnitude)
    if not isfinite(actual_mg_per_liter):
        raise ValueError("Actual ion concentration must be finite for comparison.")
    if (
        minimum_mg_per_liter is not None
        and actual_mg_per_liter < minimum_mg_per_liter
        and not isclose(
            actual_mg_per_liter,
            minimum_mg_per_liter,
            rel_tol=0.0,
            abs_tol=_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER,
        )
    ):
        return TargetIonComparison(
            ion=target.ion,
            target=target,
            actual_concentration=actual,
            target_minimum=target_minimum,
            target_maximum=target_maximum,
            status=TargetIonComparisonStatus.BELOW_TARGET,
            deviation=Q_(
                actual_mg_per_liter - minimum_mg_per_liter,
                "milligram / liter",
            ),
        )

    if (
        maximum_mg_per_liter is not None
        and actual_mg_per_liter > maximum_mg_per_liter
        and not isclose(
            actual_mg_per_liter,
            maximum_mg_per_liter,
            rel_tol=0.0,
            abs_tol=_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER,
        )
    ):
        return TargetIonComparison(
            ion=target.ion,
            target=target,
            actual_concentration=actual,
            target_minimum=target_minimum,
            target_maximum=target_maximum,
            status=TargetIonComparisonStatus.ABOVE_TARGET,
            deviation=Q_(
                actual_mg_per_liter - maximum_mg_per_liter,
                "milligram / liter",
            ),
        )

    return TargetIonComparison(
        ion=target.ion,
        target=target,
        actual_concentration=actual,
        target_minimum=target_minimum,
        target_maximum=target_maximum,
        status=TargetIonComparisonStatus.WITHIN_TARGET,
        deviation=Q_(0.0, "milligram / liter"),
    )


def _profile_status(
    ion_comparisons: tuple[TargetIonComparison, ...],
    ph_comparison: TargetPHComparison | None,
) -> TargetProfileComparisonStatus:
    if any(
        comparison.status
        in (
            TargetIonComparisonStatus.BELOW_TARGET,
            TargetIonComparisonStatus.ABOVE_TARGET,
        )
        for comparison in ion_comparisons
    ):
        return TargetProfileComparisonStatus.NOT_SATISFIED

    if (
        ph_comparison is not None
        and ph_comparison.status is TargetPHComparisonStatus.NOT_CALCULATED
    ) or any(
        comparison.status
        in (
            TargetIonComparisonStatus.ACTUAL_UNKNOWN,
            TargetIonComparisonStatus.TARGET_UNSUPPORTED,
        )
        for comparison in ion_comparisons
    ):
        return TargetProfileComparisonStatus.INDETERMINATE

    if ion_comparisons:
        return TargetProfileComparisonStatus.SATISFIED

    return TargetProfileComparisonStatus.NO_CRITERIA


def compare_state_to_target(
    state: AqueousChemicalState,
    target_profile: TargetWaterProfile,
) -> TargetProfileComparison:
    """Compare one derived aqueous state with a target/reference profile.

    Exact ion targets, exact-ended ranges, and standalone numeric upper/lower
    bounds are comparable.  Boundary checks use a tiny absolute mg/L tolerance
    solely to suppress floating-point arithmetic noise; it is not a chemical or
    user-facing closeness policy.  Missing state ions remain explicitly unknown.
    Qualified ranges and not-detected target criteria are represented as
    unsupported rather than being silently converted into numeric targets.

    Working-water pH is not yet calculated by the engine.  A target pH is
    therefore retained as an explicit ``NOT_CALCULATED`` outcome instead of
    being ignored or compared with reported source pH.
    """
    ion_comparisons = tuple(
        _compare_ion(state, target) for target in target_profile.concentrations
    )
    ph_comparison = (
        None
        if target_profile.ph is None
        else TargetPHComparison(
            target_ph=target_profile.ph,
            actual_ph=None,
            status=TargetPHComparisonStatus.NOT_CALCULATED,
        )
    )

    return TargetProfileComparison(
        state=state,
        target_profile=target_profile,
        ion_comparisons=ion_comparisons,
        ph_comparison=ph_comparison,
        status=_profile_status(ion_comparisons, ph_comparison),
    )
