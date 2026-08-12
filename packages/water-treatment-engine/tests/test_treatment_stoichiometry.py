from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_
from water_treatment_engine.ions import Ion
from water_treatment_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    EPSOM_SALT,
    GYPSUM,
    POTASSIUM_CHLORIDE,
    SODIUM_BICARBONATE,
    SODIUM_CHLORIDE,
    TreatmentIngredient,
)
from water_treatment_engine.treatment_stoichiometry import (
    IonContribution,
    calculate_ion_contributions,
)

_DEFAULT_MASS = Q_(1.0, "gram")
_DEFAULT_VOLUME = Q_(1.0, "liter")


def _as_mg_per_liter(
    ingredient: TreatmentIngredient,
    *,
    mass=_DEFAULT_MASS,
    volume=_DEFAULT_VOLUME,
) -> dict[Ion, float]:
    contributions = calculate_ion_contributions(ingredient, mass, volume)
    return {
        contribution.ion: contribution.concentration.to("milligram / liter").magnitude
        for contribution in contributions
    }


@pytest.mark.parametrize(
    ("ingredient", "expected"),
    [
        (
            CALCIUM_CHLORIDE_DIHYDRATE,
            {Ion.CALCIUM: 272.625, Ion.CHLORIDE: 482.286},
        ),
        (GYPSUM, {Ion.CALCIUM: 232.790, Ion.SULFATE: 557.933}),
        (EPSOM_SALT, {Ion.MAGNESIUM: 98.614, Ion.SULFATE: 389.733}),
        (SODIUM_CHLORIDE, {Ion.SODIUM: 393.393, Ion.CHLORIDE: 606.607}),
        (
            SODIUM_BICARBONATE,
            {Ion.SODIUM: 273.669, Ion.BICARBONATE: 726.331},
        ),
        (POTASSIUM_CHLORIDE, {Ion.POTASSIUM: 524.469, Ion.CHLORIDE: 475.531}),
    ],
)
def test_one_gram_per_liter_has_expected_stoichiometric_contribution(
    ingredient: TreatmentIngredient,
    expected: dict[Ion, float],
) -> None:
    actual = _as_mg_per_liter(ingredient)

    assert actual.keys() == expected.keys()
    for ion, expected_value in expected.items():
        assert actual[ion] == pytest.approx(expected_value, abs=0.01)


def test_scalar_input_magnitudes_are_normalized_at_calculation_boundary() -> None:
    contributions = calculate_ion_contributions(
        SODIUM_CHLORIDE,
        Q_(Decimal("1.0"), "gram"),
        Q_(Fraction(1, 1), "liter"),
    )

    assert all(
        isinstance(item.concentration.magnitude, float) for item in contributions
    )
    actual = {
        item.ion: item.concentration.to("milligram / liter").magnitude
        for item in contributions
    }
    assert actual[Ion.SODIUM] == pytest.approx(393.393, abs=0.01)
    assert actual[Ion.CHLORIDE] == pytest.approx(606.607, abs=0.01)


def test_doubling_addition_mass_doubles_concentrations() -> None:
    once = _as_mg_per_liter(GYPSUM, mass=Q_(1, "gram"))
    twice = _as_mg_per_liter(GYPSUM, mass=Q_(2, "gram"))

    for ion in once:
        assert twice[ion] == pytest.approx(2 * once[ion])


def test_doubling_water_volume_halves_concentrations() -> None:
    one_liter = _as_mg_per_liter(EPSOM_SALT, volume=Q_(1, "liter"))
    two_liters = _as_mg_per_liter(EPSOM_SALT, volume=Q_(2, "liter"))

    for ion in one_liter:
        assert two_liters[ion] == pytest.approx(one_liter[ion] / 2)


def test_equivalent_mass_and_volume_units_give_same_result() -> None:
    metric = _as_mg_per_liter(
        SODIUM_CHLORIDE,
        mass=Q_(1, "gram"),
        volume=Q_(1, "liter"),
    )
    converted = _as_mg_per_liter(
        SODIUM_CHLORIDE,
        mass=Q_(1000, "milligram"),
        volume=Q_(1000, "milliliter"),
    )

    assert converted == pytest.approx(metric)


def test_us_customary_volume_is_normalized_through_fermunits() -> None:
    contribution = _as_mg_per_liter(
        CALCIUM_CHLORIDE_DIHYDRATE,
        mass=Q_(1, "gram"),
        volume=Q_(1, "US_liquid_gallon"),
    )

    assert contribution[Ion.CALCIUM] == pytest.approx(72.020, abs=0.01)
    assert contribution[Ion.CHLORIDE] == pytest.approx(127.407, abs=0.01)


def test_zero_addition_returns_zero_concentrations() -> None:
    contribution = _as_mg_per_liter(
        POTASSIUM_CHLORIDE,
        mass=Q_(0, "gram"),
    )

    assert contribution == {
        Ion.POTASSIUM: 0.0,
        Ion.CHLORIDE: 0.0,
    }


def test_negative_addition_mass_is_rejected() -> None:
    with pytest.raises(ValueError, match="mass cannot be negative"):
        calculate_ion_contributions(
            GYPSUM,
            Q_(-1, "gram"),
            Q_(20, "liter"),
        )


@pytest.mark.parametrize("volume", [Q_(0, "liter"), Q_(-1, "liter")])
def test_non_positive_water_volume_is_rejected(volume) -> None:
    with pytest.raises(ValueError, match="volume must be greater than zero"):
        calculate_ion_contributions(
            GYPSUM,
            Q_(1, "gram"),
            volume,
        )


def test_non_mass_addition_is_rejected() -> None:
    with pytest.raises(ValueError, match="addition must be convertible to mass"):
        calculate_ion_contributions(
            GYPSUM,
            Q_(1, "liter"),
            Q_(20, "liter"),
        )


def test_non_volume_treatment_size_is_rejected() -> None:
    with pytest.raises(ValueError, match="volume must be convertible to volume"):
        calculate_ion_contributions(
            GYPSUM,
            Q_(1, "gram"),
            Q_(20, "gram"),
        )


def test_ion_contribution_rejects_non_concentration_quantity() -> None:
    with pytest.raises(ValueError, match="convertible to mass per volume"):
        IonContribution(
            ion=Ion.CALCIUM,
            concentration=Q_(1, "gram"),
        )
