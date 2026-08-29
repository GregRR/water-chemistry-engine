from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_
from hypothesis import given
from hypothesis import strategies as st

from water_chemistry_engine.blending import (
    BlendSource,
    FractionalBlendSource,
    ResolvedBlendIon,
    UnresolvedBlendIon,
    UnresolvedBlendIonReason,
    blend_waters,
    blend_waters_by_fractions,
)
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    apply_treatment_additions,
)
from water_chemistry_engine.treatment_ingredients import GYPSUM


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


_CONSERVATIVE_BLEND_IONS = (
    Ion.CALCIUM,
    Ion.MAGNESIUM,
    Ion.SODIUM,
    Ion.POTASSIUM,
    Ion.CHLORIDE,
    Ion.SULFATE,
)
_CONCENTRATIONS = st.floats(
    min_value=0.0,
    max_value=1000.0,
    allow_nan=False,
    allow_infinity=False,
)
_POSITIVE_VOLUMES = st.floats(
    min_value=0.001,
    max_value=1000.0,
    allow_nan=False,
    allow_infinity=False,
)
_SOURCE_VALUE_SETS = st.lists(
    st.tuples(_CONCENTRATIONS, _POSITIVE_VOLUMES),
    min_size=2,
    max_size=6,
)


def _single_ion_state(ion: Ion, value: float) -> AqueousChemicalState:
    return AqueousChemicalState(
        concentrations=(DerivedIonConcentration.mg_per_liter(ion, value),)
    )


@given(
    ion=st.sampled_from(_CONSERVATIVE_BLEND_IONS),
    source_values=_SOURCE_VALUE_SETS,
)
def test_conservative_blend_stays_within_source_extrema(
    ion: Ion,
    source_values: list[tuple[float, float]],
) -> None:
    sources = tuple(
        BlendSource(
            f"Source {index}",
            _single_ion_state(ion, concentration),
            Q_(volume, "liter"),
        )
        for index, (concentration, volume) in enumerate(source_values)
    )

    result = blend_waters(sources)
    blended = _mg_per_liter(result.state, ion)
    assert blended is not None

    concentrations = [concentration for concentration, _ in source_values]
    assert min(concentrations) - 1e-9 <= blended <= max(concentrations) + 1e-9


@given(source_values=_SOURCE_VALUE_SETS)
def test_normalized_blend_fractions_sum_to_one(
    source_values: list[tuple[float, float]],
) -> None:
    sources = tuple(
        BlendSource(
            f"Source {index}",
            _single_ion_state(Ion.CALCIUM, concentration),
            Q_(volume, "liter"),
        )
        for index, (concentration, volume) in enumerate(source_values)
    )

    result = blend_waters(sources)

    assert sum(source.fraction for source in result.sources) == pytest.approx(1.0)


@given(
    ion=st.sampled_from(_CONSERVATIVE_BLEND_IONS),
    source_values=st.lists(
        st.tuples(_CONCENTRATIONS, _POSITIVE_VOLUMES),
        min_size=3,
        max_size=6,
    ),
)
def test_reordering_three_or_more_sources_preserves_blend_chemistry(
    ion: Ion,
    source_values: list[tuple[float, float]],
) -> None:
    sources = tuple(
        BlendSource(
            f"Source {index}",
            _single_ion_state(ion, concentration),
            Q_(volume, "liter"),
        )
        for index, (concentration, volume) in enumerate(source_values)
    )

    forward = blend_waters(sources)
    reverse = blend_waters(tuple(reversed(sources)))

    assert _mg_per_liter(forward.state, ion) == pytest.approx(
        _mg_per_liter(reverse.state, ion)
    )
    assert forward.total_volume == reverse.total_volume


def test_two_source_volume_blend_uses_volume_weighted_concentrations() -> None:
    result = blend_waters(
        (
            BlendSource(
                "Tap",
                _state(calcium=60.0, magnesium=12.0),
                Q_(3, "liter"),
            ),
            BlendSource(
                "RO",
                _state(calcium=0.0, magnesium=0.0),
                Q_(1, "liter"),
            ),
        )
    )

    assert result.total_volume.to("liter").magnitude == pytest.approx(4.0)
    assert result.sources[0].fraction == pytest.approx(0.75)
    assert result.sources[1].fraction == pytest.approx(0.25)
    assert _mg_per_liter(result.state, Ion.CALCIUM) == pytest.approx(45.0)
    assert _mg_per_liter(result.state, Ion.MAGNESIUM) == pytest.approx(9.0)


def test_three_source_blend_produces_baseline_before_treatment() -> None:
    blend = blend_waters(
        (
            BlendSource(
                "Tap",
                _state(calcium=80.0, chloride=20.0, sulfate=30.0),
                Q_(5, "gallon"),
            ),
            BlendSource(
                "Sparkletts",
                _state(calcium=30.0, chloride=10.0, sulfate=5.0),
                Q_(2, "gallon"),
            ),
            BlendSource(
                "Distilled",
                _state(calcium=0.0, chloride=0.0, sulfate=0.0),
                Q_(3, "gallon"),
            ),
        )
    )

    assert _mg_per_liter(blend.state, Ion.CALCIUM) == pytest.approx(46.0)
    assert _mg_per_liter(blend.state, Ion.CHLORIDE) == pytest.approx(12.0)
    assert _mg_per_liter(blend.state, Ion.SULFATE) == pytest.approx(16.0)

    treated = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (TreatmentAddition(GYPSUM, Q_(2, "gram")),),
    )

    assert treated.initial_state == blend.state
    treated_calcium = _mg_per_liter(treated.final_state, Ion.CALCIUM)
    treated_sulfate = _mg_per_liter(treated.final_state, Ion.SULFATE)
    assert treated_calcium is not None
    assert treated_sulfate is not None
    assert treated_calcium > 46.0
    assert treated_sulfate > 16.0


def test_missing_positive_volume_source_concentration_keeps_blend_unknown() -> None:
    result = blend_waters(
        (
            BlendSource("Known", _state(calcium=50.0), Q_(1, "liter")),
            BlendSource("Unknown", _state(), Q_(1, "liter")),
        )
    )

    assert result.state.concentration_for(Ion.CALCIUM) is None

    resolution = result.resolution_for(Ion.CALCIUM)
    assert isinstance(resolution, UnresolvedBlendIon)
    assert resolution.reason is UnresolvedBlendIonReason.MISSING_SOURCE_CONCENTRATION
    assert resolution.missing_source_indices == (1,)
    assert resolution.missing_source_names == ("Unknown",)
    assert len(resolution.known_source_contributions) == 1
    assert resolution.known_source_contributions[
        0
    ].weighted_contribution.magnitude == pytest.approx(25.0)


def test_zero_volume_source_does_not_propagate_unknown_concentration() -> None:
    result = blend_waters(
        (
            BlendSource("Tap", _state(calcium=50.0), Q_(4, "liter")),
            BlendSource("Unused", _state(), Q_(0, "liter")),
        )
    )

    assert _mg_per_liter(result.state, Ion.CALCIUM) == pytest.approx(50.0)
    resolution = result.resolution_for(Ion.CALCIUM)
    assert isinstance(resolution, ResolvedBlendIon)
    assert len(resolution.source_contributions) == 1
    assert resolution.source_contributions[0].source_name == "Tap"


def test_explicit_zero_is_a_known_source_concentration() -> None:
    result = blend_waters(
        (
            BlendSource("Tap", _state(sodium=40.0), Q_(1, "liter")),
            BlendSource("Distilled", _state(sodium=0.0), Q_(1, "liter")),
        )
    )

    assert _mg_per_liter(result.state, Ion.SODIUM) == pytest.approx(20.0)
    resolution = result.resolution_for(Ion.SODIUM)
    assert isinstance(resolution, ResolvedBlendIon)
    assert len(resolution.source_contributions) == 2


def test_source_contributions_sum_to_resolved_blend_concentration() -> None:
    result = blend_waters(
        (
            BlendSource("A", _state(chloride=15.0), Q_(2, "liter")),
            BlendSource("B", _state(chloride=45.0), Q_(3, "liter")),
        )
    )

    resolution = result.resolution_for(Ion.CHLORIDE)
    assert isinstance(resolution, ResolvedBlendIon)
    contribution_sum = sum(
        float(item.weighted_contribution.magnitude)
        for item in resolution.source_contributions
    )
    assert contribution_sum == pytest.approx(33.0)
    assert _mg_per_liter(result.state, Ion.CHLORIDE) == pytest.approx(contribution_sum)


def test_reordering_sources_does_not_change_blended_state() -> None:
    first = BlendSource(
        "A",
        _state(calcium=20.0, sulfate=40.0),
        Q_(1, "liter"),
    )
    second = BlendSource(
        "B",
        _state(calcium=80.0, sulfate=10.0),
        Q_(3, "liter"),
    )

    forward = blend_waters((first, second))
    reverse = blend_waters((second, first))

    assert forward.state == reverse.state


def test_equivalent_volume_units_produce_equivalent_blends() -> None:
    state_a = _state(calcium=20.0)
    state_b = _state(calcium=80.0)

    liters = blend_waters(
        (
            BlendSource("A", state_a, Q_(1, "liter")),
            BlendSource("B", state_b, Q_(3, "liter")),
        )
    )
    milliliters = blend_waters(
        (
            BlendSource("A", state_a, Q_(1000, "milliliter")),
            BlendSource("B", state_b, Q_(3000, "milliliter")),
        )
    )

    assert liters.state == milliliters.state
    assert liters.total_volume == milliliters.total_volume


def test_fraction_blend_matches_equivalent_volume_blend() -> None:
    state_a = _state(calcium=10.0, sulfate=100.0)
    state_b = _state(calcium=70.0, sulfate=20.0)

    by_volume = blend_waters(
        (
            BlendSource("A", state_a, Q_(2, "liter")),
            BlendSource("B", state_b, Q_(3, "liter")),
        )
    )
    by_fraction = blend_waters_by_fractions(
        (
            FractionalBlendSource("A", state_a, Fraction(2, 5)),
            FractionalBlendSource("B", state_b, Decimal("0.6")),
        ),
        total_volume=Q_(5, "liter"),
    )

    assert by_fraction.state == by_volume.state
    assert by_fraction.total_volume == by_volume.total_volume
    assert by_fraction.sources[0].volume.magnitude == pytest.approx(2.0)
    assert by_fraction.sources[1].volume.magnitude == pytest.approx(3.0)


def test_zero_fraction_source_does_not_propagate_unknown_concentration() -> None:
    result = blend_waters_by_fractions(
        (
            FractionalBlendSource("Tap", _state(calcium=55.0), 1),
            FractionalBlendSource("Unused", _state(), 0),
        ),
        total_volume=Q_(20, "liter"),
    )

    assert _mg_per_liter(result.state, Ion.CALCIUM) == pytest.approx(55.0)


def test_single_source_blend_is_identity_for_known_ions() -> None:
    source_state = _state(calcium=42.0, magnesium=7.0)

    result = blend_waters((BlendSource("Only", source_state, Q_(8, "liter")),))

    result_calcium = result.state.concentration_for(Ion.CALCIUM)
    result_magnesium = result.state.concentration_for(Ion.MAGNESIUM)
    assert result_calcium == source_state.concentration_for(Ion.CALCIUM)
    assert result_magnesium == source_state.concentration_for(Ion.MAGNESIUM)


def test_empty_blend_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one source"):
        blend_waters(())


def test_all_zero_source_volumes_are_rejected() -> None:
    with pytest.raises(ValueError, match="total volume must be greater than zero"):
        blend_waters(
            (
                BlendSource("A", _state(calcium=10.0), Q_(0, "liter")),
                BlendSource("B", _state(calcium=20.0), Q_(0, "liter")),
            )
        )


def test_negative_source_volume_is_rejected() -> None:
    with pytest.raises(ValueError, match="volume cannot be negative"):
        BlendSource("A", _state(), Q_(-1, "liter"))


def test_non_volume_source_amount_is_rejected() -> None:
    with pytest.raises(ValueError, match="convertible to volume"):
        BlendSource("A", _state(), Q_(1, "gram"))


def test_fraction_sources_must_sum_to_one() -> None:
    with pytest.raises(ValueError, match="fractions must sum to one"):
        blend_waters_by_fractions(
            (
                FractionalBlendSource("A", _state(), 0.4),
                FractionalBlendSource("B", _state(), 0.5),
            ),
            total_volume=Q_(10, "liter"),
        )


def test_negative_fraction_is_rejected() -> None:
    with pytest.raises(ValueError, match="fraction cannot be negative"):
        FractionalBlendSource("A", _state(), -0.1)


def test_fraction_greater_than_one_is_rejected() -> None:
    with pytest.raises(ValueError, match="fraction cannot be greater than one"):
        FractionalBlendSource("A", _state(), 1.1)


def test_fraction_blend_requires_positive_total_volume() -> None:
    with pytest.raises(ValueError, match="total volume must be greater than zero"):
        blend_waters_by_fractions(
            (FractionalBlendSource("A", _state(), 1),),
            total_volume=Q_(0, "liter"),
        )
