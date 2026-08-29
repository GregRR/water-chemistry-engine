"""Derived aqueous chemical states used by deterministic calculations.

A source-water report is not itself a calculated chemical state.  Reported
values may be exact, ranged, qualified, censored, or associated with named
statistics and sampling context.  Those semantics remain in the source-profile
model.

This module represents the point *after* an explicit calculation policy has
resolved usable numeric inputs.  State concentrations are therefore derived
values, normalized to float magnitudes in mg/L.  The current state is an ion
inventory, not an equilibrium solution model: storing bicarbonate, carbonate,
or treatment-derived ions here does not imply that acid/base speciation,
activity, precipitation, or solubility has been solved.
"""

from __future__ import annotations

from dataclasses import dataclass

from fermunits import Q_
from pint import Quantity

from water_treatment_engine.ions import Ion
from water_treatment_engine.quantity_types import ScalarQuantity


@dataclass(frozen=True, slots=True)
class DerivedIonConcentration:
    """One exact, derived ion concentration in canonical calculation units."""

    ion: Ion
    concentration: Quantity[float]

    def __post_init__(self) -> None:
        try:
            normalized = self.concentration.to("milligram / liter")
        except Exception as exc:
            raise ValueError(
                "Derived ion concentration must be convertible to mass per volume."
            ) from exc

        magnitude = float(normalized.magnitude)
        if magnitude < 0:
            raise ValueError("Derived ion concentration cannot be negative.")

        # Derived numerical state deliberately uses one stable scalar type and
        # canonical unit.  This is different from source-report objects, which
        # preserve the source's legitimate int/float/Decimal/Fraction magnitude.
        object.__setattr__(
            self,
            "concentration",
            Q_(magnitude, "milligram / liter"),
        )

    @classmethod
    def from_quantity(
        cls,
        ion: Ion,
        concentration: ScalarQuantity,
    ) -> DerivedIonConcentration:
        """Construct a derived concentration from any supported scalar quantity."""
        try:
            normalized = concentration.to("milligram / liter")
        except Exception as exc:
            raise ValueError(
                "Derived ion concentration must be convertible to mass per volume."
            ) from exc

        return cls(
            ion=ion,
            concentration=Q_(float(normalized.magnitude), "milligram / liter"),
        )

    @classmethod
    def mg_per_liter(cls, ion: Ion, value: float) -> DerivedIonConcentration:
        """Construct an exact derived concentration already expressed in mg/L."""
        return cls(ion=ion, concentration=Q_(value, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class AqueousChemicalState:
    """Exact derived ion inventory for one water-calculation checkpoint.

    The state is intentionally independent of how it was produced.  A future
    source-resolution step, a blend calculation, and treatment application can
    all produce the same state type.  That common boundary is important for
    later reusable calculations such as ``calculate_ph(state)``.
    """

    concentrations: tuple[DerivedIonConcentration, ...]

    def __post_init__(self) -> None:
        ions = [concentration.ion for concentration in self.concentrations]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Aqueous chemical state cannot contain duplicate ion concentrations."
            )

    def concentration_for(self, ion: Ion) -> Quantity[float] | None:
        """Return one derived concentration, if the state contains that ion."""
        for concentration in self.concentrations:
            if concentration.ion is ion:
                return concentration.concentration

        return None
