from datetime import date

import pytest
from water_treatment_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.profiles import SourceWaterProfile
from water_treatment_engine.provenance import SourceWaterProvenance
from water_treatment_engine.reported_properties import ReportedPH


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
    provenance = SourceWaterProvenance(
        provider="Example Water Company",
        report_title="2026 Water Quality Report",
        source_url="https://example.com/water-report.pdf",
    )

    profile = SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(calcium, sulfate, sodium),
        ph=ReportedPH.exact(7.6),
        observed_on=date(2026, 7, 1),
        provenance=provenance,
    )

    assert profile.name == "Example Municipal Water"
    assert profile.ph is not None
    assert profile.ph.calculation_value == 7.6
    assert profile.observed_on == date(2026, 7, 1)
    assert profile.provenance is provenance
    assert profile.concentration_for(Ion.CALCIUM) is calcium
    assert profile.concentration_for(Ion.SULFATE) is sulfate
    assert profile.concentration_for(Ion.SODIUM) is sodium


def test_profile_can_exist_without_provenance() -> None:
    profile = SourceWaterProfile(
        name="Manually Entered Water",
        concentrations=(),
    )

    assert profile.provenance is None


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
    assert profile.ph.minimum == 7.0
    assert profile.ph.maximum == 7.4
    assert profile.ph.reported_average == 7.2
    assert profile.ph.calculation_value == 7.2


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
    from water_treatment_engine.reported_properties import (
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
