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
        ph=7.6,
        observed_on=date(2026, 7, 1),
        provenance=provenance,
    )

    assert profile.name == "Example Municipal Water"
    assert profile.ph == 7.6
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


@pytest.mark.parametrize("ph", [-0.1, 14.1])
def test_invalid_ph_is_rejected(ph: float) -> None:
    with pytest.raises(
        ValueError,
        match="pH must be between 0 and 14",
    ):
        SourceWaterProfile(
            name="Example Water",
            concentrations=(),
            ph=ph,
        )


@pytest.mark.parametrize("ph", [0.0, 7.0, 14.0])
def test_valid_ph_is_accepted(ph: float) -> None:
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(),
        ph=ph,
    )

    assert profile.ph == ph


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
