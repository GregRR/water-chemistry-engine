import pytest
from fermunits import Q_
from water_treatment_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_treatment_engine.ions import Ion


def test_mg_per_liter_constructor() -> None:
    concentration = IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0)

    assert concentration.ion is Ion.CALCIUM
    assert concentration.value.magnitude == 50.0
    assert concentration.value.units == Q_(1, "milligram / liter").units


def test_equivalent_mass_concentration_is_accepted() -> None:
    concentration = IonConcentration(
        ion=Ion.MAGNESIUM,
        value=Q_(0.025, "gram / liter"),
    )

    assert concentration.value.to("milligram / liter").magnitude == 25.0


def test_non_concentration_quantity_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Ion concentration must be convertible to mass per volume",
    ):
        IonConcentration(
            ion=Ion.SODIUM,
            value=Q_(5, "gram"),
        )


def test_concentration_range_constructor() -> None:
    concentration = IonConcentrationRange.mg_per_liter(
        Ion.SULFATE,
        minimum=50.0,
        maximum=150.0,
    )

    assert concentration.ion is Ion.SULFATE
    assert concentration.minimum.magnitude == 50.0
    assert concentration.maximum.magnitude == 150.0


def test_concentration_range_accepts_convertible_units() -> None:
    concentration = IonConcentrationRange(
        ion=Ion.CHLORIDE,
        minimum=Q_(0.025, "gram / liter"),
        maximum=Q_(75, "milligram / liter"),
    )

    assert concentration.minimum.to("milligram / liter").magnitude == 25.0
    assert concentration.maximum.to("milligram / liter").magnitude == 75.0


def test_concentration_range_rejects_reversed_bounds() -> None:
    with pytest.raises(
        ValueError,
        match="range minimum cannot exceed maximum",
    ):
        IonConcentrationRange.mg_per_liter(
            Ion.SODIUM,
            minimum=100.0,
            maximum=50.0,
        )


def test_concentration_range_rejects_non_concentration_quantity() -> None:
    with pytest.raises(
        ValueError,
        match="Ion concentration must be convertible to mass per volume",
    ):
        IonConcentrationRange(
            ion=Ion.POTASSIUM,
            minimum=Q_(10, "milligram / liter"),
            maximum=Q_(20, "milligram"),
        )


def test_upper_bound_constructor() -> None:
    concentration = IonConcentrationUpperBound.mg_per_liter(
        Ion.SODIUM,
        maximum=5.0,
    )

    assert concentration.ion is Ion.SODIUM
    assert concentration.maximum.magnitude == 5.0
    assert concentration.maximum.units == Q_(1, "milligram / liter").units


def test_upper_bound_accepts_convertible_units() -> None:
    concentration = IonConcentrationUpperBound(
        ion=Ion.MAGNESIUM,
        maximum=Q_(0.005, "gram / liter"),
    )

    assert concentration.maximum.to("milligram / liter").magnitude == 5.0


def test_upper_bound_rejects_negative_value() -> None:
    with pytest.raises(
        ValueError,
        match="upper bound cannot be negative",
    ):
        IonConcentrationUpperBound.mg_per_liter(
            Ion.CHLORIDE,
            maximum=-1.0,
        )


def test_upper_bound_rejects_non_concentration_quantity() -> None:
    with pytest.raises(
        ValueError,
        match="Ion concentration must be convertible to mass per volume",
    ):
        IonConcentrationUpperBound(
            ion=Ion.CALCIUM,
            maximum=Q_(5, "milligram"),
        )
