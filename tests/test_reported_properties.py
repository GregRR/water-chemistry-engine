from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_, PHValue

from water_chemistry_engine.reported_properties import (
    Alkalinity,
    AlkalinityAnalyticalContext,
    AlkalinityResultIdentity,
    Conductivity,
    ReportedPH,
    ReportingBasis,
    SampleFiltrationState,
    TotalDissolvedSolids,
    TotalHardness,
)
from water_chemistry_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)
from water_chemistry_engine.reported_values import SourceResolutionPolicy

ALLOW_MIDPOINTS = SourceResolutionPolicy(allow_exact_range_midpoints=True)
REPORTED_ONLY = SourceResolutionPolicy(allow_exact_range_midpoints=False)


def test_exact_alkalinity_preserves_as_caco3_basis() -> None:
    measurement = Alkalinity.mg_per_liter_as_caco3(108.0)

    assert measurement.basis is ReportingBasis.AS_CACO3
    assert measurement.value is not None
    assert measurement.reported_average is None
    assert measurement.value.to("milligram / liter").magnitude == 108.0
    assert measurement.calculation_value is measurement.value


def test_alkalinity_preserves_reported_statistic_and_analytical_context() -> None:
    statistic = ReportedStatistic(
        kind=ReportedStatisticKind.REPORTED_AVERAGE,
        label="Average of monthly results",
    )
    analytical_context = AlkalinityAnalyticalContext(
        result_identity=AlkalinityResultIdentity.TOTAL_ALKALINITY,
        sample_filtration_state=SampleFiltrationState.FILTERED,
        original_analyte_label="Alkalinity, Total",
        original_unit_label="mg/L as CaCO3",
        analytical_method="Example laboratory titration",
        method_code="EXAMPLE-ALK-1",
        titration_endpoint=PHValue(4.5),
    )

    measurement = Alkalinity.mg_per_liter_as_caco3(
        108.0,
        reported_statistic=statistic,
        analytical_context=analytical_context,
    )

    assert measurement.reported_statistic is statistic
    assert measurement.analytical_context is analytical_context
    assert measurement.analytical_context.result_identity is (
        AlkalinityResultIdentity.TOTAL_ALKALINITY
    )
    assert measurement.analytical_context.titration_endpoint == PHValue(4.5)


def test_alkalinity_analytical_context_rejects_empty_context() -> None:
    with pytest.raises(ValueError, match="requires at least one reported field"):
        AlkalinityAnalyticalContext()


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("original_analyte_label", " ", "analyte label cannot be empty"),
        ("original_unit_label", "", "unit label cannot be empty"),
        ("analytical_method", "\t", "analytical method cannot be empty"),
        ("method_code", " ", "method code cannot be empty"),
    ),
)
def test_alkalinity_analytical_context_rejects_empty_text(
    field: str,
    value: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        AlkalinityAnalyticalContext(**{field: value})


def test_alkalinity_analytical_context_requires_phvalue_endpoint() -> None:
    with pytest.raises(TypeError, match="must use fermunits.PHValue"):
        AlkalinityAnalyticalContext(titration_endpoint=4.5)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        (
            "result_identity",
            "total_alkalinity",
            "must use AlkalinityResultIdentity",
        ),
        (
            "sample_filtration_state",
            "filtered",
            "must use SampleFiltrationState",
        ),
        ("analytical_method", 2320, "must be text"),
    ),
)
def test_alkalinity_analytical_context_rejects_untyped_metadata(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        AlkalinityAnalyticalContext(**{field: value})  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("reported_statistic", "average", "must use ReportedStatistic"),
        (
            "analytical_context",
            {"result_identity": "total_alkalinity"},
            "must use AlkalinityAnalyticalContext",
        ),
    ),
)
def test_alkalinity_rejects_untyped_source_metadata(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(TypeError, match=message):
        Alkalinity(  # type: ignore[arg-type]
            value=Q_(108.0, "milligram / liter"),
            **{field: value},
        )


def test_reported_property_preserves_decimal_magnitude() -> None:
    value = Q_(Decimal("108.25"), "milligram / liter")
    measurement = Alkalinity(value=value)

    assert measurement.value is not None
    assert measurement.value.magnitude == Decimal("108.25")
    assert measurement.calculation_value is measurement.value


def test_reported_property_mixed_scalar_midpoint_is_float() -> None:
    measurement = TotalDissolvedSolids(
        minimum=Q_(Fraction(1, 5), "gram / liter"),
        maximum=Q_(Decimal("0.250"), "gram / liter"),
    )

    midpoint = measurement.calculation_value_with_policy(ALLOW_MIDPOINTS).to(
        "milligram / liter"
    )

    assert midpoint.magnitude == pytest.approx(225.0)
    assert isinstance(midpoint.magnitude, float)


def test_alkalinity_range_without_average_requires_midpoint_policy() -> None:
    measurement = Alkalinity.mg_per_liter_as_caco3_range(
        minimum=100.0,
        maximum=140.0,
    )

    assert measurement.reported_average is None
    with pytest.raises(
        ValueError,
        match="range alone has no representative calculation value",
    ):
        _ = measurement.calculation_value

    with pytest.raises(ValueError, match="explicit midpoint permission"):
        measurement.calculation_value_with_policy(REPORTED_ONLY)

    midpoint = measurement.calculation_value_with_policy(ALLOW_MIDPOINTS)
    assert midpoint.to("milligram / liter").magnitude == 120.0


def test_alkalinity_reported_average_takes_precedence_over_midpoint() -> None:
    measurement = Alkalinity.mg_per_liter_as_caco3_range(
        minimum=100.0,
        maximum=120.0,
        reported_average=108.0,
    )

    assert measurement.reported_average is not None
    assert measurement.reported_average.to("milligram / liter").magnitude == 108.0
    assert measurement.calculation_value.to("milligram / liter").magnitude == 108.0


@pytest.mark.parametrize(
    ("measurement", "expected_bound"),
    (
        (Alkalinity.mg_per_liter_as_caco3_lower_bound(40.0), 40.0),
        (Alkalinity.mg_per_liter_as_caco3_upper_bound(120.0), 120.0),
    ),
)
def test_alkalinity_bound_is_preserved_without_representative_value(
    measurement: Alkalinity,
    expected_bound: float,
) -> None:
    bound = measurement.minimum or measurement.maximum
    assert bound is not None
    assert bound.to("milligram / liter").magnitude == expected_bound
    with pytest.raises(ValueError, match="bound has no representative"):
        _ = measurement.calculation_value
    with pytest.raises(ValueError, match="bound has no representative"):
        measurement.calculation_value_with_policy(ALLOW_MIDPOINTS)


def test_alkalinity_bound_rejects_reported_average() -> None:
    with pytest.raises(ValueError, match="bound cannot be combined"):
        Alkalinity(
            minimum=Q_(40.0, "milligram / liter"),
            reported_average=Q_(50.0, "milligram / liter"),
        )


def test_total_hardness_preserves_as_caco3_basis() -> None:
    measurement = TotalHardness.mg_per_liter_as_caco3_range(
        minimum=130.0,
        maximum=150.0,
        reported_average=138.0,
    )

    assert measurement.basis is ReportingBasis.AS_CACO3
    assert measurement.calculation_value.to("milligram / liter").magnitude == 138.0


def test_total_hardness_range_without_average_requires_midpoint_policy() -> None:
    measurement = TotalHardness.mg_per_liter_as_caco3_range(
        minimum=130.0,
        maximum=150.0,
    )

    with pytest.raises(ValueError):
        _ = measurement.calculation_value

    midpoint = measurement.calculation_value_with_policy(ALLOW_MIDPOINTS)
    assert midpoint.to("milligram / liter").magnitude == 140.0


def test_conductivity_range_without_average_requires_midpoint_policy() -> None:
    measurement = Conductivity.microsiemens_per_cm_range(
        minimum=180.0,
        maximum=210.0,
    )

    with pytest.raises(ValueError):
        _ = measurement.calculation_value

    midpoint = measurement.calculation_value_with_policy(ALLOW_MIDPOINTS)
    assert midpoint.to("microsiemens / centimeter").magnitude == 195.0


def test_total_dissolved_solids_accepts_mass_concentration() -> None:
    measurement = TotalDissolvedSolids(
        value=Q_(0.225, "gram / liter"),
    )

    assert measurement.calculation_value.to("milligram / liter").magnitude == 225.0


def test_tds_range_without_reported_average_requires_midpoint_policy() -> None:
    measurement = TotalDissolvedSolids.mg_per_liter_range(
        minimum=200.0,
        maximum=250.0,
    )

    with pytest.raises(ValueError):
        _ = measurement.calculation_value

    midpoint = measurement.calculation_value_with_policy(ALLOW_MIDPOINTS)
    assert midpoint.to("milligram / liter").magnitude == 225.0


def test_conductivity_preserves_reference_temperature_and_reported_average() -> None:
    measurement = Conductivity.microsiemens_per_cm_range(
        minimum=180.0,
        maximum=210.0,
        reported_average=192.0,
        reference_temperature_celsius=25.0,
    )

    assert measurement.reported_average is not None
    assert (
        measurement.calculation_value.to("microsiemens / centimeter").magnitude == 192.0
    )
    assert measurement.reference_temperature_celsius == 25.0


def test_reported_average_must_fall_within_range() -> None:
    with pytest.raises(
        ValueError,
        match="reported average must fall within the reported range",
    ):
        Alkalinity.mg_per_liter_as_caco3_range(
            minimum=100.0,
            maximum=120.0,
            reported_average=125.0,
        )


def test_incomplete_range_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="range requires both minimum and maximum",
    ):
        TotalDissolvedSolids(
            minimum=Q_(100, "milligram / liter"),
        )


def test_exact_value_cannot_be_combined_with_reported_average() -> None:
    with pytest.raises(
        ValueError,
        match="exact value cannot be combined",
    ):
        Alkalinity(
            value=Q_(108, "milligram / liter"),
            reported_average=Q_(108, "milligram / liter"),
        )


def test_invalid_alkalinity_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Alkalinity must be convertible to mass per volume",
    ):
        Alkalinity(value=Q_(5, "gram"))


def test_invalid_hardness_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Total hardness must be convertible to mass per volume",
    ):
        TotalHardness(value=Q_(5, "gram"))


def test_invalid_tds_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Total dissolved solids must be convertible to mass per volume",
    ):
        TotalDissolvedSolids(value=Q_(5, "gram"))


def test_invalid_conductivity_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Conductivity must be convertible to electrical conductivity",
    ):
        Conductivity(value=Q_(5, "milligram / liter"))


@pytest.mark.parametrize("invalid", [-1.0, float("nan"), float("inf"), float("-inf")])
def test_reported_linear_properties_reject_invalid_values(invalid: float) -> None:
    constructors = (
        lambda: Alkalinity.mg_per_liter_as_caco3(invalid),
        lambda: TotalHardness.mg_per_liter_as_caco3(invalid),
        lambda: TotalDissolvedSolids.mg_per_liter(invalid),
        lambda: Conductivity.microsiemens_per_cm(invalid),
    )

    for constructor in constructors:
        with pytest.raises(ValueError, match="finite|negative"):
            constructor()


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_reported_linear_property_ranges_reject_non_finite_values(
    invalid: float,
) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        Alkalinity.mg_per_liter_as_caco3_range(
            minimum=10.0,
            maximum=20.0,
            reported_average=invalid,
        )


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_conductivity_rejects_non_finite_reference_temperature(
    invalid: float,
) -> None:
    with pytest.raises(ValueError, match="reference temperature must be finite"):
        Conductivity.microsiemens_per_cm(
            200.0,
            reference_temperature_celsius=invalid,
        )


def test_reported_ph_exact_value_is_usable_for_calculations() -> None:
    measurement = ReportedPH.exact(7.2)

    assert measurement.value == PHValue(7.2)
    assert measurement.reported_average is None
    assert measurement.calculation_value == PHValue(7.2)


def test_reported_ph_preserves_range_without_inventing_average() -> None:
    measurement = ReportedPH.range(
        minimum=7.0,
        maximum=7.4,
    )

    assert measurement.minimum == PHValue(7.0)
    assert measurement.maximum == PHValue(7.4)
    assert measurement.reported_average is None


def test_reported_ph_range_alone_has_no_calculation_value() -> None:
    measurement = ReportedPH.range(
        minimum=7.0,
        maximum=7.4,
    )

    with pytest.raises(
        ValueError,
        match="range alone has no representative calculation value",
    ):
        _ = measurement.calculation_value


def test_reported_ph_uses_reported_average_not_arithmetic_midpoint() -> None:
    measurement = ReportedPH.range(
        minimum=7.0,
        maximum=7.4,
        reported_average=7.1,
    )

    assert measurement.reported_average == PHValue(7.1)
    assert measurement.calculation_value == PHValue(7.1)
    assert measurement.minimum is not None
    assert measurement.maximum is not None
    assert measurement.calculation_value.value != pytest.approx(
        (measurement.minimum.value + measurement.maximum.value) / 2
    )


def test_reported_ph_can_store_reported_average_without_range() -> None:
    measurement = ReportedPH.average(7.35)

    assert measurement.value is None
    assert measurement.minimum is None
    assert measurement.maximum is None
    assert measurement.reported_average == PHValue(7.35)
    assert measurement.calculation_value == PHValue(7.35)


@pytest.mark.parametrize("value", [-0.1, 14.1])
def test_reported_ph_does_not_impose_a_universal_zero_to_fourteen_range(
    value: float,
) -> None:
    measurement = ReportedPH.exact(value)

    assert measurement.value == PHValue(value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_reported_ph_rejects_non_finite_values(value: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        ReportedPH.exact(value)


def test_reported_ph_fields_require_semantic_ph_values() -> None:
    with pytest.raises(TypeError, match="fermunits.PHValue"):
        ReportedPH(value=7.2)  # type: ignore[arg-type]


def test_reported_ph_rejects_reversed_range() -> None:
    with pytest.raises(
        ValueError,
        match="minimum cannot exceed maximum",
    ):
        ReportedPH.range(
            minimum=8.0,
            maximum=7.0,
        )


def test_reported_ph_average_must_fall_within_reported_range() -> None:
    with pytest.raises(
        ValueError,
        match="reported average must fall within the reported range",
    ):
        ReportedPH.range(
            minimum=7.0,
            maximum=7.4,
            reported_average=7.5,
        )


def test_reported_ph_rejects_incomplete_range() -> None:
    with pytest.raises(
        ValueError,
        match="range requires both minimum and maximum",
    ):
        ReportedPH(minimum=PHValue(7.0))


def test_exact_ph_cannot_be_combined_with_reported_average() -> None:
    with pytest.raises(
        ValueError,
        match="exact value cannot be combined",
    ):
        ReportedPH(
            value=PHValue(7.2),
            reported_average=PHValue(7.2),
        )


def test_reported_property_preserves_result_specific_context() -> None:
    from datetime import date

    from water_chemistry_engine.reporting_context import (
        ObservationPeriod,
        ReportedResultContext,
        ResultCoverage,
        WaterStage,
    )

    context = ReportedResultContext(
        observation_period=ObservationPeriod(
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
        ),
        coverage=ResultCoverage.OBSERVATION_PERIOD_SUMMARY,
        water_stage=WaterStage.TREATMENT_PLANT_OUTPUT,
        sample_location="Example Treatment Plant",
    )

    measurement = Alkalinity(
        value=Q_(108, "milligram / liter"),
        result_context=context,
    )

    assert measurement.result_context is context


def test_reported_ph_preserves_result_specific_context() -> None:
    from water_chemistry_engine.reporting_context import (
        ReportedResultContext,
        ResultCoverage,
    )

    context = ReportedResultContext(
        coverage=ResultCoverage.TYPICAL_ANALYSIS,
    )

    measurement = ReportedPH(
        reported_average=PHValue(7.2),
        result_context=context,
    )

    assert measurement.result_context is context
