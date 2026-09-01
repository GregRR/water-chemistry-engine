"""Contract tests for the supported package-root consumer API."""

import re
from datetime import date
from pathlib import Path

import pytest
from fermunits import Q_, PHValue

import water_chemistry_engine as wce

EXPECTED_PUBLIC_API = {
    "AqueousChemicalState",
    "Alkalinity",
    "AppliedTreatment",
    "BlendIonContribution",
    "BlendIonResolution",
    "BlendPreparationInstruction",
    "BlendedSource",
    "CALCIUM_CHLORIDE_DIHYDRATE",
    "EPSOM_SALT",
    "GYPSUM",
    "POTASSIUM_CHLORIDE",
    "SIMPLE_MINERAL_INGREDIENTS",
    "SODIUM_BICARBONATE",
    "SODIUM_CHLORIDE",
    "ConcentrationRangeEndpoint",
    "Conductivity",
    "DerivedIonConcentration",
    "DisinfectantKind",
    "ExactConcentrationEndpoint",
    "ForwardCalculationNotice",
    "ForwardNoticeCode",
    "ForwardNoticeLevel",
    "ForwardSourceResult",
    "ForwardWaterCalculationResult",
    "ForwardWaterSource",
    "Ion",
    "IonConcentration",
    "IonConcentrationLowerBound",
    "IonConcentrationNotDetected",
    "IonConcentrationRange",
    "IonConcentrationUpperBound",
    "IonConcentrationValue",
    "IonContribution",
    "IonContributionMatrixRow",
    "LowerBoundConcentrationEndpoint",
    "NotDetectedConcentrationEndpoint",
    "ObservationPeriod",
    "PhysicalSourceType",
    "PhysicalWaterSource",
    "ReportedDisinfectant",
    "ReportedPH",
    "ReportedResultContext",
    "ReportedStatistic",
    "ReportedStatisticKind",
    "ReportingBasis",
    "ResolvedBlendIon",
    "ResolvedSourceIon",
    "ResolvedTreatmentIon",
    "SourceContributionCell",
    "SourceContributionCellStatus",
    "SourceContributionColumn",
    "SourceIonResolution",
    "SourceIonResolutionMethod",
    "SourceProfileResolutionResult",
    "SourceResolutionPolicy",
    "SourceDocumentMetadata",
    "SourceVolumeInstruction",
    "SourceWaterProfile",
    "TargetIonComparison",
    "TargetIonComparisonStatus",
    "TargetPHComparison",
    "TargetPHComparisonStatus",
    "TargetProfileComparison",
    "TargetProfileComparisonStatus",
    "TargetWaterProfile",
    "TreatmentAddition",
    "TreatmentApplicationResult",
    "TreatmentContributionCell",
    "TreatmentContributionCellStatus",
    "TreatmentContributionColumn",
    "TreatmentIonContribution",
    "TreatmentIonResolution",
    "TreatmentPreparationInstruction",
    "TotalDissolvedSolids",
    "TotalHardness",
    "UnresolvedBlendIon",
    "UnresolvedBlendIonReason",
    "UnresolvedSourceIon",
    "UnresolvedSourceIonReason",
    "UnresolvedTreatmentIon",
    "UnresolvedTreatmentIonReason",
    "UnsupportedTargetIonReason",
    "UpperBoundConcentrationEndpoint",
    "WaterBlendResult",
    "WaterContributionMatrix",
    "WaterIdentity",
    "WaterPreparationInstructions",
    "WaterStage",
    "WaterType",
    "ResultCoverage",
    "__version__",
    "calculate_forward_water",
}

_PUBLIC_API_DOC = Path(__file__).parents[1] / "docs" / "CONSUMER_API.md"
_PUBLIC_API_START = "<!-- public-api-inventory-start -->"
_PUBLIC_API_END = "<!-- public-api-inventory-end -->"


def test_public_api_exports_are_explicit_and_complete() -> None:
    """The package root exposes exactly the documented 0.3 consumer surface."""
    assert len(wce.__all__) == len(set(wce.__all__))
    assert set(wce.__all__) == EXPECTED_PUBLIC_API
    assert all(hasattr(wce, name) for name in wce.__all__)


def test_consumer_api_inventory_matches_package_exports() -> None:
    """The documented exact inventory cannot silently drift from ``__all__``."""
    document = _PUBLIC_API_DOC.read_text(encoding="utf-8")
    inventory = document.split(_PUBLIC_API_START, maxsplit=1)[1].split(
        _PUBLIC_API_END,
        maxsplit=1,
    )[0]
    documented_names = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", inventory))

    assert documented_names == EXPECTED_PUBLIC_API


def test_complete_forward_workflow_uses_only_package_root_imports() -> None:
    """A consumer can construct and interpret the proven workflow via the facade."""
    source_a = wce.SourceWaterProfile(
        name="Source A",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 40.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.SULFATE, 20.0),
        ),
    )
    source_b = wce.SourceWaterProfile(
        name="Source B",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 80.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.SULFATE, 40.0),
        ),
    )
    target = wce.TargetWaterProfile(
        name="Calcium target",
        concentrations=(
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.CALCIUM,
                minimum=65.0,
                maximum=75.0,
            ),
        ),
    )

    result = wce.calculate_forward_water(
        (
            wce.ForwardWaterSource(source_a, Q_(10, "liter")),
            wce.ForwardWaterSource(source_b, Q_(10, "liter")),
        ),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        treatment_additions=(wce.TreatmentAddition(wce.GYPSUM, Q_(0.5, "gram")),),
        target_profile=target,
    )

    calcium = result.final_state.concentration_for(wce.Ion.CALCIUM)
    assert calcium is not None
    assert float(calcium.to("milligram / liter").magnitude) == pytest.approx(65.81975)
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status
        is wce.TargetProfileComparisonStatus.SATISFIED
    )
    assert tuple(notice.code for notice in result.notices) == (
        wce.ForwardNoticeCode.TREATMENT_COMPLETE_DISSOLUTION_MODEL,
    )

    source_result = result.source_results[0]
    assert isinstance(source_result.resolution, wce.SourceProfileResolutionResult)
    assert isinstance(source_result.state, wce.AqueousChemicalState)
    source_calcium = source_result.resolution.resolution_for(wce.Ion.CALCIUM)
    assert isinstance(source_calcium, wce.ResolvedSourceIon)
    assert source_calcium.method is wce.SourceIonResolutionMethod.REPORTED_VALUE
    assert isinstance(source_calcium.concentration, wce.DerivedIonConcentration)

    assert isinstance(result.blend_result, wce.WaterBlendResult)
    assert all(
        isinstance(source, wce.BlendedSource) for source in result.blend_result.sources
    )
    blend_calcium = result.blend_result.resolution_for(wce.Ion.CALCIUM)
    assert isinstance(blend_calcium, wce.ResolvedBlendIon)
    assert all(
        isinstance(contribution, wce.BlendIonContribution)
        for contribution in blend_calcium.source_contributions
    )

    assert isinstance(result.treatment_result, wce.TreatmentApplicationResult)
    assert isinstance(
        result.treatment_result.applied_treatments[0], wce.AppliedTreatment
    )
    assert all(
        isinstance(contribution, wce.IonContribution)
        for contribution in result.treatment_result.applied_treatments[
            0
        ].ion_contributions
    )
    treated_calcium = result.treatment_result.resolution_for(wce.Ion.CALCIUM)
    assert isinstance(treated_calcium, wce.ResolvedTreatmentIon)
    assert all(
        isinstance(contribution, wce.TreatmentIonContribution)
        for contribution in treated_calcium.treatment_contributions
    )

    assert isinstance(result.contribution_matrix, wce.WaterContributionMatrix)
    assert all(
        isinstance(column, wce.SourceContributionColumn)
        for column in result.contribution_matrix.source_columns
    )
    assert all(
        isinstance(column, wce.TreatmentContributionColumn)
        for column in result.contribution_matrix.treatment_columns
    )
    calcium_row = result.contribution_matrix.row_for(wce.Ion.CALCIUM)
    assert isinstance(calcium_row, wce.IonContributionMatrixRow)
    assert all(
        isinstance(cell, wce.SourceContributionCell)
        and cell.status is wce.SourceContributionCellStatus.KNOWN
        for cell in calcium_row.source_contributions
    )
    assert isinstance(
        calcium_row.treatment_contributions[0],
        wce.TreatmentContributionCell,
    )
    assert (
        calcium_row.treatment_contributions[0].status
        is wce.TreatmentContributionCellStatus.CONTRIBUTES
    )

    assert isinstance(result.preparation_instructions, wce.WaterPreparationInstructions)
    assert isinstance(
        result.preparation_instructions.blend,
        wce.BlendPreparationInstruction,
    )
    assert all(
        isinstance(source, wce.SourceVolumeInstruction)
        for source in result.preparation_instructions.blend.sources
    )
    assert isinstance(
        result.preparation_instructions.treatments[0],
        wce.TreatmentPreparationInstruction,
    )
    assert result.preparation_instructions.lines == (
        "Combine 10 L of Source A + 10 L of Source B to make 20 L of blended water.",
        "Add 0.5 g of Gypsum (CaSO4·2H2O).",
    )


def test_complete_source_reporting_contract_uses_package_root_imports() -> None:
    """Consumers can preserve source identity, provenance, and report semantics."""
    period = wce.ObservationPeriod(
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
    )
    context = wce.ReportedResultContext(
        observation_period=period,
        coverage=wce.ResultCoverage.OBSERVATION_PERIOD_SUMMARY,
        water_stage=wce.WaterStage.TREATMENT_PLANT_OUTPUT,
        sample_location="Example Treatment Plant",
    )
    statistic = wce.ReportedStatistic(
        kind=wce.ReportedStatisticKind.REPORTED_AVERAGE,
    )
    source_document = wce.SourceDocumentMetadata(
        publisher="Example Water Utility",
        analysis_provider="Example Laboratory",
        title="2025 Water Quality Report",
        publication_date=date(2026, 5, 1),
        source_url="https://example.com/2025-water-quality-report.pdf",
        retrieved_on=date(2026, 8, 31),
        page_reference="Page 12, Table 3",
    )
    identity = wce.WaterIdentity(
        provider="Example Water Utility",
        water_type=wce.WaterType.MUNICIPAL_WATER,
        physical_sources=(
            wce.PhysicalWaterSource(
                source_type=wce.PhysicalSourceType.RESERVOIR,
                name="Example Reservoir",
                location="Example County",
            ),
        ),
    )
    chlorine = wce.ReportedDisinfectant(
        kind=wce.DisinfectantKind.TOTAL_CHLORINE,
        minimum=Q_(0.2, "milligram / liter"),
        maximum=Q_(0.8, "milligram / liter"),
        reported_average=Q_(0.5, "milligram / liter"),
        reported_statistic=statistic,
        result_context=context,
    )
    profile = wce.SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(
            wce.IonConcentration(
                ion=wce.Ion.CALCIUM,
                value=Q_(42.0, "milligram / liter"),
                reported_statistic=statistic,
                result_context=context,
            ),
        ),
        ph=wce.ReportedPH(
            minimum=PHValue(7.2),
            maximum=PHValue(7.8),
            reported_average=PHValue(7.5),
            result_context=context,
        ),
        observation_period=period,
        identity=identity,
        source_document=source_document,
        alkalinity=wce.Alkalinity(
            value=Q_(105.0, "milligram / liter"),
            basis=wce.ReportingBasis.AS_CACO3,
            result_context=context,
        ),
        total_hardness=wce.TotalHardness(
            value=Q_(140.0, "milligram / liter"),
            result_context=context,
        ),
        total_dissolved_solids=wce.TotalDissolvedSolids(
            value=Q_(220.0, "milligram / liter"),
            result_context=context,
        ),
        conductivity=wce.Conductivity(
            value=Q_(350.0, "microsiemens / centimeter"),
            reference_temperature_celsius=25.0,
            result_context=context,
        ),
        disinfectants=(chlorine,),
    )

    assert profile.observation_period is period
    assert profile.identity is identity
    assert profile.identity.physical_sources[0].source_type is (
        wce.PhysicalSourceType.RESERVOIR
    )
    assert profile.source_document is source_document
    assert profile.source_document.analysis_provider == "Example Laboratory"
    assert profile.ph is not None
    assert profile.ph.calculation_value == PHValue(7.5)
    assert profile.alkalinity is not None
    assert profile.alkalinity.basis is wce.ReportingBasis.AS_CACO3
    assert profile.total_hardness is not None
    assert profile.total_dissolved_solids is not None
    assert profile.conductivity is not None
    assert profile.disinfectant_for(wce.DisinfectantKind.TOTAL_CHLORINE) is chlorine
    assert chlorine.reported_statistic is statistic
    assert chlorine.result_context is context


def test_public_api_preserves_unknown_and_notice_semantics() -> None:
    """The facade does not turn a bounded report result into a known value."""
    source = wce.SourceWaterProfile(
        name="Bounded source",
        concentrations=(
            wce.IonConcentrationUpperBound.mg_per_liter(
                wce.Ion.CHLORIDE,
                maximum=20.0,
            ),
        ),
    )
    target = wce.TargetWaterProfile(
        name="Chloride target",
        concentrations=(wce.IonConcentration.mg_per_liter(wce.Ion.CHLORIDE, 20.0),),
    )

    result = wce.calculate_forward_water(
        (wce.ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        target_profile=target,
    )

    assert result.final_state.concentration_for(wce.Ion.CHLORIDE) is None
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status
        is wce.TargetProfileComparisonStatus.INDETERMINATE
    )
    assert tuple(notice.code for notice in result.notices) == (
        wce.ForwardNoticeCode.SOURCE_ION_UNRESOLVED,
        wce.ForwardNoticeCode.TARGET_ACTUAL_UNKNOWN,
    )

    source_resolution = result.source_results[0].resolution.resolution_for(
        wce.Ion.CHLORIDE
    )
    assert isinstance(source_resolution, wce.UnresolvedSourceIon)
    assert source_resolution.reason is wce.UnresolvedSourceIonReason.UPPER_BOUND

    blend_resolution = result.blend_result.resolution_for(wce.Ion.CHLORIDE)
    assert isinstance(blend_resolution, wce.UnresolvedBlendIon)
    assert (
        blend_resolution.reason
        is wce.UnresolvedBlendIonReason.MISSING_SOURCE_CONCENTRATION
    )

    treatment_resolution = result.treatment_result.resolution_for(wce.Ion.CHLORIDE)
    assert isinstance(treatment_resolution, wce.UnresolvedTreatmentIon)
    assert (
        treatment_resolution.reason
        is wce.UnresolvedTreatmentIonReason.MISSING_INITIAL_CONCENTRATION
    )

    chloride_row = result.contribution_matrix.row_for(wce.Ion.CHLORIDE)
    assert chloride_row.source_contributions[0].status is (
        wce.SourceContributionCellStatus.SOURCE_CONCENTRATION_UNKNOWN
    )
