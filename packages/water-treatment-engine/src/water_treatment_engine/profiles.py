from dataclasses import dataclass
from datetime import date

from water_treatment_engine.concentrations import IonConcentrationValue
from water_treatment_engine.ions import Ion
from water_treatment_engine.reported_properties import (
    Alkalinity,
    Conductivity,
    ReportedPH,
    TotalDissolvedSolids,
    TotalHardness,
)
from water_treatment_engine.reporting_context import ObservationPeriod
from water_treatment_engine.source_document import SourceDocumentMetadata
from water_treatment_engine.water_identity import WaterIdentity


@dataclass(frozen=True, slots=True)
class SourceWaterProfile:
    """Measured or reported chemistry for a source of water."""

    name: str
    concentrations: tuple[IonConcentrationValue, ...]
    ph: ReportedPH | None = None
    observed_on: date | None = None
    observation_period: ObservationPeriod | None = None
    identity: WaterIdentity | None = None
    source_document: SourceDocumentMetadata | None = None
    alkalinity: Alkalinity | None = None
    total_hardness: TotalHardness | None = None
    total_dissolved_solids: TotalDissolvedSolids | None = None
    conductivity: Conductivity | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Source water profile name cannot be empty.")

        if self.observed_on is not None and self.observation_period is not None:
            raise ValueError(
                "Source water profile cannot have both observed_on "
                "and observation_period."
            )

        ions = [concentration.ion for concentration in self.concentrations]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Source water profile cannot contain duplicate ion concentrations."
            )

    def concentration_for(self, ion: Ion) -> IonConcentrationValue | None:
        """Return the reported concentration for an ion, if present."""
        for concentration in self.concentrations:
            if concentration.ion is ion:
                return concentration

        return None
