import pytest
from fermunits import Q_
from water_treatment_engine.reported_properties import (
    Alkalinity,
    Conductivity,
    ReportingBasis,
    TotalDissolvedSolids,
    TotalHardness,
)


def test_exact_alkalinity_preserves_as_caco3_basis() -> None:
    measurement = Alkalinity.mg_per_liter_as_caco3(108.0)

    assert measurement.basis is ReportingBasis.AS_CACO3
    assert measurement.value is not None
    assert measurement.reported_average is None
    assert measurement.value.to("milligram / liter").magnitude == 108.0
    assert measurement.calculation_value is measurement.value


def test_alkalinity_range_without_average_uses_midpoint() -> None:
    measurement = Alkalinity.mg_per_liter_as_caco3_range(
        minimum=100.0,
        maximum=140.0,
    )

    assert measurement.reported_average is None
    assert measurement.calculation_value.to("milligram / liter").magnitude == 120.0


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


def test_total_dissolved_solids_accepts_mass_concentration() -> None:
    measurement = TotalDissolvedSolids(
        value=Q_(0.225, "gram / liter"),
    )

    assert measurement.calculation_value.to("milligram / liter").magnitude == 225.0


def test_tds_range_without_reported_average_uses_midpoint() -> None:
    measurement = TotalDissolvedSolids.mg_per_liter_range(
        minimum=200.0,
        maximum=250.0,
    )

    assert measurement.calculation_value.to("milligram / liter").magnitude == 225.0


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
