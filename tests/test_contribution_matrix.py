import pytest
from fermunits import Q_
from hypothesis import given
from hypothesis import strategies as st

from water_chemistry_engine.blending import BlendSource, blend_waters
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.contribution_matrix import (
    SourceContributionCellStatus,
    TreatmentContributionCellStatus,
    build_contribution_matrix,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    apply_treatment_additions,
)
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    GYPSUM,
    SODIUM_CHLORIDE,
)


def _state(**values: float) -> AqueousChemicalState:
    return AqueousChemicalState(
        concentrations=tuple(
            DerivedIonConcentration.mg_per_liter(Ion(ion_name), value)
            for ion_name, value in values.items()
        )
    )


def _mg_per_liter(value) -> float | None:
    if value is None:
        return None
    return float(value.to("milligram / liter").magnitude)


def test_matrix_combines_known_source_and_treatment_contributions() -> None:
    blend = blend_waters(
        (
            BlendSource("Source A", _state(calcium=40.0), Q_(10, "liter")),
            BlendSource("Source B", _state(calcium=60.0), Q_(10, "liter")),
        )
    )
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (TreatmentAddition(GYPSUM, Q_(1, "gram")),),
    )

    matrix = build_contribution_matrix(blend, treatment)
    calcium = matrix.row_for(Ion.CALCIUM)

    assert tuple(column.source_name for column in matrix.source_columns) == (
        "Source A",
        "Source B",
    )
    assert tuple(column.fraction for column in matrix.source_columns) == pytest.approx(
        (0.5, 0.5)
    )
    assert tuple(column.addition.ingredient for column in matrix.treatment_columns) == (
        GYPSUM,
    )
    assert tuple(cell.status for cell in calcium.source_contributions) == (
        SourceContributionCellStatus.KNOWN,
        SourceContributionCellStatus.KNOWN,
    )
    assert _mg_per_liter(
        calcium.source_contributions[0].weighted_contribution
    ) == pytest.approx(20.0)
    assert _mg_per_liter(
        calcium.source_contributions[1].weighted_contribution
    ) == pytest.approx(30.0)
    assert _mg_per_liter(calcium.known_source_contribution_sum) == pytest.approx(50.0)
    assert calcium.treatment_contributions[0].status is (
        TreatmentContributionCellStatus.CONTRIBUTES
    )
    assert _mg_per_liter(calcium.blend_concentration) == pytest.approx(50.0)
    assert _mg_per_liter(calcium.final_concentration) == pytest.approx(
        61.6395,
        abs=0.001,
    )
    assert calcium.blend_is_known
    assert calcium.final_is_known


def test_unknown_positive_source_keeps_partial_source_detail_without_total() -> None:
    blend = blend_waters(
        (
            BlendSource("Known", _state(calcium=50.0), Q_(1, "liter")),
            BlendSource("Unknown", _state(), Q_(1, "liter")),
        )
    )
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (TreatmentAddition(GYPSUM, Q_(1, "gram")),),
    )

    calcium = build_contribution_matrix(blend, treatment).row_for(Ion.CALCIUM)

    assert calcium.source_contributions[0].status is SourceContributionCellStatus.KNOWN
    assert calcium.source_contributions[1].status is (
        SourceContributionCellStatus.SOURCE_CONCENTRATION_UNKNOWN
    )
    assert _mg_per_liter(calcium.known_source_contribution_sum) == pytest.approx(25.0)
    assert calcium.blend_concentration is None
    assert not calcium.blend_is_known
    assert _mg_per_liter(calcium.known_treatment_contribution_sum) == pytest.approx(
        116.395,
        abs=0.001,
    )
    assert calcium.final_concentration is None
    assert not calcium.final_is_known


def test_zero_volume_unknown_source_is_marked_as_no_chemical_effect() -> None:
    blend = blend_waters(
        (
            BlendSource("Known", _state(calcium=50.0), Q_(10, "liter")),
            BlendSource("Unused", _state(), Q_(0, "liter")),
        )
    )
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    calcium = build_contribution_matrix(blend, treatment).row_for(Ion.CALCIUM)

    assert calcium.source_contributions[1].status is (
        SourceContributionCellStatus.ZERO_VOLUME
    )
    assert calcium.source_contributions[1].source_concentration is None
    assert calcium.source_contributions[1].weighted_contribution is None
    assert _mg_per_liter(calcium.blend_concentration) == pytest.approx(50.0)
    assert _mg_per_liter(calcium.final_concentration) == pytest.approx(50.0)


def test_noncontributing_treatment_is_not_presented_as_unknown() -> None:
    blend = blend_waters(
        (BlendSource("Source", _state(calcium=50.0), Q_(10, "liter")),)
    )
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (TreatmentAddition(SODIUM_CHLORIDE, Q_(1, "gram")),),
    )

    calcium = build_contribution_matrix(blend, treatment).row_for(Ion.CALCIUM)

    assert calcium.treatment_contributions[0].status is (
        TreatmentContributionCellStatus.DOES_NOT_CONTRIBUTE
    )
    assert calcium.treatment_contributions[0].contribution is None
    assert _mg_per_liter(calcium.known_treatment_contribution_sum) == pytest.approx(0.0)
    assert _mg_per_liter(calcium.final_concentration) == pytest.approx(50.0)


def test_multiple_treatment_columns_preserve_requested_order() -> None:
    blend = blend_waters(
        (
            BlendSource(
                "Source",
                _state(calcium=50.0, chloride=20.0),
                Q_(10, "liter"),
            ),
        )
    )
    treatment = apply_treatment_additions(
        blend.state,
        blend.total_volume,
        (
            TreatmentAddition(GYPSUM, Q_(1, "gram")),
            TreatmentAddition(CALCIUM_CHLORIDE_DIHYDRATE, Q_(2, "gram")),
        ),
    )

    matrix = build_contribution_matrix(blend, treatment)
    calcium = matrix.row_for(Ion.CALCIUM)
    chloride = matrix.row_for(Ion.CHLORIDE)

    assert tuple(column.addition.ingredient for column in matrix.treatment_columns) == (
        GYPSUM,
        CALCIUM_CHLORIDE_DIHYDRATE,
    )
    assert tuple(cell.treatment_index for cell in calcium.treatment_contributions) == (
        0,
        1,
    )
    assert tuple(cell.status for cell in calcium.treatment_contributions) == (
        TreatmentContributionCellStatus.CONTRIBUTES,
        TreatmentContributionCellStatus.CONTRIBUTES,
    )
    assert tuple(cell.status for cell in chloride.treatment_contributions) == (
        TreatmentContributionCellStatus.DOES_NOT_CONTRIBUTE,
        TreatmentContributionCellStatus.CONTRIBUTES,
    )


def test_matrix_rows_follow_canonical_ion_order() -> None:
    blend = blend_waters((BlendSource("Source", _state(calcium=50.0), Q_(1, "liter")),))
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    matrix = build_contribution_matrix(blend, treatment)

    assert tuple(row.ion for row in matrix.rows) == tuple(Ion)
    assert matrix.row_for(Ion.SULFATE) is matrix.rows[5]


def test_matrix_requires_treatment_to_start_from_supplied_blend() -> None:
    blend = blend_waters((BlendSource("Source", _state(calcium=50.0), Q_(1, "liter")),))
    unrelated_treatment = apply_treatment_additions(
        _state(calcium=60.0),
        Q_(1, "liter"),
        (),
    )

    with pytest.raises(ValueError, match="initial state must match"):
        build_contribution_matrix(blend, unrelated_treatment)


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
    min_size=1,
    max_size=6,
)


@given(source_values=_SOURCE_VALUE_SETS)
def test_known_source_contribution_sum_matches_resolved_blend(
    source_values: list[tuple[float, float]],
) -> None:
    blend = blend_waters(
        tuple(
            BlendSource(
                f"Source {index}",
                _state(calcium=concentration),
                Q_(volume, "liter"),
            )
            for index, (concentration, volume) in enumerate(source_values)
        )
    )
    treatment = apply_treatment_additions(blend.state, blend.total_volume, ())

    calcium = build_contribution_matrix(blend, treatment).row_for(Ion.CALCIUM)

    assert calcium.blend_concentration is not None
    assert _mg_per_liter(calcium.known_source_contribution_sum) == pytest.approx(
        _mg_per_liter(calcium.blend_concentration),
        abs=1e-9,
    )
