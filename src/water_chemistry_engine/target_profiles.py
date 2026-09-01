from dataclasses import dataclass

from fermunits import PHValue

from water_chemistry_engine.concentrations import IonConcentrationValue
from water_chemistry_engine.ions import Ion


@dataclass(frozen=True, slots=True)
class TargetWaterProfile:
    """Desired or reference chemistry for treated water."""

    name: str
    concentrations: tuple[IonConcentrationValue, ...]
    ph: PHValue | None = None
    style_associations: tuple[str, ...] = ()
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Target water profile name cannot be empty.")

        ions = [concentration.ion for concentration in self.concentrations]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Target water profile cannot contain duplicate ion concentrations."
            )

        if self.ph is not None and not isinstance(self.ph, PHValue):
            raise TypeError("Target water profile pH must use fermunits.PHValue.")

        if any(not style.strip() for style in self.style_associations):
            raise ValueError("Target water profile style associations cannot be empty.")

        if self.notes is not None and not self.notes.strip():
            raise ValueError("Target water profile notes cannot be empty.")

    def concentration_for(self, ion: Ion) -> IonConcentrationValue | None:
        """Return the target concentration for an ion, if present."""
        for concentration in self.concentrations:
            if concentration.ion is ion:
                return concentration

        return None
