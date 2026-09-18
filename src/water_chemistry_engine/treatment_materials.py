"""Physical treatment materials and mass-dose composition semantics.

``TreatmentIngredient`` remains the ideal chemical identity used for
stoichiometry.  This module represents what an operator measures.  Exact mass
fractions can resolve a measured material mass to active chemical mass without
density.  Ranged fractions remain ranges and deliberately cannot produce one
exact ``TreatmentAddition`` without a future explicit resolution policy.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from fermunits import Q_, Quantity

from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.source_document import SourceDocumentMetadata
from water_chemistry_engine.treatment_application import TreatmentAddition
from water_chemistry_engine.treatment_ingredients import TreatmentIngredient


class TreatmentMaterialForm(StrEnum):
    """Physical form retained separately from chemical identity."""

    SOLID = "solid"
    AQUEOUS_SOLUTION = "aqueous_solution"


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
