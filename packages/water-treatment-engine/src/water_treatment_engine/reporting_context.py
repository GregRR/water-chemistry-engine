from dataclasses import dataclass
from datetime import date
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class ObservationPeriod:
    """Inclusive period over which reported water chemistry applies."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("Observation period start cannot be after end.")


class ResultCoverage(StrEnum):
    """How the source characterizes the coverage of a reported result."""

    SINGLE_OBSERVATION = "single_observation"
    OBSERVATION_PERIOD_SUMMARY = "observation_period_summary"
    TYPICAL_ANALYSIS = "typical_analysis"
    HISTORICAL_REFERENCE = "historical_reference"


class WaterStage(StrEnum):
    """Stage or sampling context at which water chemistry was measured."""

    RAW_SOURCE = "raw_source"
    FINISHED_WATER = "finished_water"
    TREATMENT_PLANT_OUTPUT = "treatment_plant_output"
    DISTRIBUTION_SYSTEM = "distribution_system"
    CUSTOMER_TAP = "customer_tap"
    BOTTLED_FINISHED_PRODUCT = "bottled_finished_product"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ReportedResultContext:
    """Timing and sampling context explicitly associated with a result."""

    observed_on: date | None = None
    observation_period: ObservationPeriod | None = None
    coverage: ResultCoverage | None = None
    water_stage: WaterStage | None = None
    sample_location: str | None = None

    def __post_init__(self) -> None:
        if self.observed_on is not None and self.observation_period is not None:
            raise ValueError(
                "Reported result context cannot have both observed_on "
                "and observation_period."
            )

        if self.sample_location is not None and not self.sample_location.strip():
            raise ValueError("Reported result sample location cannot be empty.")
