"""Definitions for simple mineral treatment ingredients.

This module deliberately starts with ingredients whose first-order ion
contributions can be represented by fixed chemical stoichiometry.  It does not
claim that every added gram necessarily remains dissolved under every water
condition; solubility limits, precipitation, acid/base equilibria, and other
solution chemistry belong to later equilibrium modeling.

Hydration state is part of an ingredient's chemical identity.  For example,
CaCl2 and CaCl2·2H2O contain different fractions of calcium and chloride by
mass, so treating them as interchangeable would produce systematically wrong
addition calculations.  These definitions describe pure chemical identities;
commercial-product purity or extra retained moisture is a separate concern that
can be modeled later without changing the underlying stoichiometry.
"""

from dataclasses import dataclass

from fermunits import Q_

from water_chemistry_engine.ions import Ion
from water_chemistry_engine.quantity_types import ScalarQuantity

# Abridged conventional atomic weights used for ordinary chemical-formulation
# calculations.  These values follow the current IUPAC/CIAAW periodic-table
# convention and are intentionally not isotope-specific.  Keeping the weights
# here makes every ingredient and ion molar mass internally consistent.
_H = 1.0080
_C = 12.011
_O = 15.999
_NA = 22.98976928
_MG = 24.305
_S = 32.06
_CL = 35.45
_K = 39.0983
_CA = 40.078

_WATER_MOLAR_MASS = 2 * _H + _O


@dataclass(frozen=True, slots=True)
class IonStoichiometry:
    """One dissolved ion produced by one formula unit of an ingredient.

    ``coefficient`` is the number of moles of this ion produced per mole of
    ingredient under the complete-dissociation model.  ``molar_mass`` is the
    molar mass of the ionic species used to convert those moles to a mass
    concentration.  Electron mass is negligible at formulation precision.
    """

    ion: Ion
    coefficient: int
    molar_mass: ScalarQuantity

    def __post_init__(self) -> None:
        if self.coefficient <= 0:
            raise ValueError("Ion stoichiometric coefficient must be positive.")

        try:
            normalized = self.molar_mass.to("gram / mole")
        except Exception as exc:
            raise ValueError(
                "Ion molar mass must be convertible to mass per amount."
            ) from exc

        if normalized.magnitude <= 0:
            raise ValueError("Ion molar mass must be positive.")


@dataclass(frozen=True, slots=True)
class TreatmentIngredient:
    """Chemical identity used for a simple stoichiometric water addition."""

    key: str
    name: str
    formula: str
    molar_mass: ScalarQuantity
    ion_stoichiometry: tuple[IonStoichiometry, ...]

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Treatment ingredient key cannot be empty.")
        if not self.name.strip():
            raise ValueError("Treatment ingredient name cannot be empty.")
        if not self.formula.strip():
            raise ValueError("Treatment ingredient formula cannot be empty.")
        if not self.ion_stoichiometry:
            raise ValueError("Treatment ingredient must contribute at least one ion.")

        try:
            normalized = self.molar_mass.to("gram / mole")
        except Exception as exc:
            raise ValueError(
                "Treatment ingredient molar mass must be convertible to mass per amount."
            ) from exc

        if normalized.magnitude <= 0:
            raise ValueError("Treatment ingredient molar mass must be positive.")

        ions = [entry.ion for entry in self.ion_stoichiometry]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Treatment ingredient cannot contain duplicate ion stoichiometry entries."
            )


def _ion(ion: Ion, coefficient: int, molar_mass_g_per_mol: float) -> IonStoichiometry:
    return IonStoichiometry(
        ion=ion,
        coefficient=coefficient,
        molar_mass=Q_(molar_mass_g_per_mol, "gram / mole"),
    )


# The formula masses below are calculated from the same atomic-weight constants
# used for the ion masses.  Waters of hydration contribute to the compound's
# total molar mass but do not appear in ion_stoichiometry because they do not add
# calcium, chloride, sulfate, etc. to the ion inventory.
CALCIUM_CHLORIDE_DIHYDRATE = TreatmentIngredient(
    key="calcium_chloride_dihydrate",
    name="Calcium chloride dihydrate",
    formula="CaCl2·2H2O",
    molar_mass=Q_(_CA + 2 * _CL + 2 * _WATER_MOLAR_MASS, "gram / mole"),
    ion_stoichiometry=(
        _ion(Ion.CALCIUM, 1, _CA),
        _ion(Ion.CHLORIDE, 2, _CL),
    ),
)

GYPSUM = TreatmentIngredient(
    key="gypsum",
    name="Gypsum",
    formula="CaSO4·2H2O",
    molar_mass=Q_(
        _CA + _S + 4 * _O + 2 * _WATER_MOLAR_MASS,
        "gram / mole",
    ),
    ion_stoichiometry=(
        _ion(Ion.CALCIUM, 1, _CA),
        _ion(Ion.SULFATE, 1, _S + 4 * _O),
    ),
)

EPSOM_SALT = TreatmentIngredient(
    key="epsom_salt",
    name="Epsom salt",
    formula="MgSO4·7H2O",
    molar_mass=Q_(
        _MG + _S + 4 * _O + 7 * _WATER_MOLAR_MASS,
        "gram / mole",
    ),
    ion_stoichiometry=(
        _ion(Ion.MAGNESIUM, 1, _MG),
        _ion(Ion.SULFATE, 1, _S + 4 * _O),
    ),
)

SODIUM_CHLORIDE = TreatmentIngredient(
    key="sodium_chloride",
    name="Sodium chloride",
    formula="NaCl",
    molar_mass=Q_(_NA + _CL, "gram / mole"),
    ion_stoichiometry=(
        _ion(Ion.SODIUM, 1, _NA),
        _ion(Ion.CHLORIDE, 1, _CL),
    ),
)

# Sodium bicarbonate is represented here as an initial formal ion inventory.
# A later carbonate-equilibrium model may redistribute that bicarbonate among
# dissolved carbonate species as pH and dissolved CO2 are solved.
SODIUM_BICARBONATE = TreatmentIngredient(
    key="sodium_bicarbonate",
    name="Sodium bicarbonate",
    formula="NaHCO3",
    molar_mass=Q_(_NA + _H + _C + 3 * _O, "gram / mole"),
    ion_stoichiometry=(
        _ion(Ion.SODIUM, 1, _NA),
        _ion(Ion.BICARBONATE, 1, _H + _C + 3 * _O),
    ),
)

POTASSIUM_CHLORIDE = TreatmentIngredient(
    key="potassium_chloride",
    name="Potassium chloride",
    formula="KCl",
    molar_mass=Q_(_K + _CL, "gram / mole"),
    ion_stoichiometry=(
        _ion(Ion.POTASSIUM, 1, _K),
        _ion(Ion.CHLORIDE, 1, _CL),
    ),
)

# Calcium carbonate (chalk) is intentionally absent.  Its useful dissolved
# contribution depends strongly on pH, dissolved CO2, and dissolution/precipitation
# equilibria, so treating an added gram as a fixed dissolved-ion contribution would
# overstate what the water actually receives.
SIMPLE_MINERAL_INGREDIENTS = (
    CALCIUM_CHLORIDE_DIHYDRATE,
    GYPSUM,
    EPSOM_SALT,
    SODIUM_CHLORIDE,
    SODIUM_BICARBONATE,
    POTASSIUM_CHLORIDE,
)
