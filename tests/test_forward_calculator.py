import pytest
from fermunits import Q_

from water_chemistry_engine.blending import ResolvedBlendIon, UnresolvedBlendIon
from water_chemistry_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_chemistry_engine.forward_calculator import (
    ForwardWaterSource,
    calculate_forward_water,
)
from water_chemistry_engine.forward_notices import ForwardNoticeCode
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.source_resolution import (
    ResolvedSourceIon,
    SourceIonResolutionMethod,
    UnresolvedSourceIon,
)
from water_chemistry_engine.target_comparison import (
    TargetIonComparisonStatus,
    TargetProfileComparisonStatus,
)
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    UnresolvedTreatmentIon,
)
from water_chemistry_engine.treatment_ingredients import GYPSUM

REPORTED_ONLY = SourceResolutionPolicy(allow_exact_range_midpoints=False)
ALLOW_MIDPOINTS = SourceResolutionPolicy(allow_exact_range_midpoints=True)


def _profile(name: str, **values: float) -> SourceWaterProfile:
    return SourceWaterProfile(
        name=name,
        concentrations=tuple(
            IonConcentration.mg_per_liter(Ion(ion_name), value)
            for ion_name, value in values.items()
        ),
    )


def _mg_per_liter(state, ion: Ion) -> float | None:
    concentration = state.concentration_for(ion)
    if concentration is None:
        return None
    return float(concentration.to("milligram / liter").magnitude)


def test_complete_forward_workflow_preserves_each_stage() -> None:
    source_a = _profile("Source A", calcium=40.0, sulfate=20.0, chloride=10.0)
    source_b = _profile("Source B", calcium=60.0, sulfate=40.0, chloride=30.0)
    target = TargetWaterProfile(
        name="Calcium target",
        concentrations=(
            IonConcentrationRange.mg_per_liter(
                Ion.CALCIUM,
                minimum=60.0,
                maximum=70.0,
            ),
        ),
    )

    result = calculate_forward_water(
        (
            ForwardWaterSource(source_a, Q_(10, "liter")),
            ForwardWaterSource(source_b, Q_(10, "liter")),
        ),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(GYPSUM, Q_(1, "gram")),),
        target_profile=target,
    )

    assert len(result.source_results) == 2
    assert result.source_results[0].resolution.source_profile is source_a
    assert result.source_results[1].resolution.source_profile is source_b
    assert _mg_per_liter(result.source_results[0].state, Ion.CALCIUM) == 40.0
    assert _mg_per_liter(result.source_results[1].state, Ion.CALCIUM) == 60.0

    assert result.blend_result.total_volume.to("liter").magnitude == 20.0
    assert tuple(source.name for source in result.blend_result.sources) == (
        "Source A",
        "Source B",
    )
    assert _mg_per_liter(result.blend_state, Ion.CALCIUM) == pytest.approx(50.0)
    assert _mg_per_liter(result.blend_state, Ion.SULFATE) == pytest.approx(30.0)

    assert result.treatment_result.water_volume.to("liter").magnitude == 20.0
    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(
        61.6395,
        abs=0.001,
    )
    assert _mg_per_liter(result.final_state, Ion.SULFATE) == pytest.approx(
        57.8967,
        abs=0.001,
    )

    source_a_comparison = result.source_results[0].target_comparison
    source_b_comparison = result.source_results[1].target_comparison
    assert source_a_comparison is not None
    assert source_b_comparison is not None
    assert (
        source_a_comparison.comparison_for(Ion.CALCIUM).status
        is TargetIonComparisonStatus.BELOW_TARGET
    )
    assert (
        source_b_comparison.comparison_for(Ion.CALCIUM).status
        is TargetIonComparisonStatus.WITHIN_TARGET
    )

    assert result.blend_target_comparison is not None
    assert (
        result.blend_target_comparison.comparison_for(Ion.CALCIUM).status
        is TargetIonComparisonStatus.BELOW_TARGET
    )
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status is TargetProfileComparisonStatus.SATISFIED
    )
    assert (
        result.final_target_comparison.comparison_for(Ion.CALCIUM).status
        is TargetIonComparisonStatus.WITHIN_TARGET
    )


def test_range_policy_remains_auditable_through_blend_and_final_state() -> None:
    ranged = SourceWaterProfile(
        name="Ranged",
        concentrations=(
            IonConcentrationRange.mg_per_liter(
                Ion.SULFATE,
                minimum=50.0,
                maximum=150.0,
            ),
        ),
    )
    exact = _profile("Exact", sulfate=100.0)
    target = TargetWaterProfile(
        name="Sulfate target",
        concentrations=(IonConcentration.mg_per_liter(Ion.SULFATE, 100.0),),
    )

    result = calculate_forward_water(
        (
            ForwardWaterSource(ranged, Q_(5, "liter")),
            ForwardWaterSource(exact, Q_(5, "liter")),
        ),
        source_resolution_policy=REPORTED_ONLY,
        target_profile=target,
    )

    source_resolution = result.source_results[0].resolution.resolution_for(Ion.SULFATE)
    assert isinstance(source_resolution, UnresolvedSourceIon)
    assert isinstance(
        result.blend_result.resolution_for(Ion.SULFATE),
        UnresolvedBlendIon,
    )
    assert isinstance(
        result.treatment_result.resolution_for(Ion.SULFATE),
        UnresolvedTreatmentIon,
    )
    assert result.final_state.concentration_for(Ion.SULFATE) is None
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.comparison_for(Ion.SULFATE).status
        is TargetIonComparisonStatus.ACTUAL_UNKNOWN
    )
    assert tuple(notice.code for notice in result.notices) == (
        ForwardNoticeCode.SOURCE_ION_UNRESOLVED,
        ForwardNoticeCode.TARGET_ACTUAL_UNKNOWN,
    )


def test_explicit_midpoint_policy_flows_into_blend_and_comparison() -> None:
    ranged = SourceWaterProfile(
        name="Ranged",
        concentrations=(
            IonConcentrationRange.mg_per_liter(
                Ion.SULFATE,
                minimum=50.0,
                maximum=150.0,
            ),
        ),
    )
    exact = _profile("Exact", sulfate=100.0)
    target = TargetWaterProfile(
        name="Sulfate target",
        concentrations=(IonConcentration.mg_per_liter(Ion.SULFATE, 100.0),),
    )

    result = calculate_forward_water(
        (
            ForwardWaterSource(ranged, Q_(5, "liter")),
            ForwardWaterSource(exact, Q_(5, "liter")),
        ),
        source_resolution_policy=ALLOW_MIDPOINTS,
        target_profile=target,
    )

    source_resolution = result.source_results[0].resolution.resolution_for(Ion.SULFATE)
    assert isinstance(source_resolution, ResolvedSourceIon)
    assert (
        source_resolution.method
        is SourceIonResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT
    )
    assert isinstance(result.blend_result.resolution_for(Ion.SULFATE), ResolvedBlendIon)
    assert _mg_per_liter(result.blend_state, Ion.SULFATE) == pytest.approx(100.0)
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status is TargetProfileComparisonStatus.SATISFIED
    )


def test_unknown_starting_ion_keeps_known_treatment_contribution_auditable() -> None:
    source = _profile("Source", calcium=50.0)

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(GYPSUM, Q_(1, "gram")),),
    )

    sulfate_resolution = result.treatment_result.resolution_for(Ion.SULFATE)
    assert isinstance(sulfate_resolution, UnresolvedTreatmentIon)
    assert len(sulfate_resolution.known_treatment_contributions) == 1
    assert (
        sulfate_resolution.known_treatment_contributions[0].addition.ingredient
        is GYPSUM
    )
    assert result.final_state.concentration_for(Ion.SULFATE) is None


def test_zero_volume_unresolved_source_does_not_poison_workflow() -> None:
    known = _profile("Known", calcium=50.0)
    unresolved = SourceWaterProfile(
        name="Unresolved",
        concentrations=(IonConcentrationUpperBound.mg_per_liter(Ion.CALCIUM, 20.0),),
    )

    result = calculate_forward_water(
        (
            ForwardWaterSource(known, Q_(10, "liter")),
            ForwardWaterSource(unresolved, Q_(0, "liter")),
        ),
        source_resolution_policy=REPORTED_ONLY,
    )

    assert _mg_per_liter(result.blend_state, Ion.CALCIUM) == pytest.approx(50.0)
    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(50.0)
    assert isinstance(result.blend_result.resolution_for(Ion.CALCIUM), ResolvedBlendIon)


def test_target_is_optional_without_skipping_forward_calculation() -> None:
    source = _profile("Source", calcium=50.0, sulfate=0.0)

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(GYPSUM, Q_(1, "gram")),),
    )

    assert result.target_profile is None
    assert result.source_results[0].target_comparison is None
    assert result.blend_target_comparison is None
    assert result.final_target_comparison is None
    assert result.preparation_instructions.lines == (
        "Use 10 L of Source as the starting water.",
        "Add 1 g of Gypsum (CaSO4·2H2O).",
    )
    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(
        73.279,
        abs=0.001,
    )


def test_forward_calculation_requires_at_least_one_source() -> None:
    with pytest.raises(ValueError, match="requires at least one source"):
        calculate_forward_water(
            (),
            source_resolution_policy=REPORTED_ONLY,
        )
