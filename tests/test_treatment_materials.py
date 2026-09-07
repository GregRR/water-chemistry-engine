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
    "increment", [Q_(0, "gram"), Q_(-1, "gram"), Q_(float("nan"), "gram")]
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
