import pytest
from fermunits import Q_

from water_chemistry_engine.ions import Ion
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    EPSOM_SALT,
    GYPSUM,
    POTASSIUM_CHLORIDE,
    SIMPLE_MINERAL_INGREDIENTS,
    SODIUM_BICARBONATE,
    SODIUM_CHLORIDE,
    IonStoichiometry,
    TreatmentIngredient,
)


def test_initial_ingredient_keys_are_unique() -> None:
    keys = [ingredient.key for ingredient in SIMPLE_MINERAL_INGREDIENTS]

    assert len(keys) == len(set(keys))


@pytest.mark.parametrize(
    ("ingredient", "formula", "expected_g_per_mol"),
    [
        (CALCIUM_CHLORIDE_DIHYDRATE, "CaCl2·2H2O", 147.008),
        (GYPSUM, "CaSO4·2H2O", 172.164),
        (EPSOM_SALT, "MgSO4·7H2O", 246.466),
        (SODIUM_CHLORIDE, "NaCl", 58.440),
        (SODIUM_BICARBONATE, "NaHCO3", 84.006),
        (POTASSIUM_CHLORIDE, "KCl", 74.548),
    ],
)
def test_formula_and_molar_mass_are_stable(
    ingredient: TreatmentIngredient,
    formula: str,
    expected_g_per_mol: float,
) -> None:
    assert ingredient.formula == formula
    assert ingredient.molar_mass.to("gram / mole").magnitude == pytest.approx(
        expected_g_per_mol,
        abs=0.001,
    )


def test_calcium_chloride_dihydrate_has_one_to_two_ion_stoichiometry() -> None:
    entries = {
        entry.ion: entry.coefficient
        for entry in CALCIUM_CHLORIDE_DIHYDRATE.ion_stoichiometry
    }

    assert entries == {
        Ion.CALCIUM: 1,
        Ion.CHLORIDE: 2,
    }


def test_hydration_water_changes_formula_mass_without_adding_treatment_ions() -> None:
    ions = {entry.ion for entry in CALCIUM_CHLORIDE_DIHYDRATE.ion_stoichiometry}

    assert ions == {Ion.CALCIUM, Ion.CHLORIDE}
    assert (
        CALCIUM_CHLORIDE_DIHYDRATE.molar_mass.to("gram / mole").magnitude
        > Q_(110, "gram / mole").magnitude
    )


def test_ingredient_rejects_duplicate_ion_entries() -> None:
    calcium = IonStoichiometry(
        ion=Ion.CALCIUM,
        coefficient=1,
        molar_mass=Q_(40.078, "gram / mole"),
    )

    with pytest.raises(
        ValueError,
        match="duplicate ion stoichiometry entries",
    ):
        TreatmentIngredient(
            key="invalid",
            name="Invalid duplicate calcium",
            formula="invalid",
            molar_mass=Q_(100, "gram / mole"),
            ion_stoichiometry=(calcium, calcium),
        )


def test_stoichiometric_coefficient_must_be_positive() -> None:
    with pytest.raises(
        ValueError,
        match="coefficient must be positive",
    ):
        IonStoichiometry(
            ion=Ion.CHLORIDE,
            coefficient=0,
            molar_mass=Q_(35.45, "gram / mole"),
        )
