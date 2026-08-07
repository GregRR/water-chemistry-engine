import pytest
from water_treatment_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)


def test_running_annual_average_is_distinct_statistic() -> None:
    statistic = ReportedStatistic(
        kind=ReportedStatisticKind.RUNNING_ANNUAL_AVERAGE,
    )

    assert statistic.kind is ReportedStatisticKind.RUNNING_ANNUAL_AVERAGE


def test_locational_running_annual_average_is_distinct_statistic() -> None:
    statistic = ReportedStatistic(
        kind=ReportedStatisticKind.LOCATIONAL_RUNNING_ANNUAL_AVERAGE,
    )

    assert statistic.kind is ReportedStatisticKind.LOCATIONAL_RUNNING_ANNUAL_AVERAGE


def test_percentile_preserves_percentile_value() -> None:
    statistic = ReportedStatistic.percentile_result(90.0)

    assert statistic.kind is ReportedStatisticKind.PERCENTILE
    assert statistic.percentile == 90.0


@pytest.mark.parametrize("percentile", [-0.1, 100.1])
def test_percentile_must_be_between_zero_and_one_hundred(
    percentile: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="Percentile must be between 0 and 100",
    ):
        ReportedStatistic.percentile_result(percentile)


def test_percentile_kind_requires_percentile_value() -> None:
    with pytest.raises(
        ValueError,
        match="requires a percentile value",
    ):
        ReportedStatistic(kind=ReportedStatisticKind.PERCENTILE)


def test_non_percentile_statistic_rejects_percentile_value() -> None:
    with pytest.raises(
        ValueError,
        match="only be supplied for a percentile statistic",
    ):
        ReportedStatistic(
            kind=ReportedStatisticKind.REPORTED_AVERAGE,
            percentile=90.0,
        )


def test_other_statistic_preserves_source_label() -> None:
    statistic = ReportedStatistic.other("Highest quarterly average")

    assert statistic.kind is ReportedStatisticKind.OTHER
    assert statistic.label == "Highest quarterly average"


def test_other_statistic_requires_label() -> None:
    with pytest.raises(
        ValueError,
        match="requires a label",
    ):
        ReportedStatistic(kind=ReportedStatisticKind.OTHER)
