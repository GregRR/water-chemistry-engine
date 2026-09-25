"""Physical treatment materials and mass-dose composition semantics.

``TreatmentIngredient`` remains the ideal chemical identity used for
stoichiometry.  This module represents what an operator measures.  Exact mass
fractions can resolve a measured material mass to active chemical mass without
density.  Ranged fractions remain ranges and deliberately cannot produce one
exact ``TreatmentAddition`` without a future explicit resolution policy. Exact
solution volume dosing additionally supports either mass fraction plus density
or an explicit active-chemical mass-per-volume concentration. Both volume
bases require a stated reference temperature and a matching measurement
temperature.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isclose, isfinite

from fermunits import Q_, Quantity

from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.source_document import SourceDocumentMetadata
from water_chemistry_engine.treatment_application import TreatmentAddition
from water_chemistry_engine.treatment_ingredients import TreatmentIngredient


class TreatmentMaterialForm(StrEnum):
    """Physical form retained separately from chemical identity."""

    SOLID = "solid"
    AQUEOUS_SOLUTION = "aqueous_solution"


class TreatmentMaterialUseLimitVolumeBasis(StrEnum):
    """Water-volume denominator supported by a material-use policy.

    The initial optimizer supports only its requested total treated-water
    volume. This is calculation-policy identity, not a reported sampling
    ``WaterStage`` and not finished-beverage or process-product volume.
    """

    OPTIMIZER_TOTAL_WATER_VOLUME = "optimizer_total_water_volume"


def _validate_required_text(value: str, *, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} cannot be empty.")


def _validate_identity(
    key: str,
    name: str,
    ingredient: TreatmentIngredient,
) -> None:
    if not key.strip():
        raise ValueError("Treatment material key cannot be empty.")
    if not name.strip():
        raise ValueError("Treatment material name cannot be empty.")
    if not isinstance(ingredient, TreatmentIngredient):
        raise TypeError("Treatment material ingredient must be TreatmentIngredient.")


def _validate_composition_source(
    composition_source: SourceDocumentMetadata | None,
) -> None:
    if composition_source is not None and not isinstance(
        composition_source,
        SourceDocumentMetadata,
    ):
        raise TypeError(
            "Treatment material composition source must be "
            "SourceDocumentMetadata or None."
        )


def _validate_density_source(density_source: SourceDocumentMetadata | None) -> None:
    if density_source is not None and not isinstance(
        density_source,
        SourceDocumentMetadata,
    ):
        raise TypeError(
            "Treatment material density source must be SourceDocumentMetadata or None."
        )


def _normalized_positive_mass(value: ScalarQuantity, *, label: str) -> Quantity[float]:
    try:
        normalized = value.to("gram")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and positive.")
    return Q_(magnitude, "gram")


def _normalized_nonnegative_mass(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("gram")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude < 0:
        raise ValueError(f"{label} must be finite and nonnegative.")
    return Q_(magnitude, "gram")


def _normalized_positive_volume(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("milliliter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and positive.")
    return Q_(magnitude, "milliliter")


def _normalized_nonnegative_volume(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("milliliter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude < 0:
        raise ValueError(f"{label} must be finite and nonnegative.")
    return Q_(magnitude, "milliliter")


def _normalized_positive_density(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("gram / milliliter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass per volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and positive.")
    return Q_(magnitude, "gram / milliliter")


def _normalized_positive_mass_concentration(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("gram / milliliter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass per volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and positive.")
    return Q_(magnitude, "gram / milliliter")


def _normalized_positive_material_use_rate(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("gram / liter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass per volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and positive.")
    return Q_(magnitude, "gram / liter")


def _normalized_temperature(
    value: ScalarQuantity,
    *,
    label: str,
) -> Quantity[float]:
    try:
        normalized = value.to("degree_Celsius")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to temperature.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude):
        raise ValueError(f"{label} must be finite.")
    return Q_(magnitude, "degree_Celsius")


def _normalized_mass_fraction(
    value: ScalarQuantity,
    *,
    label: str,
    allow_zero: bool,
) -> Quantity[float]:
    try:
        normalized = value.to("dimensionless")
    except Exception as exc:
        raise ValueError(f"{label} must be a dimensionless mass fraction.") from exc
    magnitude = float(normalized.magnitude)
    invalid_minimum = magnitude < 0.0 if allow_zero else magnitude <= 0.0
    if not isfinite(magnitude) or invalid_minimum or magnitude > 1.0:
        interval = (
            "between zero and one"
            if allow_zero
            else "greater than zero and at most one"
        )
        raise ValueError(f"{label} must be finite and {interval}.")
    return Q_(magnitude, "dimensionless")


@dataclass(frozen=True, slots=True)
class TreatmentMaterialUseLimit:
    """One sourced, caller-selected practical material-use policy.

    The maximum is measured material mass per optimizer total water volume,
    not active-chemical mass. ``applicability`` states the conditions under
    which the cited limit is intended to be used. Selecting this policy does
    not make it a universal safety, sensory, solubility, or regulatory limit.
    """

    key: str
    version: str
    material_key: str
    description: str
    applicability: str
    volume_basis: TreatmentMaterialUseLimitVolumeBasis
    maximum_measured_mass_per_volume: ScalarQuantity
    source_document: SourceDocumentMetadata

    def __post_init__(self) -> None:
        _validate_required_text(self.key, label="Treatment material use-limit key")
        _validate_required_text(
            self.version,
            label="Treatment material use-limit version",
        )
        _validate_required_text(
            self.material_key,
            label="Treatment material use-limit material key",
        )
        _validate_required_text(
            self.description,
            label="Treatment material use-limit description",
        )
        _validate_required_text(
            self.applicability,
            label="Treatment material use-limit applicability",
        )
        if not isinstance(
            self.volume_basis,
            TreatmentMaterialUseLimitVolumeBasis,
        ):
            raise TypeError(
                "Treatment material use-limit volume_basis must be "
                "TreatmentMaterialUseLimitVolumeBasis."
            )
        _normalized_positive_material_use_rate(
            self.maximum_measured_mass_per_volume,
            label="Treatment material use-limit maximum",
        )
        if not isinstance(self.source_document, SourceDocumentMetadata):
            raise TypeError(
                "Treatment material use-limit source_document must be "
                "SourceDocumentMetadata."
            )

    @property
    def normalized_maximum_measured_mass_per_volume(self) -> Quantity[float]:
        """Return the policy maximum in grams of material per liter of water."""
        return _normalized_positive_material_use_rate(
            self.maximum_measured_mass_per_volume,
            label="Treatment material use-limit maximum",
        )

    def maximum_measured_mass_for(
        self,
        total_volume: ScalarQuantity,
    ) -> Quantity[float]:
        """Calculate the maximum for positive optimizer total-water volume."""
        volume_ml = _normalized_positive_volume(
            total_volume,
            label="Treatment material use-limit total volume",
        )
        volume_liters = float(volume_ml.to("liter").magnitude)
        rate = float(self.normalized_maximum_measured_mass_per_volume.magnitude)
        return Q_(rate * volume_liters, "gram")


@dataclass(frozen=True, slots=True)
class TreatmentMaterialActiveMassRange:
    """Active chemical mass bounds from one unresolved ranged composition."""

    minimum: Quantity[float]
    maximum: Quantity[float]

    def __post_init__(self) -> None:
        minimum = _normalized_nonnegative_mass(
            self.minimum,
            label="Minimum active ingredient mass",
        )
        maximum = _normalized_nonnegative_mass(
            self.maximum,
            label="Maximum active ingredient mass",
        )
        if float(minimum.magnitude) > float(maximum.magnitude):
            raise ValueError(
                "Minimum active ingredient mass cannot exceed the maximum."
            )


@dataclass(frozen=True, slots=True)
class ResolvedTreatmentMaterialVolumeDose:
    """One exact solution-volume dose resolved at its density condition."""

    material: ExactVolumeDosedSolutionTreatmentMaterial
    measured_volume: Quantity[float]
    measurement_temperature: Quantity[float]
    solution_mass: Quantity[float]
    active_chemical_mass: Quantity[float]
    treatment_addition: TreatmentAddition

    @property
    def preparation_text(self) -> str:
        """Describe physical volume and resolved solution/chemical masses."""
        volume = format(float(self.measured_volume.magnitude), ".12g")
        temperature = format(float(self.measurement_temperature.magnitude), ".12g")
        solution_mass = format(float(self.solution_mass.magnitude), ".12g")
        active_mass = format(float(self.active_chemical_mass.magnitude), ".12g")
        ingredient = self.treatment_addition.ingredient
        return (
            f"Measure {volume} mL of {self.material.name} at {temperature} °C; "
            f"this is {solution_mass} g of solution and supplies {active_mass} g "
            f"of {ingredient.name} ({ingredient.formula})."
        )


@dataclass(frozen=True, slots=True)
class ResolvedMassPerVolumeSolutionDose:
    """One exact mass-per-volume solution dose resolved by measured volume."""

    material: ExactMassPerVolumeDosedSolutionTreatmentMaterial
    measured_volume: Quantity[float]
    measurement_temperature: Quantity[float]
    active_chemical_mass: Quantity[float]
    treatment_addition: TreatmentAddition

    @property
    def preparation_text(self) -> str:
        """Describe physical volume and resolved active chemical mass."""
        volume = format(float(self.measured_volume.magnitude), ".12g")
        temperature = format(float(self.measurement_temperature.magnitude), ".12g")
        active_mass = format(float(self.active_chemical_mass.magnitude), ".12g")
        ingredient = self.treatment_addition.ingredient
        return (
            f"Measure {volume} mL of {self.material.name} at {temperature} °C; "
            f"this supplies {active_mass} g of {ingredient.name} "
            f"({ingredient.formula})."
        )


@dataclass(frozen=True, slots=True)
class ExactMassDosedTreatmentMaterial:
    """An exactly composed solid material measured by mass.

    One gram of this material is one gram of its ``ingredient``.  This narrow
    contract intentionally excludes commercial assay variation, retained
    moisture, liquid solutions, and volume dosing.  ``dose_increment`` is the
    smallest operationally permitted measured increment. The optimizer chooses
    whole counts of that increment; this material type never silently rounds a
    caller-supplied mass on its own.
    """

    key: str
    name: str
    ingredient: TreatmentIngredient
    dose_increment: ScalarQuantity
    composition_source: SourceDocumentMetadata | None = None

    def __post_init__(self) -> None:
        _validate_identity(self.key, self.name, self.ingredient)
        _normalized_positive_mass(
            self.dose_increment,
            label="Treatment material dose increment",
        )
        _validate_composition_source(self.composition_source)

    def treatment_addition(self, measured_mass: ScalarQuantity) -> TreatmentAddition:
        """Resolve an exact measured material mass to ordinary treatment semantics."""
        return TreatmentAddition(self.ingredient, measured_mass)

    @property
    def normalized_dose_increment(self) -> Quantity[float]:
        """Return the increment in canonical grams without changing its policy."""
        return _normalized_positive_mass(
            self.dose_increment,
            label="Treatment material dose increment",
        )


@dataclass(frozen=True, slots=True)
class ExactMassFractionTreatmentMaterial:
    """A mass-dosed material with an exact active-chemical mass fraction.

    The fraction must carry an explicit dimensionless basis, for example
    ``Q_(80, "percent")`` or ``Q_(0.8, "dimensionless")``.  Physical form is
    retained separately so an aqueous solution is never modeled as a chemical
    hydration state.  Density is unnecessary for mass dosing and is not
    inferred.
    """

    key: str
    name: str
    ingredient: TreatmentIngredient
    form: TreatmentMaterialForm
    active_mass_fraction: ScalarQuantity
    dose_increment: ScalarQuantity
    composition_source: SourceDocumentMetadata | None = None

    def __post_init__(self) -> None:
        _validate_identity(self.key, self.name, self.ingredient)
        if not isinstance(self.form, TreatmentMaterialForm):
            raise TypeError("Treatment material form must be TreatmentMaterialForm.")
        _normalized_mass_fraction(
            self.active_mass_fraction,
            label="Treatment material active mass fraction",
            allow_zero=False,
        )
        _normalized_positive_mass(
            self.dose_increment,
            label="Treatment material dose increment",
        )
        _validate_composition_source(self.composition_source)

    @property
    def normalized_active_mass_fraction(self) -> Quantity[float]:
        """Return the exact mass fraction on a zero-to-one basis."""
        return _normalized_mass_fraction(
            self.active_mass_fraction,
            label="Treatment material active mass fraction",
            allow_zero=False,
        )

    @property
    def normalized_dose_increment(self) -> Quantity[float]:
        """Return the measured-material increment in canonical grams."""
        return _normalized_positive_mass(
            self.dose_increment,
            label="Treatment material dose increment",
        )

    def active_ingredient_mass(self, measured_mass: ScalarQuantity) -> Quantity[float]:
        """Resolve measured material mass to exact active chemical mass."""
        measured = _normalized_nonnegative_mass(
            measured_mass,
            label="Measured treatment material mass",
        )
        fraction = float(self.normalized_active_mass_fraction.magnitude)
        return Q_(float(measured.magnitude) * fraction, "gram")

    def treatment_addition(self, measured_mass: ScalarQuantity) -> TreatmentAddition:
        """Resolve an exact mass-fraction dose to ordinary treatment semantics."""
        return TreatmentAddition(
            self.ingredient,
            self.active_ingredient_mass(measured_mass),
        )


@dataclass(frozen=True, slots=True)
class RangedMassFractionTreatmentMaterial:
    """A mass-dosed material whose active mass fraction is reported as a range.

    This type preserves the specification and can calculate active-mass bounds.
    It intentionally has no ``treatment_addition`` method because selecting one
    exact composition requires an explicit future calculation policy.
    """

    key: str
    name: str
    ingredient: TreatmentIngredient
    form: TreatmentMaterialForm
    minimum_active_mass_fraction: ScalarQuantity
    maximum_active_mass_fraction: ScalarQuantity
    dose_increment: ScalarQuantity
    composition_source: SourceDocumentMetadata | None = None

    def __post_init__(self) -> None:
        _validate_identity(self.key, self.name, self.ingredient)
        if not isinstance(self.form, TreatmentMaterialForm):
            raise TypeError("Treatment material form must be TreatmentMaterialForm.")
        minimum = _normalized_mass_fraction(
            self.minimum_active_mass_fraction,
            label="Treatment material minimum active mass fraction",
            allow_zero=True,
        )
        maximum = _normalized_mass_fraction(
            self.maximum_active_mass_fraction,
            label="Treatment material maximum active mass fraction",
            allow_zero=False,
        )
        if float(minimum.magnitude) > float(maximum.magnitude):
            raise ValueError(
                "Treatment material minimum active mass fraction cannot exceed "
                "the maximum."
            )
        _normalized_positive_mass(
            self.dose_increment,
            label="Treatment material dose increment",
        )
        _validate_composition_source(self.composition_source)

    @property
    def normalized_minimum_active_mass_fraction(self) -> Quantity[float]:
        """Return the lower fraction endpoint on a zero-to-one basis."""
        return _normalized_mass_fraction(
            self.minimum_active_mass_fraction,
            label="Treatment material minimum active mass fraction",
            allow_zero=True,
        )

    @property
    def normalized_maximum_active_mass_fraction(self) -> Quantity[float]:
        """Return the upper fraction endpoint on a zero-to-one basis."""
        return _normalized_mass_fraction(
            self.maximum_active_mass_fraction,
            label="Treatment material maximum active mass fraction",
            allow_zero=False,
        )

    @property
    def normalized_dose_increment(self) -> Quantity[float]:
        """Return the measured-material increment in canonical grams."""
        return _normalized_positive_mass(
            self.dose_increment,
            label="Treatment material dose increment",
        )

    def active_ingredient_mass_range(
        self,
        measured_mass: ScalarQuantity,
    ) -> TreatmentMaterialActiveMassRange:
        """Return active chemical mass bounds without choosing a midpoint."""
        measured = _normalized_nonnegative_mass(
            measured_mass,
            label="Measured treatment material mass",
        )
        measured_grams = float(measured.magnitude)
        minimum = float(self.normalized_minimum_active_mass_fraction.magnitude)
        maximum = float(self.normalized_maximum_active_mass_fraction.magnitude)
        return TreatmentMaterialActiveMassRange(
            minimum=Q_(measured_grams * minimum, "gram"),
            maximum=Q_(measured_grams * maximum, "gram"),
        )


@dataclass(frozen=True, slots=True)
class ExactMassPerVolumeDosedSolutionTreatmentMaterial:
    """An aqueous solution with exact active mass per solution volume.

    The concentration basis directly relates active chemical mass to measured
    solution volume, so density and total solution mass are neither required
    nor inferred. Because a volume-based concentration is condition-dependent,
    resolution requires the actual measurement temperature to match the stated
    concentration reference temperature. Thermal correction is unsupported.
    """

    key: str
    name: str
    ingredient: TreatmentIngredient
    active_mass_concentration: ScalarQuantity
    concentration_reference_temperature: ScalarQuantity
    dose_increment: ScalarQuantity
    concentration_source: SourceDocumentMetadata | None = None

    def __post_init__(self) -> None:
        _validate_identity(self.key, self.name, self.ingredient)
        _normalized_positive_mass_concentration(
            self.active_mass_concentration,
            label="Treatment material active mass concentration",
        )
        _normalized_temperature(
            self.concentration_reference_temperature,
            label="Treatment material concentration reference temperature",
        )
        _normalized_positive_volume(
            self.dose_increment,
            label="Treatment material volume dose increment",
        )
        if self.concentration_source is not None and not isinstance(
            self.concentration_source,
            SourceDocumentMetadata,
        ):
            raise TypeError(
                "Treatment material concentration source must be "
                "SourceDocumentMetadata or None."
            )

    @property
    def form(self) -> TreatmentMaterialForm:
        """Return the physical form required by this concentration basis."""
        return TreatmentMaterialForm.AQUEOUS_SOLUTION

    @property
    def normalized_active_mass_concentration(self) -> Quantity[float]:
        """Return active mass concentration in grams per milliliter."""
        return _normalized_positive_mass_concentration(
            self.active_mass_concentration,
            label="Treatment material active mass concentration",
        )

    @property
    def normalized_concentration_reference_temperature(self) -> Quantity[float]:
        """Return the concentration reference temperature in degrees Celsius."""
        return _normalized_temperature(
            self.concentration_reference_temperature,
            label="Treatment material concentration reference temperature",
        )

    @property
    def normalized_dose_increment(self) -> Quantity[float]:
        """Return the measured-solution increment in canonical milliliters."""
        return _normalized_positive_volume(
            self.dose_increment,
            label="Treatment material volume dose increment",
        )

    def resolve_volume_dose(
        self,
        measured_volume: ScalarQuantity,
        *,
        measurement_temperature: ScalarQuantity,
    ) -> ResolvedMassPerVolumeSolutionDose:
        """Resolve volume directly to active mass at the stated condition."""
        volume = _normalized_nonnegative_volume(
            measured_volume,
            label="Measured treatment material volume",
        )
        temperature = _normalized_temperature(
            measurement_temperature,
            label="Treatment material measurement temperature",
        )
        reference_temperature = self.normalized_concentration_reference_temperature
        if not isclose(
            float(temperature.magnitude),
            float(reference_temperature.magnitude),
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "Treatment material measurement temperature must match the "
                "concentration reference temperature; temperature correction "
                "is unsupported."
            )

        active_mass = Q_(
            float(volume.magnitude)
            * float(self.normalized_active_mass_concentration.magnitude),
            "gram",
        )
        addition = TreatmentAddition(self.ingredient, active_mass)
        return ResolvedMassPerVolumeSolutionDose(
            material=self,
            measured_volume=volume,
            measurement_temperature=temperature,
            active_chemical_mass=active_mass,
            treatment_addition=addition,
        )


@dataclass(frozen=True, slots=True)
class ExactVolumeDosedSolutionTreatmentMaterial:
    """An exact mass-fraction solution dosed by volume at a known density.

    Density is valid only at ``density_reference_temperature``. Dose resolution
    therefore requires the actual measurement temperature and rejects a
    mismatch rather than inventing a thermal density correction. The active
    mass fraction remains mass/mass; density converts measured solution volume
    to solution mass before the fraction is applied.
    """

    key: str
    name: str
    ingredient: TreatmentIngredient
    active_mass_fraction: ScalarQuantity
    density: ScalarQuantity
    density_reference_temperature: ScalarQuantity
    dose_increment: ScalarQuantity
    composition_source: SourceDocumentMetadata | None = None
    density_source: SourceDocumentMetadata | None = None

    def __post_init__(self) -> None:
        _validate_identity(self.key, self.name, self.ingredient)
        _normalized_mass_fraction(
            self.active_mass_fraction,
            label="Treatment material active mass fraction",
            allow_zero=False,
        )
        _normalized_positive_density(
            self.density,
            label="Treatment material density",
        )
        _normalized_temperature(
            self.density_reference_temperature,
            label="Treatment material density reference temperature",
        )
        _normalized_positive_volume(
            self.dose_increment,
            label="Treatment material volume dose increment",
        )
        _validate_composition_source(self.composition_source)
        _validate_density_source(self.density_source)

    @property
    def form(self) -> TreatmentMaterialForm:
        """Return the physical form required by this volume-dosed contract."""
        return TreatmentMaterialForm.AQUEOUS_SOLUTION

    @property
    def normalized_active_mass_fraction(self) -> Quantity[float]:
        """Return the exact solution mass fraction on a zero-to-one basis."""
        return _normalized_mass_fraction(
            self.active_mass_fraction,
            label="Treatment material active mass fraction",
            allow_zero=False,
        )

    @property
    def normalized_density(self) -> Quantity[float]:
        """Return density in canonical grams per milliliter."""
        return _normalized_positive_density(
            self.density,
            label="Treatment material density",
        )

    @property
    def normalized_density_reference_temperature(self) -> Quantity[float]:
        """Return the density reference temperature in degrees Celsius."""
        return _normalized_temperature(
            self.density_reference_temperature,
            label="Treatment material density reference temperature",
        )

    @property
    def normalized_dose_increment(self) -> Quantity[float]:
        """Return the measured-solution increment in canonical milliliters."""
        return _normalized_positive_volume(
            self.dose_increment,
            label="Treatment material volume dose increment",
        )

    def resolve_volume_dose(
        self,
        measured_volume: ScalarQuantity,
        *,
        measurement_temperature: ScalarQuantity,
    ) -> ResolvedTreatmentMaterialVolumeDose:
        """Resolve volume to active mass when the density condition matches."""
        volume = _normalized_nonnegative_volume(
            measured_volume,
            label="Measured treatment material volume",
        )
        temperature = _normalized_temperature(
            measurement_temperature,
            label="Treatment material measurement temperature",
        )
        reference_temperature = self.normalized_density_reference_temperature
        if not isclose(
            float(temperature.magnitude),
            float(reference_temperature.magnitude),
            rel_tol=0.0,
            abs_tol=1e-9,
        ):
            raise ValueError(
                "Treatment material measurement temperature must match the "
                "density reference temperature; temperature correction is "
                "unsupported."
            )

        volume_ml = float(volume.magnitude)
        solution_mass = Q_(
            volume_ml * float(self.normalized_density.magnitude),
            "gram",
        )
        active_mass = Q_(
            float(solution_mass.magnitude)
            * float(self.normalized_active_mass_fraction.magnitude),
            "gram",
        )
        addition = TreatmentAddition(self.ingredient, active_mass)
        return ResolvedTreatmentMaterialVolumeDose(
            material=self,
            measured_volume=volume,
            measurement_temperature=temperature,
            solution_mass=solution_mass,
            active_chemical_mass=active_mass,
            treatment_addition=addition,
        )
