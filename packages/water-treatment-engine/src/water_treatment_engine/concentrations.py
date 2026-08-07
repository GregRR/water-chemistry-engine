from dataclasses import dataclass

from fermunits import Q_
from pint import Quantity

from water_treatment_engine.ions import Ion


@dataclass(frozen=True, slots=True)
class IonConcentration:
    """Exact concentration of a single ion."""

    ion: Ion
    value: Quantity

    def __post_init__(self) -> None:
        try:
            self.value.to("milligram / liter")
        except Exception as exc:
            raise ValueError(
                "Ion concentration must be convertible to mass per volume."
            ) from exc

    @classmethod
    def mg_per_liter(cls, ion: Ion, value: float) -> IonConcentration:
        """Construct an ion concentration reported in mg/L."""
        return cls(ion=ion, value=Q_(value, "milligram / liter"))
