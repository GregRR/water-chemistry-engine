from itertools import product
from types import SimpleNamespace

import pytest
from fermunits import Q_, PHValue

from water_chemistry_engine import optimizer_solver
from water_chemistry_engine.concentrations import (
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_chemistry_engine.forward_calculator import (
    ForwardWaterSource,
    calculate_forward_water,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.optimization import (
    OptimizerBlendPolicy,
    OptimizerDiagnosticCode,
    OptimizerFeasibilityStatus,
    OptimizerInputSupportStatus,
    OptimizerMaterialConstraint,
    OptimizerPracticalityStatus,
    OptimizerRequest,
    OptimizerSource,
    OptimizerStrategy,
    OptimizerTargetFitStatus,
)
from water_chemistry_engine.optimizer_solver import optimize_treatment
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_application import TreatmentAddition
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    GYPSUM,
    POTASSIUM_CHLORIDE,
)
from water_chemistry_engine.treatment_materials import ExactMassDosedTreatmentMaterial

_POLICY = SourceResolutionPolicy(allow_exact_range_midpoints=False)
_GYPSUM_MOLAR_MASS_G_PER_MOL = 172.164
_CALCIUM_MOLAR_MASS_G_PER_MOL = 40.078
_SULFATE_MOLAR_MASS_G_PER_MOL = 96.056
_CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS = (
    _CALCIUM_MOLAR_MASS_G_PER_MOL / _GYPSUM_MOLAR_MASS_G_PER_MOL * 100.0
)
_SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TWENTY_LITERS = (
    _SULFATE_MOLAR_MASS_G_PER_MOL / _GYPSUM_MOLAR_MASS_G_PER_MOL * 50.0
)
_SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS = (
    2.0 * _SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TWENTY_LITERS
)


def _source(*, volume_liters: float = 10.0, **values: float) -> OptimizerSource:
    profile = SourceWaterProfile(
        name="Source",
        concentrations=tuple(
            IonConcentration.mg_per_liter(Ion(name), value)
            for name, value in values.items()
        ),
    )
    return OptimizerSource(
        profile,
        Q_(volume_liters, "liter"),
        Q_(volume_liters, "liter"),
    )


def _available_source(
    name: str,
    *,
    current_liters: float,
    maximum_liters: float,
    **values: float,
) -> OptimizerSource:
    return OptimizerSource(
        SourceWaterProfile(
            name=name,
            concentrations=tuple(
                IonConcentration.mg_per_liter(Ion(ion), value)
                for ion, value in values.items()
            ),
        ),
        Q_(current_liters, "liter"),
        Q_(maximum_liters, "liter"),
    )


def _gypsum_constraint(
    *, increment_grams: float = 0.1, maximum_grams: float = 2.0
) -> OptimizerMaterialConstraint:
    material = ExactMassDosedTreatmentMaterial(
        "gypsum",
        "Gypsum",
        GYPSUM,
        Q_(increment_grams, "gram"),
    )
    return OptimizerMaterialConstraint(material, Q_(maximum_grams, "gram"))


def _target(calcium_mg_per_liter: float) -> TargetWaterProfile:
    return TargetWaterProfile(
        "Calcium target",
        (IonConcentration.mg_per_liter(Ion.CALCIUM, calcium_mg_per_liter),),
    )


def _fixed_request(
    *,
    source: OptimizerSource,
    target: TargetWaterProfile | None,
    constraints: tuple[OptimizerMaterialConstraint, ...],
) -> OptimizerRequest:
    return OptimizerRequest(
        total_volume=source.current_volume,
        sources=(source,),
        material_constraints=constraints,
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.FIXED,
        target_profile=target,
    )


def test_fixed_optimizer_selects_analytically_expected_gypsum_dose() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(_CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.SUPPORTED
    assert result.feasibility is OptimizerFeasibilityStatus.FEASIBLE
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert plan.strategy is OptimizerStrategy.CLOSEST_ABSOLUTE_MG_PER_LITER
    assert plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert plan.practicality is OptimizerPracticalityStatus.PRACTICAL
    assert len(plan.material_additions) == 1
    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(1.0)
    calcium = plan.calculation.final_state.concentration_for(Ion.CALCIUM)
    assert calcium is not None
    assert float(calcium.to("milligram / liter").magnitude) == pytest.approx(
        _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS
    )
    assert plan.solver_report.primary_objective_mg_per_liter == pytest.approx(0.0)
    assert (
        plan.solver_report.solver_reported_primary_objective_mg_per_liter
        == pytest.approx(0.0)
    )
    assert plan.solver_report.secondary_objective_grams == pytest.approx(1.0)
    assert plan.solver_report.mip_relative_gap == pytest.approx(0.0)
    assert result.solver_report is plan.solver_report


def test_dose_increment_is_an_integral_solver_constraint() -> None:
    ideal_mass_grams = 0.16
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(
            ideal_mass_grams * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS
        ),
        constraints=(_gypsum_constraint(increment_grams=0.1),),
    )

    plan = optimize_treatment(request).plans[0]

    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.2)
    assert plan.target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET
    assert tuple(diagnostic.code for diagnostic in plan.diagnostics) == (
        OptimizerDiagnosticCode.TARGET_NOT_MET,
    )


def test_equal_target_deviation_prefers_lower_total_material_mass() -> None:
    halfway_mass_grams = 0.15
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(
            halfway_mass_grams * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS
        ),
        constraints=(_gypsum_constraint(increment_grams=0.1),),
    )

    plan = optimize_treatment(request).plans[0]

    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.1)


def test_returns_distinct_fewest_materials_candidate_with_equal_target_fit() -> None:
    coarse = ExactMassDosedTreatmentMaterial(
        "coarse_gypsum",
        "Coarse gypsum measure",
        GYPSUM,
        Q_(1.0, "gram"),
    )
    split_a = ExactMassDosedTreatmentMaterial(
        "split_gypsum_a",
        "First small gypsum measure",
        GYPSUM,
        Q_(0.4, "gram"),
    )
    split_b = ExactMassDosedTreatmentMaterial(
        "split_gypsum_b",
        "Second small gypsum measure",
        GYPSUM,
        Q_(0.4, "gram"),
    )
    target = TargetWaterProfile(
        "Gypsum contribution ranges",
        (
            IonConcentrationRange.mg_per_liter(
                Ion.CALCIUM,
                minimum=(0.8 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
                maximum=_CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS,
            ),
            IonConcentrationRange.mg_per_liter(
                Ion.SULFATE,
                minimum=(0.8 * _SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
                maximum=_SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS,
            ),
        ),
    )
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=target,
        constraints=(
            OptimizerMaterialConstraint(coarse, Q_(1.0, "gram")),
            OptimizerMaterialConstraint(split_a, Q_(0.4, "gram")),
            OptimizerMaterialConstraint(split_b, Q_(0.4, "gram")),
        ),
    )

    result = optimize_treatment(request)

    assert len(result.plans) == 2
    lowest_mass, fewest = result.plans
    assert lowest_mass.strategy is OptimizerStrategy.CLOSEST_ABSOLUTE_MG_PER_LITER
    assert tuple(
        addition.constraint.material.key for addition in lowest_mass.material_additions
    ) == ("split_gypsum_a", "split_gypsum_b")
    assert sum(
        float(addition.measured_mass.to("gram").magnitude)
        for addition in lowest_mass.material_additions
    ) == pytest.approx(0.8)
    assert fewest.strategy is (
        OptimizerStrategy.FEWEST_MATERIALS_CLOSEST_ABSOLUTE_MG_PER_LITER
    )
    assert tuple(
        addition.constraint.material.key for addition in fewest.material_additions
    ) == ("coarse_gypsum",)
    assert float(fewest.material_additions[0].measured_mass.magnitude) == pytest.approx(
        1.0
    )
    assert fewest.diagnostics[-1].code is (
        OptimizerDiagnosticCode.FEWEST_MATERIALS_TRADEOFF
    )
    assert "1 treatment product(s) instead of 2" in fewest.summary
    assert all(
        plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
        for plan in result.plans
    )


def test_material_maximum_limits_best_effort_plan() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(2.0 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(_gypsum_constraint(maximum_grams=0.9),),
    )

    plan = optimize_treatment(request).plans[0]

    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.9)
    assert plan.target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET
    assert plan.feasibility is OptimizerFeasibilityStatus.FEASIBLE


def test_nonincrement_material_maximum_is_never_exceeded() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(0.3 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(_gypsum_constraint(increment_grams=0.1, maximum_grams=0.29),),
    )

    plan = optimize_treatment(request).plans[0]

    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.2)


def test_numeric_range_uses_lowest_mass_inside_range() -> None:
    target = TargetWaterProfile(
        "Calcium range",
        (
            IonConcentrationRange.mg_per_liter(
                Ion.CALCIUM,
                minimum=(0.2 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
                maximum=(0.4 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
            ),
        ),
    )
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=target,
        constraints=(_gypsum_constraint(),),
    )

    plan = optimize_treatment(request).plans[0]

    assert plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.2)


def test_one_sided_numeric_target_bounds_are_supported() -> None:
    lower_target = TargetWaterProfile(
        "Calcium minimum",
        (
            IonConcentrationLowerBound.mg_per_liter(
                Ion.CALCIUM,
                0.2 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS,
            ),
        ),
    )
    upper_target = TargetWaterProfile(
        "Calcium maximum",
        (IonConcentrationUpperBound.mg_per_liter(Ion.CALCIUM, 5.0),),
    )

    lower_plan = optimize_treatment(
        _fixed_request(
            source=_source(calcium=0.0, sulfate=0.0),
            target=lower_target,
            constraints=(_gypsum_constraint(),),
        )
    ).plans[0]
    upper_plan = optimize_treatment(
        _fixed_request(
            source=_source(calcium=10.0),
            target=upper_target,
            constraints=(),
        )
    ).plans[0]

    assert float(
        lower_plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.2)
    assert lower_plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert upper_plan.material_additions == ()
    assert upper_plan.target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET


def test_unknown_nontarget_counterion_remains_unknown_without_blocking_plan() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0),
        target=_target(_CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(_gypsum_constraint(),),
    )

    plan = optimize_treatment(request).plans[0]

    assert plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert plan.calculation.final_state.concentration_for(Ion.SULFATE) is None
    sulfate = plan.calculation.treatment_result.resolution_for(Ion.SULFATE)
    assert sulfate is not None
    assert len(sulfate.known_treatment_contributions) == 1


def test_unknown_target_actual_is_indeterminate_not_zero() -> None:
    request = _fixed_request(
        source=_source(sulfate=0.0),
        target=_target(20.0),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.INDETERMINATE
    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.REQUIRED_SOURCE_CHEMISTRY_UNKNOWN,
    )


def test_unsupported_target_forms_return_structured_diagnostics() -> None:
    source = _source(calcium=0.0, sulfate=0.0)
    not_detected = TargetWaterProfile(
        "ND target",
        (IonConcentrationNotDetected(ion=Ion.CALCIUM),),
    )
    ph_target = TargetWaterProfile("pH target", (), ph=PHValue(7.0))

    nd_result = optimize_treatment(
        _fixed_request(source=source, target=not_detected, constraints=())
    )
    ph_result = optimize_treatment(
        _fixed_request(source=source, target=ph_target, constraints=())
    )

    assert nd_result.input_support is OptimizerInputSupportStatus.UNSUPPORTED
    assert tuple(diagnostic.code for diagnostic in nd_result.diagnostics) == (
        OptimizerDiagnosticCode.TARGET_CRITERION_UNSUPPORTED,
    )
    assert ph_result.input_support is OptimizerInputSupportStatus.UNSUPPORTED
    assert tuple(diagnostic.code for diagnostic in ph_result.diagnostics) == (
        OptimizerDiagnosticCode.TARGET_PH_UNSUPPORTED,
    )


def test_no_target_returns_deterministic_zero_addition_plan() -> None:
    request = _fixed_request(
        source=_source(calcium=5.0),
        target=None,
        constraints=(_gypsum_constraint(),),
    )

    first = optimize_treatment(request)
    second = optimize_treatment(request)

    assert first == second
    assert first.plans[0].material_additions == ()
    assert first.plans[0].target_fit is OptimizerTargetFitStatus.NOT_EVALUATED
    assert first.plans[0].solver_report.method == "no_target_zero_addition"


def test_empty_target_profile_is_not_mislabeled_indeterminate() -> None:
    request = _fixed_request(
        source=_source(calcium=5.0),
        target=TargetWaterProfile("Empty target", ()),
        constraints=(_gypsum_constraint(),),
    )

    plan = optimize_treatment(request).plans[0]

    assert plan.target_fit is OptimizerTargetFitStatus.NOT_EVALUATED
    assert plan.material_additions == ()


def test_source_volume_policy_finds_exact_bounded_blend() -> None:
    high_calcium = _available_source(
        "High calcium",
        current_liters=10.0,
        maximum_liters=20.0,
        calcium=100.0,
    )
    zero_calcium = _available_source(
        "Zero calcium",
        current_liters=10.0,
        maximum_liters=20.0,
        calcium=0.0,
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(high_calcium, zero_calcium),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(25.0),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.FEASIBLE
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert tuple(
        float(entry.volume.to("liter").magnitude) for entry in plan.source_volumes
    ) == pytest.approx((5.0, 15.0))


def test_source_volume_policy_honors_source_maximums() -> None:
    high_calcium = _available_source(
        "Limited high calcium",
        current_liters=0.0,
        maximum_liters=4.0,
        calcium=100.0,
    )
    zero_calcium = _available_source(
        "Zero calcium",
        current_liters=0.0,
        maximum_liters=20.0,
        calcium=0.0,
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(high_calcium, zero_calcium),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(50.0),
    )

    plan = optimize_treatment(request).plans[0]

    assert tuple(
        float(entry.volume.to("liter").magnitude) for entry in plan.source_volumes
    ) == pytest.approx((4.0, 16.0))
    assert plan.target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET


def test_source_volume_and_material_decisions_solve_together() -> None:
    high_calcium = _available_source(
        "High calcium",
        current_liters=10.0,
        maximum_liters=20.0,
        calcium=100.0,
        sulfate=0.0,
    )
    zero_water = _available_source(
        "Zero water",
        current_liters=10.0,
        maximum_liters=20.0,
        calcium=0.0,
        sulfate=0.0,
    )
    gypsum_grams = 0.2
    target = TargetWaterProfile(
        "Blend and treatment target",
        (
            IonConcentration.mg_per_liter(
                Ion.CALCIUM,
                25.0
                + gypsum_grams
                * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS
                / 2.0,
            ),
            IonConcentration.mg_per_liter(
                Ion.SULFATE,
                gypsum_grams * _SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TWENTY_LITERS,
            ),
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(high_calcium, zero_water),
        material_constraints=(_gypsum_constraint(maximum_grams=1.0),),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=target,
    )

    plan = optimize_treatment(request).plans[0]

    assert plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert tuple(float(entry.volume.magnitude) for entry in plan.source_volumes) == (
        pytest.approx(5.0),
        pytest.approx(15.0),
    )
    assert len(plan.material_additions) == 1
    assert float(plan.material_additions[0].measured_mass.magnitude) == pytest.approx(
        gypsum_grams
    )


def test_source_volume_policy_reports_insufficient_total_availability() -> None:
    sources = (
        _available_source(
            "Source A",
            current_liters=0.0,
            maximum_liters=4.0,
            calcium=100.0,
        ),
        _available_source(
            "Source B",
            current_liters=0.0,
            maximum_liters=5.0,
            calcium=0.0,
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=sources,
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(50.0),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INFEASIBLE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.SOURCE_VOLUME_CONSTRAINTS_INFEASIBLE,
    )


def test_source_volume_policy_does_not_broaden_availability_by_solver_tolerance() -> (
    None
):
    sources = (
        _available_source(
            "Source A",
            current_liters=0.0,
            maximum_liters=5.0,
            calcium=100.0,
        ),
        _available_source(
            "Source B",
            current_liters=0.0,
            maximum_liters=4.9999995,
            calcium=0.0,
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=sources,
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(50.0),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INFEASIBLE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.SOURCE_VOLUME_CONSTRAINTS_INFEASIBLE,
    )


def test_source_volume_policy_does_not_use_unknown_source_chemistry() -> None:
    known = _available_source(
        "Known",
        current_liters=20.0,
        maximum_liters=20.0,
        calcium=100.0,
    )
    unknown = OptimizerSource(
        SourceWaterProfile("Unknown candidate", ()),
        Q_(0, "liter"),
        Q_(20, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(known, unknown),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(50.0),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.INDETERMINATE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.REQUIRED_SOURCE_CHEMISTRY_UNKNOWN,
    )
    assert result.diagnostics[0].source_index == 1
    assert result.diagnostics[0].source_name == "Unknown candidate"


def test_source_volume_policy_preserves_duplicate_display_names_by_position() -> None:
    sources = (
        _available_source(
            "Well",
            current_liters=0.0,
            maximum_liters=20.0,
            calcium=100.0,
        ),
        _available_source(
            "Well",
            current_liters=0.0,
            maximum_liters=20.0,
            calcium=0.0,
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=sources,
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(25.0),
    )

    plan = optimize_treatment(request).plans[0]

    assert tuple(entry.source for entry in plan.source_volumes) == sources
    assert tuple(float(entry.volume.magnitude) for entry in plan.source_volumes) == (
        pytest.approx(5.0),
        pytest.approx(15.0),
    )


def test_source_volume_policy_is_deterministic_for_same_request() -> None:
    sources = (
        _available_source(
            "Source A",
            current_liters=0.0,
            maximum_liters=20.0,
            calcium=100.0,
        ),
        _available_source(
            "Source B",
            current_liters=0.0,
            maximum_liters=20.0,
            calcium=0.0,
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=sources,
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(25.0),
    )

    assert optimize_treatment(request) == optimize_treatment(request)


def test_source_volume_policy_rejects_solver_volume_sum_violation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_milp(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            success=True,
            status=0,
            message="claimed success",
            fun=0.0,
            x=(0.1, 0.1, 0.0, 0.0),
            mip_gap=0.0,
        )

    monkeypatch.setattr(optimizer_solver, "milp", invalid_milp)
    sources = (
        _available_source(
            "Source A",
            current_liters=10.0,
            maximum_liters=20.0,
            calcium=100.0,
        ),
        _available_source(
            "Source B",
            current_liters=10.0,
            maximum_liters=20.0,
            calcium=0.0,
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=sources,
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.SOURCE_VOLUMES,
        target_profile=_target(50.0),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert result.solver_report is not None
    assert "invalid decision values" in result.solver_report.message


def test_proportional_dilution_finds_exact_target_and_preserves_proportions() -> None:
    sources = (
        OptimizerSource(
            SourceWaterProfile(
                "Source A",
                (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
            ),
            Q_(1, "liter"),
            Q_(10, "liter"),
        ),
        OptimizerSource(
            SourceWaterProfile(
                "Source B",
                (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
            ),
            Q_(3, "liter"),
            Q_(30, "liter"),
        ),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Characterized RO",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(20, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=sources,
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(50.0),
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.FEASIBLE
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert plan.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert tuple(
        float(entry.volume.to("liter").magnitude) for entry in plan.source_volumes
    ) == pytest.approx((2.5, 7.5, 10.0))
    assert float(
        plan.source_volumes[1].volume.to("liter").magnitude
        / plan.source_volumes[0].volume.to("liter").magnitude
    ) == pytest.approx(3.0)


def test_proportional_dilution_honors_source_availability() -> None:
    source = OptimizerSource(
        SourceWaterProfile(
            "Limited source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(1, "liter"),
        Q_(5, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Characterized RO",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(10, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(100.0),
        diluent_source=diluent,
    )

    plan = optimize_treatment(request).plans[0]

    assert tuple(
        float(entry.volume.to("liter").magnitude) for entry in plan.source_volumes
    ) == pytest.approx((5.0, 5.0))
    assert plan.target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET


def test_proportional_dilution_reports_infeasible_volume_limits() -> None:
    source = OptimizerSource(
        SourceWaterProfile(
            "Limited source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(1, "liter"),
        Q_(4, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Limited diluent",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(5, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(50.0),
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INFEASIBLE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.SOURCE_VOLUME_CONSTRAINTS_INFEASIBLE,
    )


def test_proportional_dilution_does_not_broaden_availability_by_solver_tolerance() -> (
    None
):
    source = OptimizerSource(
        SourceWaterProfile(
            "Limited source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(1, "liter"),
        Q_(5, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Limited diluent",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(4.9999995, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(50.0),
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INFEASIBLE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.SOURCE_VOLUME_CONSTRAINTS_INFEASIBLE,
    )


def test_proportional_dilution_does_not_treat_unknown_diluent_as_zero() -> None:
    source = OptimizerSource(
        SourceWaterProfile(
            "Source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(10, "liter"),
        Q_(20, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile("Uncharacterized RO", ()),
        Q_(0, "liter"),
        Q_(20, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(50.0),
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.INDETERMINATE
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.REQUIRED_DILUENT_CHEMISTRY_UNKNOWN,
    )
    assert result.diagnostics[0].source_name == "Uncharacterized RO"


def test_requested_no_dilution_plan_is_returned_when_materially_different() -> None:
    source = OptimizerSource(
        SourceWaterProfile(
            "Source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(20, "liter"),
        Q_(20, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Characterized RO",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(20, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(50.0),
        request_no_dilution_plan=True,
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert len(result.plans) == 2
    closest, no_dilution = result.plans
    assert closest.target_fit is OptimizerTargetFitStatus.WITHIN_TARGET
    assert float(closest.source_volumes[-1].volume.magnitude) == pytest.approx(10.0)
    assert no_dilution.strategy is (
        OptimizerStrategy.NO_DILUTION_CLOSEST_ABSOLUTE_MG_PER_LITER
    )
    assert no_dilution.target_fit is OptimizerTargetFitStatus.OUTSIDE_TARGET
    assert float(no_dilution.source_volumes[-1].volume.magnitude) == pytest.approx(0.0)
    comparison = no_dilution.target_comparison
    assert comparison is not None
    calcium = comparison.comparison_for(Ion.CALCIUM)
    assert calcium is not None
    assert float(calcium.deviation.magnitude) == pytest.approx(50.0)
    assert tuple(diagnostic.code for diagnostic in no_dilution.diagnostics) == (
        OptimizerDiagnosticCode.TARGET_NOT_MET,
        OptimizerDiagnosticCode.UNAVOIDABLE_TARGET_OVERSHOOT,
    )
    assert no_dilution.diagnostics[1].ion is Ion.CALCIUM
    assert float(no_dilution.diagnostics[1].deviation.magnitude) == pytest.approx(50.0)


def test_requested_no_dilution_plan_is_deduplicated() -> None:
    source = OptimizerSource(
        SourceWaterProfile(
            "Source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(20, "liter"),
        Q_(20, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Characterized RO",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(20, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(100.0),
        request_no_dilution_plan=True,
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert len(result.plans) == 1
    assert float(result.plans[0].source_volumes[-1].volume.magnitude) == pytest.approx(
        0.0
    )


def test_no_dilution_plan_is_deduplicated_against_fewest_materials_plan() -> None:
    coarse = ExactMassDosedTreatmentMaterial(
        "coarse_gypsum",
        "Coarse gypsum measure",
        GYPSUM,
        Q_(1.0, "gram"),
    )
    split_a = ExactMassDosedTreatmentMaterial(
        "split_gypsum_a",
        "First small gypsum measure",
        GYPSUM,
        Q_(0.4, "gram"),
    )
    split_b = ExactMassDosedTreatmentMaterial(
        "split_gypsum_b",
        "Second small gypsum measure",
        GYPSUM,
        Q_(0.4, "gram"),
    )
    source = OptimizerSource(
        SourceWaterProfile(
            "Source",
            (
                IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),
                IonConcentration.mg_per_liter(Ion.SULFATE, 0.0),
            ),
        ),
        Q_(10, "liter"),
        Q_(10, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Characterized supplementary water",
            (
                IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),
                IonConcentration.mg_per_liter(Ion.SULFATE, 0.0),
            ),
        ),
        Q_(0, "liter"),
        Q_(10, "liter"),
    )
    target = TargetWaterProfile(
        "Gypsum-equivalent target",
        (
            IonConcentration.mg_per_liter(
                Ion.CALCIUM,
                _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS,
            ),
            IonConcentrationRange.mg_per_liter(
                Ion.SULFATE,
                minimum=(0.8 * _SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
                maximum=_SULFATE_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS,
            ),
        ),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=(source,),
        material_constraints=(
            OptimizerMaterialConstraint(coarse, Q_(1.0, "gram")),
            OptimizerMaterialConstraint(split_a, Q_(0.4, "gram")),
            OptimizerMaterialConstraint(split_b, Q_(0.4, "gram")),
        ),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=target,
        request_no_dilution_plan=True,
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert len(result.plans) == 2
    closest, fewest = result.plans
    assert tuple(
        addition.constraint.material.key for addition in closest.material_additions
    ) == ("split_gypsum_a", "split_gypsum_b")
    assert float(closest.source_volumes[-1].volume.magnitude) > 0.0
    assert fewest.strategy is (
        OptimizerStrategy.FEWEST_MATERIALS_CLOSEST_ABSOLUTE_MG_PER_LITER
    )
    assert tuple(
        addition.constraint.material.key for addition in fewest.material_additions
    ) == ("coarse_gypsum",)
    assert float(fewest.source_volumes[-1].volume.magnitude) == pytest.approx(0.0)


def test_requested_no_dilution_plan_reports_source_limit_infeasibility() -> None:
    source = OptimizerSource(
        SourceWaterProfile(
            "Limited source",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 100.0),),
        ),
        Q_(1, "liter"),
        Q_(5, "liter"),
    )
    diluent = OptimizerSource(
        SourceWaterProfile(
            "Characterized RO",
            (IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),),
        ),
        Q_(0, "liter"),
        Q_(10, "liter"),
    )
    request = OptimizerRequest(
        total_volume=Q_(10, "liter"),
        sources=(source,),
        material_constraints=(),
        source_resolution_policy=_POLICY,
        blend_policy=OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=_target(50.0),
        request_no_dilution_plan=True,
        diluent_source=diluent,
    )

    result = optimize_treatment(request)

    assert len(result.plans) == 1
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.NO_DILUTION_PLAN_INFEASIBLE,
    )


def test_excessive_material_increment_range_is_explicitly_unsupported() -> None:
    tiny_increment = _gypsum_constraint(
        increment_grams=1e-9,
        maximum_grams=10.0,
    )
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(50.0),
        constraints=(tiny_increment,),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.UNSUPPORTED
    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert result.solver_report is None
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.MATERIAL_INCREMENT_RANGE_UNSUPPORTED,
    )
    assert result.diagnostics[0].material_key == "gypsum"


def test_increment_range_at_supported_ceiling_is_accepted() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(5.0 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(
            _gypsum_constraint(
                increment_grams=1e-5,
                maximum_grams=10.0,
            ),
        ),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.SUPPORTED
    assert len(result.plans) == 1
    assert float(
        result.plans[0].material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(5.0)


@pytest.mark.parametrize("volume_liters", [1e12, 1e-19])
def test_solver_rejects_material_effect_outside_backend_matrix_range(
    volume_liters: float,
) -> None:
    source = _source(volume_liters=volume_liters, calcium=0.0, sulfate=0.0)
    request = _fixed_request(
        source=source,
        target=_target(1e-4),
        constraints=(
            _gypsum_constraint(
                increment_grams=1e-5,
                maximum_grams=10.0,
            ),
        ),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.UNSUPPORTED
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.NUMERICAL_MODEL_RANGE_UNSUPPORTED,
    )
    assert result.diagnostics[0].ion is Ion.CALCIUM
    assert result.diagnostics[0].material_key == "gypsum"


def test_solver_rejects_target_difference_at_backend_infinite_bound() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0),
        target=_target(1e20),
        constraints=(),
    )

    result = optimize_treatment(request)

    assert result.input_support is OptimizerInputSupportStatus.UNSUPPORTED
    assert result.plans == ()
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        OptimizerDiagnosticCode.NUMERICAL_MODEL_RANGE_UNSUPPORTED,
    )
    assert result.diagnostics[0].ion is Ion.CALCIUM
    assert result.diagnostics[0].material_key is None


def test_impossible_negative_solver_objective_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_milp(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            success=True,
            status=0,
            message="claimed success",
            fun=-1e-7,
            x=(0.0, 50.0, 0.0),
            mip_gap=0.0,
        )

    monkeypatch.setattr(optimizer_solver, "milp", invalid_milp)
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(50.0),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert result.solver_report is not None
    assert result.solver_report.success is False
    assert result.solver_report.solver_reported_primary_objective_mg_per_liter == (
        pytest.approx(-1e-7)
    )
    assert "negative primary objective" in result.solver_report.message


def test_solver_integer_noise_within_backend_tolerance_is_accepted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        (
            SimpleNamespace(
                success=True,
                status=0,
                message="primary optimal",
                fun=0.0,
                x=(1.0000005, 0.0, 0.0),
                mip_gap=0.0,
            ),
            SimpleNamespace(
                success=True,
                status=0,
                message="secondary optimal",
                fun=0.1,
                x=(1.0000005, 0.0, 0.0),
                mip_gap=0.0,
            ),
        )
    )

    def staged_milp(**_kwargs: object) -> SimpleNamespace:
        return next(responses)

    monkeypatch.setattr(optimizer_solver, "milp", staged_milp)
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(0.1 * _CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.FEASIBLE
    assert len(result.plans) == 1
    assert float(
        result.plans[0].material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(0.1)


def test_solver_integer_noise_above_backend_tolerance_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def invalid_milp(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            success=True,
            status=0,
            message="claimed success",
            fun=0.0,
            x=(1.0000011, 0.0, 0.0),
            mip_gap=0.0,
        )

    monkeypatch.setattr(optimizer_solver, "milp", invalid_milp)
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(10.0),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert result.solver_report is not None
    assert result.solver_report.success is False
    assert "invalid decision values" in result.solver_report.message


@pytest.mark.parametrize(
    "invalid_x",
    [
        (1.0, 0.0),
        (1.0, 0.0, 0.0, 0.0),
    ],
    ids=("truncated", "overlong"),
)
def test_solver_requires_complete_decision_vector(
    monkeypatch: pytest.MonkeyPatch,
    invalid_x: tuple[float, ...],
) -> None:
    def invalid_milp(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            success=True,
            status=0,
            message="claimed success",
            fun=0.0,
            x=invalid_x,
            mip_gap=0.0,
        )

    monkeypatch.setattr(optimizer_solver, "milp", invalid_milp)
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(10.0),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert result.solver_report is not None
    assert result.solver_report.success is False
    assert "invalid decision values" in result.solver_report.message


def test_secondary_solver_failure_does_not_silently_drop_mass_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        (
            SimpleNamespace(
                success=True,
                status=0,
                message="primary optimal",
                fun=50.0,
                x=(0.0, 50.0, 0.0),
                mip_gap=0.0,
            ),
            SimpleNamespace(
                success=False,
                status=4,
                message="secondary failed",
                fun=None,
                x=None,
                mip_gap=None,
            ),
        )
    )

    def staged_milp(**_kwargs: object) -> SimpleNamespace:
        return next(responses)

    monkeypatch.setattr(optimizer_solver, "milp", staged_milp)
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(50.0),
        constraints=(_gypsum_constraint(),),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.INDETERMINATE
    assert result.plans == ()
    assert result.solver_report is not None
    assert result.solver_report.success is False
    assert result.solver_report.message == "secondary failed"
    assert result.solver_report.primary_objective_mg_per_liter == pytest.approx(50.0)


def test_fewest_material_solver_rejects_inconsistent_usage_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    potassium_chloride = ExactMassDosedTreatmentMaterial(
        "potassium_chloride",
        "Potassium chloride",
        POTASSIUM_CHLORIDE,
        Q_(0.1, "gram"),
    )
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(50.0),
        constraints=(
            _gypsum_constraint(),
            OptimizerMaterialConstraint(potassium_chloride, Q_(1.0, "gram")),
        ),
    )
    initial = calculate_forward_water(
        (ForwardWaterSource(request.sources[0].source_profile, Q_(10, "liter")),),
        source_resolution_policy=_POLICY,
        target_profile=request.target_profile,
    )
    assert initial.final_target_comparison is not None

    def invalid_milp(**_kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(
            success=True,
            status=0,
            message="claimed success",
            fun=50.0,
            x=(0.0, 0.0, 1.0, 0.0, 50.0, 0.0),
            mip_gap=0.0,
        )

    monkeypatch.setattr(optimizer_solver, "milp", invalid_milp)

    decisions, report = optimizer_solver._solve_increment_counts(
        request,
        initial.final_target_comparison.ion_comparisons,
        prefer_fewest_materials=True,
    )

    assert decisions is None
    assert report.success is False
    assert "invalid decision values" in report.message


def test_fewest_material_solver_does_not_hide_tertiary_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    potassium_chloride = ExactMassDosedTreatmentMaterial(
        "potassium_chloride",
        "Potassium chloride",
        POTASSIUM_CHLORIDE,
        Q_(0.1, "gram"),
    )
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(50.0),
        constraints=(
            _gypsum_constraint(),
            OptimizerMaterialConstraint(potassium_chloride, Q_(1.0, "gram")),
        ),
    )
    initial = calculate_forward_water(
        (ForwardWaterSource(request.sources[0].source_profile, Q_(10, "liter")),),
        source_resolution_policy=_POLICY,
        target_profile=request.target_profile,
    )
    assert initial.final_target_comparison is not None
    valid_x = (0.0, 0.0, 0.0, 0.0, 50.0, 0.0)
    responses = iter(
        (
            SimpleNamespace(
                success=True,
                status=0,
                message="primary optimal",
                fun=50.0,
                x=valid_x,
                mip_gap=0.0,
            ),
            SimpleNamespace(
                success=True,
                status=0,
                message="fewest optimal",
                fun=0.0,
                x=valid_x,
                mip_gap=0.0,
            ),
            SimpleNamespace(
                success=False,
                status=4,
                message="tertiary failed",
                fun=None,
                x=None,
                mip_gap=None,
            ),
        )
    )

    def staged_milp(**_kwargs: object) -> SimpleNamespace:
        return next(responses)

    monkeypatch.setattr(optimizer_solver, "milp", staged_milp)

    decisions, report = optimizer_solver._solve_increment_counts(
        request,
        initial.final_target_comparison.ion_comparisons,
        prefer_fewest_materials=True,
    )

    assert decisions is None
    assert report.success is False
    assert report.message == "tertiary failed"


def test_postvalidation_uses_returned_counts_not_solver_fun() -> None:
    source = _source(calcium=40.0, chloride=20.0, potassium=1.0)
    potassium_chloride = ExactMassDosedTreatmentMaterial(
        "potassium_chloride",
        "Potassium chloride",
        POTASSIUM_CHLORIDE,
        Q_(0.37, "gram"),
    )
    calcium_chloride = ExactMassDosedTreatmentMaterial(
        "calcium_chloride",
        "Calcium chloride dihydrate",
        CALCIUM_CHLORIDE_DIHYDRATE,
        Q_(0.13, "gram"),
    )
    target = TargetWaterProfile(
        "Calcium and chloride target",
        (
            IonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),
            IonConcentration.mg_per_liter(Ion.CHLORIDE, 90.0),
        ),
    )
    request = _fixed_request(
        source=source,
        target=target,
        constraints=(
            OptimizerMaterialConstraint(potassium_chloride, Q_(6, "gram")),
            OptimizerMaterialConstraint(calcium_chloride, Q_(6, "gram")),
        ),
    )

    result = optimize_treatment(request)

    assert result.feasibility is OptimizerFeasibilityStatus.FEASIBLE
    assert len(result.plans) == 1
    plan = result.plans[0]
    assert len(plan.material_additions) == 1
    assert plan.material_additions[0].constraint.material.key == "potassium_chloride"
    assert float(
        plan.material_additions[0].measured_mass.to("gram").magnitude
    ) == pytest.approx(1.48)
    assert plan.solver_report.primary_objective_mg_per_liter == pytest.approx(
        0.37853311208974505
    )
    assert (
        plan.solver_report.solver_reported_primary_objective_mg_per_liter
        == pytest.approx(0.3785321120897411)
    )


def test_plan_replays_exactly_through_ordinary_forward_calculator() -> None:
    request = _fixed_request(
        source=_source(calcium=0.0, sulfate=0.0),
        target=_target(_CALCIUM_MG_PER_LITER_PER_GYPSUM_GRAM_IN_TEN_LITERS),
        constraints=(_gypsum_constraint(),),
    )
    plan = optimize_treatment(request).plans[0]

    replay = calculate_forward_water(
        tuple(
            ForwardWaterSource(
                source.source.source_profile,
                source.volume,
            )
            for source in plan.source_volumes
        ),
        source_resolution_policy=request.source_resolution_policy,
        treatment_additions=tuple(
            addition.treatment_addition for addition in plan.material_additions
        ),
        target_profile=request.target_profile,
    )

    assert replay == plan.calculation


def test_two_material_result_matches_exhaustive_practical_grid() -> None:
    source = _source(calcium=0.0, sulfate=0.0, chloride=0.0)
    calcium_chloride = ExactMassDosedTreatmentMaterial(
        "calcium_chloride",
        "Calcium chloride dihydrate",
        CALCIUM_CHLORIDE_DIHYDRATE,
        Q_(0.1, "gram"),
    )
    constraints = (
        _gypsum_constraint(maximum_grams=0.5),
        OptimizerMaterialConstraint(calcium_chloride, Q_(0.5, "gram")),
    )
    target = TargetWaterProfile(
        "Three-ion target",
        (
            IonConcentration.mg_per_liter(Ion.CALCIUM, 8.7),
            IonConcentration.mg_per_liter(Ion.SULFATE, 9.1),
            IonConcentration.mg_per_liter(Ion.CHLORIDE, 4.3),
        ),
    )
    request = _fixed_request(
        source=source,
        target=target,
        constraints=constraints,
    )

    plan = optimize_treatment(request).plans[0]
    assert plan.target_comparison is not None
    selected_objective = sum(
        abs(float(comparison.deviation.to("milligram / liter").magnitude))
        for comparison in plan.target_comparison.ion_comparisons
        if comparison.deviation is not None
    )
    selected_mass = sum(
        float(addition.measured_mass.to("gram").magnitude)
        for addition in plan.material_additions
    )

    practical_grid: list[tuple[float, float]] = []
    ingredients = (GYPSUM, CALCIUM_CHLORIDE_DIHYDRATE)
    for counts in product(range(6), repeat=2):
        additions = tuple(
            TreatmentAddition(ingredient, Q_(count * 0.1, "gram"))
            for ingredient, count in zip(ingredients, counts, strict=True)
            if count
        )
        forward = calculate_forward_water(
            (ForwardWaterSource(source.source_profile, Q_(10, "liter")),),
            source_resolution_policy=_POLICY,
            treatment_additions=additions,
            target_profile=target,
        )
        comparison = forward.final_target_comparison
        assert comparison is not None
        objective = sum(
            abs(float(item.deviation.to("milligram / liter").magnitude))
            for item in comparison.ion_comparisons
            if item.deviation is not None
        )
        practical_grid.append((objective, sum(counts) * 0.1))

    best_objective = min(objective for objective, _ in practical_grid)
    best_mass = min(
        mass
        for objective, mass in practical_grid
        if abs(objective - best_objective) <= 1e-9
    )
    assert selected_objective == pytest.approx(best_objective, abs=1e-7)
    assert selected_mass == pytest.approx(best_mass, abs=1e-7)
