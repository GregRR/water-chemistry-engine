from decimal import Decimal

import pytest
from fermunits import Q_

from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.treatment_application import (
    ResolvedTreatmentIon,
    TreatmentAddition,
    UnresolvedTreatmentIon,
    UnresolvedTreatmentIonReason,
    apply_treatment_additions,
)
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    GYPSUM,
    SODIUM_CHLORIDE,
)


def _state(**values: float) -> AqueousChemicalState:
    concentrations = tuple(
        DerivedIonConcentration.mg_per_liter(Ion(ion_name), value)
        for ion_name, value in values.items()
    )
    return AqueousChemicalState(concentrations=concentrations)


def _mg_per_liter(state: AqueousChemicalState, ion: Ion) -> float | None:
    concentration = state.concentration_for(ion)
    if concentration is None:
        return None
    return float(concentration.to("milligram / liter").magnitude)


def test_one_addition_updates_known_ions() -> None:
    initial = _state(calcium=50.0, chloride=0.0, sulfate=80.0)

    result = apply_treatment_additions(
        initial,
        Q_(10, "liter"),
        (
            TreatmentAddition(
                ingredient=CALCIUM_CHLORIDE_DIHYDRATE,
                mass=Q_(1, "gram"),
            ),
        ),
    )

    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(
        77.2625,
        abs=0.001,
    )
    assert _mg_per_liter(result.final_state, Ion.CHLORIDE) == pytest.approx(
        48.2286,
        abs=0.001,
    )
    assert _mg_per_liter(result.final_state, Ion.SULFATE) == pytest.approx(80.0)


def test_missing_initial_ion_remains_unknown_after_known_contribution() -> None:
    result = apply_treatment_additions(
        _state(calcium=50.0),
        Q_(10, "liter"),
        (
            TreatmentAddition(
                CALCIUM_CHLORIDE_DIHYDRATE,
                Q_(1, "gram"),
            ),
        ),
    )

    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(
        77.2625,
        abs=0.001,
    )
    assert result.final_state.concentration_for(Ion.CHLORIDE) is None

    chloride_resolution = result.resolution_for(Ion.CHLORIDE)
    assert isinstance(chloride_resolution, UnresolvedTreatmentIon)
    assert (
        chloride_resolution.reason
        is UnresolvedTreatmentIonReason.MISSING_INITIAL_CONCENTRATION
    )
    assert len(chloride_resolution.known_treatment_contributions) == 1
    audit_contribution = chloride_resolution.known_treatment_contributions[0]
    assert audit_contribution.treatment_index == 0
    assert audit_contribution.addition.ingredient is CALCIUM_CHLORIDE_DIHYDRATE
    assert audit_contribution.contribution.concentration.magnitude == pytest.approx(
        48.2286,
        abs=0.001,
    )

    chloride_contribution = next(
        item
        for item in result.applied_treatments[0].ion_contributions
        if item.ion is Ion.CHLORIDE
    )
    assert chloride_contribution.concentration.magnitude == pytest.approx(
        48.2286,
        abs=0.001,
    )


def test_multiple_additions_accumulate_overlapping_contributions() -> None:
    initial = _state(calcium=20.0, chloride=10.0, sulfate=0.0, sodium=0.0)

    result = apply_treatment_additions(
        initial,
        Q_(20, "liter"),
        (
            TreatmentAddition(GYPSUM, Q_(2, "gram")),
            TreatmentAddition(SODIUM_CHLORIDE, Q_(1, "gram")),
        ),
    )

    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(
        43.279,
        abs=0.001,
    )
    assert _mg_per_liter(result.final_state, Ion.SULFATE) == pytest.approx(
        55.7933,
        abs=0.001,
    )
    assert _mg_per_liter(result.final_state, Ion.SODIUM) == pytest.approx(
        19.6697,
        abs=0.001,
    )
    assert _mg_per_liter(result.final_state, Ion.CHLORIDE) == pytest.approx(
        40.3303,
        abs=0.001,
    )


def test_per_treatment_contributions_remain_auditable() -> None:
    result = apply_treatment_additions(
        _state(),
        Q_(5, "liter"),
        (
            TreatmentAddition(GYPSUM, Q_(1, "gram")),
            TreatmentAddition(SODIUM_CHLORIDE, Q_(1, "gram")),
        ),
    )

    assert len(result.applied_treatments) == 2
    assert result.applied_treatments[0].addition.ingredient is GYPSUM
    assert {item.ion for item in result.applied_treatments[0].ion_contributions} == {
        Ion.CALCIUM,
        Ion.SULFATE,
    }
    assert result.applied_treatments[1].addition.ingredient is SODIUM_CHLORIDE
    assert {item.ion for item in result.applied_treatments[1].ion_contributions} == {
        Ion.SODIUM,
        Ion.CHLORIDE,
    }


def test_known_initial_ion_has_resolved_audit_record() -> None:
    result = apply_treatment_additions(
        _state(calcium=50.0, chloride=0.0),
        Q_(10, "liter"),
        (
            TreatmentAddition(
                CALCIUM_CHLORIDE_DIHYDRATE,
                Q_(1, "gram"),
            ),
        ),
    )

    chloride_resolution = result.resolution_for(Ion.CHLORIDE)
    assert isinstance(chloride_resolution, ResolvedTreatmentIon)
    assert chloride_resolution.initial_concentration.concentration.magnitude == 0.0
    assert chloride_resolution.concentration.concentration.magnitude == pytest.approx(
        48.2286,
        abs=0.001,
    )
    assert len(chloride_resolution.treatment_contributions) == 1


def test_missing_unaffected_ion_has_explicit_unresolved_audit_record() -> None:
    result = apply_treatment_additions(
        _state(calcium=50.0),
        Q_(10, "liter"),
        (),
    )

    sulfate_resolution = result.resolution_for(Ion.SULFATE)
    assert isinstance(sulfate_resolution, UnresolvedTreatmentIon)
    assert (
        sulfate_resolution.reason
        is UnresolvedTreatmentIonReason.MISSING_INITIAL_CONCENTRATION
    )
    assert sulfate_resolution.known_treatment_contributions == ()


def test_per_ion_audit_links_multiple_contributions_to_treatment_indices() -> None:
    first = TreatmentAddition(CALCIUM_CHLORIDE_DIHYDRATE, Q_(1, "gram"))
    second = TreatmentAddition(SODIUM_CHLORIDE, Q_(1, "gram"))
    result = apply_treatment_additions(
        _state(chloride=10.0),
        Q_(10, "liter"),
        (first, second),
    )

    chloride_resolution = result.resolution_for(Ion.CHLORIDE)
    assert isinstance(chloride_resolution, ResolvedTreatmentIon)
    assert [
        contribution.treatment_index
        for contribution in chloride_resolution.treatment_contributions
    ] == [0, 1]
    assert [
        contribution.addition
        for contribution in chloride_resolution.treatment_contributions
    ] == [first, second]


def test_zero_additions_leave_chemical_state_unchanged() -> None:
    initial = _state(calcium=42.0, chloride=17.0)

    result = apply_treatment_additions(initial, Q_(12, "liter"), ())

    assert result.final_state == initial
    assert result.applied_treatments == ()


def test_equivalent_volume_units_produce_same_final_state() -> None:
    addition = TreatmentAddition(SODIUM_CHLORIDE, Q_(2, "gram"))

    liters = apply_treatment_additions(_state(), Q_(10, "liter"), (addition,))
    milliliters = apply_treatment_additions(
        _state(),
        Q_(10000, "milliliter"),
        (addition,),
    )

    assert liters.final_state == milliliters.final_state
    assert milliliters.water_volume.to("liter").magnitude == pytest.approx(10.0)
    assert isinstance(milliliters.water_volume.magnitude, float)


def test_decimal_addition_mass_is_supported() -> None:
    result = apply_treatment_additions(
        _state(calcium=0.0),
        Q_(10, "liter"),
        (
            TreatmentAddition(
                CALCIUM_CHLORIDE_DIHYDRATE,
                Q_(Decimal("1.5"), "gram"),
            ),
        ),
    )

    assert _mg_per_liter(result.final_state, Ion.CALCIUM) == pytest.approx(
        40.8938,
        abs=0.001,
    )


def test_negative_treatment_addition_is_rejected_at_domain_boundary() -> None:
    with pytest.raises(ValueError, match="mass cannot be negative"):
        TreatmentAddition(GYPSUM, Q_(-1, "gram"))


def test_non_mass_treatment_addition_is_rejected_at_domain_boundary() -> None:
    with pytest.raises(ValueError, match="convertible to mass"):
        TreatmentAddition(GYPSUM, Q_(1, "liter"))


@pytest.mark.parametrize("volume", [Q_(0, "liter"), Q_(-1, "liter")])
def test_non_positive_water_volume_is_rejected_even_without_additions(volume) -> None:
    with pytest.raises(ValueError, match="volume must be greater than zero"):
        apply_treatment_additions(_state(calcium=25.0), volume, ())


def test_non_volume_water_size_is_rejected() -> None:
    with pytest.raises(ValueError, match="volume must be convertible to volume"):
        apply_treatment_additions(_state(), Q_(20, "gram"), ())
