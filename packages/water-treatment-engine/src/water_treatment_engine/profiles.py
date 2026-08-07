from dataclasses import dataclass
from datetime import date

from water_treatment_engine.concentrations import IonConcentrationValue
from water_treatment_engine.ions import Ion


@dataclass(frozen=True, slots=True)
class SourceWaterProfile:
    """Measured or reported chemistry for a source of water."""

    name: str
    concentrations: tuple[IonConcentrationValue, ...]
    ph: float | None = None
    observed_on: date | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Source water profile name cannot be empty.")

        ions = [concentration.ion for concentration in self.concentrations]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Source water profile cannot contain duplicate ion concentrations."
            )

        if self.ph is not None and not 0.0 <= self.ph <= 14.0:
            raise ValueError("Source water profile pH must be between 0 and 14.")

    def concentration_for(self, ion: Ion) -> IonConcentrationValue | None:
        """Return the reported concentration for an ion, if present."""
        for concentration in self.concentrations:
            if concentration.ion is ion:
                return concentration

        return None
