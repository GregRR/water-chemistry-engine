import pytest
from fermunits import Q_

from water_chemistry_engine.blending import BlendSource, blend_waters
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.preparation_instructions import (
    build_preparation_instructions,
)
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    apply_treatment_additions,
)
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    GYPSUM,
)


def _state(calcium: float = 50.0) -> AqueousChemicalState:
    return AqueousChemicalState(
        concentrations=(DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, calcium),)
    )


def test_single_source_instruction_is_direct_and_actionable() -> None:
    blend = blend_waters((BlendSource("Tap water", _state(), Q_(10, "liter")),))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    instructions = build_preparation_instructions(blend, treatment)

    assert instructions.blend.text == "Use 10 L of Tap water as the starting water."
    assert instructions.blend.sources[0].source_index == 0
    assert instructions.blend.sources[0].fraction == pytest.approx(1.0)
    assert instructions.treatments == ()
    assert instructions.lines == ("Use 10 L of Tap water as the starting water.",)


def test_multi_source_instruction_preserves_source_order_and_total() -> None:
    blend = blend_waters(
        (
            BlendSource("Tap water", _state(60.0), Q_(7.5, "liter")),
            BlendSource("RO water", _state(0.0), Q_(2.5, "liter")),
        )
    )
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    instructions = build_preparation_instructions(blend, treatment)

    assert tuple(source.source_name for source in instructions.blend.sources) == (
        "Tap water",
        "RO water",
    )
    assert instructions.blend.text == (
        "Combine 7.5 L of Tap water + 2.5 L of RO water to make 10 L of blended water."
    )


def test_zero_volume_sources_are_omitted_from_actionable_blend_text() -> None:
    blend = blend_waters(
        (
            BlendSource("Tap water", _state(), Q_(10, "liter")),
            BlendSource(
                "Unused source", AqueousChemicalState(concentrations=()), Q_(0, "liter")
            ),
        )
    )
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    instructions = build_preparation_instructions(blend, treatment)

    assert tuple(source.source_index for source in instructions.blend.sources) == (0,)
    assert "Unused source" not in instructions.blend.text
    assert instructions.blend.text == "Use 10 L of Tap water as the starting water."


def test_treatment_instructions_preserve_order_identity_and_canonical_mass() -> None:
    blend = blend_waters((BlendSource("Source", _state(), Q_(10, "liter")),))
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (
            TreatmentAddition(GYPSUM, Q_(500, "milligram")),
            TreatmentAddition(CALCIUM_CHLORIDE_DIHYDRATE, Q_(1.25, "gram")),
        ),
    )

    instructions = build_preparation_instructions(blend, treatment)

    assert tuple(item.treatment_index for item in instructions.treatments) == (0, 1)
    assert tuple(item.addition.ingredient for item in instructions.treatments) == (
        GYPSUM,
        CALCIUM_CHLORIDE_DIHYDRATE,
    )
    assert tuple(
        float(item.mass.to("gram").magnitude) for item in instructions.treatments
    ) == pytest.approx((0.5, 1.25))
    assert instructions.lines == (
        "Use 10 L of Source as the starting water.",
        "Add 0.5 g of Gypsum (CaSO4·2H2O).",
        "Add 1.25 g of Calcium chloride dihydrate (CaCl2·2H2O).",
    )


def test_zero_mass_treatments_are_kept_in_audit_but_omitted_from_instructions() -> None:
    blend = blend_waters((BlendSource("Source", _state(), Q_(10, "liter")),))
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (
            TreatmentAddition(GYPSUM, Q_(0, "gram")),
            TreatmentAddition(CALCIUM_CHLORIDE_DIHYDRATE, Q_(1, "gram")),
        ),
    )

    instructions = build_preparation_instructions(blend, treatment)

    assert len(treatment.applied_treatments) == 2
    assert tuple(item.treatment_index for item in instructions.treatments) == (1,)
    assert instructions.treatments[0].text == (
        "Add 1 g of Calcium chloride dihydrate (CaCl2·2H2O)."
    )


def test_instruction_builder_rejects_treatment_from_another_state() -> None:
    blend = blend_waters((BlendSource("Source", _state(50.0), Q_(10, "liter")),))
    unrelated_treatment = apply_treatment_additions(
        _state(60.0),
        Q_(10, "liter"),
        (),
    )

    with pytest.raises(ValueError, match="initial state must match"):
        build_preparation_instructions(blend, unrelated_treatment)


def test_instruction_builder_rejects_treatment_for_another_volume() -> None:
    blend = blend_waters((BlendSource("Source", _state(), Q_(10, "liter")),))
    treatment_for_other_volume = apply_treatment_additions(
        blend.state,
        Q_(5, "liter"),
        (),
    )

    with pytest.raises(ValueError, match="water volume must match"):
        build_preparation_instructions(blend, treatment_for_other_volume)
