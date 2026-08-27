from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_
from water_treatment_engine.reported_disinfectants import (
    DisinfectantKind,
    ReportedDisinfectant,
)
from water_treatment_engine.reported_values import SourceResolutionPolicy
from water_treatment_engine.reporting_context import (
    ReportedResultContext,
    ResultCoverage,
    WaterStage,
)

ALLOW_MIDPOINTS = SourceResolutionPolicy(allow_exact_range_midpoints=True)
REPORTED_ONLY = SourceResolutionPolicy(allow_exact_range_midpoints=False)


def test_exact_disinfectant_preserves_source_metadata() -> None:
    context = ReportedResultContext(
        coverage=ResultCoverage.SINGLE_OBSERVATION,
        water_stage=WaterStage.DISTRIBUTION_SYSTEM,
    )
    result = ReportedDisinfectant(
        kind=DisinfectantKind.TOTAL_CHLORINE,
        value=Q_(Decimal("0.42"), "milligram / liter"),
        reported_label="Total Chlorine",
        reporting_basis="as Cl2",
        result_context=context,
    )

    assert result.kind is DisinfectantKind.TOTAL_CHLORINE
    assert result.value is not None
    assert result.value.magnitude == Decimal("0.42")
    assert result.calculation_value is result.value
    assert result.reported_label == "Total Chlorine"
    assert result.reporting_basis == "as Cl2"
    assert result.result_context is context


def test_disinfectant_range_prefers_reported_average() -> None:
    result = ReportedDisinfectant.mg_per_liter_range(
        DisinfectantKind.CHLORINE,
        minimum=0.11,
        maximum=1.52,
        reported_average=0.86,
        reported_label="Chlorine",
    )

    assert result.calculation_value.to("milligram / liter").magnitude == pytest.approx(
        0.86
    )


def test_disinfectant_range_midpoint_requires_explicit_policy() -> None:
    result = ReportedDisinfectant(
        kind=DisinfectantKind.FREE_CHLORINE,
        minimum=Q_(Decimal("0.20"), "milligram / liter"),
        maximum=Q_(Fraction(4, 5), "milligram / liter"),
    )

    with pytest.raises(
        ValueError,
        match="range alone has no representative calculation value",
    ):
        _ = result.calculation_value

    with pytest.raises(ValueError, match="explicit midpoint permission"):
        result.calculation_value_with_policy(REPORTED_ONLY)

    midpoint = result.calculation_value_with_policy(ALLOW_MIDPOINTS).to(
        "milligram / liter"
    )
    assert midpoint.magnitude == pytest.approx(0.5)
    assert isinstance(midpoint.magnitude, float)


def test_unqualified_chlorine_remains_distinct_from_free_chlorine() -> None:
    chlorine = ReportedDisinfectant.mg_per_liter(
        DisinfectantKind.CHLORINE,
        0.5,
        reported_label="Chlorine",
    )
    free_chlorine = ReportedDisinfectant.mg_per_liter(
        DisinfectantKind.FREE_CHLORINE,
        0.5,
        reported_label="Free Chlorine",
    )

    assert chlorine.identity_key != free_chlorine.identity_key


def test_named_chloramine_species_preserves_source_name() -> None:
    result = ReportedDisinfectant.mg_per_liter(
        DisinfectantKind.CHLORAMINE,
        1.1,
        species_name="Monochloramine",
        reported_label="Monochloramine Residual",
        reporting_basis="as Cl2",
    )

    assert result.species_name == "Monochloramine"
    assert result.identity_key == (
        DisinfectantKind.CHLORAMINE,
        "monochloramine",
    )


def test_named_species_is_rejected_for_non_chloramine_kind() -> None:
    with pytest.raises(
        ValueError,
        match="supported only for chloramine",
    ):
        ReportedDisinfectant.mg_per_liter(
            DisinfectantKind.CHLORINE_DIOXIDE,
            0.2,
            species_name="Example species",
        )


def test_disinfectant_rejects_non_concentration_quantity() -> None:
    with pytest.raises(
        ValueError,
        match="convertible to mass per volume",
    ):
        ReportedDisinfectant(
            kind=DisinfectantKind.CHLORINE,
            value=Q_(1.0, "gram"),
        )


def test_disinfectant_rejects_negative_concentration() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        ReportedDisinfectant.mg_per_liter(
            DisinfectantKind.CHLORINE,
            -0.1,
        )


def test_disinfectant_rejects_reversed_range() -> None:
    with pytest.raises(ValueError, match="minimum cannot exceed maximum"):
        ReportedDisinfectant.mg_per_liter_range(
            DisinfectantKind.CHLORINE,
            minimum=1.0,
            maximum=0.5,
        )


def test_disinfectant_average_must_fall_within_range() -> None:
    with pytest.raises(
        ValueError,
        match="reported average must fall within the reported range",
    ):
        ReportedDisinfectant.mg_per_liter_range(
            DisinfectantKind.CHLORINE,
            minimum=0.2,
            maximum=0.8,
            reported_average=1.0,
        )


def test_disinfectant_does_not_invent_reporting_basis() -> None:
    result = ReportedDisinfectant.mg_per_liter(
        DisinfectantKind.CHLORINE,
        0.5,
        reported_label="Chlorine",
    )

    assert result.reporting_basis is None
