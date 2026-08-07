import pytest
from fermunits import Q_
from water_treatment_engine.concentrations import IonConcentration
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
