from decimal import Decimal

import pytest
from fermunits import Q_

from water_chemistry_engine.alkalinity_conversions import (
    bicarbonate_from_bicarbonate_alkalinity_as_caco3,
)


def test_bicarbonate_alkalinity_as_caco3_converts_by_equivalent_mass() -> None:
    # USGS documents ~50.04 g/eq for alkalinity reported as CaCO3 and
    # 61.0173 g/eq for alkalinity reported as HCO3. Therefore 100 mg/L
    # bicarbonate alkalinity as CaCO3 corresponds to about 121.94 mg/L HCO3.
    result = bicarbonate_from_bicarbonate_alkalinity_as_caco3(
        Q_(100.0, "milligram / liter")
    )

    assert result.to("milligram / liter").magnitude == pytest.approx(121.93705035971222)


def test_conversion_accepts_decimal_and_returns_float_result() -> None:
    result = bicarbonate_from_bicarbonate_alkalinity_as_caco3(
        Q_(Decimal("100.0"), "milligram / liter")
    )

    assert result.to("milligram / liter").magnitude == pytest.approx(121.93705035971222)
    assert isinstance(result.magnitude, float)


def test_conversion_accepts_other_mass_per_volume_units() -> None:
    result = bicarbonate_from_bicarbonate_alkalinity_as_caco3(Q_(0.1, "gram / liter"))

    assert result.to("milligram / liter").magnitude == pytest.approx(121.93705035971222)


def test_zero_bicarbonate_alkalinity_remains_zero() -> None:
    result = bicarbonate_from_bicarbonate_alkalinity_as_caco3(
        Q_(0.0, "milligram / liter")
    )

    assert result.to("milligram / liter").magnitude == 0.0


def test_negative_bicarbonate_alkalinity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Bicarbonate alkalinity cannot be negative",
    ):
        bicarbonate_from_bicarbonate_alkalinity_as_caco3(Q_(-1.0, "milligram / liter"))


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_bicarbonate_alkalinity_is_rejected(invalid: float) -> None:
    with pytest.raises(ValueError, match="must be finite"):
        bicarbonate_from_bicarbonate_alkalinity_as_caco3(
            Q_(invalid, "milligram / liter")
        )


def test_non_concentration_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="must be convertible to mass per volume",
    ):
        bicarbonate_from_bicarbonate_alkalinity_as_caco3(Q_(1.0, "gram"))
