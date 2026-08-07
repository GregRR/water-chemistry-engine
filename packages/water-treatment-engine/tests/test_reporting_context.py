from datetime import date

import pytest
from water_treatment_engine.reporting_context import (
    ObservationPeriod,
    ReportedResultContext,
    ResultCoverage,
    WaterStage,
)


def test_observation_period_preserves_inclusive_dates() -> None:
    period = ObservationPeriod(
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
    )

    assert period.start == date(2025, 1, 1)
    assert period.end == date(2025, 12, 31)


def test_observation_period_rejects_reversed_dates() -> None:
    with pytest.raises(
        ValueError,
        match="start cannot be after end",
    ):
        ObservationPeriod(
            start=date(2025, 12, 31),
            end=date(2025, 1, 1),
        )


def test_result_context_supports_single_observation() -> None:
    context = ReportedResultContext(
        observed_on=date(2025, 6, 15),
        coverage=ResultCoverage.SINGLE_OBSERVATION,
        water_stage=WaterStage.TREATMENT_PLANT_OUTPUT,
        sample_location="Graham Hill Water Treatment Plant",
    )

    assert context.observed_on == date(2025, 6, 15)
    assert context.observation_period is None
    assert context.coverage is ResultCoverage.SINGLE_OBSERVATION
    assert context.water_stage is WaterStage.TREATMENT_PLANT_OUTPUT
    assert context.sample_location == "Graham Hill Water Treatment Plant"


def test_result_context_supports_period_summary() -> None:
    period = ObservationPeriod(
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
    )

    context = ReportedResultContext(
        observation_period=period,
        coverage=ResultCoverage.OBSERVATION_PERIOD_SUMMARY,
        water_stage=WaterStage.DISTRIBUTION_SYSTEM,
    )

    assert context.observation_period is period


def test_result_context_supports_typical_analysis() -> None:
    context = ReportedResultContext(
        coverage=ResultCoverage.TYPICAL_ANALYSIS,
        water_stage=WaterStage.BOTTLED_FINISHED_PRODUCT,
    )

    assert context.coverage is ResultCoverage.TYPICAL_ANALYSIS


def test_result_context_rejects_date_and_period_together() -> None:
    with pytest.raises(
        ValueError,
        match="cannot have both observed_on and observation_period",
    ):
        ReportedResultContext(
            observed_on=date(2025, 6, 15),
            observation_period=ObservationPeriod(
                start=date(2025, 1, 1),
                end=date(2025, 12, 31),
            ),
        )


def test_result_context_rejects_empty_sample_location() -> None:
    with pytest.raises(
        ValueError,
        match="sample location cannot be empty",
    ):
        ReportedResultContext(sample_location="   ")
