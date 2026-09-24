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
    ExactMassPerVolumeDosedSolutionTreatmentMaterial,
    ExactVolumeDosedSolutionTreatmentMaterial,
    RangedMassFractionTreatmentMaterial,
    ResolvedMassPerVolumeSolutionDose,
    ResolvedTreatmentMaterialVolumeDose,
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


def _mass_per_volume_solution() -> ExactMassPerVolumeDosedSolutionTreatmentMaterial:
    source = SourceDocumentMetadata(
        publisher="Example manufacturer",
        title="Mass-per-volume solution specification",
    )
    return ExactMassPerVolumeDosedSolutionTreatmentMaterial(
        key="calcium_chloride_mass_per_volume_solution",
        name="10 g per 100 mL calcium chloride solution",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        active_mass_concentration=Q_(10, "gram / deciliter"),
        concentration_reference_temperature=Q_(20, "degree_Celsius"),
        dose_increment=Q_(1, "milliliter"),
        concentration_source=source,
    )


def test_mass_per_volume_solution_resolves_active_mass_directly() -> None:
    material = _mass_per_volume_solution()

    result = material.resolve_volume_dose(
        Q_(25, "milliliter"),
        measurement_temperature=Q_(68, "degree_Fahrenheit"),
    )

    assert isinstance(result, ResolvedMassPerVolumeSolutionDose)
    assert material.form is TreatmentMaterialForm.AQUEOUS_SOLUTION
    assert material.normalized_active_mass_concentration.magnitude == pytest.approx(0.1)
    assert material.normalized_concentration_reference_temperature.magnitude == (
        pytest.approx(20.0)
    )
    assert result.measured_volume.magnitude == pytest.approx(25.0)
    assert result.measurement_temperature.magnitude == pytest.approx(20.0)
    assert result.active_chemical_mass.magnitude == pytest.approx(2.5)
    assert result.treatment_addition.mass.magnitude == pytest.approx(2.5)
    assert material.concentration_source is not None
    assert not hasattr(material, "density")
    assert not hasattr(result, "solution_mass")
    assert result.preparation_text == (
        "Measure 25 mL of 10 g per 100 mL calcium chloride solution at 20 °C; "
        "this supplies 2.5 g of Calcium chloride anhydrous (CaCl2)."
    )


def test_mass_per_volume_solution_normalizes_equivalent_units() -> None:
    material = ExactMassPerVolumeDosedSolutionTreatmentMaterial(
        key="equivalent_units",
        name="Solution with g/L concentration",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        active_mass_concentration=Q_(100, "gram / liter"),
        concentration_reference_temperature=Q_(20, "degree_Celsius"),
        dose_increment=Q_(0.001, "liter"),
    )

    result = material.resolve_volume_dose(
        Q_(0.025, "liter"),
        measurement_temperature=Q_(20, "degree_Celsius"),
    )

    assert material.normalized_active_mass_concentration.magnitude == pytest.approx(0.1)
    assert material.normalized_dose_increment.magnitude == pytest.approx(1.0)
    assert result.active_chemical_mass.magnitude == pytest.approx(2.5)


@pytest.mark.parametrize(
    "concentration",
    (
        Q_(0, "gram / liter"),
        Q_(-1, "gram / liter"),
        Q_(float("nan"), "gram / liter"),
        Q_(float("inf"), "gram / liter"),
    ),
)
def test_mass_per_volume_solution_rejects_invalid_concentration(
    concentration: object,
) -> None:
    with pytest.raises(ValueError, match="concentration must be finite and positive"):
        ExactMassPerVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_concentration=concentration,  # type: ignore[arg-type]
            concentration_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_mass_per_volume_solution_rejects_wrong_concentration_dimension() -> None:
    with pytest.raises(ValueError, match="convertible to mass per volume"):
        ExactMassPerVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_concentration=Q_(100, "gram"),
            concentration_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_mass_per_volume_solution_rejects_temperature_mismatch() -> None:
    material = _mass_per_volume_solution()

    with pytest.raises(ValueError, match="must match the concentration reference"):
        material.resolve_volume_dose(
            Q_(25, "milliliter"),
            measurement_temperature=Q_(25, "degree_Celsius"),
        )


def test_mass_per_volume_solution_rejects_invalid_reference_temperature() -> None:
    with pytest.raises(ValueError, match="reference temperature must be finite"):
        ExactMassPerVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_concentration=Q_(100, "gram / liter"),
            concentration_reference_temperature=Q_(float("nan"), "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_mass_per_volume_solution_rejects_wrong_temperature_dimension() -> None:
    material = _mass_per_volume_solution()

    with pytest.raises(ValueError, match="convertible to temperature"):
        material.resolve_volume_dose(
            Q_(25, "milliliter"),
            measurement_temperature=Q_(20, "gram"),
        )


@pytest.mark.parametrize(
    "increment",
    (
        Q_(0, "milliliter"),
        Q_(-1, "milliliter"),
        Q_(float("nan"), "milliliter"),
        Q_(float("inf"), "milliliter"),
    ),
)
def test_mass_per_volume_solution_rejects_invalid_increment(increment: object) -> None:
    with pytest.raises(ValueError, match="increment must be finite and positive"):
        ExactMassPerVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_concentration=Q_(100, "gram / liter"),
            concentration_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=increment,  # type: ignore[arg-type]
        )


def test_mass_per_volume_solution_rejects_nonvolume_increment() -> None:
    with pytest.raises(ValueError, match="convertible to volume"):
        ExactMassPerVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_concentration=Q_(100, "gram / liter"),
            concentration_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "gram"),
        )


def test_mass_per_volume_solution_allows_zero_measured_volume() -> None:
    material = _mass_per_volume_solution()

    result = material.resolve_volume_dose(
        Q_(0, "milliliter"),
        measurement_temperature=Q_(20, "degree_Celsius"),
    )

    assert result.active_chemical_mass.magnitude == pytest.approx(0.0)


def test_mass_per_volume_solution_rejects_negative_measured_volume() -> None:
    material = _mass_per_volume_solution()

    with pytest.raises(ValueError, match="finite and nonnegative"):
        material.resolve_volume_dose(
            Q_(-1, "milliliter"),
            measurement_temperature=Q_(20, "degree_Celsius"),
        )


def test_mass_per_volume_solution_rejects_nonvolume_measurement() -> None:
    material = _mass_per_volume_solution()

    with pytest.raises(ValueError, match="convertible to volume"):
        material.resolve_volume_dose(
            Q_(1, "gram"),
            measurement_temperature=Q_(20, "degree_Celsius"),
        )


def test_mass_per_volume_solution_rejects_invalid_concentration_source() -> None:
    with pytest.raises(TypeError, match="concentration source must be"):
        ExactMassPerVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_concentration=Q_(100, "gram / liter"),
            concentration_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
            concentration_source="product label",  # type: ignore[arg-type]
        )


def _volume_dosed_solution() -> ExactVolumeDosedSolutionTreatmentMaterial:
    specification = SourceDocumentMetadata(
        publisher="Example manufacturer",
        title="Solution specification",
    )
    density_source = SourceDocumentMetadata(
        publisher="Example manufacturer",
        title="Solution density table",
    )
    return ExactVolumeDosedSolutionTreatmentMaterial(
        key="calcium_chloride_solution",
        name="Exact calcium chloride solution",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        active_mass_fraction=Q_(32.5, "percent"),
        density=Q_(1.2, "gram / milliliter"),
        density_reference_temperature=Q_(20, "degree_Celsius"),
        dose_increment=Q_(1, "milliliter"),
        composition_source=specification,
        density_source=density_source,
    )


def test_exact_volume_dose_resolves_solution_and_active_mass() -> None:
    material = _volume_dosed_solution()

    result = material.resolve_volume_dose(
        Q_(10, "milliliter"),
        measurement_temperature=Q_(68, "degree_Fahrenheit"),
    )

    assert isinstance(result, ResolvedTreatmentMaterialVolumeDose)
    assert material.form is TreatmentMaterialForm.AQUEOUS_SOLUTION
    assert material.normalized_density.magnitude == pytest.approx(1.2)
    assert material.normalized_density_reference_temperature.magnitude == (
        pytest.approx(20.0)
    )
    assert result.measured_volume.magnitude == pytest.approx(10.0)
    assert result.measurement_temperature.magnitude == pytest.approx(20.0)
    assert result.solution_mass.magnitude == pytest.approx(12.0)
    assert result.active_chemical_mass.magnitude == pytest.approx(3.9)
    assert result.treatment_addition.mass.magnitude == pytest.approx(3.9)
    assert material.composition_source is not None
    assert material.density_source is not None
    assert result.preparation_text == (
        "Measure 10 mL of Exact calcium chloride solution at 20 °C; this is "
        "12 g of solution and supplies 3.9 g of Calcium chloride anhydrous "
        "(CaCl2)."
    )


def test_volume_dose_rejects_temperature_without_density_correction() -> None:
    material = _volume_dosed_solution()

    with pytest.raises(ValueError, match="must match the density reference"):
        material.resolve_volume_dose(
            Q_(10, "milliliter"),
            measurement_temperature=Q_(25, "degree_Celsius"),
        )


def test_volume_dosed_solution_normalizes_equivalent_density_units() -> None:
    material = ExactVolumeDosedSolutionTreatmentMaterial(
        key="equivalent_density_units",
        name="Solution with kg/L density",
        ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
        active_mass_fraction=Q_(25, "percent"),
        density=Q_(1.2, "kilogram / liter"),
        density_reference_temperature=Q_(20, "degree_Celsius"),
        dose_increment=Q_(0.001, "liter"),
    )

    result = material.resolve_volume_dose(
        Q_(0.01, "liter"),
        measurement_temperature=Q_(20, "degree_Celsius"),
    )

    assert material.normalized_density.magnitude == pytest.approx(1.2)
    assert material.normalized_dose_increment.magnitude == pytest.approx(1.0)
    assert result.solution_mass.magnitude == pytest.approx(12.0)
    assert result.active_chemical_mass.magnitude == pytest.approx(3.0)


@pytest.mark.parametrize(
    "density",
    (
        Q_(0, "gram / milliliter"),
        Q_(-1, "gram / milliliter"),
        Q_(float("nan"), "gram / milliliter"),
        Q_(float("inf"), "gram / milliliter"),
    ),
)
def test_volume_dosed_solution_rejects_invalid_density(density: object) -> None:
    with pytest.raises(ValueError, match="density must be finite and positive"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=density,  # type: ignore[arg-type]
            density_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_volume_dosed_solution_rejects_density_with_wrong_dimension() -> None:
    with pytest.raises(ValueError, match="convertible to mass per volume"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=Q_(1.2, "gram"),
            density_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_volume_dosed_solution_rejects_invalid_reference_temperature() -> None:
    with pytest.raises(ValueError, match="reference temperature must be finite"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=Q_(1.2, "gram / milliliter"),
            density_reference_temperature=Q_(float("nan"), "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_volume_dosed_solution_rejects_wrong_temperature_dimension() -> None:
    with pytest.raises(ValueError, match="convertible to temperature"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=Q_(1.2, "gram / milliliter"),
            density_reference_temperature=Q_(20, "gram"),
            dose_increment=Q_(1, "milliliter"),
        )


def test_volume_dose_rejects_wrong_measurement_temperature_dimension() -> None:
    material = _volume_dosed_solution()

    with pytest.raises(ValueError, match="convertible to temperature"):
        material.resolve_volume_dose(
            Q_(10, "milliliter"),
            measurement_temperature=Q_(20, "gram"),
        )


def test_volume_dosed_solution_rejects_nonvolume_increment() -> None:
    with pytest.raises(ValueError, match="convertible to volume"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=Q_(1.2, "gram / milliliter"),
            density_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "gram"),
        )


@pytest.mark.parametrize(
    "increment",
    (
        Q_(0, "milliliter"),
        Q_(-1, "milliliter"),
        Q_(float("nan"), "milliliter"),
        Q_(float("inf"), "milliliter"),
    ),
)
def test_volume_dosed_solution_rejects_invalid_increment(increment: object) -> None:
    with pytest.raises(ValueError, match="increment must be finite and positive"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=Q_(1.2, "gram / milliliter"),
            density_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=increment,  # type: ignore[arg-type]
        )


def test_volume_dose_rejects_negative_measured_volume() -> None:
    material = _volume_dosed_solution()

    with pytest.raises(ValueError, match="finite and nonnegative"):
        material.resolve_volume_dose(
            Q_(-1, "milliliter"),
            measurement_temperature=Q_(20, "degree_Celsius"),
        )


def test_density_based_volume_dose_rejects_nonvolume_measurement() -> None:
    material = _volume_dosed_solution()

    with pytest.raises(ValueError, match="convertible to volume"):
        material.resolve_volume_dose(
            Q_(1, "gram"),
            measurement_temperature=Q_(20, "degree_Celsius"),
        )


def test_volume_dosed_solution_rejects_invalid_density_source() -> None:
    with pytest.raises(TypeError, match="density source must be"):
        ExactVolumeDosedSolutionTreatmentMaterial(
            key="invalid",
            name="Invalid solution",
            ingredient=CALCIUM_CHLORIDE_ANHYDROUS,
            active_mass_fraction=Q_(32.5, "percent"),
            density=Q_(1.2, "gram / milliliter"),
            density_reference_temperature=Q_(20, "degree_Celsius"),
            dose_increment=Q_(1, "milliliter"),
            density_source="density table",  # type: ignore[arg-type]
        )
