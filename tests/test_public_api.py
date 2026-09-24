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
    "AlkalinityAnalyticalContext",
    "AlkalinityBalanceResult",
    "AlkalinityContributionMatrixRow",
    "AlkalinityModelLimitation",
    "AlkalinityResultIdentity",
    "AppliedTreatment",
    "BlendIonContribution",
    "BlendIonResolution",
    "BlendPreparationInstruction",
    "BlendedSource",
    "BlendedAlkalinityResult",
    "CALCIUM_CHLORIDE_ANHYDROUS",
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
    "ExactMassDosedTreatmentMaterial",
    "ExactMassFractionTreatmentMaterial",
    "ExactMassPerVolumeDosedSolutionTreatmentMaterial",
    "ExactVolumeDosedSolutionTreatmentMaterial",
    "ForwardCalculationNotice",
    "ForwardNoticeCode",
    "ForwardNoticeLevel",
    "ForwardSourceResult",
    "ForwardWaterCalculationResult",
    "ForwardWaterSource",
    "FinalAlkalinityResult",
    "Ion",
    "IonConcentration",
    "IonConcentrationLowerBound",
    "IonConcentrationNotDetected",
    "IonConcentrationRange",
    "IonConcentrationUpperBound",
    "IonConcentrationValue",
    "IonContribution",
    "IonContributionCalculationBasis",
    "IonContributionMatrixRow",
    "LowerBoundConcentrationEndpoint",
    "ModeledAlkalinity",
    "NotDetectedConcentrationEndpoint",
    "ObservationPeriod",
    "OptimizerBlendPolicy",
    "OptimizerDiagnostic",
    "OptimizerDiagnosticCode",
    "OptimizerFeasibilityStatus",
    "OptimizerInputSupportStatus",
    "OptimizerMaterialAddition",
    "OptimizerMaterialConstraint",
    "OptimizerPlan",
    "OptimizerPracticalityStatus",
    "OptimizerRequest",
    "OptimizerResult",
    "OptimizerSolverReport",
    "OptimizerSource",
    "OptimizerSourceVolume",
    "OptimizerStrategy",
    "OptimizerTargetFitStatus",
    "PhysicalSourceType",
    "PhysicalWaterSource",
    "ReportedDisinfectant",
    "ReportedPH",
    "ReportedResultContext",
    "ReportedStatistic",
    "ReportedStatisticKind",
    "RangedMassFractionTreatmentMaterial",
    "ReportingBasis",
    "ResolvedBlendIon",
    "ResolvedMassPerVolumeSolutionDose",
    "ResolvedSourceAlkalinity",
    "ResolvedSourceIon",
    "ResolvedTreatmentIon",
    "ResolvedTreatmentMaterialVolumeDose",
    "SourceContributionCell",
    "SourceContributionCellStatus",
    "SourceContributionColumn",
    "SourceAlkalinityContribution",
    "SourceAlkalinityResolution",
    "SourceAlkalinityResolutionMethod",
    "SourceIonResolution",
    "SourceIonResolutionMethod",
    "SourceProfileResolutionResult",
    "SourceResolutionPolicy",
    "SourceDocumentMetadata",
    "SourceVolumeInstruction",
    "SourceWaterProfile",
    "TargetAlkalinityComparison",
    "TargetAlkalinityComparisonStatus",
    "TargetComparisonPolicy",
    "TargetIonCalculationBasis",
    "TargetIonComparison",
    "TargetIonComparisonStatus",
    "TargetIonClosenessPolicy",
    "TargetIonClosenessStatus",
    "TargetPHComparison",
    "TargetPHComparisonStatus",
    "TargetProfileCatalog",
    "TargetProfileClassification",
    "TargetProfileComparison",
    "TargetProfileComparisonStatus",
    "TargetProfileProvenance",
    "TargetWaterProfile",
    "TreatmentAddition",
    "TreatmentMaterialActiveMassRange",
    "TreatmentMaterialForm",
    "TreatmentMaterialUseLimit",
    "TreatmentAlkalinityContribution",
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
    "UnresolvedSourceAlkalinity",
    "UnresolvedSourceAlkalinityReason",
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
    "ScalarQuantity",
    "SampleFiltrationState",
    "__version__",
    "calculate_forward_water",
    "optimize_treatment",
}

_PUBLIC_API_DOC = Path(__file__).parents[1] / "docs" / "CONSUMER_API.md"
_PUBLIC_API_START = "<!-- public-api-inventory-start -->"
_PUBLIC_API_END = "<!-- public-api-inventory-end -->"


def test_public_api_exports_are_explicit_and_complete() -> None:
    """The package root exposes exactly the documented consumer surface."""
    assert len(wce.__all__) == len(set(wce.__all__))
    assert set(wce.__all__) == EXPECTED_PUBLIC_API
    assert all(hasattr(wce, name) for name in wce.__all__)


def test_consumer_can_construct_sourced_material_use_limit_from_package_root() -> None:
    source = wce.SourceDocumentMetadata(
        publisher="Example standards organization",
        title="Example material-use guidance",
    )

    use_limit = wce.TreatmentMaterialUseLimit(
        key="example.gypsum.finished-water.v1",
        version="1.0.0",
        material_key="pure_gypsum",
        description="Example upper operational dose for finished water.",
        applicability="Only for the process and water state described by the source.",
        maximum_measured_mass_per_volume=Q_(0.2, "gram / liter"),
        source_document=source,
    )

    assert use_limit.maximum_measured_mass_for(Q_(5, "liter")).magnitude == (
        pytest.approx(1.0)
    )


def test_consumer_api_inventory_matches_package_exports() -> None:
    """The documented exact inventory cannot silently drift from ``__all__``."""
    document = _PUBLIC_API_DOC.read_text(encoding="utf-8")
    inventory = document.split(_PUBLIC_API_START, maxsplit=1)[1].split(
        _PUBLIC_API_END,
        maxsplit=1,
    )[0]
    documented_names = set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", inventory))

    assert documented_names == EXPECTED_PUBLIC_API


def test_target_profile_provenance_uses_only_package_root_imports() -> None:
    """Consumers can preserve a reference's evidence through the facade."""
    document = wce.SourceDocumentMetadata(
        publisher="Example Standards Organization",
        title="Example Water Standard",
        source_url="https://example.com/water-standard",
    )
    provenance = wce.TargetProfileProvenance(
        classification=wce.TargetProfileClassification.PUBLISHED_STANDARD,
        source_document=document,
        profile_key="example-water-standard",
        profile_version="2026",
    )

    target = wce.TargetWaterProfile(
        name="Example standard",
        concentrations=(),
        provenance=provenance,
    )

    assert target.provenance is provenance


def test_curated_target_profile_catalog_uses_package_root_imports() -> None:
    profile = wce.TargetWaterProfile(
        name="Example published recommendation",
        concentrations=(wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 50.0),),
        provenance=wce.TargetProfileProvenance(
            classification=wce.TargetProfileClassification.PUBLISHED_RECOMMENDATION,
            source_document=wce.SourceDocumentMetadata(
                publisher="Example Standards Organization",
            ),
            profile_key="example-published-recommendation",
            profile_version="1",
        ),
    )
    catalog = wce.TargetProfileCatalog(
        catalog_key="example-catalog",
        catalog_version="2026.1",
        profiles=(profile,),
    )

    assert catalog.profile_for("example-published-recommendation", "1") is profile


def test_volume_dosed_solution_flows_through_package_root_forward_api() -> None:
    """A resolved physical volume dose becomes an ordinary forward addition."""
    material = wce.ExactVolumeDosedSolutionTreatmentMaterial(
        key="calcium_chloride_solution",
        name="Exact calcium chloride solution",
        ingredient=wce.CALCIUM_CHLORIDE_ANHYDROUS,
        active_mass_fraction=Q_(32.5, "percent"),
        density=Q_(1.2, "gram / milliliter"),
        density_reference_temperature=Q_(20, "degree_Celsius"),
        dose_increment=Q_(1, "milliliter"),
    )
    resolved = material.resolve_volume_dose(
        Q_(10, "milliliter"),
        measurement_temperature=Q_(20, "degree_Celsius"),
    )
    source = wce.SourceWaterProfile(
        name="Source",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 0.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.CHLORIDE, 0.0),
        ),
    )

    result = wce.calculate_forward_water(
        (wce.ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        treatment_additions=(resolved.treatment_addition,),
    )

    moles = 3.9 / 110.978
    calcium = result.final_state.concentration_for(wce.Ion.CALCIUM)
    chloride = result.final_state.concentration_for(wce.Ion.CHLORIDE)
    assert calcium is not None
    assert chloride is not None
    assert resolved.solution_mass.magnitude == pytest.approx(12.0)
    assert resolved.active_chemical_mass.magnitude == pytest.approx(3.9)
    assert calcium.magnitude == pytest.approx(moles * 40.078 * 100.0)
    assert chloride.magnitude == pytest.approx(moles * 2 * 35.45 * 100.0)


def test_mass_per_volume_solution_flows_through_package_root_forward_api() -> None:
    """A stated mass/volume basis resolves without inferred solution density."""
    material = wce.ExactMassPerVolumeDosedSolutionTreatmentMaterial(
        key="calcium_chloride_mass_per_volume_solution",
        name="100 g/L calcium chloride solution",
        ingredient=wce.CALCIUM_CHLORIDE_ANHYDROUS,
        active_mass_concentration=Q_(100, "gram / liter"),
        concentration_reference_temperature=Q_(20, "degree_Celsius"),
        dose_increment=Q_(1, "milliliter"),
    )
    resolved = material.resolve_volume_dose(
        Q_(25, "milliliter"),
        measurement_temperature=Q_(20, "degree_Celsius"),
    )
    source = wce.SourceWaterProfile(
        name="Source",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 0.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.CHLORIDE, 0.0),
        ),
    )

    result = wce.calculate_forward_water(
        (wce.ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        treatment_additions=(resolved.treatment_addition,),
    )

    moles = 2.5 / 110.978
    calcium = result.final_state.concentration_for(wce.Ion.CALCIUM)
    chloride = result.final_state.concentration_for(wce.Ion.CHLORIDE)
    assert calcium is not None
    assert chloride is not None
    assert resolved.active_chemical_mass.magnitude == pytest.approx(2.5)
    assert calcium.magnitude == pytest.approx(moles * 40.078 * 100.0)
    assert chloride.magnitude == pytest.approx(moles * 2 * 35.45 * 100.0)


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


def test_complete_optimizer_workflow_uses_only_package_root_imports() -> None:
    """A consumer can construct and interpret a practical plan via the facade."""
    gypsum_calcium_mg_per_liter = 40.078 / 172.164 * 50.0
    gypsum_sulfate_mg_per_liter = 96.056 / 172.164 * 50.0
    source = wce.SourceWaterProfile(
        name="Source water",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 100.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.SULFATE, 0.0),
        ),
    )
    diluent = wce.SourceWaterProfile(
        name="Characterized RO",
        concentrations=(
            wce.IonConcentration.mg_per_liter(wce.Ion.CALCIUM, 0.0),
            wce.IonConcentration.mg_per_liter(wce.Ion.SULFATE, 0.0),
        ),
    )
    target = wce.TargetWaterProfile(
        name="Calcium and sulfate target",
        concentrations=(
            wce.IonConcentration.mg_per_liter(
                wce.Ion.CALCIUM,
                50.0 + gypsum_calcium_mg_per_liter,
            ),
            wce.IonConcentration.mg_per_liter(
                wce.Ion.SULFATE,
                gypsum_sulfate_mg_per_liter,
            ),
        ),
    )
    material = wce.ExactMassDosedTreatmentMaterial(
        key="gypsum",
        name="Gypsum",
        ingredient=wce.GYPSUM,
        dose_increment=Q_(0.1, "gram"),
    )
    request = wce.OptimizerRequest(
        total_volume=Q_(20, "liter"),
        sources=(
            wce.OptimizerSource(
                source_profile=source,
                current_volume=Q_(20, "liter"),
                maximum_volume=Q_(20, "liter"),
            ),
        ),
        diluent_source=wce.OptimizerSource(
            source_profile=diluent,
            current_volume=Q_(0, "liter"),
            maximum_volume=Q_(20, "liter"),
        ),
        material_constraints=(
            wce.OptimizerMaterialConstraint(
                material=material,
                maximum_mass=Q_(2, "gram"),
            ),
        ),
        source_resolution_policy=wce.SourceResolutionPolicy(
            allow_exact_range_midpoints=False,
        ),
        blend_policy=wce.OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        target_profile=target,
        request_no_dilution_plan=True,
    )

    result = wce.optimize_treatment(request)

    assert isinstance(result, wce.OptimizerResult)
    assert result.input_support is wce.OptimizerInputSupportStatus.SUPPORTED
    assert result.feasibility is wce.OptimizerFeasibilityStatus.FEASIBLE
    assert len(result.plans) == 2
    preferred = result.plans[0]
    assert isinstance(preferred, wce.OptimizerPlan)
    assert preferred.strategy is wce.OptimizerStrategy.CLOSEST_ABSOLUTE_MG_PER_LITER
    assert preferred.target_fit is wce.OptimizerTargetFitStatus.WITHIN_TARGET
    assert preferred.practicality is wce.OptimizerPracticalityStatus.PRACTICAL
    assert all(
        isinstance(entry, wce.OptimizerSourceVolume)
        for entry in preferred.source_volumes
    )
    assert tuple(
        float(entry.volume.magnitude) for entry in preferred.source_volumes
    ) == (
        pytest.approx(10.0),
        pytest.approx(10.0),
    )
    assert len(preferred.material_additions) == 1
    assert isinstance(preferred.material_additions[0], wce.OptimizerMaterialAddition)
    assert float(preferred.material_additions[0].measured_mass.magnitude) == (
        pytest.approx(1.0)
    )
    assert isinstance(preferred.solver_report, wce.OptimizerSolverReport)
    assert (
        preferred.calculation.final_state
        is preferred.calculation.treatment_result.final_state
    )
    assert result.plans[1].strategy is (
        wce.OptimizerStrategy.NO_DILUTION_CLOSEST_ABSOLUTE_MG_PER_LITER
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
    alkalinity_analytical_context = wce.AlkalinityAnalyticalContext(
        result_identity=wce.AlkalinityResultIdentity.TOTAL_ALKALINITY,
        sample_filtration_state=wce.SampleFiltrationState.FILTERED,
        original_analyte_label="Alkalinity, Total",
        original_unit_label="mg/L as CaCO3",
        analytical_method="Example laboratory titration",
        method_code="EXAMPLE-ALK-1",
        titration_endpoint=PHValue(4.5),
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
            reported_average=PHValue(7.4),
            result_context=context,
        ),
        observation_period=period,
        identity=identity,
        source_document=source_document,
        alkalinity=wce.Alkalinity(
            value=Q_(105.0, "milligram / liter"),
            basis=wce.ReportingBasis.AS_CACO3,
            result_context=context,
            reported_statistic=statistic,
            analytical_context=alkalinity_analytical_context,
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
    assert profile.ph.calculation_value == PHValue(7.4)
    assert profile.alkalinity is not None
    assert profile.alkalinity.basis is wce.ReportingBasis.AS_CACO3
    assert profile.alkalinity.reported_statistic is statistic
    assert profile.alkalinity.analytical_context is alkalinity_analytical_context
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
