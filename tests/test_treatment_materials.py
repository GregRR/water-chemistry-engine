import pytest
from fermunits import Q_

from water_chemistry_engine.source_document import SourceDocumentMetadata
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_ANHYDROUS,
    GYPSUM,
)
from water_chemistry_engine.treatment_materials import (
    ExactMassDosedTreatmentMaterial,
    ExactMassFractionTreatmentMaterial,
    RangedMassFractionTreatmentMaterial,
    TreatmentMaterialActiveMassRange,
    TreatmentMaterialForm,
)


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


@pytest.mark.parametrize(
    ("form", "fraction"),
    (
        (TreatmentMaterialForm.SOLID, Q_(80, "percent")),
        (TreatmentMaterialForm.AQUEOUS_SOLUTION, Q_(0.8, "dimensionless")),
    ),
)
def test_exact_mass_fraction_material_resolves_measured_mass(
    form: TreatmentMaterialForm,
    fraction: object,
) -> None:
    material = ExactMassFractionTreatmentMaterial(
        key="calcium_chloride_material",
        name="Calcium chloride material",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        form=form,
        active_mass_fraction=fraction,  # type: ignore[arg-type]
        dose_increment=Q_(0.1, "gram"),
    )

    active_mass = material.active_ingredient_mass(Q_(10, "gram"))
    addition = material.treatment_addition(Q_(10, "gram"))

    assert material.normalized_active_mass_fraction.magnitude == pytest.approx(0.8)
    assert active_mass.to("gram").magnitude == pytest.approx(8.0)
    assert addition.ingredient is CALCIUM_CHLORIDE_ANHYDROUS
    assert addition.mass.to("gram").magnitude == pytest.approx(8.0)


def test_exact_mass_fraction_material_mass_dosing_does_not_require_density() -> None:
    solution = ExactMassFractionTreatmentMaterial(
        key="calcium_chloride_solution",
        name="32.5 percent calcium chloride solution",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        form=TreatmentMaterialForm.AQUEOUS_SOLUTION,
        active_mass_fraction=Q_(32.5, "percent"),
        dose_increment=Q_(1, "gram"),
    )

    assert solution.active_ingredient_mass(Q_(10, "gram")).magnitude == (
        pytest.approx(3.25)
    )


def test_ranged_mass_fraction_preserves_active_mass_bounds() -> None:
    source = SourceDocumentMetadata(
        publisher="Example manufacturer",
        title="Calcium chloride flake specification",
        source_url="https://example.com/calcium-chloride-specification",
    )
    material = RangedMassFractionTreatmentMaterial(
        key="calcium_chloride_flake",
        name="77-80 percent calcium chloride flake",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        form=TreatmentMaterialForm.SOLID,
        minimum_active_mass_fraction=Q_(77, "percent"),
        maximum_active_mass_fraction=Q_(80, "percent"),
        dose_increment=Q_(0.1, "gram"),
        composition_source=source,
    )

    active_mass = material.active_ingredient_mass_range(Q_(10, "gram"))

    assert isinstance(active_mass, TreatmentMaterialActiveMassRange)
    assert active_mass.minimum.to("gram").magnitude == pytest.approx(7.7)
    assert active_mass.maximum.to("gram").magnitude == pytest.approx(8.0)
    assert material.composition_source is source
    assert not hasattr(material, "treatment_addition")


@pytest.mark.parametrize(
    "fraction",
    (
        Q_(0, "percent"),
        Q_(-1, "percent"),
        Q_(101, "percent"),
        Q_(float("nan"), "percent"),
        Q_(float("inf"), "percent"),
    ),
)
def test_exact_mass_fraction_rejects_invalid_fraction(fraction: object) -> None:
    with pytest.raises(ValueError, match="greater than zero and at most one"):
        ExactMassFractionTreatmentMaterial(
            key="invalid",
            name="Invalid",
            ingredient=GYPSUM,
            form=TreatmentMaterialForm.SOLID,
            active_mass_fraction=fraction,  # type: ignore[arg-type]
            dose_increment=Q_(0.1, "gram"),
        )


def test_mass_fraction_rejects_dimensional_quantity() -> None:
    with pytest.raises(ValueError, match="dimensionless mass fraction"):
        ExactMassFractionTreatmentMaterial(
            key="invalid",
            name="Invalid",
            ingredient=GYPSUM,
            form=TreatmentMaterialForm.SOLID,
            active_mass_fraction=Q_(80, "gram"),
            dose_increment=Q_(0.1, "gram"),
        )


def test_ranged_mass_fraction_rejects_reversed_bounds() -> None:
    with pytest.raises(ValueError, match="cannot exceed the maximum"):
        RangedMassFractionTreatmentMaterial(
            key="invalid",
            name="Invalid",
            ingredient=GYPSUM,
            form=TreatmentMaterialForm.SOLID,
            minimum_active_mass_fraction=Q_(80, "percent"),
            maximum_active_mass_fraction=Q_(77, "percent"),
            dose_increment=Q_(0.1, "gram"),
        )


def test_ranged_mass_fraction_never_selects_a_midpoint() -> None:
    material = RangedMassFractionTreatmentMaterial(
        key="ranged",
        name="Ranged gypsum material",
        ingredient=GYPSUM,
        form=TreatmentMaterialForm.SOLID,
        minimum_active_mass_fraction=Q_(50, "percent"),
        maximum_active_mass_fraction=Q_(100, "percent"),
        dose_increment=Q_(0.1, "gram"),
    )

    result = material.active_ingredient_mass_range(Q_(2, "gram"))

    assert result.minimum.magnitude == pytest.approx(1.0)
    assert result.maximum.magnitude == pytest.approx(2.0)


def test_mass_fraction_material_rejects_negative_measured_mass() -> None:
    material = ExactMassFractionTreatmentMaterial(
        key="exact",
        name="Exact gypsum material",
        ingredient=GYPSUM,
        form=TreatmentMaterialForm.SOLID,
        active_mass_fraction=Q_(90, "percent"),
        dose_increment=Q_(0.1, "gram"),
    )

    with pytest.raises(ValueError, match="finite and nonnegative"):
        material.treatment_addition(Q_(-1, "gram"))


def test_mass_fraction_material_requires_explicit_form_enum() -> None:
    with pytest.raises(TypeError, match="form must be TreatmentMaterialForm"):
        ExactMassFractionTreatmentMaterial(
            key="invalid",
            name="Invalid",
            ingredient=GYPSUM,
            form="solid",  # type: ignore[arg-type]
            active_mass_fraction=Q_(90, "percent"),
            dose_increment=Q_(0.1, "gram"),
        )


def test_treatment_material_rejects_invalid_composition_source() -> None:
    with pytest.raises(TypeError, match="SourceDocumentMetadata or None"):
        ExactMassFractionTreatmentMaterial(
            key="invalid",
            name="Invalid",
            ingredient=GYPSUM,
            form=TreatmentMaterialForm.SOLID,
            active_mass_fraction=Q_(90, "percent"),
            dose_increment=Q_(0.1, "gram"),
            composition_source="manufacturer website",  # type: ignore[arg-type]
        )
