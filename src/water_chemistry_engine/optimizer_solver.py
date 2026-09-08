"""First bounded fixed-blend treatment optimizer.

The implemented strategy minimizes the unweighted sum of absolute target
deviations in canonical mg/L. Material decisions are integer counts of each
caller's declared dose increment, so the returned plan is practical by
construction rather than a rounded approximation of a continuous solution.

This score is a transparent mathematical policy, not a claim that equal mg/L
deviations across ions have equal sensory, process, or health significance.
Every selected dose is rerun through the ordinary forward calculator before a
plan is returned.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from math import fabs, fsum, inf, isclose, isfinite
from typing import Protocol, cast

from fermunits import Q_
from scipy.optimize import (  # type: ignore[import-untyped]
    Bounds,
    LinearConstraint,
    milp,
)

from water_chemistry_engine.forward_calculator import (
    ForwardWaterSource,
    calculate_forward_water,
)
from water_chemistry_engine.optimization import (
    OptimizerBlendPolicy,
    OptimizerDiagnostic,
    OptimizerDiagnosticCode,
    OptimizerFeasibilityStatus,
    OptimizerInputSupportStatus,
    OptimizerMaterialAddition,
    OptimizerMaterialConstraint,
    OptimizerPlan,
    OptimizerPracticalityStatus,
    OptimizerRequest,
    OptimizerResult,
    OptimizerSolverReport,
    OptimizerSourceVolume,
    OptimizerStrategy,
    OptimizerTargetFitStatus,
)
from water_chemistry_engine.source_resolution import resolve_source_profile
from water_chemistry_engine.target_comparison import (
    TargetIonComparison,
    TargetIonComparisonStatus,
    TargetProfileComparison,
    TargetProfileComparisonStatus,
)
from water_chemistry_engine.treatment_stoichiometry import (
    calculate_ion_contributions,
)

_SOLVER = "scipy.optimize.milp"
_METHOD = "highs"
_PRIMARY_OBJECTIVE_TOLERANCE_MG_PER_LITER = 1e-9
_POSTVALIDATION_ABS_TOLERANCE_MG_PER_LITER = 1e-7
_POSTVALIDATION_REL_TOLERANCE = 1e-12
_INTEGER_ABS_TOLERANCE = 1e-6
_CONTINUOUS_ABS_TOLERANCE = 1e-6
_MIP_RELATIVE_GAP = 0.0
_MAXIMUM_INCREMENT_COUNT = 1_000_000
_SMALLEST_SOLVER_MATRIX_VALUE = 1e-9
_LARGEST_SOLVER_MATRIX_VALUE = 1e15
_LARGEST_SOLVER_BOUND = 1e20


class _MilpResult(Protocol):
    success: bool
    status: int
    message: str
    fun: float | None
    x: Sequence[float] | None
    mip_gap: float | None


@dataclass(frozen=True, slots=True)
class _ValidatedDecisions:
    material_counts: tuple[int, ...]
    continuous_values: tuple[float, ...]


def _solver_report(
    result: _MilpResult,
    *,
    solver_reported_primary_objective: float | None,
    primary_objective: float | None,
    secondary_objective: float | None,
) -> OptimizerSolverReport:
    return OptimizerSolverReport(
        solver=_SOLVER,
        method=_METHOD,
        success=result.success,
        status_code=result.status,
        message=result.message,
        solver_reported_primary_objective_mg_per_liter=(
            solver_reported_primary_objective
        ),
        primary_objective_mg_per_liter=primary_objective,
        secondary_objective_grams=secondary_objective,
        primary_objective_tolerance_mg_per_liter=(
            _PRIMARY_OBJECTIVE_TOLERANCE_MG_PER_LITER
        ),
        mip_relative_gap=(None if result.mip_gap is None else float(result.mip_gap)),
    )


def _rejected_solver_report(
    result: _MilpResult,
    *,
    message: str,
    solver_reported_primary_objective: float | None,
    primary_objective: float | None = None,
) -> OptimizerSolverReport:
    return OptimizerSolverReport(
        solver=_SOLVER,
        method=_METHOD,
        success=False,
        status_code=4,
        message=message,
        solver_reported_primary_objective_mg_per_liter=(
            solver_reported_primary_objective
        ),
        primary_objective_mg_per_liter=primary_objective,
        secondary_objective_grams=None,
        primary_objective_tolerance_mg_per_liter=(
            _PRIMARY_OBJECTIVE_TOLERANCE_MG_PER_LITER
        ),
        mip_relative_gap=(None if result.mip_gap is None else float(result.mip_gap)),
    )


def _unsupported_result(
    request: OptimizerRequest,
    *,
    support: OptimizerInputSupportStatus,
    diagnostics: tuple[OptimizerDiagnostic, ...],
) -> OptimizerResult:
    return OptimizerResult(
        request=request,
        input_support=support,
        feasibility=OptimizerFeasibilityStatus.INDETERMINATE,
        plans=(),
        diagnostics=diagnostics,
        solver_report=None,
    )


def _input_diagnostics(
    request: OptimizerRequest,
    comparisons: tuple[TargetIonComparison, ...],
) -> tuple[OptimizerInputSupportStatus, tuple[OptimizerDiagnostic, ...]]:
    diagnostics: list[OptimizerDiagnostic] = []
    support = OptimizerInputSupportStatus.SUPPORTED

    if request.target_profile is not None and request.target_profile.ph is not None:
        support = OptimizerInputSupportStatus.UNSUPPORTED
        diagnostics.append(
            OptimizerDiagnostic(
                code=OptimizerDiagnosticCode.TARGET_PH_UNSUPPORTED,
                message="Working-water pH optimization is not implemented.",
            )
        )

    for comparison in comparisons:
        if comparison.status is TargetIonComparisonStatus.TARGET_UNSUPPORTED:
            support = OptimizerInputSupportStatus.UNSUPPORTED
            diagnostics.append(
                OptimizerDiagnostic(
                    code=OptimizerDiagnosticCode.TARGET_CRITERION_UNSUPPORTED,
                    message=f"The target criterion for {comparison.ion.value} is unsupported.",
                    ion=comparison.ion,
                )
            )
        elif comparison.status is TargetIonComparisonStatus.ACTUAL_UNKNOWN:
            if support is OptimizerInputSupportStatus.SUPPORTED:
                support = OptimizerInputSupportStatus.INDETERMINATE
            diagnostics.append(
                OptimizerDiagnostic(
                    code=OptimizerDiagnosticCode.REQUIRED_SOURCE_CHEMISTRY_UNKNOWN,
                    message=(
                        f"Starting {comparison.ion.value} concentration is unknown; "
                        "optimization cannot assume zero."
                    ),
                    ion=comparison.ion,
                )
            )

    for constraint in request.material_constraints:
        increment_count = _maximum_increment_count(constraint)
        if increment_count > _MAXIMUM_INCREMENT_COUNT:
            support = OptimizerInputSupportStatus.UNSUPPORTED
            diagnostics.append(
                OptimizerDiagnostic(
                    code=(OptimizerDiagnosticCode.MATERIAL_INCREMENT_RANGE_UNSUPPORTED),
                    message=(
                        f"Material {constraint.material.key} permits "
                        f"{increment_count} dose increments; this solver supports at "
                        f"most {_MAXIMUM_INCREMENT_COUNT} per material."
                    ),
                    material_key=constraint.material.key,
                )
            )

    return support, tuple(diagnostics)


def _maximum_increment_count(constraint: OptimizerMaterialConstraint) -> int:
    maximum = Decimal(str(float(constraint.maximum_mass.to("gram").magnitude)))
    increment = Decimal(
        str(float(constraint.material.normalized_dose_increment.magnitude))
    )
    return int((maximum / increment).to_integral_value(rounding=ROUND_FLOOR))


def _increment_coefficients(
    request: OptimizerRequest,
    comparisons: tuple[TargetIonComparison, ...],
) -> tuple[tuple[float, ...], ...]:
    total_volume = request.total_volume.to("liter")
    by_material = []
    for constraint in request.material_constraints:
        per_increment = {
            contribution.ion: float(
                contribution.concentration.to("milligram / liter").magnitude
            )
            for contribution in calculate_ion_contributions(
                constraint.material.ingredient,
                constraint.material.normalized_dose_increment,
                total_volume,
            )
        }
        by_material.append(
            tuple(per_increment.get(comparison.ion, 0.0) for comparison in comparisons)
        )
    return tuple(by_material)


def _numerical_model_diagnostics(
    request: OptimizerRequest,
    comparisons: tuple[TargetIonComparison, ...],
) -> tuple[OptimizerDiagnostic, ...]:
    diagnostics: list[OptimizerDiagnostic] = []
    coefficients = _increment_coefficients(request, comparisons)
    for material_index, material_coefficients in enumerate(coefficients):
        constraint = request.material_constraints[material_index]
        contributed_ions = {
            entry.ion for entry in constraint.material.ingredient.ion_stoichiometry
        }
        for comparison, coefficient in zip(
            comparisons,
            material_coefficients,
            strict=True,
        ):
            magnitude = fabs(coefficient)
            if comparison.ion in contributed_ions and (
                magnitude <= _SMALLEST_SOLVER_MATRIX_VALUE
                or magnitude >= _LARGEST_SOLVER_MATRIX_VALUE
            ):
                diagnostics.append(
                    OptimizerDiagnostic(
                        code=(
                            OptimizerDiagnosticCode.NUMERICAL_MODEL_RANGE_UNSUPPORTED
                        ),
                        message=(
                            f"The {constraint.material.key} dose-increment effect on "
                            f"{comparison.ion.value} is outside this solver's "
                            "supported numerical coefficient range."
                        ),
                        ion=comparison.ion,
                        material_key=constraint.material.key,
                    )
                )

    for comparison in comparisons:
        assert comparison.actual_concentration is not None
        actual = float(
            comparison.actual_concentration.to("milligram / liter").magnitude
        )
        for bound in (comparison.target_minimum, comparison.target_maximum):
            if bound is not None and fabs(float(bound.magnitude) - actual) >= (
                _LARGEST_SOLVER_BOUND
            ):
                diagnostics.append(
                    OptimizerDiagnostic(
                        code=(
                            OptimizerDiagnosticCode.NUMERICAL_MODEL_RANGE_UNSUPPORTED
                        ),
                        message=(
                            f"The {comparison.ion.value} target difference is outside "
                            "this solver's supported numerical bound range."
                        ),
                        ion=comparison.ion,
                    )
                )
                break

    return tuple(diagnostics)


def _validated_decisions(
    result: _MilpResult,
    *,
    material_count: int,
    variable_count: int,
    maximum_counts: Sequence[int],
    continuous_lower_bounds: Sequence[float],
    continuous_upper_bounds: Sequence[float],
) -> _ValidatedDecisions | None:
    if result.x is None:
        return None
    if len(result.x) != variable_count:
        return None

    counts: list[int] = []
    for raw_count, maximum_count in zip(
        result.x[:material_count],
        maximum_counts,
        strict=True,
    ):
        count_value = float(raw_count)
        if not isfinite(count_value):
            return None
        rounded_count = round(count_value)
        if (
            fabs(count_value - rounded_count) > _INTEGER_ABS_TOLERANCE
            or rounded_count < 0
            or rounded_count > maximum_count
        ):
            return None
        counts.append(rounded_count)

    continuous_values: list[float] = []
    continuous_start = material_count
    continuous_stop = continuous_start + len(continuous_lower_bounds)
    for raw_value, lower, upper in zip(
        result.x[continuous_start:continuous_stop],
        continuous_lower_bounds,
        continuous_upper_bounds,
        strict=True,
    ):
        value = float(raw_value)
        if (
            not isfinite(value)
            or value < lower - _CONTINUOUS_ABS_TOLERANCE
            or value > upper + _CONTINUOUS_ABS_TOLERANCE
        ):
            return None
        continuous_values.append(min(max(value, lower), upper))

    return _ValidatedDecisions(tuple(counts), tuple(continuous_values))


def _objective_from_decisions(
    comparisons: tuple[TargetIonComparison, ...],
    material_coefficients: tuple[tuple[float, ...], ...],
    material_counts: tuple[int, ...],
    continuous_coefficients: tuple[tuple[float, ...], ...],
    continuous_values: tuple[float, ...],
) -> float:
    objective = 0.0
    for comparison_index, comparison in enumerate(comparisons):
        assert comparison.actual_concentration is not None
        predicted = (
            float(comparison.actual_concentration.to("milligram / liter").magnitude)
            + sum(
                count * material_coefficients[material_index][comparison_index]
                for material_index, count in enumerate(material_counts)
            )
            + sum(
                value * continuous_coefficients[continuous_index][comparison_index]
                for continuous_index, value in enumerate(continuous_values)
            )
        )
        if comparison.target_minimum is not None:
            minimum = float(comparison.target_minimum.magnitude)
            objective += max(0.0, minimum - predicted)
        if comparison.target_maximum is not None:
            maximum = float(comparison.target_maximum.magnitude)
            objective += max(0.0, predicted - maximum)
    return objective


def _solve_increment_counts(
    request: OptimizerRequest,
    comparisons: tuple[TargetIonComparison, ...],
    *,
    continuous_coefficients: tuple[tuple[float, ...], ...] = (),
    continuous_lower_bounds: tuple[float, ...] = (),
    continuous_upper_bounds: tuple[float, ...] = (),
) -> tuple[_ValidatedDecisions | None, OptimizerSolverReport]:
    material_count = len(request.material_constraints)
    comparison_count = len(comparisons)
    continuous_count = len(continuous_coefficients)
    if not (
        continuous_count == len(continuous_lower_bounds) == len(continuous_upper_bounds)
    ):
        raise ValueError("Continuous solver inputs must have matching lengths.")
    if comparison_count == 0:
        return (
            _ValidatedDecisions(
                material_counts=(0,) * material_count,
                continuous_values=continuous_lower_bounds,
            ),
            OptimizerSolverReport(
                solver="engine",
                method="no_target_zero_addition",
                success=True,
                status_code=0,
                message="No numeric ion targets were supplied; no additions selected.",
                solver_reported_primary_objective_mg_per_liter=0.0,
                primary_objective_mg_per_liter=0.0,
                secondary_objective_grams=0.0,
                primary_objective_tolerance_mg_per_liter=(
                    _PRIMARY_OBJECTIVE_TOLERANCE_MG_PER_LITER
                ),
                mip_relative_gap=0.0,
            ),
        )

    material_coefficients = _increment_coefficients(request, comparisons)
    decision_count = material_count + continuous_count
    variable_count = decision_count + 2 * comparison_count
    primary_objective = [0.0] * decision_count + [1.0] * (2 * comparison_count)
    lower_bounds = (
        [0.0] * material_count
        + list(continuous_lower_bounds)
        + [0.0] * (2 * comparison_count)
    )
    maximum_counts = tuple(
        _maximum_increment_count(constraint)
        for constraint in request.material_constraints
    )
    upper_bounds = (
        [float(count) for count in maximum_counts]
        + list(continuous_upper_bounds)
        + [inf] * (2 * comparison_count)
    )
    integrality = [1] * material_count + [0] * (continuous_count + 2 * comparison_count)
    rows: list[list[float]] = []
    row_upper_bounds: list[float] = []

    for comparison_index, comparison in enumerate(comparisons):
        lower_slack_index = decision_count + 2 * comparison_index
        upper_slack_index = lower_slack_index + 1
        assert comparison.actual_concentration is not None
        actual = float(
            comparison.actual_concentration.to("milligram / liter").magnitude
        )
        decision_terms = [
            material_coefficients[material_index][comparison_index]
            for material_index in range(material_count)
        ] + [
            continuous_coefficients[continuous_index][comparison_index]
            for continuous_index in range(continuous_count)
        ]

        if comparison.target_minimum is not None:
            minimum = float(comparison.target_minimum.magnitude)
            row = [-term for term in decision_terms] + [0.0] * (2 * comparison_count)
            row[lower_slack_index] = -1.0
            rows.append(row)
            row_upper_bounds.append(actual - minimum)
        else:
            upper_bounds[lower_slack_index] = 0.0

        if comparison.target_maximum is not None:
            maximum = float(comparison.target_maximum.magnitude)
            row = decision_terms + [0.0] * (2 * comparison_count)
            row[upper_slack_index] = -1.0
            rows.append(row)
            row_upper_bounds.append(maximum - actual)
        else:
            upper_bounds[upper_slack_index] = 0.0

    primary = cast(
        _MilpResult,
        milp(
            c=primary_objective,
            integrality=integrality,
            bounds=Bounds(lower_bounds, upper_bounds),
            constraints=LinearConstraint(
                rows,
                [-inf] * len(rows),
                row_upper_bounds,
            ),
            options={"mip_rel_gap": _MIP_RELATIVE_GAP},
        ),
    )
    if not primary.success or primary.fun is None or primary.x is None:
        return None, _solver_report(
            primary,
            solver_reported_primary_objective=(
                None if primary.fun is None else float(primary.fun)
            ),
            primary_objective=None,
            secondary_objective=None,
        )
    raw_primary_objective = float(primary.fun)
    if not isfinite(raw_primary_objective) or raw_primary_objective < 0.0:
        return None, _rejected_solver_report(
            primary,
            message="Solver returned a non-finite or negative primary objective.",
            solver_reported_primary_objective=raw_primary_objective,
        )
    primary_decisions = _validated_decisions(
        primary,
        material_count=material_count,
        variable_count=variable_count,
        maximum_counts=maximum_counts,
        continuous_lower_bounds=continuous_lower_bounds,
        continuous_upper_bounds=continuous_upper_bounds,
    )
    if primary_decisions is None:
        return None, _rejected_solver_report(
            primary,
            message="Solver returned invalid material increment counts.",
            solver_reported_primary_objective=raw_primary_objective,
        )
    primary_recomputed_objective = _objective_from_decisions(
        comparisons,
        material_coefficients,
        primary_decisions.material_counts,
        continuous_coefficients,
        primary_decisions.continuous_values,
    )

    secondary_objective = [
        float(constraint.material.normalized_dose_increment.magnitude)
        for constraint in request.material_constraints
    ] + [0.0] * (continuous_count + 2 * comparison_count)
    secondary = cast(
        _MilpResult,
        milp(
            c=secondary_objective,
            integrality=integrality,
            bounds=Bounds(lower_bounds, upper_bounds),
            constraints=(
                LinearConstraint(
                    rows,
                    [-inf] * len(rows),
                    row_upper_bounds,
                ),
                LinearConstraint(
                    [primary_objective],
                    [-inf],
                    [
                        primary_recomputed_objective
                        + _PRIMARY_OBJECTIVE_TOLERANCE_MG_PER_LITER
                    ],
                ),
            ),
            options={"mip_rel_gap": _MIP_RELATIVE_GAP},
        ),
    )
    secondary_fun = secondary.fun
    if not secondary.success or secondary_fun is None or secondary.x is None:
        return None, _solver_report(
            secondary,
            solver_reported_primary_objective=raw_primary_objective,
            primary_objective=primary_recomputed_objective,
            secondary_objective=None,
        )
    if not isfinite(secondary_fun) or secondary_fun < 0:
        return None, _rejected_solver_report(
            secondary,
            message="Solver returned a non-finite or negative secondary objective.",
            solver_reported_primary_objective=raw_primary_objective,
            primary_objective=primary_recomputed_objective,
        )
    secondary_decisions = _validated_decisions(
        secondary,
        material_count=material_count,
        variable_count=variable_count,
        maximum_counts=maximum_counts,
        continuous_lower_bounds=continuous_lower_bounds,
        continuous_upper_bounds=continuous_upper_bounds,
    )
    if secondary_decisions is None:
        return None, _rejected_solver_report(
            secondary,
            message="Solver returned invalid secondary material increment counts.",
            solver_reported_primary_objective=raw_primary_objective,
            primary_objective=primary_recomputed_objective,
        )
    secondary_recomputed_objective = _objective_from_decisions(
        comparisons,
        material_coefficients,
        secondary_decisions.material_counts,
        continuous_coefficients,
        secondary_decisions.continuous_values,
    )
    if secondary_recomputed_objective > (
        primary_recomputed_objective + _PRIMARY_OBJECTIVE_TOLERANCE_MG_PER_LITER
    ):
        return None, _rejected_solver_report(
            secondary,
            message="Secondary solve violated the primary-objective tolerance.",
            solver_reported_primary_objective=raw_primary_objective,
            primary_objective=secondary_recomputed_objective,
        )

    selected_secondary = sum(
        count * increment
        for count, increment in zip(
            secondary_decisions.material_counts,
            secondary_objective[:material_count],
            strict=True,
        )
    )
    return secondary_decisions, _solver_report(
        secondary,
        solver_reported_primary_objective=raw_primary_objective,
        primary_objective=secondary_recomputed_objective,
        secondary_objective=selected_secondary,
    )


def _target_deviation_sum(comparison: TargetProfileComparison | None) -> float:
    if comparison is None:
        return 0.0
    return sum(
        fabs(float(ion.deviation.to("milligram / liter").magnitude))
        for ion in comparison.ion_comparisons
        if ion.deviation is not None
    )


def _material_additions(
    request: OptimizerRequest,
    material_counts: tuple[int, ...],
) -> tuple[OptimizerMaterialAddition, ...]:
    additions: list[OptimizerMaterialAddition] = []
    for constraint, increment_count in zip(
        request.material_constraints,
        material_counts,
        strict=True,
    ):
        if increment_count == 0:
            continue
        increment_grams = float(constraint.material.normalized_dose_increment.magnitude)
        measured = Q_(increment_count * increment_grams, "gram")
        addition = constraint.material.treatment_addition(measured)
        additions.append(
            OptimizerMaterialAddition(
                constraint=constraint,
                measured_mass=measured,
                active_chemical_mass=measured,
                treatment_addition=addition,
            )
        )
    return tuple(additions)


def _build_plan(
    request: OptimizerRequest,
    *,
    source_volumes: tuple[OptimizerSourceVolume, ...],
    material_counts: tuple[int, ...],
    solver_report: OptimizerSolverReport,
    plan_id: str,
    strategy: OptimizerStrategy,
    summary_label: str,
) -> tuple[OptimizerPlan | None, OptimizerDiagnostic | None]:
    additions = _material_additions(request, material_counts)
    sources = tuple(
        ForwardWaterSource(entry.source.source_profile, entry.volume)
        for entry in source_volumes
    )
    calculation = calculate_forward_water(
        sources,
        source_resolution_policy=request.source_resolution_policy,
        treatment_additions=tuple(
            addition.treatment_addition for addition in additions
        ),
        target_profile=request.target_profile,
    )
    final_comparison = calculation.final_target_comparison
    final_objective = _target_deviation_sum(final_comparison)
    expected_objective = solver_report.primary_objective_mg_per_liter
    if expected_objective is None or not isclose(
        final_objective,
        expected_objective,
        rel_tol=_POSTVALIDATION_REL_TOLERANCE,
        abs_tol=_POSTVALIDATION_ABS_TOLERANCE_MG_PER_LITER,
    ):
        return None, OptimizerDiagnostic(
            code=OptimizerDiagnosticCode.SOLVER_POSTVALIDATION_FAILED,
            message=(
                "The ordinary forward calculation did not reproduce the solver's "
                "predicted target-deviation objective."
            ),
        )

    if (
        final_comparison is None
        or final_comparison.status is TargetProfileComparisonStatus.NO_CRITERIA
    ):
        target_fit = OptimizerTargetFitStatus.NOT_EVALUATED
    elif final_comparison.status is TargetProfileComparisonStatus.SATISFIED:
        target_fit = OptimizerTargetFitStatus.WITHIN_TARGET
    elif final_comparison.status is TargetProfileComparisonStatus.NOT_SATISFIED:
        target_fit = OptimizerTargetFitStatus.OUTSIDE_TARGET
    else:
        target_fit = OptimizerTargetFitStatus.INDETERMINATE

    plan_diagnostics: list[OptimizerDiagnostic] = []
    if target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET:
        plan_diagnostics.append(
            OptimizerDiagnostic(
                code=OptimizerDiagnosticCode.TARGET_NOT_MET,
                message=(
                    "The closest plan under the declared material limits and dose "
                    "increments remains outside one or more target criteria."
                ),
            )
        )

    if target_fit is OptimizerTargetFitStatus.NOT_EVALUATED:
        summary = f"{summary_label}: no numeric ion targets were supplied."
    elif target_fit is OptimizerTargetFitStatus.WITHIN_TARGET:
        summary = f"{summary_label} is within all supported target criteria."
    else:
        summary = f"{summary_label} under the declared practical constraints."

    return (
        OptimizerPlan(
            plan_id=plan_id,
            strategy=strategy,
            source_volumes=source_volumes,
            material_additions=additions,
            calculation=calculation,
            target_comparison=final_comparison,
            input_support=OptimizerInputSupportStatus.SUPPORTED,
            feasibility=OptimizerFeasibilityStatus.FEASIBLE,
            target_fit=target_fit,
            practicality=OptimizerPracticalityStatus.PRACTICAL,
            solver_report=solver_report,
            diagnostics=tuple(plan_diagnostics),
            summary=summary,
        ),
        None,
    )


def _proportional_dilution_bounds(
    request: OptimizerRequest,
) -> tuple[float, float] | None:
    assert request.diluent_source is not None
    total_liters = float(request.total_volume.to("liter").magnitude)
    current_liters = tuple(
        float(source.current_volume.to("liter").magnitude) for source in request.sources
    )
    current_total = fsum(current_liters)
    maximum_non_diluent = total_liters
    for source, current in zip(request.sources, current_liters, strict=True):
        if current == 0.0:
            continue
        proportion = current / current_total
        maximum = float(source.maximum_volume.to("liter").magnitude)
        maximum_non_diluent = min(maximum_non_diluent, maximum / proportion)

    diluent_maximum = min(
        total_liters,
        float(request.diluent_source.maximum_volume.to("liter").magnitude),
    )
    diluent_minimum = max(0.0, total_liters - maximum_non_diluent)
    if diluent_minimum > diluent_maximum + _CONTINUOUS_ABS_TOLERANCE:
        return None
    return min(diluent_minimum, diluent_maximum), diluent_maximum


def _proportional_source_volumes(
    request: OptimizerRequest,
    diluent_liters: float,
) -> tuple[OptimizerSourceVolume, ...]:
    assert request.diluent_source is not None
    total_liters = float(request.total_volume.to("liter").magnitude)
    current_liters = tuple(
        float(source.current_volume.to("liter").magnitude) for source in request.sources
    )
    current_total = fsum(current_liters)
    non_diluent_liters = total_liters - diluent_liters
    volumes = tuple(
        OptimizerSourceVolume(
            source=source,
            volume=Q_(non_diluent_liters * current / current_total, "liter"),
        )
        for source, current in zip(request.sources, current_liters, strict=True)
    )
    return volumes + (
        OptimizerSourceVolume(
            source=request.diluent_source,
            volume=Q_(diluent_liters, "liter"),
        ),
    )


def _dilution_coefficients(
    request: OptimizerRequest,
    comparisons: tuple[TargetIonComparison, ...],
) -> tuple[tuple[float, ...] | None, tuple[OptimizerDiagnostic, ...]]:
    assert request.diluent_source is not None
    resolution = resolve_source_profile(
        request.diluent_source.source_profile,
        policy=request.source_resolution_policy,
    )
    total_liters = float(request.total_volume.to("liter").magnitude)
    coefficients: list[float] = []
    diagnostics: list[OptimizerDiagnostic] = []
    for comparison in comparisons:
        if comparison.status is TargetIonComparisonStatus.TARGET_UNSUPPORTED:
            continue
        assert comparison.actual_concentration is not None
        diluent_concentration = resolution.state.concentration_for(comparison.ion)
        if diluent_concentration is None:
            diagnostics.append(
                OptimizerDiagnostic(
                    code=(OptimizerDiagnosticCode.REQUIRED_DILUENT_CHEMISTRY_UNKNOWN),
                    message=(
                        f"Diluent {request.diluent_source.source_profile.name} has "
                        f"unknown {comparison.ion.value} concentration; optimization "
                        "cannot assume zero."
                    ),
                    ion=comparison.ion,
                    source_index=len(request.sources),
                    source_name=request.diluent_source.source_profile.name,
                )
            )
            continue
        baseline = float(
            comparison.actual_concentration.to("milligram / liter").magnitude
        )
        diluent = float(diluent_concentration.to("milligram / liter").magnitude)
        coefficient = (diluent - baseline) / total_liters
        magnitude = fabs(coefficient)
        if magnitude != 0.0 and (
            magnitude <= _SMALLEST_SOLVER_MATRIX_VALUE
            or magnitude >= _LARGEST_SOLVER_MATRIX_VALUE
        ):
            diagnostics.append(
                OptimizerDiagnostic(
                    code=OptimizerDiagnosticCode.NUMERICAL_MODEL_RANGE_UNSUPPORTED,
                    message=(
                        f"The diluent effect on {comparison.ion.value} is outside "
                        "this solver's supported numerical coefficient range."
                    ),
                    ion=comparison.ion,
                    source_index=len(request.sources),
                    source_name=request.diluent_source.source_profile.name,
                )
            )
            continue
        coefficients.append(coefficient)

    if diagnostics:
        return None, tuple(diagnostics)
    return tuple(coefficients), ()


def _plans_operationally_equivalent(
    left: OptimizerPlan,
    right: OptimizerPlan,
) -> bool:
    if len(left.source_volumes) != len(right.source_volumes) or len(
        left.material_additions
    ) != len(right.material_additions):
        return False
    volumes_equal = all(
        left_entry.source is right_entry.source
        and isclose(
            float(left_entry.volume.to("liter").magnitude),
            float(right_entry.volume.to("liter").magnitude),
            rel_tol=0.0,
            abs_tol=_CONTINUOUS_ABS_TOLERANCE,
        )
        for left_entry, right_entry in zip(
            left.source_volumes,
            right.source_volumes,
            strict=True,
        )
    )
    additions_equal = all(
        left_entry.constraint.material.key == right_entry.constraint.material.key
        and isclose(
            float(left_entry.measured_mass.to("gram").magnitude),
            float(right_entry.measured_mass.to("gram").magnitude),
            rel_tol=0.0,
            abs_tol=0.0,
        )
        for left_entry, right_entry in zip(
            left.material_additions,
            right.material_additions,
            strict=True,
        )
    )
    return volumes_equal and additions_equal


def _solver_failure_result(
    request: OptimizerRequest,
    solver_report: OptimizerSolverReport,
) -> OptimizerResult:
    failure = OptimizerDiagnostic(
        code=OptimizerDiagnosticCode.SOLVER_FAILED,
        message=solver_report.message,
    )
    feasibility = (
        OptimizerFeasibilityStatus.INFEASIBLE
        if solver_report.status_code == 2
        else OptimizerFeasibilityStatus.INDETERMINATE
    )
    return OptimizerResult(
        request=request,
        input_support=OptimizerInputSupportStatus.SUPPORTED,
        feasibility=feasibility,
        plans=(),
        diagnostics=(failure,),
        solver_report=solver_report,
    )


def _postvalidation_failure_result(
    request: OptimizerRequest,
    solver_report: OptimizerSolverReport,
    diagnostic: OptimizerDiagnostic,
) -> OptimizerResult:
    return OptimizerResult(
        request=request,
        input_support=OptimizerInputSupportStatus.SUPPORTED,
        feasibility=OptimizerFeasibilityStatus.INDETERMINATE,
        plans=(),
        diagnostics=(diagnostic,),
        solver_report=solver_report,
    )


def _optimize_proportional_dilution(request: OptimizerRequest) -> OptimizerResult:
    bounds = _proportional_dilution_bounds(request)
    if bounds is None:
        diagnostic = OptimizerDiagnostic(
            code=OptimizerDiagnosticCode.SOURCE_VOLUME_CONSTRAINTS_INFEASIBLE,
            message=(
                "The proportional source limits and diluent availability cannot "
                "supply the requested total volume."
            ),
        )
        return OptimizerResult(
            request=request,
            input_support=OptimizerInputSupportStatus.SUPPORTED,
            feasibility=OptimizerFeasibilityStatus.INFEASIBLE,
            plans=(),
            diagnostics=(diagnostic,),
            solver_report=None,
        )
    diluent_minimum, diluent_maximum = bounds
    if diluent_maximum >= _LARGEST_SOLVER_BOUND:
        return _unsupported_result(
            request,
            support=OptimizerInputSupportStatus.UNSUPPORTED,
            diagnostics=(
                OptimizerDiagnostic(
                    code=(OptimizerDiagnosticCode.NUMERICAL_MODEL_RANGE_UNSUPPORTED),
                    message=(
                        "The diluent-volume bound is outside this solver's supported "
                        "numerical range."
                    ),
                ),
            ),
        )

    no_dilution_source_volumes = _proportional_source_volumes(request, 0.0)
    initial = calculate_forward_water(
        tuple(
            ForwardWaterSource(entry.source.source_profile, entry.volume)
            for entry in no_dilution_source_volumes[:-1]
        ),
        source_resolution_policy=request.source_resolution_policy,
        target_profile=request.target_profile,
    )
    comparison = initial.final_target_comparison
    comparisons = () if comparison is None else comparison.ion_comparisons
    support, diagnostics = _input_diagnostics(request, comparisons)
    if support is not OptimizerInputSupportStatus.SUPPORTED:
        return _unsupported_result(
            request,
            support=support,
            diagnostics=diagnostics,
        )
    material_diagnostics = _numerical_model_diagnostics(request, comparisons)
    if material_diagnostics:
        return _unsupported_result(
            request,
            support=OptimizerInputSupportStatus.UNSUPPORTED,
            diagnostics=material_diagnostics,
        )
    dilution_coefficients, dilution_diagnostics = _dilution_coefficients(
        request,
        comparisons,
    )
    if dilution_coefficients is None:
        support = (
            OptimizerInputSupportStatus.INDETERMINATE
            if all(
                diagnostic.code
                is OptimizerDiagnosticCode.REQUIRED_DILUENT_CHEMISTRY_UNKNOWN
                for diagnostic in dilution_diagnostics
            )
            else OptimizerInputSupportStatus.UNSUPPORTED
        )
        return _unsupported_result(
            request,
            support=support,
            diagnostics=dilution_diagnostics,
        )

    decisions, solver_report = _solve_increment_counts(
        request,
        comparisons,
        continuous_coefficients=(dilution_coefficients,),
        continuous_lower_bounds=(diluent_minimum,),
        continuous_upper_bounds=(diluent_maximum,),
    )
    if decisions is None:
        return _solver_failure_result(request, solver_report)
    diluent_liters = decisions.continuous_values[0]
    primary_plan, postvalidation_diagnostic = _build_plan(
        request,
        source_volumes=_proportional_source_volumes(request, diluent_liters),
        material_counts=decisions.material_counts,
        solver_report=solver_report,
        plan_id="closest_absolute_mg_per_liter_v1:1",
        strategy=OptimizerStrategy.CLOSEST_ABSOLUTE_MG_PER_LITER,
        summary_label="Closest absolute mg/L proportional-dilution plan",
    )
    if primary_plan is None:
        assert postvalidation_diagnostic is not None
        return _postvalidation_failure_result(
            request,
            solver_report,
            postvalidation_diagnostic,
        )

    plans = [primary_plan]
    result_diagnostics: list[OptimizerDiagnostic] = []
    if request.request_no_dilution_plan:
        if diluent_minimum > _CONTINUOUS_ABS_TOLERANCE:
            result_diagnostics.append(
                OptimizerDiagnostic(
                    code=OptimizerDiagnosticCode.NO_DILUTION_PLAN_INFEASIBLE,
                    message=(
                        "A no-dilution plan cannot supply the requested total volume "
                        "within the declared source limits."
                    ),
                )
            )
        else:
            no_dilution_decisions, no_dilution_report = _solve_increment_counts(
                request,
                comparisons,
                continuous_coefficients=(dilution_coefficients,),
                continuous_lower_bounds=(0.0,),
                continuous_upper_bounds=(0.0,),
            )
            if no_dilution_decisions is None:
                return _solver_failure_result(request, no_dilution_report)
            no_dilution_plan, postvalidation_diagnostic = _build_plan(
                request,
                source_volumes=_proportional_source_volumes(request, 0.0),
                material_counts=no_dilution_decisions.material_counts,
                solver_report=no_dilution_report,
                plan_id="no_dilution_closest_absolute_mg_per_liter_v1:2",
                strategy=(OptimizerStrategy.NO_DILUTION_CLOSEST_ABSOLUTE_MG_PER_LITER),
                summary_label="Best-effort no-dilution plan",
            )
            if no_dilution_plan is None:
                assert postvalidation_diagnostic is not None
                return _postvalidation_failure_result(
                    request,
                    no_dilution_report,
                    postvalidation_diagnostic,
                )
            if not _plans_operationally_equivalent(primary_plan, no_dilution_plan):
                plans.append(no_dilution_plan)

    return OptimizerResult(
        request=request,
        input_support=OptimizerInputSupportStatus.SUPPORTED,
        feasibility=OptimizerFeasibilityStatus.FEASIBLE,
        plans=tuple(plans),
        diagnostics=tuple(result_diagnostics),
        solver_report=solver_report,
    )


def optimize_treatment(request: OptimizerRequest) -> OptimizerResult:
    """Return one bounded practical plan for the implemented fixed-blend policy."""
    if request.blend_policy is OptimizerBlendPolicy.PROPORTIONAL_DILUTION:
        return _optimize_proportional_dilution(request)
    if request.blend_policy is not OptimizerBlendPolicy.FIXED:
        return _unsupported_result(
            request,
            support=OptimizerInputSupportStatus.UNSUPPORTED,
            diagnostics=(
                OptimizerDiagnostic(
                    code=OptimizerDiagnosticCode.BLEND_POLICY_NOT_IMPLEMENTED,
                    message=(
                        f"Blend policy {request.blend_policy.value} is not implemented "
                        "by the first solver slice."
                    ),
                ),
            ),
        )

    sources = tuple(
        ForwardWaterSource(source.source_profile, source.current_volume)
        for source in request.sources
    )
    initial = calculate_forward_water(
        sources,
        source_resolution_policy=request.source_resolution_policy,
        target_profile=request.target_profile,
    )
    comparison = initial.final_target_comparison
    comparisons = () if comparison is None else comparison.ion_comparisons
    support, diagnostics = _input_diagnostics(request, comparisons)
    if support is not OptimizerInputSupportStatus.SUPPORTED:
        return _unsupported_result(
            request,
            support=support,
            diagnostics=diagnostics,
        )
    numerical_diagnostics = _numerical_model_diagnostics(request, comparisons)
    if numerical_diagnostics:
        return _unsupported_result(
            request,
            support=OptimizerInputSupportStatus.UNSUPPORTED,
            diagnostics=numerical_diagnostics,
        )

    decisions, solver_report = _solve_increment_counts(request, comparisons)
    if decisions is None:
        return _solver_failure_result(request, solver_report)

    source_volumes = tuple(
        OptimizerSourceVolume(
            source=source,
            volume=Q_(
                float(source.current_volume.to("liter").magnitude),
                "liter",
            ),
        )
        for source in request.sources
    )
    plan, postvalidation_diagnostic = _build_plan(
        request,
        source_volumes=source_volumes,
        material_counts=decisions.material_counts,
        solver_report=solver_report,
        plan_id="closest_absolute_mg_per_liter_v1:1",
        strategy=OptimizerStrategy.CLOSEST_ABSOLUTE_MG_PER_LITER,
        summary_label="Closest absolute mg/L plan",
    )
    if plan is None:
        assert postvalidation_diagnostic is not None
        return _postvalidation_failure_result(
            request,
            solver_report,
            postvalidation_diagnostic,
        )
    return OptimizerResult(
        request=request,
        input_support=OptimizerInputSupportStatus.SUPPORTED,
        feasibility=OptimizerFeasibilityStatus.FEASIBLE,
        plans=(plan,),
        diagnostics=(),
        solver_report=solver_report,
    )
