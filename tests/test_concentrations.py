from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_

from water_chemistry_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    LowerBoundConcentrationEndpoint,
    NotDetectedConcentrationEndpoint,
    UpperBoundConcentrationEndpoint,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)
from water_chemistry_engine.reported_values import SourceResolutionPolicy

ALLOW_MIDPOINTS = SourceResolutionPolicy(allow_exact_range_midpoints=True)
REPORTED_ONLY = SourceResolutionPolicy(allow_exact_range_midpoints=False)


def test_mg_per_liter_constructor() -> None:
    concentration = IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0)

    assert concentration.ion is Ion.CALCIUM
    assert concentration.value.magnitude == 50.0
    assert concentration.value.units == Q_(1, "milligram / liter").units
    assert concentration.calculation_value is concentration.value


def test_reported_scalar_magnitudes_are_preserved() -> None:
    decimal_value = Q_(Decimal("12.50"), "milligram / liter")
    fraction_value = Q_(Fraction(25, 2), "milligram / liter")

    decimal_concentration = IonConcentration(
        ion=Ion.CALCIUM,
        value=decimal_value,
    )
    fraction_concentration = IonConcentration(
        ion=Ion.MAGNESIUM,
        value=fraction_value,
    )

    assert decimal_concentration.value.magnitude == Decimal("12.50")
    assert fraction_concentration.value.magnitude == Fraction(25, 2)


def test_mixed_scalar_range_midpoint_is_derived_as_float() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=ExactConcentrationEndpoint(Q_(Decimal("50.0"), "milligram / liter")),
        maximum=ExactConcentrationEndpoint(Q_(Fraction(3, 20), "gram / liter")),
    )

    midpoint = concentration.calculation_value_with_policy(ALLOW_MIDPOINTS).to(
        "milligram / liter"
    )

    assert midpoint.magnitude == pytest.approx(100.0)
    assert isinstance(midpoint.magnitude, float)


def test_exact_result_can_preserve_reported_statistic() -> None:
    statistic = ReportedStatistic.percentile_result(90.0)
    concentration = IonConcentration(
        ion=Ion.SODIUM,
        value=Q_(12, "milligram / liter"),
        reported_statistic=statistic,
    )

    assert concentration.reported_statistic is statistic


def test_non_concentration_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Ion concentration must be convertible to mass per volume",
    ):
        IonConcentration(
            ion=Ion.SODIUM,
            value=Q_(5, "gram"),
        )


@pytest.mark.parametrize("invalid", [-1.0, float("nan"), float("inf"), float("-inf")])
def test_all_numeric_concentration_forms_reject_invalid_values(invalid: float) -> None:
    constructors = (
        lambda: IonConcentration.mg_per_liter(Ion.SODIUM, invalid),
        lambda: ExactConcentrationEndpoint.mg_per_liter(invalid),
        lambda: UpperBoundConcentrationEndpoint.mg_per_liter(invalid),
        lambda: LowerBoundConcentrationEndpoint.mg_per_liter(invalid),
        lambda: NotDetectedConcentrationEndpoint.with_detection_limit_mg_per_liter(
            invalid
        ),
        lambda: IonConcentrationUpperBound.mg_per_liter(Ion.SODIUM, invalid),
        lambda: IonConcentrationLowerBound.mg_per_liter(Ion.SODIUM, invalid),
        lambda: IonConcentrationNotDetected.with_detection_limit_mg_per_liter(
            Ion.SODIUM,
            invalid,
        ),
    )

    for constructor in constructors:
        with pytest.raises(ValueError, match="finite|negative"):
            constructor()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_concentration_range_rejects_non_finite_reported_average(
    invalid: float,
) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        IonConcentrationRange.mg_per_liter(
            Ion.CALCIUM,
            minimum=10.0,
            maximum=20.0,
            reported_average=invalid,
        )


def test_exact_concentration_range_constructor() -> None:
    concentration = IonConcentrationRange.mg_per_liter(
        Ion.SULFATE,
        minimum=50.0,
        maximum=150.0,
    )

    assert isinstance(concentration.minimum, ExactConcentrationEndpoint)
    assert isinstance(concentration.maximum, ExactConcentrationEndpoint)
    assert concentration.minimum.value.magnitude == 50.0
    assert concentration.maximum.value.magnitude == 150.0
    assert concentration.reported_average is None


def test_exact_range_without_reported_average_requires_midpoint_policy() -> None:
    concentration = IonConcentrationRange.mg_per_liter(
        Ion.SULFATE,
        minimum=50.0,
        maximum=150.0,
    )

    with pytest.raises(
        ValueError,
        match="range alone has no representative calculation value",
    ):
        _ = concentration.calculation_value

    with pytest.raises(ValueError, match="explicit midpoint permission"):
        concentration.calculation_value_with_policy(REPORTED_ONLY)

    midpoint = concentration.calculation_value_with_policy(ALLOW_MIDPOINTS)
    assert midpoint.to("milligram / liter").magnitude == 100.0


def test_reported_average_takes_precedence_over_midpoint() -> None:
    concentration = IonConcentrationRange.mg_per_liter(
        Ion.CALCIUM,
        minimum=50.0,
        maximum=53.0,
        reported_average=51.0,
    )

    assert concentration.reported_average is not None
    assert concentration.calculation_value.to("milligram / liter").magnitude == 51.0


def test_reported_average_can_be_qualified_by_statistic_type() -> None:
    statistic = ReportedStatistic(
        kind=ReportedStatisticKind.RUNNING_ANNUAL_AVERAGE,
    )
    concentration = IonConcentrationRange(
        ion=Ion.CHLORIDE,
        minimum=ExactConcentrationEndpoint.mg_per_liter(10.0),
        maximum=ExactConcentrationEndpoint.mg_per_liter(20.0),
        reported_average=Q_(14, "milligram / liter"),
        reported_statistic=statistic,
    )

    assert concentration.reported_statistic is statistic
    assert concentration.calculation_value.to("milligram / liter").magnitude == 14.0


def test_reported_average_must_fall_within_exact_range() -> None:
    with pytest.raises(
        ValueError,
        match="reported average must fall within the reported range",
    ):
        IonConcentrationRange.mg_per_liter(
            Ion.CALCIUM,
            minimum=50.0,
            maximum=53.0,
            reported_average=54.0,
        )


def test_exact_range_rejects_reversed_bounds() -> None:
    with pytest.raises(
        ValueError,
        match="range minimum cannot exceed maximum",
    ):
        IonConcentrationRange.mg_per_liter(
            Ion.SODIUM,
            minimum=100.0,
            maximum=50.0,
        )


def test_upper_bound_concentration() -> None:
    concentration = IonConcentrationUpperBound.mg_per_liter(
        Ion.SODIUM,
        maximum=5.0,
    )

    assert concentration.maximum.to("milligram / liter").magnitude == 5.0


def test_lower_bound_concentration() -> None:
    concentration = IonConcentrationLowerBound.mg_per_liter(
        Ion.SULFATE,
        minimum=100.0,
    )

    assert concentration.minimum.to("milligram / liter").magnitude == 100.0


def test_not_detected_is_distinct_from_zero() -> None:
    concentration = IonConcentrationNotDetected(ion=Ion.CHLORIDE)

    assert concentration.detection_limit is None


def test_not_detected_can_preserve_explicit_detection_limit() -> None:
    concentration = IonConcentrationNotDetected.with_detection_limit_mg_per_liter(
        Ion.CHLORIDE,
        detection_limit=0.3,
    )

    assert concentration.detection_limit is not None
    assert concentration.detection_limit.to(
        "milligram / liter"
    ).magnitude == pytest.approx(0.3)


def test_qualified_range_supports_less_than_endpoint() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.SODIUM,
        minimum=UpperBoundConcentrationEndpoint.mg_per_liter(3.0),
        maximum=ExactConcentrationEndpoint.mg_per_liter(14.0),
    )

    assert isinstance(
        concentration.minimum,
        UpperBoundConcentrationEndpoint,
    )
    assert concentration.minimum.limit.to("milligram / liter").magnitude == 3.0


def test_qualified_range_supports_not_detected_endpoint() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=NotDetectedConcentrationEndpoint(),
        maximum=ExactConcentrationEndpoint.mg_per_liter(11.1),
    )

    assert isinstance(
        concentration.minimum,
        NotDetectedConcentrationEndpoint,
    )


def test_qualified_range_rejects_reversed_numeric_thresholds() -> None:
    with pytest.raises(
        ValueError,
        match="range minimum cannot exceed maximum",
    ):
        IonConcentrationRange(
            ion=Ion.SODIUM,
            minimum=UpperBoundConcentrationEndpoint.mg_per_liter(20.0),
            maximum=ExactConcentrationEndpoint.mg_per_liter(14.0),
        )


def test_lower_and_upper_bound_range_rejects_reversed_thresholds() -> None:
    with pytest.raises(
        ValueError,
        match="range minimum cannot exceed maximum",
    ):
        IonConcentrationRange(
            ion=Ion.SODIUM,
            minimum=LowerBoundConcentrationEndpoint.mg_per_liter(20.0),
            maximum=UpperBoundConcentrationEndpoint.mg_per_liter(14.0),
        )


def test_not_detected_limit_participates_in_range_coherence() -> None:
    with pytest.raises(
        ValueError,
        match="range minimum cannot exceed maximum",
    ):
        IonConcentrationRange(
            ion=Ion.SULFATE,
            minimum=NotDetectedConcentrationEndpoint.with_detection_limit_mg_per_liter(
                20.0
            ),
            maximum=ExactConcentrationEndpoint.mg_per_liter(14.0),
        )


def test_not_detected_without_limit_skips_numeric_coherence_check() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=NotDetectedConcentrationEndpoint(),
        maximum=ExactConcentrationEndpoint.mg_per_liter(0.0),
    )

    assert isinstance(concentration.minimum, NotDetectedConcentrationEndpoint)


def test_qualified_range_has_no_automatic_midpoint() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=NotDetectedConcentrationEndpoint(),
        maximum=ExactConcentrationEndpoint.mg_per_liter(11.1),
    )

    with pytest.raises(
        ValueError,
        match="qualified concentration range has no automatic representative",
    ):
        _ = concentration.calculation_value


def test_qualified_range_uses_real_reported_average_when_present() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=NotDetectedConcentrationEndpoint(),
        maximum=ExactConcentrationEndpoint.mg_per_liter(11.1),
        reported_average=Q_(4.2, "milligram / liter"),
    )

    assert concentration.calculation_value.to("milligram / liter").magnitude == 4.2


def test_invalid_endpoint_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Ion concentration must be convertible to mass per volume",
    ):
        UpperBoundConcentrationEndpoint(limit=Q_(3, "milligram"))


def test_ion_result_preserves_result_specific_context() -> None:
    from datetime import date

    from water_chemistry_engine.reporting_context import (
        ReportedResultContext,
        ResultCoverage,
        WaterStage,
    )

    context = ReportedResultContext(
        observed_on=date(2023, 6, 1),
        coverage=ResultCoverage.SINGLE_OBSERVATION,
        water_stage=WaterStage.TREATMENT_PLANT_OUTPUT,
        sample_location="Example Treatment Plant",
    )

    concentration = IonConcentration(
        ion=Ion.CALCIUM,
        value=Q_(50, "milligram / liter"),
        result_context=context,
    )

    assert concentration.result_context is context


def test_not_detected_result_preserves_result_specific_context() -> None:
    from water_chemistry_engine.reporting_context import (
        ReportedResultContext,
        ResultCoverage,
    )

    context = ReportedResultContext(
        coverage=ResultCoverage.TYPICAL_ANALYSIS,
    )

    concentration = IonConcentrationNotDetected(
        ion=Ion.CHLORIDE,
        result_context=context,
    )

    assert concentration.result_context is context
