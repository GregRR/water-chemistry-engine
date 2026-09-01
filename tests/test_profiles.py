from datetime import date

import pytest
from fermunits import PHValue

from water_chemistry_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_properties import ReportedPH
from water_chemistry_engine.reporting_context import ObservationPeriod
from water_chemistry_engine.source_document import SourceDocumentMetadata


def test_source_water_profile_stores_reported_chemistry() -> None:
    calcium = IonConcentration.mg_per_liter(Ion.CALCIUM, 42.0)
    sulfate = IonConcentrationRange.mg_per_liter(
        Ion.SULFATE,
        minimum=25.0,
        maximum=40.0,
    )
    sodium = IonConcentrationUpperBound.mg_per_liter(
        Ion.SODIUM,
        maximum=5.0,
    )
    source_document = SourceDocumentMetadata(
        publisher="Example Water Company",
        title="2026 Water Quality Report",
        source_url="https://example.com/water-report.pdf",
    )

    profile = SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(calcium, sulfate, sodium),
        ph=ReportedPH.exact(7.6),
        observed_on=date(2026, 7, 1),
        source_document=source_document,
    )

    assert profile.name == "Example Municipal Water"
    assert profile.ph is not None
    assert profile.ph.calculation_value == PHValue(7.6)
    assert profile.observed_on == date(2026, 7, 1)
    assert profile.source_document is source_document
    assert profile.concentration_for(Ion.CALCIUM) is calcium
    assert profile.concentration_for(Ion.SULFATE) is sulfate
    assert profile.concentration_for(Ion.SODIUM) is sodium


def test_profile_can_exist_without_source_document() -> None:
    profile = SourceWaterProfile(
        name="Manually Entered Water",
        concentrations=(),
    )

    assert profile.source_document is None


def test_missing_ion_returns_none() -> None:
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),),
    )

    assert profile.concentration_for(Ion.MAGNESIUM) is None


def test_empty_name_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        SourceWaterProfile(
            name="   ",
            concentrations=(),
        )


def test_duplicate_ions_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate ion concentrations",
    ):
        SourceWaterProfile(
            name="Example Water",
            concentrations=(
                IonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),
                IonConcentrationRange.mg_per_liter(
                    Ion.CALCIUM,
                    minimum=35.0,
                    maximum=45.0,
                ),
            ),
        )


def test_source_profile_accepts_reported_ph_range_and_average() -> None:
    ph = ReportedPH.range(
        minimum=7.0,
        maximum=7.4,
        reported_average=7.2,
    )

    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(),
        ph=ph,
    )

    assert profile.ph is ph
    assert profile.ph.minimum == PHValue(7.0)
    assert profile.ph.maximum == PHValue(7.4)
    assert profile.ph.reported_average == PHValue(7.2)
    assert profile.ph.calculation_value == PHValue(7.2)


def test_source_profile_preserves_range_only_ph() -> None:
    ph = ReportedPH.range(
        minimum=7.0,
        maximum=7.4,
    )

    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(),
        ph=ph,
    )

    assert profile.ph is ph

    with pytest.raises(
        ValueError,
        match="range alone has no representative calculation value",
    ):
        _ = profile.ph.calculation_value


def test_source_profile_stores_reported_water_properties() -> None:
    from water_chemistry_engine.reported_properties import (
        Alkalinity,
        Conductivity,
        TotalDissolvedSolids,
        TotalHardness,
    )

    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(),
        alkalinity=Alkalinity.mg_per_liter_as_caco3(108.0),
        total_hardness=TotalHardness.mg_per_liter_as_caco3(140.0),
        total_dissolved_solids=TotalDissolvedSolids.mg_per_liter(225.0),
        conductivity=Conductivity.microsiemens_per_cm(
            350.0,
            reference_temperature_celsius=25.0,
        ),
    )

    assert profile.alkalinity is not None
    assert profile.total_hardness is not None
    assert profile.total_dissolved_solids is not None
    assert profile.conductivity is not None


def test_source_profile_accepts_observation_period() -> None:
    period = ObservationPeriod(
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
    )

    profile = SourceWaterProfile(
        name="2025 Annual Water",
        concentrations=(),
        observation_period=period,
    )

    assert profile.observed_on is None
    assert profile.observation_period is period


def test_observation_period_rejects_reversed_dates() -> None:
    with pytest.raises(
        ValueError,
        match="start cannot be after end",
    ):
        ObservationPeriod(
            start=date(2025, 12, 31),
            end=date(2025, 1, 1),
        )


def test_profile_rejects_single_date_and_period_together() -> None:
    with pytest.raises(
        ValueError,
        match="cannot have both observed_on and observation_period",
    ):
        SourceWaterProfile(
            name="Example Water",
            concentrations=(),
            observed_on=date(2025, 6, 1),
            observation_period=ObservationPeriod(
                start=date(2025, 1, 1),
                end=date(2025, 12, 31),
            ),
        )


def test_source_profile_preserves_water_identity() -> None:
    from water_chemistry_engine.water_identity import (
        PhysicalSourceType,
        PhysicalWaterSource,
        WaterIdentity,
        WaterType,
    )

    identity = WaterIdentity(
        provider="Example Water Utility",
        water_type=WaterType.MUNICIPAL_WATER,
        physical_sources=(
            PhysicalWaterSource(
                source_type=PhysicalSourceType.RESERVOIR,
                name="Example Reservoir",
            ),
        ),
    )

    profile = SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(),
        identity=identity,
    )

    assert profile.identity is identity


def test_source_profile_preserves_source_document_metadata() -> None:
    from water_chemistry_engine.source_document import SourceDocumentMetadata

    source_document = SourceDocumentMetadata(
        publisher="Example Water Utility",
        analysis_provider="Example Laboratory",
        title="2025 Water Quality Report",
    )

    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(),
        source_document=source_document,
    )

    assert profile.source_document is source_document


def test_source_profile_preserves_disinfectants_separately_from_chloride() -> None:
    from water_chemistry_engine.reported_disinfectants import (
        DisinfectantKind,
        ReportedDisinfectant,
    )

    chloride = IonConcentration.mg_per_liter(Ion.CHLORIDE, 35.0)
    chlorine = ReportedDisinfectant.mg_per_liter_range(
        DisinfectantKind.CHLORINE,
        minimum=0.11,
        maximum=1.52,
        reported_average=0.86,
        reported_label="Chlorine",
    )

    profile = SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(chloride,),
        disinfectants=(chlorine,),
    )

    assert profile.concentration_for(Ion.CHLORIDE) is chloride
    assert profile.disinfectant_for(DisinfectantKind.CHLORINE) is chlorine
    assert profile.disinfectant_for(DisinfectantKind.FREE_CHLORINE) is None


def test_source_profile_does_not_derive_combined_chlorine() -> None:
    from water_chemistry_engine.reported_disinfectants import (
        DisinfectantKind,
        ReportedDisinfectant,
    )

    free_chlorine = ReportedDisinfectant.mg_per_liter(
        DisinfectantKind.FREE_CHLORINE,
        0.4,
    )
    total_chlorine = ReportedDisinfectant.mg_per_liter(
        DisinfectantKind.TOTAL_CHLORINE,
        0.9,
    )
    profile = SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(),
        disinfectants=(free_chlorine, total_chlorine),
    )

    assert profile.disinfectant_for(DisinfectantKind.FREE_CHLORINE) is free_chlorine
    assert profile.disinfectant_for(DisinfectantKind.TOTAL_CHLORINE) is total_chlorine
    assert profile.disinfectant_for(DisinfectantKind.COMBINED_CHLORINE) is None
    assert profile.disinfectant_for(DisinfectantKind.CHLORAMINE) is None


def test_source_profile_rejects_duplicate_disinfectant_identity() -> None:
    from water_chemistry_engine.reported_disinfectants import (
        DisinfectantKind,
        ReportedDisinfectant,
    )

    with pytest.raises(ValueError, match="duplicate disinfectant results"):
        SourceWaterProfile(
            name="Example Municipal Water",
            concentrations=(),
            disinfectants=(
                ReportedDisinfectant.mg_per_liter(
                    DisinfectantKind.CHLORAMINE,
                    0.5,
                    species_name="Monochloramine",
                ),
                ReportedDisinfectant.mg_per_liter(
                    DisinfectantKind.CHLORAMINE,
                    0.7,
                    species_name="monochloramine",
                ),
            ),
        )
