from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_
from water_treatment_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_treatment_engine.ions import Ion


def test_derived_concentration_normalizes_to_float_mg_per_liter() -> None:
    concentration = DerivedIonConcentration.from_quantity(
        Ion.CALCIUM,
        Q_(Decimal("0.125"), "gram / liter"),
    )

    assert concentration.concentration.units == Q_(1, "milligram / liter").units
    assert concentration.concentration.magnitude == pytest.approx(125.0)
    assert isinstance(concentration.concentration.magnitude, float)


def test_fraction_magnitude_is_supported_at_derived_state_boundary() -> None:
    concentration = DerivedIonConcentration.from_quantity(
        Ion.MAGNESIUM,
        Q_(Fraction(1, 40), "gram / liter"),
    )

    assert concentration.concentration.magnitude == pytest.approx(25.0)
    assert isinstance(concentration.concentration.magnitude, float)


def test_derived_concentration_rejects_non_concentration_quantity() -> None:
    with pytest.raises(ValueError, match="convertible to mass per volume"):
        DerivedIonConcentration.from_quantity(
            Ion.SODIUM,
            Q_(10, "gram"),
        )


def test_derived_concentration_rejects_negative_value() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        DerivedIonConcentration.mg_per_liter(Ion.CHLORIDE, -1.0)


def test_aqueous_state_rejects_duplicate_ions() -> None:
    with pytest.raises(ValueError, match="duplicate ion concentrations"):
        AqueousChemicalState(
            concentrations=(
                DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
                DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, 60.0),
            )
        )


def test_aqueous_state_lookup_returns_quantity_or_none() -> None:
    state = AqueousChemicalState(
        concentrations=(
            DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
            DerivedIonConcentration.mg_per_liter(Ion.SULFATE, 80.0),
        )
    )

    calcium = state.concentration_for(Ion.CALCIUM)

    assert calcium is not None
    assert calcium.to("milligram / liter").magnitude == pytest.approx(50.0)
    assert state.concentration_for(Ion.CHLORIDE) is None
