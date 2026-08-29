import pytest
from fermunits import Q_

from water_chemistry_engine._workflow_validation import (
    require_treatment_matches_blend,
)
from water_chemistry_engine.blending import BlendSource, blend_waters
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.treatment_application import apply_treatment_additions


def _state(calcium: float) -> AqueousChemicalState:
    return AqueousChemicalState(
        concentrations=(DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, calcium),)
    )


def test_linked_stage_validation_rejects_different_initial_state() -> None:
    blend = blend_waters((BlendSource("Source", _state(50.0), Q_(1, "liter")),))
    treatment = apply_treatment_additions(_state(60.0), Q_(1, "liter"), ())

    with pytest.raises(ValueError, match="initial state must match"):
        require_treatment_matches_blend(blend, treatment)


def test_linked_stage_validation_allows_only_volume_rounding_noise() -> None:
    blend = blend_waters((BlendSource("Source", _state(50.0), Q_(1, "liter")),))
    treatment = apply_treatment_additions(
        blend.state,
        Q_(1.0 + 5e-13, "liter"),
        (),
    )

    require_treatment_matches_blend(blend, treatment)


def test_linked_stage_validation_rejects_material_volume_difference() -> None:
    blend = blend_waters((BlendSource("Source", _state(50.0), Q_(1, "liter")),))
    treatment = apply_treatment_additions(
        blend.state,
        Q_(1.000001, "liter"),
        (),
    )

    with pytest.raises(ValueError, match="water volume must match"):
        require_treatment_matches_blend(blend, treatment)
