import pytest
from fermunits import Q_
from hypothesis import given
from hypothesis import strategies as st
from pint import Quantity

from water_chemistry_engine.blending import BlendSource, blend_waters
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    UpperBoundConcentrationEndpoint,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.target_comparison import (
    TargetIonComparisonStatus,
    TargetPHComparisonStatus,
    TargetProfileComparisonStatus,
    UnsupportedTargetIonReason,
    compare_state_to_target,
)
from water_chemistry_engine.target_profiles import TargetWaterProfile


def _state(**values: float) -> AqueousChemicalState:
    return AqueousChemicalState(
        concentrations=tuple(
            DerivedIonConcentration.mg_per_liter(Ion(name), value)
            for name, value in values.items()
        )
    )


def _mg_per_liter(value: Quantity[float]) -> float:
    return float(value.to("milligram / liter").magnitude)


def test_exact_target_reports_signed_raw_deviation() -> None:
    target = TargetWaterProfile(
        name="Exact target",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
    )

    below = compare_state_to_target(_state(calcium=45.0), target).comparison_for(
        Ion.CALCIUM
    )
    at_target = compare_state_to_target(_state(calcium=50.0), target).comparison_for(
        Ion.CALCIUM
    )
    above = compare_state_to_target(_state(calcium=55.0), target).comparison_for(
        Ion.CALCIUM
    )

    assert below is not None
    assert below.status is TargetIonComparisonStatus.BELOW_TARGET
    assert below.deviation is not None
    assert _mg_per_liter(below.deviation) == pytest.approx(-5.0)

    assert at_target is not None
    assert at_target.status is TargetIonComparisonStatus.WITHIN_TARGET
    assert at_target.deviation is not None
    assert _mg_per_liter(at_target.deviation) == 0.0

    assert above is not None
    assert above.status is TargetIonComparisonStatus.ABOVE_TARGET
    assert above.deviation is not None
    assert _mg_per_liter(above.deviation) == pytest.approx(5.0)


def test_exact_ended_range_is_inclusive_and_measures_distance_to_range() -> None:
    target = TargetWaterProfile(
        name="Range target",
        concentrations=(
            IonConcentrationRange.mg_per_liter(
                Ion.SULFATE,
                minimum=100.0,
                maximum=150.0,
            ),
        ),
    )

    minimum = compare_state_to_target(_state(sulfate=100.0), target).comparison_for(
        Ion.SULFATE
    )
    inside = compare_state_to_target(_state(sulfate=125.0), target).comparison_for(
        Ion.SULFATE
    )
    maximum = compare_state_to_target(_state(sulfate=150.0), target).comparison_for(
        Ion.SULFATE
    )
    below = compare_state_to_target(_state(sulfate=90.0), target).comparison_for(
        Ion.SULFATE
    )
    above = compare_state_to_target(_state(sulfate=170.0), target).comparison_for(
        Ion.SULFATE
    )

    for comparison in (minimum, inside, maximum):
        assert comparison is not None
        assert comparison.status is TargetIonComparisonStatus.WITHIN_TARGET
        assert comparison.deviation is not None
        assert _mg_per_liter(comparison.deviation) == 0.0

    assert below is not None and below.deviation is not None
    assert below.status is TargetIonComparisonStatus.BELOW_TARGET
    assert _mg_per_liter(below.deviation) == pytest.approx(-10.0)

    assert above is not None and above.deviation is not None
    assert above.status is TargetIonComparisonStatus.ABOVE_TARGET
    assert _mg_per_liter(above.deviation) == pytest.approx(20.0)


def test_missing_actual_ion_is_indeterminate_not_zero() -> None:
    target = TargetWaterProfile(
        name="Missing actual",
        concentrations=(IonConcentration.mg_per_liter(Ion.MAGNESIUM, 10.0),),
    )

    result = compare_state_to_target(_state(calcium=50.0), target)
    comparison = result.comparison_for(Ion.MAGNESIUM)

    assert comparison is not None
    assert comparison.actual_concentration is None
    assert comparison.status is TargetIonComparisonStatus.ACTUAL_UNKNOWN
    assert comparison.deviation is None
    assert result.status is TargetProfileComparisonStatus.INDETERMINATE


def test_explicit_zero_actual_is_compared_as_known_zero() -> None:
    target = TargetWaterProfile(
        name="Known zero",
        concentrations=(IonConcentration.mg_per_liter(Ion.SODIUM, 10.0),),
    )

    comparison = compare_state_to_target(_state(sodium=0.0), target).comparison_for(
        Ion.SODIUM
    )

    assert comparison is not None
    assert comparison.actual_concentration is not None
    assert comparison.status is TargetIonComparisonStatus.BELOW_TARGET
    assert comparison.deviation is not None
    assert _mg_per_liter(comparison.deviation) == pytest.approx(-10.0)


def test_one_sided_numeric_target_bounds_are_comparable() -> None:
    target = TargetWaterProfile(
        name="Bound targets",
        concentrations=(
            IonConcentrationUpperBound(
                ion=Ion.SODIUM,
                maximum=Q_(20.0, "milligram / liter"),
            ),
            IonConcentrationLowerBound(
                ion=Ion.CALCIUM,
                minimum=Q_(50.0, "milligram / liter"),
            ),
        ),
    )

    result = compare_state_to_target(_state(sodium=25.0, calcium=55.0), target)
    sodium = result.comparison_for(Ion.SODIUM)
    calcium = result.comparison_for(Ion.CALCIUM)

    assert sodium is not None and sodium.deviation is not None
    assert sodium.status is TargetIonComparisonStatus.ABOVE_TARGET
    assert sodium.target_minimum is None
    assert sodium.target_maximum is not None
    assert _mg_per_liter(sodium.deviation) == pytest.approx(5.0)

    assert calcium is not None and calcium.deviation is not None
    assert calcium.status is TargetIonComparisonStatus.WITHIN_TARGET
    assert calcium.target_minimum is not None
    assert calcium.target_maximum is None
    assert _mg_per_liter(calcium.deviation) == 0.0
    assert result.status is TargetProfileComparisonStatus.NOT_SATISFIED


def test_qualified_range_target_is_explicitly_unsupported() -> None:
    target_range = IonConcentrationRange(
        ion=Ion.CHLORIDE,
        minimum=ExactConcentrationEndpoint.mg_per_liter(0.0),
        maximum=UpperBoundConcentrationEndpoint.mg_per_liter(50.0),
    )
    target = TargetWaterProfile(
        name="Qualified reference",
        concentrations=(target_range,),
    )

    result = compare_state_to_target(_state(chloride=25.0), target)
    comparison = result.comparison_for(Ion.CHLORIDE)

    assert comparison is not None
    assert comparison.status is TargetIonComparisonStatus.TARGET_UNSUPPORTED
    assert comparison.unsupported_reason is UnsupportedTargetIonReason.QUALIFIED_RANGE
    assert comparison.deviation is None
    assert result.status is TargetProfileComparisonStatus.INDETERMINATE


def test_not_detected_target_is_not_reinterpreted_as_zero() -> None:
    target = TargetWaterProfile(
        name="ND reference",
        concentrations=(
            IonConcentrationNotDetected.with_detection_limit_mg_per_liter(
                Ion.CARBONATE,
                0.5,
            ),
        ),
    )

    comparison = compare_state_to_target(
        _state(carbonate=0.0),
        target,
    ).comparison_for(Ion.CARBONATE)

    assert comparison is not None
    assert comparison.status is TargetIonComparisonStatus.TARGET_UNSUPPORTED
    assert comparison.unsupported_reason is UnsupportedTargetIonReason.NOT_DETECTED
    assert comparison.deviation is None


def test_target_ph_is_retained_as_explicit_not_calculated_outcome() -> None:
    target = TargetWaterProfile(
        name="Target with pH",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
        ph=7.0,
    )

    result = compare_state_to_target(_state(calcium=50.0), target)

    assert result.ph_comparison is not None
    assert result.ph_comparison.target_ph == 7.0
    assert result.ph_comparison.actual_ph is None
    assert result.ph_comparison.status is TargetPHComparisonStatus.NOT_CALCULATED
    assert result.status is TargetProfileComparisonStatus.INDETERMINATE


def test_all_comparable_ion_targets_satisfied_has_satisfied_summary() -> None:
    target = TargetWaterProfile(
        name="Satisfied target",
        concentrations=(
            IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
            IonConcentrationRange.mg_per_liter(Ion.SULFATE, 80.0, 120.0),
        ),
    )

    result = compare_state_to_target(_state(calcium=50.0, sulfate=100.0), target)

    assert result.status is TargetProfileComparisonStatus.SATISFIED


def test_empty_target_profile_has_no_criteria_summary() -> None:
    result = compare_state_to_target(
        _state(calcium=50.0),
        TargetWaterProfile(name="Empty target", concentrations=()),
    )

    assert result.ion_comparisons == ()
    assert result.ph_comparison is None
    assert result.status is TargetProfileComparisonStatus.NO_CRITERIA


def test_comparison_order_follows_target_profile_order() -> None:
    target = TargetWaterProfile(
        name="Ordered target",
        concentrations=(
            IonConcentration.mg_per_liter(Ion.SULFATE, 100.0),
            IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
        ),
    )

    result = compare_state_to_target(_state(calcium=50.0, sulfate=100.0), target)

    assert [comparison.ion for comparison in result.ion_comparisons] == [
        Ion.SULFATE,
        Ion.CALCIUM,
    ]
    assert result.comparison_for(Ion.MAGNESIUM) is None


def test_equal_chemistry_thirds_blend_satisfies_exact_target() -> None:
    source = _state(calcium=50.0)
    blend = blend_waters(
        (
            BlendSource("First", source, Q_(1.0, "liter")),
            BlendSource("Second", source, Q_(1.0, "liter")),
            BlendSource("Third", source, Q_(1.0, "liter")),
        )
    )
    target = TargetWaterProfile(
        name="Exact calcium",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
    )

    result = compare_state_to_target(blend.state, target)
    comparison = result.comparison_for(Ion.CALCIUM)

    assert comparison is not None
    assert comparison.status is TargetIonComparisonStatus.WITHIN_TARGET
    assert comparison.deviation is not None
    assert _mg_per_liter(comparison.deviation) == 0.0
    assert result.status is TargetProfileComparisonStatus.SATISFIED


_TARGET_VALUES = st.floats(
    min_value=0.0,
    max_value=1000.0,
    allow_nan=False,
    allow_infinity=False,
)
_POSITIVE_VOLUMES = st.lists(
    st.floats(
        min_value=0.001,
        max_value=1000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    min_size=1,
    max_size=6,
)


@given(concentration=_TARGET_VALUES, volumes=_POSITIVE_VOLUMES)
def test_blending_identical_chemistry_preserves_exact_target_status(
    concentration: float,
    volumes: list[float],
) -> None:
    source_state = _state(calcium=concentration)
    blend = blend_waters(
        tuple(
            BlendSource(
                f"Source {index}",
                source_state,
                Q_(volume, "liter"),
            )
            for index, volume in enumerate(volumes)
        )
    )
    target = TargetWaterProfile(
        name="Exact calcium",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, concentration),),
    )

    comparison = compare_state_to_target(blend.state, target).comparison_for(
        Ion.CALCIUM
    )

    assert comparison is not None
    assert comparison.status is TargetIonComparisonStatus.WITHIN_TARGET
    assert comparison.deviation is not None
    assert _mg_per_liter(comparison.deviation) == 0.0


@given(actual=_TARGET_VALUES, target_value=_TARGET_VALUES)
def test_exact_target_deviation_sign_matches_status(
    actual: float,
    target_value: float,
) -> None:
    target = TargetWaterProfile(
        name="Exact target",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, target_value),),
    )

    comparison = compare_state_to_target(
        _state(calcium=actual),
        target,
    ).comparison_for(Ion.CALCIUM)

    assert comparison is not None
    assert comparison.deviation is not None
    deviation = _mg_per_liter(comparison.deviation)
    if comparison.status is TargetIonComparisonStatus.BELOW_TARGET:
        assert deviation < 0.0
    elif comparison.status is TargetIonComparisonStatus.ABOVE_TARGET:
        assert deviation > 0.0
    else:
        assert comparison.status is TargetIonComparisonStatus.WITHIN_TARGET
        assert deviation == 0.0


def test_definite_failure_takes_precedence_over_indeterminate_criterion() -> None:
    target = TargetWaterProfile(
        name="Mixed outcome",
        concentrations=(
            IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
            IonConcentration.mg_per_liter(Ion.SULFATE, 100.0),
        ),
    )

    result = compare_state_to_target(_state(calcium=40.0), target)

    calcium = result.comparison_for(Ion.CALCIUM)
    sulfate = result.comparison_for(Ion.SULFATE)
    assert calcium is not None
    assert calcium.status is TargetIonComparisonStatus.BELOW_TARGET
    assert sulfate is not None
    assert sulfate.status is TargetIonComparisonStatus.ACTUAL_UNKNOWN
    assert result.status is TargetProfileComparisonStatus.NOT_SATISFIED
