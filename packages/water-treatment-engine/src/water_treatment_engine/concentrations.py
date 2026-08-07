from dataclasses import dataclass

from fermunits import Q_
from pint import Quantity

from water_treatment_engine.ions import Ion


def _validate_mass_concentration(value: Quantity) -> None:
    """Require a quantity convertible to mass per volume."""
    try:
        value.to("milligram / liter")
    except Exception as exc:
        raise ValueError(
            "Ion concentration must be convertible to mass per volume."
        ) from exc


@dataclass(frozen=True, slots=True)
class IonConcentration:
    """Exact reported concentration of a single ion."""

    ion: Ion
    value: Quantity

    def __post_init__(self) -> None:
        _validate_mass_concentration(self.value)

    @classmethod
    def mg_per_liter(cls, ion: Ion, value: float) -> IonConcentration:
        """Construct an exact ion concentration reported in mg/L."""
        return cls(ion=ion, value=Q_(value, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class IonConcentrationRange:
    """Reported concentration range for a single ion."""

    ion: Ion
    minimum: Quantity
    maximum: Quantity

    def __post_init__(self) -> None:
        _validate_mass_concentration(self.minimum)
        _validate_mass_concentration(self.maximum)

        minimum = self.minimum.to("milligram / liter").magnitude
        maximum = self.maximum.to("milligram / liter").magnitude

        if minimum > maximum:
            raise ValueError("Ion concentration range minimum cannot exceed maximum.")

    @classmethod
    def mg_per_liter(
        cls,
        ion: Ion,
        minimum: float,
        maximum: float,
    ) -> IonConcentrationRange:
        """Construct an ion concentration range reported in mg/L."""
        return cls(
            ion=ion,
            minimum=Q_(minimum, "milligram / liter"),
            maximum=Q_(maximum, "milligram / liter"),
        )


@dataclass(frozen=True, slots=True)
class IonConcentrationUpperBound:
    """Reported ion concentration known only to be below an upper bound."""

    ion: Ion
    maximum: Quantity

    def __post_init__(self) -> None:
        _validate_mass_concentration(self.maximum)

        if self.maximum.to("milligram / liter").magnitude < 0:
            raise ValueError("Ion concentration upper bound cannot be negative.")

    @classmethod
    def mg_per_liter(
        cls,
        ion: Ion,
        maximum: float,
    ) -> IonConcentrationUpperBound:
        """Construct a less-than concentration reported in mg/L."""
        return cls(
            ion=ion,
            maximum=Q_(maximum, "milligram / liter"),
        )


type IonConcentrationValue = (
    IonConcentration | IonConcentrationRange | IonConcentrationUpperBound
)
