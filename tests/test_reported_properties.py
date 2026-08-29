from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_

from water_chemistry_engine.reported_properties import (
    Alkalinity,
    Conductivity,
    ReportedPH,
    ReportingBasis,
    TotalDissolvedSolids,
    TotalHardness,
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


def test_reported_ph_exact_value_is_usable_for_calculations() -> None:
    measurement = ReportedPH.exact(7.2)

    assert measurement.value == 7.2
    assert measurement.reported_average is None
    assert measurement.calculation_value == 7.2


def test_reported_ph_preserves_range_without_inventing_average() -> None:
    measurement = ReportedPH.range(
        minimum=7.0,
        maximum=7.4,
    )

    assert measurement.minimum == 7.0
    assert measurement.maximum == 7.4
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

    assert measurement.reported_average == 7.1
    assert measurement.calculation_value == 7.1
    assert measurement.calculation_value != pytest.approx(
        (measurement.minimum + measurement.maximum) / 2
    )


def test_reported_ph_can_store_reported_average_without_range() -> None:
    measurement = ReportedPH.average(7.35)

    assert measurement.value is None
    assert measurement.minimum is None
    assert measurement.maximum is None
    assert measurement.reported_average == 7.35
    assert measurement.calculation_value == 7.35


def test_reported_ph_rejects_out_of_range_value() -> None:
    with pytest.raises(
        ValueError,
        match="between 0 and 14",
    ):
        ReportedPH.exact(14.1)


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
        ReportedPH(minimum=7.0)


def test_exact_ph_cannot_be_combined_with_reported_average() -> None:
    with pytest.raises(
        ValueError,
        match="exact value cannot be combined",
    ):
        ReportedPH(
            value=7.2,
            reported_average=7.2,
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
        reported_average=7.2,
        result_context=context,
    )

    assert measurement.result_context is context
