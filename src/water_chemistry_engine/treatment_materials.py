"""Physical treatment materials supported by the first optimizer slice.

``TreatmentIngredient`` remains the ideal chemical identity used for
stoichiometry.  This module represents what an operator measures.  The 0.4
optimizer deliberately accepts only materials with an exact, mass-for-mass
relationship to one identity; products with an assay range or liquid
concentration require the later material model and must not be approximated.
"""

from dataclasses import dataclass
from math import isfinite

from fermunits import Q_, Quantity

from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.treatment_application import TreatmentAddition
from water_chemistry_engine.treatment_ingredients import TreatmentIngredient


@dataclass(frozen=True, slots=True)
class ExactMassDosedTreatmentMaterial:
    """An exactly composed solid material measured by mass.

    One gram of this material is one gram of its ``ingredient``.  This narrow
    contract intentionally excludes commercial assay variation, retained
    moisture, liquid solutions, and volume dosing.  ``dose_increment`` is the
    smallest operationally permitted measured increment; rounding policy is
    owned by the future optimizer rather than silently applied here.
    """

    key: str
    name: str
    ingredient: TreatmentIngredient
    dose_increment: ScalarQuantity

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Treatment material key cannot be empty.")
        if not self.name.strip():
            raise ValueError("Treatment material name cannot be empty.")
        if not isinstance(self.ingredient, TreatmentIngredient):
            raise TypeError(
                "Treatment material ingredient must be TreatmentIngredient."
            )
        try:
            increment = self.dose_increment.to("gram")
        except Exception as exc:
            raise ValueError(
                "Treatment material dose increment must be convertible to mass."
            ) from exc
        magnitude = float(increment.magnitude)
        if not isfinite(magnitude) or magnitude <= 0:
            raise ValueError(
                "Treatment material dose increment must be finite and positive."
            )

    def treatment_addition(self, measured_mass: ScalarQuantity) -> TreatmentAddition:
        """Resolve an exact measured material mass to ordinary treatment semantics."""
        return TreatmentAddition(self.ingredient, measured_mass)

    @property
    def normalized_dose_increment(self) -> Quantity[float]:
        """Return the increment in canonical grams without changing its policy."""
        return Q_(float(self.dose_increment.to("gram").magnitude), "gram")
