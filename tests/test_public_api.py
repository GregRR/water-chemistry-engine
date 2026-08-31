"""Contract tests for the supported package-root consumer API."""

import pytest
from fermunits import Q_

import water_chemistry_engine as wce

EXPECTED_PUBLIC_API = {
    "CALCIUM_CHLORIDE_DIHYDRATE",
    "EPSOM_SALT",
    "GYPSUM",
    "POTASSIUM_CHLORIDE",
    "SIMPLE_MINERAL_INGREDIENTS",
    "SODIUM_BICARBONATE",
    "SODIUM_CHLORIDE",
    "ConcentrationRangeEndpoint",
    "ExactConcentrationEndpoint",
    "ForwardCalculationNotice",
    "ForwardNoticeCode",
    "ForwardNoticeLevel",
    "ForwardSourceResult",
    "ForwardWaterCalculationResult",
    "ForwardWaterSource",
    "Ion",
    "IonConcentration",
    "IonConcentrationLowerBound",
    "IonConcentrationNotDetected",
    "IonConcentrationRange",
    "IonConcentrationUpperBound",
    "IonConcentrationValue",
    "LowerBoundConcentrationEndpoint",
    "NotDetectedConcentrationEndpoint",
    "SourceResolutionPolicy",
    "SourceWaterProfile",
    "TargetIonComparison",
    "TargetIonComparisonStatus",
    "TargetPHComparison",
    "TargetPHComparisonStatus",
    "TargetProfileComparison",
    "TargetProfileComparisonStatus",
    "TargetWaterProfile",
    "TreatmentAddition",
    "UnsupportedTargetIonReason",
    "UpperBoundConcentrationEndpoint",
    "__version__",
    "calculate_forward_water",
}


def test_public_api_exports_are_explicit_and_complete() -> None:
    """The package root exposes exactly the documented 0.3 consumer surface."""
    assert len(wce.__all__) == len(set(wce.__all__))
    assert set(wce.__all__) == EXPECTED_PUBLIC_API
    assert all(hasattr(wce, name) for name in wce.__all__)


def test_complete_forward_workflow_uses_only_package_root_imports() -> None:
    """A consumer can construct and interpret the proven workflow via the facade."""
    source_a = wce.SourceWaterProfile(
        name="Source A",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 40.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.SULFATE, 20.0),
        ),
    )
    source_b = wce.SourceWaterProfile(
        name="Source B",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 80.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.SULFATE, 40.0),
        ),
    )
    target = wce.TargetWaterProfile(
        name="Calcium target",
        concentrations=(
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.CALCIUM,
                minimum=65.0,
                maximum=75.0,
            ),
        ),
    )

    result = wce.calculate_forward_water(
        (
            wce.ForwardWaterSource(source_a, Q_(10, "liter")),
            wce.ForwardWaterSource(source_b, Q_(10, "liter")),
        ),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        treatment_additions=(wce.TreatmentAddition(wce.GYPSUM, Q_(0.5, "gram")),),
        target_profile=target,
    )

    calcium = result.final_state.concentration_for(wce.Ion.CALCIUM)
    assert calcium is not None
    assert float(calcium.to("milligram / liter").magnitude) == pytest.approx(65.81975)
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status
        is wce.TargetProfileComparisonStatus.SATISFIED
    )
    assert tuple(notice.code for notice in result.notices) == (
        wce.ForwardNoticeCode.TREATMENT_COMPLETE_DISSOLUTION_MODEL,
    )


def test_public_api_preserves_unknown_and_notice_semantics() -> None:
    """The facade does not turn a bounded report result into a known value."""
    source = wce.SourceWaterProfile(
        name="Bounded source",
        concentrations=(
            wce.IonConcentrationUpperBound.mg_per_liter(
                wce.Ion.CHLORIDE,
                maximum=20.0,
            ),
        ),
    )
    target = wce.TargetWaterProfile(
        name="Chloride target",
        concentrations=(wce.IonConcentration.mg_per_liter(wce.Ion.CHLORIDE, 20.0),),
    )

    result = wce.calculate_forward_water(
        (wce.ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        target_profile=target,
    )

    assert result.final_state.concentration_for(wce.Ion.CHLORIDE) is None
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status
        is wce.TargetProfileComparisonStatus.INDETERMINATE
    )
    assert tuple(notice.code for notice in result.notices) == (
        wce.ForwardNoticeCode.SOURCE_ION_UNRESOLVED,
        wce.ForwardNoticeCode.TARGET_ACTUAL_UNKNOWN,
    )
