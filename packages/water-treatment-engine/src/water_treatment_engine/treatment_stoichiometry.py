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
from typing import Any

from pint import Quantity

from water_treatment_engine.ions import Ion
from water_treatment_engine.treatment_ingredients import TreatmentIngredient


@dataclass(frozen=True, slots=True)
class IonContribution:
    """Derived mass concentration contributed by one treatment ingredient."""

    ion: Ion
    concentration: Quantity[Any]

    def __post_init__(self) -> None:
        try:
            normalized = self.concentration.to("milligram / liter")
        except Exception as exc:
            raise ValueError(
                "Ion contribution must be convertible to mass per volume."
            ) from exc

        if normalized.magnitude < 0:
            raise ValueError("Ion contribution cannot be negative.")


def calculate_ion_contributions(
    ingredient: TreatmentIngredient,
    addition_mass: Quantity[Any],
    water_volume: Quantity[Any],
) -> tuple[IonContribution, ...]:
    """Calculate theoretical ion contributions for one mineral addition.

    The calculation preserves moles through the ingredient's fixed
    stoichiometry:

        mass ingredient -> moles ingredient -> moles ion -> mass ion -> mg/L

    ``addition_mass`` and ``water_volume`` may use any FermUnits/Pint units that
    are dimensionally compatible with mass and volume.  Returned concentrations
    are normalized to mg/L so downstream water-treatment calculations have a
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

    if mass.magnitude < 0:
        raise ValueError("Treatment addition mass cannot be negative.")
    if volume.magnitude <= 0:
        raise ValueError("Treatment water volume must be greater than zero.")

    ingredient_molar_mass = ingredient.molar_mass.to("gram / mole")
    ingredient_moles = mass / ingredient_molar_mass

    contributions: list[IonContribution] = []
    for entry in ingredient.ion_stoichiometry:
        # Hydration water is already represented in ingredient_molar_mass.  Only
        # the chemically relevant ions listed in ion_stoichiometry are converted
        # back to mass here, so a hydrate correctly contributes less ion per gram
        # than its anhydrous counterpart would.
        ion_mass = ingredient_moles * entry.coefficient * entry.molar_mass
        concentration = (ion_mass.to("milligram") / volume).to("milligram / liter")
        contributions.append(
            IonContribution(
                ion=entry.ion,
                concentration=concentration,
            )
        )

    return tuple(contributions)
