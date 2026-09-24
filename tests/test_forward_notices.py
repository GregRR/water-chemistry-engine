import pytest
from fermunits import Q_, PHValue

from water_chemistry_engine.alkalinity_balance import (
    SourceAlkalinityResolutionMethod,
    UnresolvedSourceAlkalinityReason,
)
from water_chemistry_engine.blending import BlendSource, blend_waters
from water_chemistry_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationRange,
    UpperBoundConcentrationEndpoint,
)
from water_chemistry_engine.forward_notices import (
    ForwardNoticeCode,
    ForwardNoticeLevel,
    build_forward_notices,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_properties import (
    Alkalinity,
    AlkalinityAnalyticalContext,
    AlkalinityResultIdentity,
)
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.source_resolution import resolve_source_profile
from water_chemistry_engine.target_comparison import compare_state_to_target
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    apply_treatment_additions,
)
from water_chemistry_engine.treatment_ingredients import GYPSUM, SODIUM_BICARBONATE

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


def _blend_for(
    resolutions,
    volumes: tuple[float, ...],
):
    return blend_waters(
        tuple(
            BlendSource(
                resolution.source_profile.name,
                resolution.state,
                Q_(volume, "liter"),
            )
            for resolution, volume in zip(resolutions, volumes, strict=True)
        )
    )


def test_exact_single_source_without_target_has_no_notices() -> None:
    resolution = resolve_source_profile(
        _profile("Tap", calcium=50.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((resolution,), (10.0,))

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    assert build_forward_notices((resolution,), blend, treatment, None) == ()


def test_midpoint_policy_is_exposed_as_assumption() -> None:
    profile = SourceWaterProfile(
        name="Ranged source",
        concentrations=(IonConcentrationRange.mg_per_liter(Ion.SULFATE, 50.0, 150.0),),
    )
    resolution = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)
    blend = _blend_for((resolution,), (10.0,))

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())
    notices = build_forward_notices((resolution,), blend, treatment, None)

    assert len(notices) == 1
    notice = notices[0]
    assert notice.code is ForwardNoticeCode.SOURCE_RANGE_MIDPOINT_USED
    assert notice.level is ForwardNoticeLevel.ASSUMPTION
    assert notice.ion is Ion.SULFATE
    assert notice.source_index == 0
    assert notice.source_name == "Ranged source"
    assert notice.reason == "derived_exact_range_midpoint"


def test_unresolved_positive_volume_source_is_exposed_as_warning() -> None:
    profile = SourceWaterProfile(
        name="Ranged source",
        concentrations=(IonConcentrationRange.mg_per_liter(Ion.SULFATE, 50.0, 150.0),),
    )
    resolution = resolve_source_profile(profile, policy=REPORTED_ONLY)
    blend = _blend_for((resolution,), (10.0,))

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())
    notices = build_forward_notices((resolution,), blend, treatment, None)

    assert len(notices) == 1
    notice = notices[0]
    assert notice.code is ForwardNoticeCode.SOURCE_ION_UNRESOLVED
    assert notice.level is ForwardNoticeLevel.WARNING
    assert notice.ion is Ion.SULFATE
    assert notice.reason == "exact_range_midpoint_not_permitted"


def test_alkalinity_midpoint_policy_is_exposed_as_assumption() -> None:
    profile = SourceWaterProfile(
        name="Ranged alkalinity source",
        concentrations=(),
        alkalinity=Alkalinity.mg_per_liter_as_caco3_range(80.0, 120.0),
    )
    resolution = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)
    blend = _blend_for((resolution,), (10.0,))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    notices = build_forward_notices((resolution,), blend, treatment, None)

    assert len(notices) == 1
    notice = notices[0]
    assert notice.code is (ForwardNoticeCode.SOURCE_ALKALINITY_RANGE_MIDPOINT_USED)
    assert notice.level is ForwardNoticeLevel.ASSUMPTION
    assert notice.ion is None
    assert notice.source_index == 0
    assert notice.source_name == "Ranged alkalinity source"
    assert notice.reason == (
        SourceAlkalinityResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT.value
    )


@pytest.mark.parametrize(
    ("alkalinity", "expected_reason"),
    (
        (
            Alkalinity.mg_per_liter_as_caco3_range(80.0, 120.0),
            UnresolvedSourceAlkalinityReason.EXACT_RANGE_MIDPOINT_NOT_PERMITTED,
        ),
        (
            Alkalinity.mg_per_liter_as_caco3(
                100.0,
                analytical_context=AlkalinityAnalyticalContext(
                    result_identity=(
                        AlkalinityResultIdentity.ACID_NEUTRALIZING_CAPACITY
                    ),
                ),
            ),
            UnresolvedSourceAlkalinityReason.ACID_NEUTRALIZING_CAPACITY_UNSUPPORTED,
        ),
    ),
)
def test_reported_unresolved_alkalinity_is_exposed_as_warning(
    alkalinity: Alkalinity,
    expected_reason: UnresolvedSourceAlkalinityReason,
) -> None:
    profile = SourceWaterProfile(
        name="Unresolved alkalinity source",
        concentrations=(),
        alkalinity=alkalinity,
    )
    resolution = resolve_source_profile(profile, policy=REPORTED_ONLY)
    blend = _blend_for((resolution,), (10.0,))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    notices = build_forward_notices((resolution,), blend, treatment, None)

    assert len(notices) == 1
    notice = notices[0]
    assert notice.code is ForwardNoticeCode.SOURCE_ALKALINITY_UNRESOLVED
    assert notice.level is ForwardNoticeLevel.WARNING
    assert notice.ion is None
    assert notice.source_index == 0
    assert notice.source_name == "Unresolved alkalinity source"
    assert notice.reason == expected_reason.value


def test_ion_and_alkalinity_source_notices_coexist_without_interference() -> None:
    profile = SourceWaterProfile(
        name="Mixed-resolution source",
        concentrations=(
            IonConcentrationRange(
                ion=Ion.SULFATE,
                minimum=ExactConcentrationEndpoint.mg_per_liter(50.0),
                maximum=UpperBoundConcentrationEndpoint.mg_per_liter(150.0),
            ),
        ),
        alkalinity=Alkalinity.mg_per_liter_as_caco3_range(80.0, 120.0),
    )
    resolution = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)
    blend = _blend_for((resolution,), (10.0,))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    notices = build_forward_notices((resolution,), blend, treatment, None)

    assert tuple(notice.code for notice in notices) == (
        ForwardNoticeCode.SOURCE_ION_UNRESOLVED,
        ForwardNoticeCode.SOURCE_ALKALINITY_RANGE_MIDPOINT_USED,
    )
    assert tuple(notice.level for notice in notices) == (
        ForwardNoticeLevel.WARNING,
        ForwardNoticeLevel.ASSUMPTION,
    )
    assert notices[0].ion is Ion.SULFATE
    assert notices[0].reason == "qualified_range"
    assert notices[1].ion is None
    assert notices[1].reason == (
        SourceAlkalinityResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT.value
    )
    assert all(notice.source_index == 0 for notice in notices)
    assert all(notice.source_name == "Mixed-resolution source" for notice in notices)


def test_zero_volume_source_resolution_does_not_create_noise() -> None:
    known = resolve_source_profile(
        _profile("Used", calcium=50.0),
        policy=REPORTED_ONLY,
    )
    unused_profile = SourceWaterProfile(
        name="Unused",
        concentrations=(IonConcentrationRange.mg_per_liter(Ion.SULFATE, 50.0, 150.0),),
    )
    unused = resolve_source_profile(unused_profile, policy=REPORTED_ONLY)
    blend = _blend_for((known, unused), (10.0, 0.0))

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    assert build_forward_notices((known, unused), blend, treatment, None) == ()


def test_zero_volume_unresolved_alkalinity_does_not_create_noise() -> None:
    used = resolve_source_profile(
        _profile("Used", calcium=50.0),
        policy=REPORTED_ONLY,
    )
    unused = resolve_source_profile(
        SourceWaterProfile(
            name="Unused alkalinity",
            concentrations=(),
            alkalinity=Alkalinity.mg_per_liter_as_caco3_range(80.0, 120.0),
        ),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((used, unused), (10.0, 0.0))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    assert build_forward_notices((used, unused), blend, treatment, None) == ()


def test_multi_source_carbonate_species_blend_surfaces_approximation() -> None:
    first = resolve_source_profile(
        _profile("First", bicarbonate=100.0),
        policy=REPORTED_ONLY,
    )
    second = resolve_source_profile(
        _profile("Second", bicarbonate=200.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((first, second), (5.0, 5.0))

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())
    notices = build_forward_notices((first, second), blend, treatment, None)

    assert tuple(notice.code for notice in notices) == (
        ForwardNoticeCode.CARBONATE_BLEND_APPROXIMATION,
        ForwardNoticeCode.CARBONATE_SYSTEM_MODEL_LIMITATION,
    )
    assert notices[0].level is ForwardNoticeLevel.ASSUMPTION
    assert notices[1].level is ForwardNoticeLevel.WARNING
    assert notices[1].ion is Ion.BICARBONATE


def test_single_source_sodium_bicarbonate_addition_is_model_limited() -> None:
    resolution = resolve_source_profile(
        _profile("Tap", sodium=0.0, bicarbonate=0.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((resolution,), (10.0,))
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (TreatmentAddition(SODIUM_BICARBONATE, Q_(1.0, "gram")),),
    )

    notices = build_forward_notices((resolution,), blend, treatment, None)

    carbonate_notice = next(
        notice
        for notice in notices
        if notice.code is ForwardNoticeCode.CARBONATE_SYSTEM_MODEL_LIMITATION
    )
    assert carbonate_notice.ion is Ion.BICARBONATE
    assert carbonate_notice.material_key == "sodium_bicarbonate"
    assert carbonate_notice.reason == "formal_carbonate_inventory"


def test_carbonate_target_and_alkalinity_target_have_separate_limitations() -> None:
    resolution = resolve_source_profile(
        _profile("Tap", bicarbonate=100.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((resolution,), (10.0,))
    target = TargetWaterProfile(
        name="Carbonate-system target",
        concentrations=(IonConcentration.mg_per_liter(Ion.BICARBONATE, 100.0),),
        alkalinity=Alkalinity.mg_per_liter_as_caco3(80.0),
    )
    comparison = compare_state_to_target(blend.state, target)
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    notices = build_forward_notices((resolution,), blend, treatment, comparison)

    assert tuple(notice.code for notice in notices) == (
        ForwardNoticeCode.CARBONATE_SYSTEM_MODEL_LIMITATION,
        ForwardNoticeCode.TARGET_CARBONATE_SYSTEM_MODEL_LIMITED,
        ForwardNoticeCode.TARGET_ALKALINITY_ACTUAL_UNKNOWN,
    )


def test_positive_treatment_surfaces_complete_dissolution_assumption() -> None:
    resolution = resolve_source_profile(
        _profile("Tap", calcium=50.0, sulfate=0.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((resolution,), (10.0,))
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (TreatmentAddition(GYPSUM, Q_(1.0, "gram")),),
    )

    notices = build_forward_notices((resolution,), blend, treatment, None)

    assert len(notices) == 1
    notice = notices[0]
    assert notice.code is ForwardNoticeCode.TREATMENT_COMPLETE_DISSOLUTION_MODEL
    assert notice.level is ForwardNoticeLevel.ASSUMPTION
    assert "complete-dissolution" in notice.message


def test_unknown_final_target_actual_is_exposed_as_warning() -> None:
    resolution = resolve_source_profile(
        _profile("Tap", calcium=50.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((resolution,), (10.0,))
    target = TargetWaterProfile(
        name="Sulfate target",
        concentrations=(IonConcentration.mg_per_liter(Ion.SULFATE, 100.0),),
    )
    comparison = compare_state_to_target(blend.state, target)

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())
    notices = build_forward_notices((resolution,), blend, treatment, comparison)

    assert len(notices) == 1
    notice = notices[0]
    assert notice.code is ForwardNoticeCode.TARGET_ACTUAL_UNKNOWN
    assert notice.level is ForwardNoticeLevel.WARNING
    assert notice.ion is Ion.SULFATE
    assert notice.reason == "actual_unknown"


def test_unsupported_target_and_ph_are_separate_structured_notices() -> None:
    resolution = resolve_source_profile(
        _profile("Tap", chloride=25.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((resolution,), (10.0,))
    target = TargetWaterProfile(
        name="Qualified target",
        concentrations=(
            IonConcentrationRange(
                ion=Ion.CHLORIDE,
                minimum=ExactConcentrationEndpoint.mg_per_liter(0.0),
                maximum=UpperBoundConcentrationEndpoint.mg_per_liter(50.0),
            ),
        ),
        ph=PHValue(7.0),
    )
    comparison = compare_state_to_target(blend.state, target)

    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())
    notices = build_forward_notices((resolution,), blend, treatment, comparison)

    assert tuple(notice.code for notice in notices) == (
        ForwardNoticeCode.TARGET_CRITERION_UNSUPPORTED,
        ForwardNoticeCode.TARGET_PH_NOT_CALCULATED,
    )
    assert notices[0].reason == "qualified_range"
    assert notices[1].level is ForwardNoticeLevel.INFORMATION
    assert notices[1].reason == "not_calculated"


def test_source_resolution_order_must_match_blend_sources() -> None:
    first = resolve_source_profile(
        _profile("First", calcium=40.0),
        policy=REPORTED_ONLY,
    )
    second = resolve_source_profile(
        _profile("Second", calcium=60.0),
        policy=REPORTED_ONLY,
    )
    blend = _blend_for((first, second), (5.0, 5.0))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    with pytest.raises(ValueError, match="same order"):
        build_forward_notices((second, first), blend, treatment, None)
