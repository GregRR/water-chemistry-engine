import pytest
from fermunits import Q_

from water_chemistry_engine.treatment_ingredients import GYPSUM
from water_chemistry_engine.treatment_materials import ExactMassDosedTreatmentMaterial


def test_exact_material_resolves_to_ordinary_treatment_addition() -> None:
    material = ExactMassDosedTreatmentMaterial(
        key="pure_gypsum",
        name="Pure gypsum",
        ingredient=GYPSUM,
        dose_increment=Q_(0.1, "gram"),
    )

    addition = material.treatment_addition(Q_(1.2, "gram"))

    assert addition.ingredient is GYPSUM
    assert addition.mass.to("gram").magnitude == pytest.approx(1.2)
    assert material.normalized_dose_increment.magnitude == pytest.approx(0.1)


@pytest.mark.parametrize(
    "increment",
    [
        Q_(0, "gram"),
        Q_(-1, "gram"),
        Q_(float("nan"), "gram"),
        Q_(float("inf"), "gram"),
    ],
)
def test_exact_material_rejects_nonpositive_or_nonfinite_increment(
    increment: object,
) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        ExactMassDosedTreatmentMaterial(
            key="pure_gypsum",
            name="Pure gypsum",
            ingredient=GYPSUM,
            dose_increment=increment,  # type: ignore[arg-type]
        )


def test_exact_material_rejects_wrong_dimension_increment() -> None:
    with pytest.raises(ValueError, match="convertible to mass"):
        ExactMassDosedTreatmentMaterial(
            key="pure_gypsum",
            name="Pure gypsum",
            ingredient=GYPSUM,
            dose_increment=Q_(0.1, "liter"),
        )


def test_exact_material_rejects_noningredient_identity() -> None:
    with pytest.raises(TypeError, match="must be TreatmentIngredient"):
        ExactMassDosedTreatmentMaterial(
            key="invalid",
            name="Invalid",
            ingredient="gypsum",  # type: ignore[arg-type]
            dose_increment=Q_(0.1, "gram"),
        )
