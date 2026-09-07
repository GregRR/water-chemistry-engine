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
from decimal import ROUND_FLOOR, Decimal
from math import fabs, inf, isclose, isfinite
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
_INTEGER_ABS_TOLERANCE = 1e-7
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


def _validated_increment_counts(
    result: _MilpResult,
    *,
    material_count: int,
    maximum_counts: Sequence[int],
) -> tuple[int, ...] | None:
    if result.x is None:
        return None
    if len(result.x) < material_count:
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
    return tuple(counts)


def _objective_from_counts(
    comparisons: tuple[TargetIonComparison, ...],
    coefficients: tuple[tuple[float, ...], ...],
    counts: tuple[int, ...],
) -> float:
    objective = 0.0
    for comparison_index, comparison in enumerate(comparisons):
        assert comparison.actual_concentration is not None
        predicted = float(
            comparison.actual_concentration.to("milligram / liter").magnitude
        ) + sum(
            count * coefficients[material_index][comparison_index]
            for material_index, count in enumerate(counts)
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
) -> tuple[tuple[int, ...] | None, OptimizerSolverReport]:
    material_count = len(request.material_constraints)
    comparison_count = len(comparisons)
    if comparison_count == 0:
        return (
            (0,) * material_count,
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

    coefficients = _increment_coefficients(request, comparisons)
    variable_count = material_count + 2 * comparison_count
    primary_objective = [0.0] * material_count + [1.0] * (2 * comparison_count)
    lower_bounds = [0.0] * variable_count
    maximum_counts = tuple(
        _maximum_increment_count(constraint)
        for constraint in request.material_constraints
    )
    upper_bounds = [float(count) for count in maximum_counts] + [inf] * (
        2 * comparison_count
    )
    integrality = [1] * material_count + [0] * (2 * comparison_count)
    rows: list[list[float]] = []
    row_upper_bounds: list[float] = []

    for comparison_index, comparison in enumerate(comparisons):
        lower_slack_index = material_count + 2 * comparison_index
        upper_slack_index = lower_slack_index + 1
        assert comparison.actual_concentration is not None
        actual = float(
            comparison.actual_concentration.to("milligram / liter").magnitude
        )
        material_terms = [
            coefficients[material_index][comparison_index]
            for material_index in range(material_count)
        ]

        if comparison.target_minimum is not None:
            minimum = float(comparison.target_minimum.magnitude)
            row = [-term for term in material_terms] + [0.0] * (2 * comparison_count)
            row[lower_slack_index] = -1.0
            rows.append(row)
            row_upper_bounds.append(actual - minimum)
        else:
            upper_bounds[lower_slack_index] = 0.0

        if comparison.target_maximum is not None:
            maximum = float(comparison.target_maximum.magnitude)
            row = material_terms + [0.0] * (2 * comparison_count)
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
    primary_counts = _validated_increment_counts(
        primary,
        material_count=material_count,
        maximum_counts=maximum_counts,
    )
    if primary_counts is None:
        return None, _rejected_solver_report(
            primary,
            message="Solver returned invalid material increment counts.",
            solver_reported_primary_objective=raw_primary_objective,
        )
    primary_recomputed_objective = _objective_from_counts(
        comparisons,
        coefficients,
        primary_counts,
    )

    secondary_objective = [
        float(constraint.material.normalized_dose_increment.magnitude)
        for constraint in request.material_constraints
    ] + [0.0] * (2 * comparison_count)
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
    secondary_counts = _validated_increment_counts(
        secondary,
        material_count=material_count,
        maximum_counts=maximum_counts,
    )
    if secondary_counts is None:
        return None, _rejected_solver_report(
            secondary,
            message="Solver returned invalid secondary material increment counts.",
            solver_reported_primary_objective=raw_primary_objective,
            primary_objective=primary_recomputed_objective,
        )
    secondary_recomputed_objective = _objective_from_counts(
        comparisons,
        coefficients,
        secondary_counts,
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

    counts = secondary_counts

    selected_secondary = sum(
        count * increment
        for count, increment in zip(
            counts,
            secondary_objective[:material_count],
            strict=True,
        )
    )
    return counts, _solver_report(
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


def optimize_treatment(request: OptimizerRequest) -> OptimizerResult:
    """Return one bounded practical plan for the implemented fixed-blend policy."""
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

    increment_counts, solver_report = _solve_increment_counts(request, comparisons)
    if increment_counts is None:
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

    additions: list[OptimizerMaterialAddition] = []
    for constraint, increment_count in zip(
        request.material_constraints,
        increment_counts,
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
        diagnostic = OptimizerDiagnostic(
            code=OptimizerDiagnosticCode.SOLVER_POSTVALIDATION_FAILED,
            message=(
                "The ordinary forward calculation did not reproduce the solver's "
                "predicted target-deviation objective."
            ),
        )
        return OptimizerResult(
            request=request,
            input_support=OptimizerInputSupportStatus.SUPPORTED,
            feasibility=OptimizerFeasibilityStatus.INDETERMINATE,
            plans=(),
            diagnostics=(diagnostic,),
            solver_report=solver_report,
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
    if target_fit is OptimizerTargetFitStatus.NOT_EVALUATED:
        summary = "No numeric ion targets were supplied; no additions selected."
    elif target_fit is OptimizerTargetFitStatus.WITHIN_TARGET:
        summary = "Closest absolute mg/L plan is within all supported target criteria."
    else:
        summary = "Closest absolute mg/L plan under the declared practical constraints."
    plan = OptimizerPlan(
        plan_id="closest_absolute_mg_per_liter_v1:1",
        strategy=OptimizerStrategy.CLOSEST_ABSOLUTE_MG_PER_LITER,
        source_volumes=source_volumes,
        material_additions=tuple(additions),
        calculation=calculation,
        target_comparison=final_comparison,
        input_support=OptimizerInputSupportStatus.SUPPORTED,
        feasibility=OptimizerFeasibilityStatus.FEASIBLE,
        target_fit=target_fit,
        practicality=OptimizerPracticalityStatus.PRACTICAL,
        solver_report=solver_report,
        diagnostics=tuple(plan_diagnostics),
        summary=summary,
    )
    return OptimizerResult(
        request=request,
        input_support=OptimizerInputSupportStatus.SUPPORTED,
        feasibility=OptimizerFeasibilityStatus.FEASIBLE,
        plans=(plan,),
        diagnostics=(),
        solver_report=solver_report,
    )
