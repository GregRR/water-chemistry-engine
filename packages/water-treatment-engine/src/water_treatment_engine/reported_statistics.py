from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReportedStatisticKind(StrEnum):
    """Statistical meaning explicitly assigned to a result by its source."""

    SINGLE_OBSERVATION = "single_observation"
    REPORTED_AVERAGE = "reported_average"
    RUNNING_ANNUAL_AVERAGE = "running_annual_average"
    LOCATIONAL_RUNNING_ANNUAL_AVERAGE = "locational_running_annual_average"
    PERCENTILE = "percentile"
    HIGHEST_RESULT = "highest_result"
    LOWEST_RESULT = "lowest_result"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ReportedStatistic:
    """Source-reported statistical meaning for a water-quality result."""

    kind: ReportedStatisticKind
    percentile: float | None = None
    label: str | None = None

    def __post_init__(self) -> None:
        if self.kind is ReportedStatisticKind.PERCENTILE:
            if self.percentile is None:
                raise ValueError("Percentile statistic requires a percentile value.")
            if not 0.0 <= self.percentile <= 100.0:
                raise ValueError("Percentile must be between 0 and 100.")
        elif self.percentile is not None:
            raise ValueError(
                "Percentile value may only be supplied for a percentile statistic."
            )

        if self.label is not None and not self.label.strip():
            raise ValueError("Reported statistic label cannot be empty.")

        if self.kind is ReportedStatisticKind.OTHER and self.label is None:
            raise ValueError("Other reported statistic requires a label.")

    @classmethod
    def percentile_result(cls, percentile: float) -> ReportedStatistic:
        """Construct a source-reported percentile statistic."""
        return cls(
            kind=ReportedStatisticKind.PERCENTILE,
            percentile=percentile,
        )

    @classmethod
    def other(cls, label: str) -> ReportedStatistic:
        """Construct a source-specific named statistic."""
        return cls(
            kind=ReportedStatisticKind.OTHER,
            label=label,
        )
