import pytest

from water_chemistry_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.target_profiles import TargetWaterProfile


def test_target_water_profile_stores_target_chemistry() -> None:
    calcium = IonConcentration.mg_per_liter(Ion.CALCIUM, 295.0)
    sulfate = IonConcentration.mg_per_liter(Ion.SULFATE, 725.0)

    profile = TargetWaterProfile(
        name="Burton-on-Trent",
        concentrations=(calcium, sulfate),
        style_associations=("English IPA", "Bitter"),
        notes="Historical brewing-city reference profile.",
    )

    assert profile.name == "Burton-on-Trent"
    assert profile.style_associations == ("English IPA", "Bitter")
    assert profile.concentration_for(Ion.CALCIUM) is calcium
    assert profile.concentration_for(Ion.SULFATE) is sulfate


def test_target_profile_supports_ranges() -> None:
    sulfate = IonConcentrationRange.mg_per_liter(
        Ion.SULFATE,
        minimum=100.0,
        maximum=150.0,
    )

    profile = TargetWaterProfile(
        name="Example Range Target",
        concentrations=(sulfate,),
    )

    assert profile.concentration_for(Ion.SULFATE) is sulfate


def test_missing_target_ion_returns_none() -> None:
    profile = TargetWaterProfile(
        name="Example Target",
        concentrations=(),
    )

    assert profile.concentration_for(Ion.MAGNESIUM) is None


def test_empty_target_name_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="name cannot be empty",
    ):
        TargetWaterProfile(
            name="   ",
            concentrations=(),
        )


def test_duplicate_target_ions_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate ion concentrations",
    ):
        TargetWaterProfile(
            name="Example Target",
            concentrations=(
                IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
                IonConcentration.mg_per_liter(Ion.CALCIUM, 75.0),
            ),
        )


@pytest.mark.parametrize("ph", [-0.1, 14.1])
def test_invalid_target_ph_is_rejected(ph: float) -> None:
    with pytest.raises(
        ValueError,
        match="pH must be between 0 and 14",
    ):
        TargetWaterProfile(
            name="Example Target",
            concentrations=(),
            ph=ph,
        )


def test_empty_style_association_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="style associations cannot be empty",
    ):
        TargetWaterProfile(
            name="Example Target",
            concentrations=(),
            style_associations=("IPA", "   "),
        )


def test_empty_notes_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="notes cannot be empty",
    ):
        TargetWaterProfile(
            name="Example Target",
            concentrations=(),
            notes="   ",
        )
