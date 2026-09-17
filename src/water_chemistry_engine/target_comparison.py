"""Compare exact derived water states with target/reference profiles.

Target comparison is deliberately separate from source-report resolution.  The
state being compared already contains exact derived ion concentrations; missing
ions remain unknown.  Target/reference profiles may express exact values,
ordinary exact-ended ranges, or one-sided numeric bounds.

Qualified source-style ranges and not-detected results remain representable in a
``TargetWaterProfile`` for provenance, but this comparison layer does not invent
matching semantics for them.  Such criteria receive an explicit unsupported
outcome instead.

Bicarbonate and carbonate comparisons retain formal numerical inventory for
reference reproducibility, but their calculation basis is model-limited and
cannot produce a scientifically unqualified satisfied profile. Total alkalinity
is preserved separately and is compared only with a separately modeled total-
alkalinity result.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import isclose, isfinite

from fermunits import Q_, PHValue, Quantity

from water_chemistry_engine.alkalinity_balance import ModeledAlkalinity
from water_chemistry_engine.calculation_policy import capabilities_for
from water_chemistry_engine.chemical_state import AqueousChemicalState
from water_chemistry_engine.comparison_policy import TargetIonClosenessPolicy
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
from water_chemistry_engine.reported_properties import Alkalinity
from water_chemistry_engine.target_profiles import TargetWaterProfile

_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER = 1e-9


class TargetIonComparisonStatus(StrEnum):
    """Relationship between one known/unknown state ion and its target criterion."""

    WITHIN_TARGET = "within_target"
    BELOW_TARGET = "below_target"
    ABOVE_TARGET = "above_target"
    ACTUAL_UNKNOWN = "actual_unknown"
    TARGET_UNSUPPORTED = "target_unsupported"


class TargetIonClosenessStatus(StrEnum):
    """Policy-based interpretation kept separate from target position."""

    WITHIN_TARGET = "within_target"
    CLOSE = "close"
    FAR = "far"
    NOT_EVALUATED = "not_evaluated"


class UnsupportedTargetIonReason(StrEnum):
    """Why a represented target criterion has no matching semantics yet."""

    QUALIFIED_RANGE = "qualified_range"
    NOT_DETECTED = "not_detected"


class TargetIonCalculationBasis(StrEnum):
    """Scientific meaning of a numerical ion comparison."""

    SUPPORTED_CONCENTRATION = "supported_concentration"
    FORMAL_CARBONATE_INVENTORY = "formal_carbonate_inventory"


class TargetPHComparisonStatus(StrEnum):
    """Current status of a requested target-pH comparison."""

    NOT_CALCULATED = "not_calculated"


class TargetAlkalinityComparisonStatus(StrEnum):
    """Relationship between modeled total alkalinity and its target."""

    WITHIN_TARGET = "within_target"
    BELOW_TARGET = "below_target"
    ABOVE_TARGET = "above_target"
    ACTUAL_UNKNOWN = "actual_unknown"


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
    closeness: TargetIonClosenessStatus
    deviation: Quantity[float] | None
    unsupported_reason: UnsupportedTargetIonReason | None = None
    calculation_basis: TargetIonCalculationBasis = (
        TargetIonCalculationBasis.SUPPORTED_CONCENTRATION
    )


@dataclass(frozen=True, slots=True)
class TargetPHComparison:
    """Explicit placeholder for a target pH while derived pH is unsupported."""

    target_ph: PHValue
    actual_ph: PHValue | None
    status: TargetPHComparisonStatus


@dataclass(frozen=True, slots=True)
class TargetAlkalinityComparison:
    """Comparison of modeled total alkalinity with a report-basis target."""

    target_alkalinity: Alkalinity
    actual_alkalinity: ModeledAlkalinity | None
    status: TargetAlkalinityComparisonStatus
    target_minimum: Quantity[float]
    target_maximum: Quantity[float]
    deviation: Quantity[float] | None


@dataclass(frozen=True, slots=True)
class TargetProfileComparison:
    """Structured state-versus-target/reference comparison result."""

    state: AqueousChemicalState
    target_profile: TargetWaterProfile
    ion_comparisons: tuple[TargetIonComparison, ...]
    ph_comparison: TargetPHComparison | None
    status: TargetProfileComparisonStatus
    alkalinity_comparison: TargetAlkalinityComparison | None = None

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
    closeness_policy: TargetIonClosenessPolicy | None,
) -> TargetIonComparison:
    calculation_basis = (
        TargetIonCalculationBasis.SUPPORTED_CONCENTRATION
        if capabilities_for(target.ion).ordinary_target_comparison
        else TargetIonCalculationBasis.FORMAL_CARBONATE_INVENTORY
    )
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
            closeness=TargetIonClosenessStatus.NOT_EVALUATED,
            deviation=None,
            unsupported_reason=reason,
            calculation_basis=calculation_basis,
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
            closeness=TargetIonClosenessStatus.NOT_EVALUATED,
            deviation=None,
            calculation_basis=calculation_basis,
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
        deviation_mg_per_liter = actual_mg_per_liter - minimum_mg_per_liter
        return TargetIonComparison(
            ion=target.ion,
            target=target,
            actual_concentration=actual,
            target_minimum=target_minimum,
            target_maximum=target_maximum,
            status=TargetIonComparisonStatus.BELOW_TARGET,
            closeness=_closeness_status(
                deviation_mg_per_liter,
                closeness_policy,
                below=True,
            ),
            deviation=Q_(
                deviation_mg_per_liter,
                "milligram / liter",
            ),
            calculation_basis=calculation_basis,
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
        deviation_mg_per_liter = actual_mg_per_liter - maximum_mg_per_liter
        return TargetIonComparison(
            ion=target.ion,
            target=target,
            actual_concentration=actual,
            target_minimum=target_minimum,
            target_maximum=target_maximum,
            status=TargetIonComparisonStatus.ABOVE_TARGET,
            closeness=_closeness_status(
                deviation_mg_per_liter,
                closeness_policy,
                below=False,
            ),
            deviation=Q_(
                deviation_mg_per_liter,
                "milligram / liter",
            ),
            calculation_basis=calculation_basis,
        )

    return TargetIonComparison(
        ion=target.ion,
        target=target,
        actual_concentration=actual,
        target_minimum=target_minimum,
        target_maximum=target_maximum,
        status=TargetIonComparisonStatus.WITHIN_TARGET,
        closeness=TargetIonClosenessStatus.WITHIN_TARGET,
        deviation=Q_(0.0, "milligram / liter"),
        calculation_basis=calculation_basis,
    )


def _closeness_status(
    deviation_mg_per_liter: float,
    policy: TargetIonClosenessPolicy | None,
    *,
    below: bool,
) -> TargetIonClosenessStatus:
    if policy is None:
        return TargetIonClosenessStatus.NOT_EVALUATED

    maximum_deviation = (
        policy.maximum_below_deviation if below else policy.maximum_above_deviation
    )
    maximum_mg_per_liter = float(maximum_deviation.to("milligram / liter").magnitude)
    absolute_deviation = abs(deviation_mg_per_liter)
    if absolute_deviation <= maximum_mg_per_liter or isclose(
        absolute_deviation,
        maximum_mg_per_liter,
        rel_tol=0.0,
        abs_tol=_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER,
    ):
        return TargetIonClosenessStatus.CLOSE

    return TargetIonClosenessStatus.FAR


def _compare_alkalinity(
    target: Alkalinity,
    actual: ModeledAlkalinity | None,
) -> TargetAlkalinityComparison:
    """Compare modeled alkalinity without reinterpreting carbonate species."""
    if target.value is not None:
        minimum = target.value
        maximum = target.value
    elif target.minimum is not None and target.maximum is not None:
        minimum = target.minimum
        maximum = target.maximum
    elif target.reported_average is not None:
        minimum = target.reported_average
        maximum = target.reported_average
    else:  # pragma: no cover - Alkalinity validates this invariant.
        raise ValueError("Alkalinity target has no numeric criterion.")

    target_minimum = Q_(
        float(minimum.to("milligram / liter").magnitude),
        "milligram / liter",
    )
    target_maximum = Q_(
        float(maximum.to("milligram / liter").magnitude),
        "milligram / liter",
    )
    if actual is None:
        return TargetAlkalinityComparison(
            target_alkalinity=target,
            actual_alkalinity=None,
            status=TargetAlkalinityComparisonStatus.ACTUAL_UNKNOWN,
            target_minimum=target_minimum,
            target_maximum=target_maximum,
            deviation=None,
        )

    actual_value = float(actual.concentration.magnitude)
    minimum_value = float(target_minimum.magnitude)
    maximum_value = float(target_maximum.magnitude)
    if actual_value < minimum_value and not isclose(
        actual_value,
        minimum_value,
        rel_tol=0.0,
        abs_tol=_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER,
    ):
        deviation = actual_value - minimum_value
        status = TargetAlkalinityComparisonStatus.BELOW_TARGET
    elif actual_value > maximum_value and not isclose(
        actual_value,
        maximum_value,
        rel_tol=0.0,
        abs_tol=_NUMERICAL_BOUNDARY_ABS_TOL_MG_PER_LITER,
    ):
        deviation = actual_value - maximum_value
        status = TargetAlkalinityComparisonStatus.ABOVE_TARGET
    else:
        deviation = 0.0
        status = TargetAlkalinityComparisonStatus.WITHIN_TARGET

    return TargetAlkalinityComparison(
        target_alkalinity=target,
        actual_alkalinity=actual,
        status=status,
        target_minimum=target_minimum,
        target_maximum=target_maximum,
        deviation=Q_(deviation, "milligram / liter"),
    )


def _profile_status(
    ion_comparisons: tuple[TargetIonComparison, ...],
    ph_comparison: TargetPHComparison | None,
    alkalinity_comparison: TargetAlkalinityComparison | None,
) -> TargetProfileComparisonStatus:
    if any(
        comparison.calculation_basis
        is TargetIonCalculationBasis.SUPPORTED_CONCENTRATION
        and comparison.status
        in (
            TargetIonComparisonStatus.BELOW_TARGET,
            TargetIonComparisonStatus.ABOVE_TARGET,
        )
        for comparison in ion_comparisons
    ):
        return TargetProfileComparisonStatus.NOT_SATISFIED

    if alkalinity_comparison is not None and alkalinity_comparison.status in (
        TargetAlkalinityComparisonStatus.BELOW_TARGET,
        TargetAlkalinityComparisonStatus.ABOVE_TARGET,
    ):
        return TargetProfileComparisonStatus.NOT_SATISFIED

    if (
        (
            ph_comparison is not None
            and ph_comparison.status is TargetPHComparisonStatus.NOT_CALCULATED
        )
        or (
            alkalinity_comparison is not None
            and alkalinity_comparison.status
            is TargetAlkalinityComparisonStatus.ACTUAL_UNKNOWN
        )
        or any(
            comparison.calculation_basis
            is TargetIonCalculationBasis.FORMAL_CARBONATE_INVENTORY
            or comparison.status
            in (
                TargetIonComparisonStatus.ACTUAL_UNKNOWN,
                TargetIonComparisonStatus.TARGET_UNSUPPORTED,
            )
            for comparison in ion_comparisons
        )
    ):
        return TargetProfileComparisonStatus.INDETERMINATE

    if ion_comparisons or alkalinity_comparison is not None:
        return TargetProfileComparisonStatus.SATISFIED

    return TargetProfileComparisonStatus.NO_CRITERIA


def compare_state_to_target(
    state: AqueousChemicalState,
    target_profile: TargetWaterProfile,
    *,
    actual_alkalinity: ModeledAlkalinity | None = None,
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

    A total-alkalinity target is compared only when the caller supplies a
    separately modeled total-alkalinity result. Carbonate-system ion comparisons
    remain labeled as formal inventory and make the profile result indeterminate
    because equilibrium speciation is not calculated.
    """
    comparison_policy = target_profile.comparison_policy
    ion_comparisons = tuple(
        _compare_ion(
            state,
            target,
            None
            if comparison_policy is None
            else comparison_policy.policy_for(target.ion),
        )
        for target in target_profile.concentrations
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
    alkalinity_comparison = (
        None
        if target_profile.alkalinity is None
        else _compare_alkalinity(target_profile.alkalinity, actual_alkalinity)
    )

    return TargetProfileComparison(
        state=state,
        target_profile=target_profile,
        ion_comparisons=ion_comparisons,
        ph_comparison=ph_comparison,
        status=_profile_status(
            ion_comparisons,
            ph_comparison,
            alkalinity_comparison,
        ),
        alkalinity_comparison=alkalinity_comparison,
    )
