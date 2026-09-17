"""Explicit target-closeness policies without universal percentage rules."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from fermunits import Q_

from water_chemistry_engine.ions import Ion
from water_chemistry_engine.quantity_types import ScalarQuantity


def _validate_deviation(value: ScalarQuantity, field_name: str) -> None:
    try:
        normalized = value.to("milligram / liter")
    except Exception as exc:
        raise ValueError(
            f"{field_name} must be convertible to mass per volume."
        ) from exc

    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude):
        raise ValueError(f"{field_name} must be finite.")
    if magnitude < 0.0:
        raise ValueError(f"{field_name} cannot be negative.")


@dataclass(frozen=True, slots=True)
class TargetIonClosenessPolicy:
    """Absolute deviations considered close below and above one ion target.

    Deviations are measured from the nearest accepted target boundary.  The
    asymmetric thresholds are absolute mass concentrations, never percentages,
    so exact zero and very-low targets remain well defined.
    """

    ion: Ion
    maximum_below_deviation: ScalarQuantity
    maximum_above_deviation: ScalarQuantity

    def __post_init__(self) -> None:
        if not isinstance(self.ion, Ion):
            raise TypeError("Target closeness policy ion must use Ion.")
        _validate_deviation(
            self.maximum_below_deviation,
            "maximum_below_deviation",
        )
        _validate_deviation(
            self.maximum_above_deviation,
            "maximum_above_deviation",
        )

    @classmethod
    def mg_per_liter(
        cls,
        ion: Ion,
        *,
        maximum_below_deviation: float,
        maximum_above_deviation: float,
    ) -> TargetIonClosenessPolicy:
        """Construct an asymmetric closeness policy in canonical mg/L."""
        return cls(
            ion=ion,
            maximum_below_deviation=Q_(
                maximum_below_deviation,
                "milligram / liter",
            ),
            maximum_above_deviation=Q_(
                maximum_above_deviation,
                "milligram / liter",
            ),
        )


@dataclass(frozen=True, slots=True)
class TargetComparisonPolicy:
    """Versioned, described collection of explicit per-ion closeness bands."""

    key: str
    version: str
    description: str
    ion_policies: tuple[TargetIonClosenessPolicy, ...]

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Target comparison policy key cannot be empty.")
        if not self.version.strip():
            raise ValueError("Target comparison policy version cannot be empty.")
        if not self.description.strip():
            raise ValueError("Target comparison policy description cannot be empty.")
        if not self.ion_policies:
            raise ValueError(
                "Target comparison policy must contain at least one ion policy."
            )
        if any(
            not isinstance(policy, TargetIonClosenessPolicy)
            for policy in self.ion_policies
        ):
            raise TypeError(
                "Target comparison ion policies must use TargetIonClosenessPolicy."
            )

        ions = [policy.ion for policy in self.ion_policies]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Target comparison policy cannot contain duplicate ion policies."
            )

    def policy_for(self, ion: Ion) -> TargetIonClosenessPolicy | None:
        """Return the explicit closeness policy for an ion, if supplied."""
        for policy in self.ion_policies:
            if policy.ion is ion:
                return policy

        return None
