"""Stoichiometric ion contributions from simple mineral additions.

The calculation in this module is intentionally a *theoretical complete-
dissolution contribution*.  It answers: if a specified mass of this chemical
identity dissociates according to its formula, how much of each modeled ion is
introduced per unit water volume?

It is not yet an aqueous-equilibrium solver.  Solubility limits, precipitation,
carbonate equilibria, pH, activity coefficients, and reactions with existing
water chemistry can make the final dissolved state differ from this theoretical
contribution.  Keeping that boundary explicit prevents a simple mass-balance
calculation from masquerading as a complete water-chemistry model.
"""

from dataclasses import dataclass
from math import isfinite

from fermunits import Q_
from pint import Quantity

from water_chemistry_engine.ions import Ion
from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.treatment_ingredients import TreatmentIngredient


@dataclass(frozen=True, slots=True)
class IonContribution:
    """Derived mass concentration contributed by one treatment ingredient."""

    ion: Ion
    concentration: Quantity[float]

    def __post_init__(self) -> None:
        try:
            normalized = self.concentration.to("milligram / liter")
        except Exception as exc:
            raise ValueError(
                "Ion contribution must be convertible to mass per volume."
            ) from exc

        magnitude = float(normalized.magnitude)
        if not isfinite(magnitude):
            raise ValueError("Ion contribution must be finite.")
        if magnitude < 0:
            raise ValueError("Ion contribution cannot be negative.")

        object.__setattr__(
            self,
            "concentration",
            Q_(magnitude, "milligram / liter"),
        )


def calculate_ion_contributions(
    ingredient: TreatmentIngredient,
    addition_mass: ScalarQuantity,
    water_volume: ScalarQuantity,
) -> tuple[IonContribution, ...]:
    """Calculate theoretical ion contributions for one mineral addition.

    The calculation preserves moles through the ingredient's fixed
    stoichiometry:

        mass ingredient -> moles ingredient -> moles ion -> mass ion -> mg/L

    ``addition_mass`` and ``water_volume`` may use supported scalar
    FermUnits/Pint quantities in any units dimensionally compatible with mass
    and volume. Returned concentrations are normalized to mg/L so downstream
    water-treatment calculations have a
    predictable canonical representation.

    A zero addition is valid and returns zero for each ion the ingredient would
    contribute.  Negative addition masses and non-positive treatment volumes are
    physically invalid and rejected.
    """
    try:
        mass = addition_mass.to("gram")
    except Exception as exc:
        raise ValueError("Treatment addition must be convertible to mass.") from exc

    try:
        volume = water_volume.to("liter")
    except Exception as exc:
        raise ValueError(
            "Treatment water volume must be convertible to volume."
        ) from exc

    mass_grams = float(mass.magnitude)
    volume_liters = float(volume.magnitude)

    if not isfinite(mass_grams):
        raise ValueError("Treatment addition mass must be finite.")
    if mass_grams < 0:
        raise ValueError("Treatment addition mass cannot be negative.")
    if not isfinite(volume_liters):
        raise ValueError("Treatment water volume must be finite.")
    if volume_liters <= 0:
        raise ValueError("Treatment water volume must be greater than zero.")

    # Reported/input quantities may preserve int, Decimal, or Fraction
    # magnitudes.  Stoichiometric contribution is derived numerical data, so
    # this is the deliberate boundary where the solver normalizes to float.
    ingredient_molar_mass_g_per_mol = float(
        ingredient.molar_mass.to("gram / mole").magnitude
    )
    ingredient_moles = mass_grams / ingredient_molar_mass_g_per_mol

    contributions: list[IonContribution] = []
    for entry in ingredient.ion_stoichiometry:
        # Hydration water is already represented in the ingredient molar mass.
        # Only the ions in ion_stoichiometry are converted back to mass, so a
        # hydrate contributes less ion per gram than its anhydrous form would.
        ion_molar_mass_g_per_mol = float(entry.molar_mass.to("gram / mole").magnitude)
        ion_mass_mg = (
            ingredient_moles * entry.coefficient * ion_molar_mass_g_per_mol * 1000.0
        )
        concentration = Q_(
            ion_mass_mg / volume_liters,
            "milligram / liter",
        )
        contributions.append(
            IonContribution(
                ion=entry.ion,
                concentration=concentration,
            )
        )

    return tuple(contributions)
