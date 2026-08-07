from datetime import date

import pytest
from water_treatment_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.profiles import SourceWaterProfile


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

    profile = SourceWaterProfile(
        name="Example Municipal Water",
        concentrations=(calcium, sulfate, sodium),
        ph=7.6,
        observed_on=date(2026, 7, 1),
    )

    assert profile.name == "Example Municipal Water"
    assert profile.ph == 7.6
    assert profile.observed_on == date(2026, 7, 1)
    assert profile.concentration_for(Ion.CALCIUM) is calcium
    assert profile.concentration_for(Ion.SULFATE) is sulfate
    assert profile.concentration_for(Ion.SODIUM) is sodium


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
