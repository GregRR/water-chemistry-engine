from dataclasses import replace

import pytest
from fermunits import Q_

from water_chemistry_engine.alkalinity_balance import (
    CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL,
    AlkalinityBalanceResult,
    AlkalinityModelLimitation,
    ResolvedSourceAlkalinity,
    SourceAlkalinityResolutionMethod,
    UnresolvedSourceAlkalinity,
    UnresolvedSourceAlkalinityReason,
)
from water_chemistry_engine.concentrations import IonConcentration
from water_chemistry_engine.contribution_matrix import (
    SourceContributionCellStatus,
    TreatmentContributionCellStatus,
    build_contribution_matrix,
)
from water_chemistry_engine.forward_calculator import (
    ForwardWaterSource,
    calculate_forward_water,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_properties import (
    Alkalinity,
    AlkalinityAnalyticalContext,
    AlkalinityResultIdentity,
    SampleFiltrationState,
)
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.target_comparison import (
    TargetAlkalinityComparisonStatus,
    TargetProfileComparisonStatus,
    compare_state_to_target,
)
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    apply_treatment_additions,
)
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    GYPSUM,
    SODIUM_BICARBONATE,
)

REPORTED_ONLY = SourceResolutionPolicy(allow_exact_range_midpoints=False)
ALLOW_MIDPOINTS = SourceResolutionPolicy(allow_exact_range_midpoints=True)


def _source(
    name: str,
    alkalinity: Alkalinity | None,
    *,
    bicarbonate: float | None = None,
) -> SourceWaterProfile:
    concentrations = (
        ()
        if bicarbonate is None
        else (IonConcentration.mg_per_liter(Ion.BICARBONATE, bicarbonate),)
    )
    return SourceWaterProfile(
        name=name,
        concentrations=concentrations,
        alkalinity=alkalinity,
    )


def test_matrix_rejects_alkalinity_from_a_different_blend() -> None:
    # Ion states, source labels and volumes can match even when the reports
    # differ in alkalinity. Only the source report carries that measurement.
    low, high = (
        calculate_forward_water(
            (
                ForwardWaterSource(
                    _source("Well", Alkalinity.mg_per_liter_as_caco3(value)), Q_(1, "L")
                ),
            ),
            source_resolution_policy=REPORTED_ONLY,
        )
        for value in (10, 100)
    )
    assert low.blend_result == high.blend_result
    linked = build_contribution_matrix(
        low.blend_result, low.treatment_result, low.alkalinity_balance
    )
    assert linked.alkalinity_row.final_alkalinity == Q_(10, "mg/L")
    with pytest.raises(ValueError, match="Alkalinity balance must come from"):
        build_contribution_matrix(
            low.blend_result, high.treatment_result, high.alkalinity_balance
        )


def test_matrix_rejects_alkalinity_from_a_different_treatment() -> None:
    result = calculate_forward_water(
        (
            ForwardWaterSource(
                _source("Well", Alkalinity.mg_per_liter_as_caco3(10)), Q_(1, "L")
            ),
        ),
        source_resolution_policy=REPORTED_ONLY,
    )
    treated = apply_treatment_additions(
        result.blend_state,
        Q_(1, "L"),
        (TreatmentAddition(SODIUM_BICARBONATE, Q_(1, "g")),),
    )
    with pytest.raises(ValueError, match="Alkalinity balance must come from"):
        build_contribution_matrix(
            result.blend_result, treated, result.alkalinity_balance
        )

    balance = result.alkalinity_balance
    unlinked = AlkalinityBalanceResult(
        balance.source_resolutions, balance.blend, balance.final
    )
    with pytest.raises(ValueError, match="Alkalinity balance must come from"):
        build_contribution_matrix(
            result.blend_result, result.treatment_result, unlinked
        )


def test_exact_source_alkalinity_resolves_without_deriving_bicarbonate() -> None:
    source = _source(
        "Reported source",
        Alkalinity.mg_per_liter_as_caco3(108.0),
        bicarbonate=125.0,
    )

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
    )

    resolution = result.source_results[0].resolution.alkalinity_resolution
    assert isinstance(resolution, ResolvedSourceAlkalinity)
    assert resolution.method is SourceAlkalinityResolutionMethod.REPORTED_VALUE
    assert resolution.alkalinity.concentration.magnitude == pytest.approx(108.0)
    assert result.blended_alkalinity is not None
    assert result.blended_alkalinity.concentration.magnitude == pytest.approx(108.0)
    assert result.final_alkalinity is not None
    assert result.final_alkalinity.concentration.magnitude == pytest.approx(108.0)
    assert result.final_state.concentration_for(Ion.BICARBONATE).magnitude == 125.0


def test_explicit_total_alkalinity_identity_resolves_and_is_preserved() -> None:
    analytical_context = AlkalinityAnalyticalContext(
        result_identity=AlkalinityResultIdentity.TOTAL_ALKALINITY,
        original_analyte_label="Alkalinity, Total",
    )
    source = _source(
        "Reported source",
        Alkalinity.mg_per_liter_as_caco3(
            108.0,
            analytical_context=analytical_context,
        ),
    )

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
    )

    resolution = result.source_results[0].resolution.alkalinity_resolution
    assert isinstance(resolution, ResolvedSourceAlkalinity)
    assert resolution.source_result.analytical_context is analytical_context
    assert result.final_alkalinity is not None


@pytest.mark.parametrize("value", [108.0, -12.0])
def test_explicit_anc_is_preserved_but_not_used_as_total_alkalinity(
    value: float,
) -> None:
    analytical_context = AlkalinityAnalyticalContext(
        result_identity=AlkalinityResultIdentity.ACID_NEUTRALIZING_CAPACITY,
        sample_filtration_state=SampleFiltrationState.UNFILTERED,
    )
    source = _source(
        "Reported ANC source",
        Alkalinity.mg_per_liter_as_caco3(
            value,
            analytical_context=analytical_context,
        ),
    )

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
    )

    resolution = result.source_results[0].resolution.alkalinity_resolution
    assert isinstance(resolution, UnresolvedSourceAlkalinity)
    assert resolution.source_result is not None
    assert resolution.source_result.value == Q_(value, "mg/L")
    assert resolution.source_result.analytical_context is analytical_context
    assert resolution.reason is (
        UnresolvedSourceAlkalinityReason.ACID_NEUTRALIZING_CAPACITY_UNSUPPORTED
    )
    assert result.final_alkalinity is None


def test_source_alkalinity_range_requires_explicit_midpoint_policy() -> None:
    source = _source(
        "Ranged source",
        Alkalinity.mg_per_liter_as_caco3_range(80.0, 120.0),
    )

    unresolved = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
    )
    resolution = unresolved.source_results[0].resolution.alkalinity_resolution
    assert isinstance(resolution, UnresolvedSourceAlkalinity)
    assert (
        resolution.reason
        is UnresolvedSourceAlkalinityReason.EXACT_RANGE_MIDPOINT_NOT_PERMITTED
    )
    assert unresolved.final_alkalinity is None

    resolved = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=ALLOW_MIDPOINTS,
    )
    midpoint = resolved.source_results[0].resolution.alkalinity_resolution
    assert isinstance(midpoint, ResolvedSourceAlkalinity)
    assert (
        midpoint.method is SourceAlkalinityResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT
    )
    assert resolved.final_alkalinity is not None
    assert resolved.final_alkalinity.concentration.magnitude == pytest.approx(100.0)


@pytest.mark.parametrize(
    ("alkalinity", "reason"),
    (
        (
            Alkalinity.mg_per_liter_as_caco3_lower_bound(80.0),
            UnresolvedSourceAlkalinityReason.LOWER_BOUND,
        ),
        (
            Alkalinity.mg_per_liter_as_caco3_upper_bound(120.0),
            UnresolvedSourceAlkalinityReason.UPPER_BOUND,
        ),
    ),
)
def test_source_alkalinity_bound_remains_unresolved(
    alkalinity: Alkalinity,
    reason: UnresolvedSourceAlkalinityReason,
) -> None:
    result = calculate_forward_water(
        (ForwardWaterSource(_source("Bounded", alkalinity), Q_(10, "liter")),),
        source_resolution_policy=ALLOW_MIDPOINTS,
    )

    resolution = result.source_results[0].resolution.alkalinity_resolution
    assert isinstance(resolution, UnresolvedSourceAlkalinity)
    assert resolution.reason is reason
    assert result.blended_alkalinity is None
    assert result.final_alkalinity is None


def test_blend_is_volume_weighted_and_zero_volume_unknown_is_ignored() -> None:
    low = _source("Low", Alkalinity.mg_per_liter_as_caco3(40.0))
    high = _source("High", Alkalinity.mg_per_liter_as_caco3(100.0))
    unknown = _source("Unknown", None)

    result = calculate_forward_water(
        (
            ForwardWaterSource(low, Q_(1, "liter")),
            ForwardWaterSource(high, Q_(3, "liter")),
            ForwardWaterSource(unknown, Q_(0, "liter")),
        ),
        source_resolution_policy=REPORTED_ONLY,
    )

    assert result.blended_alkalinity is not None
    assert result.blended_alkalinity.concentration.magnitude == pytest.approx(85.0)
    assert len(result.alkalinity_balance.blend.source_contributions) == 2
    assert result.alkalinity_balance.blend.missing_source_indices == ()


def test_positive_volume_unknown_propagates_but_known_contributions_remain() -> None:
    known = _source("Known", Alkalinity.mg_per_liter_as_caco3(80.0))
    unknown = _source("Unknown", None)

    result = calculate_forward_water(
        (
            ForwardWaterSource(known, Q_(5, "liter")),
            ForwardWaterSource(unknown, Q_(5, "liter")),
        ),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(SODIUM_BICARBONATE, Q_(1, "gram")),),
    )

    assert result.blended_alkalinity is None
    assert result.final_alkalinity is None
    assert result.alkalinity_balance.blend.missing_source_names == ("Unknown",)
    assert len(result.alkalinity_balance.blend.source_contributions) == 1
    assert len(result.alkalinity_balance.final.treatment_contributions) == 1


def test_alkalinity_matrix_distinguishes_zero_unknown_and_known_sources() -> None:
    zero_volume = _source("Zero volume", None)
    unknown = _source("Unknown", None)
    known = _source("Known", Alkalinity.mg_per_liter_as_caco3(80.0))

    result = calculate_forward_water(
        (
            ForwardWaterSource(zero_volume, Q_(0, "liter")),
            ForwardWaterSource(unknown, Q_(5, "liter")),
            ForwardWaterSource(known, Q_(5, "liter")),
        ),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(SODIUM_BICARBONATE, Q_(1, "gram")),),
    )

    row = result.contribution_matrix.alkalinity_row
    assert row is not None
    assert tuple(cell.status for cell in row.source_contributions) == (
        SourceContributionCellStatus.ZERO_VOLUME,
        SourceContributionCellStatus.SOURCE_CONCENTRATION_UNKNOWN,
        SourceContributionCellStatus.KNOWN,
    )
    assert row.source_contributions[0].weighted_contribution is None
    assert row.source_contributions[1].weighted_contribution is None
    assert row.source_contributions[2].weighted_contribution.magnitude == 40.0
    assert row.blend_alkalinity is None
    assert row.final_alkalinity is None
    assert len(row.treatment_contributions) == 1
    assert (
        row.treatment_contributions[0].status
        is TreatmentContributionCellStatus.CONTRIBUTES
    )
    assert row.treatment_contributions[0].contribution is not None


def test_one_gram_per_liter_sodium_bicarbonate_adds_expected_alkalinity() -> None:
    source = _source("Zero", Alkalinity.mg_per_liter_as_caco3(0.0))

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(1, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(
            TreatmentAddition(SODIUM_BICARBONATE, Q_(1, "gram")),
            TreatmentAddition(GYPSUM, Q_(1, "gram")),
        ),
    )

    assert result.final_alkalinity is not None
    assert result.final_alkalinity.model == CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL
    assert result.alkalinity_balance.limitations == (
        AlkalinityModelLimitation.COMPLETE_DISSOLUTION_ASSUMED,
        AlkalinityModelLimitation.PRECIPITATION_DISSOLUTION_NOT_CALCULATED,
        AlkalinityModelLimitation.UNMODELED_REACTIONS_NOT_CALCULATED,
        AlkalinityModelLimitation.CARBONATE_SPECIATION_NOT_CALCULATED,
        AlkalinityModelLimitation.WORKING_WATER_PH_NOT_CALCULATED,
        AlkalinityModelLimitation.LABORATORY_TITRATION_NOT_SIMULATED,
    )
    assert result.final_alkalinity.concentration.magnitude == pytest.approx(
        595.7144,
        abs=0.0001,
    )
    contributions = result.alkalinity_balance.final.treatment_contributions
    assert len(contributions) == 1
    assert contributions[0].addition.ingredient is SODIUM_BICARBONATE
    assert contributions[0].equivalents_per_mole == 1.0
    sodium_contribution = next(
        contribution
        for contribution in result.treatment_result.applied_treatments[
            0
        ].ion_contributions
        if contribution.ion is Ion.SODIUM
    )
    assert sodium_contribution.concentration.magnitude == pytest.approx(
        22.98976928 / 84.00576928 * 1000.0
    )
    row = result.contribution_matrix.alkalinity_row
    assert row is not None
    assert row.calculation_model == CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL
    assert row.blend_alkalinity.magnitude == 0.0
    assert row.final_alkalinity.magnitude == pytest.approx(595.7144, abs=0.0001)
    assert row.known_treatment_contribution_sum.magnitude == pytest.approx(
        595.7144,
        abs=0.0001,
    )


def test_final_alkalinity_is_compared_with_exact_target() -> None:
    source = _source("Source", Alkalinity.mg_per_liter_as_caco3(75.0))
    target = TargetWaterProfile(
        name="Alkalinity target",
        concentrations=(),
        alkalinity=Alkalinity.mg_per_liter_as_caco3(80.0),
    )

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        target_profile=target,
    )

    comparison = result.final_target_comparison
    assert comparison is not None
    assert comparison.alkalinity_comparison is not None
    assert (
        comparison.alkalinity_comparison.status
        is TargetAlkalinityComparisonStatus.BELOW_TARGET
    )
    assert comparison.alkalinity_comparison.deviation.magnitude == pytest.approx(-5.0)
    assert comparison.status is TargetProfileComparisonStatus.NOT_SATISFIED


@pytest.mark.parametrize(
    ("source_mg_per_liter", "expected_status", "expected_deviation"),
    (
        (70, TargetAlkalinityComparisonStatus.BELOW_TARGET, -5),
        (75, TargetAlkalinityComparisonStatus.WITHIN_TARGET, 0),
        (90, TargetAlkalinityComparisonStatus.ABOVE_TARGET, 5),
    ),
)
def test_alkalinity_comparison_after_converting_modeled_result_to_grams_per_liter(
    source_mg_per_liter: int,
    expected_status: TargetAlkalinityComparisonStatus,
    expected_deviation: int,
) -> None:
    source = _source("Source", Alkalinity.mg_per_liter_as_caco3(source_mg_per_liter))
    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(1, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
    )
    actual = result.final_alkalinity
    assert actual is not None
    actual.concentration.ito("gram / liter")
    target = TargetWaterProfile(
        "Target", (), alkalinity=Alkalinity.mg_per_liter_as_caco3_range(75, 85)
    )

    comparison = compare_state_to_target(
        result.final_state, target, actual_alkalinity=actual
    )

    criterion = comparison.alkalinity_comparison
    assert criterion is not None and criterion.deviation is not None
    assert criterion.status is expected_status
    assert criterion.deviation.units == Q_(1, "mg/L").units
    assert criterion.deviation.magnitude == pytest.approx(expected_deviation)
    assert comparison.status is (
        TargetProfileComparisonStatus.SATISFIED
        if expected_deviation == 0
        else TargetProfileComparisonStatus.NOT_SATISFIED
    )


def test_final_alkalinity_is_compared_with_range_target() -> None:
    source = _source("Source", Alkalinity.mg_per_liter_as_caco3(80.0))
    target = TargetWaterProfile(
        name="Alkalinity range",
        concentrations=(),
        alkalinity=Alkalinity.mg_per_liter_as_caco3_range(75.0, 85.0),
    )

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        target_profile=target,
    )

    comparison = result.final_target_comparison
    assert comparison is not None
    assert comparison.alkalinity_comparison is not None
    assert (
        comparison.alkalinity_comparison.status
        is TargetAlkalinityComparisonStatus.WITHIN_TARGET
    )
    assert comparison.alkalinity_comparison.deviation.magnitude == 0.0
    assert comparison.status is TargetProfileComparisonStatus.SATISFIED


@pytest.mark.parametrize(
    ("source_value", "expected_status", "expected_deviation"),
    (
        (90.0, TargetAlkalinityComparisonStatus.ABOVE_TARGET, 5.0),
        (
            85.0 + 0.5e-9,
            TargetAlkalinityComparisonStatus.WITHIN_TARGET,
            0.0,
        ),
    ),
)
def test_alkalinity_range_upper_boundary_and_numerical_tolerance(
    source_value: float,
    expected_status: TargetAlkalinityComparisonStatus,
    expected_deviation: float,
) -> None:
    source = _source(
        "Source",
        Alkalinity.mg_per_liter_as_caco3(source_value),
    )
    target = TargetWaterProfile(
        name="Alkalinity range",
        concentrations=(),
        alkalinity=Alkalinity.mg_per_liter_as_caco3_range(75.0, 85.0),
    )

    result = calculate_forward_water(
        (ForwardWaterSource(source, Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        target_profile=target,
    )

    comparison = result.final_target_comparison
    assert comparison is not None
    assert comparison.alkalinity_comparison is not None
    assert comparison.alkalinity_comparison.status is expected_status
    assert comparison.alkalinity_comparison.deviation.magnitude == pytest.approx(
        expected_deviation
    )


@pytest.mark.parametrize(
    ("source_value", "target", "expected_status", "expected_deviation"),
    (
        (
            75.0,
            Alkalinity.mg_per_liter_as_caco3_lower_bound(80.0),
            TargetAlkalinityComparisonStatus.BELOW_TARGET,
            -5.0,
        ),
        (
            90.0,
            Alkalinity.mg_per_liter_as_caco3_lower_bound(80.0),
            TargetAlkalinityComparisonStatus.WITHIN_TARGET,
            0.0,
        ),
        (
            85.0,
            Alkalinity.mg_per_liter_as_caco3_upper_bound(80.0),
            TargetAlkalinityComparisonStatus.ABOVE_TARGET,
            5.0,
        ),
    ),
)
def test_one_sided_alkalinity_target_comparison(
    source_value: float,
    target: Alkalinity,
    expected_status: TargetAlkalinityComparisonStatus,
    expected_deviation: float,
) -> None:
    result = calculate_forward_water(
        (
            ForwardWaterSource(
                _source(
                    "Source",
                    Alkalinity.mg_per_liter_as_caco3(source_value),
                ),
                Q_(10, "liter"),
            ),
        ),
        source_resolution_policy=REPORTED_ONLY,
        target_profile=TargetWaterProfile(
            name="Bounded alkalinity target",
            concentrations=(),
            alkalinity=target,
        ),
    )

    comparison = result.final_target_comparison
    assert comparison is not None
    assert comparison.alkalinity_comparison is not None
    assert comparison.alkalinity_comparison.status is expected_status
    assert comparison.alkalinity_comparison.deviation.magnitude == pytest.approx(
        expected_deviation
    )


@pytest.mark.parametrize("reverse_order", [False, True])
def test_renamed_bicarbonate_exceeds_alkalinity_target(reverse_order: bool) -> None:
    initial = Alkalinity.mg_per_liter_as_caco3(50)
    result = calculate_forward_water(
        (ForwardWaterSource(_source("Source", initial), Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(
            TreatmentAddition(
                replace(
                    SODIUM_BICARBONATE,
                    name="Sodium hydrogen carbonate",
                    ion_stoichiometry=SODIUM_BICARBONATE.ion_stoichiometry[::-1]
                    if reverse_order
                    else SODIUM_BICARBONATE.ion_stoichiometry,
                ),
                Q_(1, "gram"),
            ),
        ),
        target_profile=TargetWaterProfile("Target", (), alkalinity=initial),
    )
    assert result.final_alkalinity is not None
    assert result.final_alkalinity.concentration.magnitude == pytest.approx(
        109.57, abs=0.005
    )
    comparison = result.final_target_comparison
    assert comparison is not None and comparison.alkalinity_comparison is not None
    assert (
        comparison.alkalinity_comparison.status
        is TargetAlkalinityComparisonStatus.ABOVE_TARGET
    )
    assert comparison.status is TargetProfileComparisonStatus.NOT_SATISFIED


@pytest.mark.parametrize("grams", [0, 1])
def test_unreviewed_treatment_preserves_known_contributions(grams: int) -> None:
    initial = Alkalinity.mg_per_liter_as_caco3(50)
    result = calculate_forward_water(
        (ForwardWaterSource(_source("Source", initial), Q_(10, "liter")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(
            TreatmentAddition(SODIUM_BICARBONATE, Q_(1, "gram")),
            TreatmentAddition(
                replace(GYPSUM, molar_mass=Q_(170, "g/mol")), Q_(grams, "gram")
            ),
        ),
        target_profile=TargetWaterProfile("Target", (), alkalinity=initial),
    )
    row = result.contribution_matrix.alkalinity_row
    assert row is not None
    assert row.known_treatment_contribution_sum.magnitude == pytest.approx(
        59.57, abs=0.005
    )
    comparison = result.final_target_comparison
    assert comparison is not None and comparison.alkalinity_comparison is not None
    if grams:
        assert result.final_alkalinity is None
        assert result.alkalinity_balance.final.unresolved_treatment_indices == (1,)
        assert (
            row.treatment_contributions[1].status
            is TreatmentContributionCellStatus.UNRESOLVED
        )
        assert (
            comparison.alkalinity_comparison.status
            is TargetAlkalinityComparisonStatus.ACTUAL_UNKNOWN
        )
    else:
        assert result.final_alkalinity is not None
        assert (
            comparison.alkalinity_comparison.status
            is TargetAlkalinityComparisonStatus.ABOVE_TARGET
        )


@pytest.mark.parametrize(
    ("compound_unit", "ion_unit"), [("kg/mol", "g/mol"), ("g/mol", "oz/mol")]
)
def test_forward_alkalinity_accepts_equivalent_molar_mass_units(
    compound_unit: str, ion_unit: str
) -> None:
    original = SODIUM_BICARBONATE
    ingredient = replace(
        original,
        molar_mass=original.molar_mass.to(compound_unit),
        ion_stoichiometry=tuple(
            replace(entry, molar_mass=entry.molar_mass.to(ion_unit))
            for entry in original.ion_stoichiometry
        ),
    )
    initial = Alkalinity.mg_per_liter_as_caco3(50)
    result = calculate_forward_water(
        (ForwardWaterSource(_source("Source", initial), Q_(10, "L")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(ingredient, Q_(1, "g")),),
        target_profile=TargetWaterProfile("Target", (), alkalinity=initial),
    )
    assert result.final_alkalinity is not None
    assert result.final_alkalinity.concentration.magnitude == pytest.approx(109.571444)
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status
        is TargetProfileComparisonStatus.NOT_SATISFIED
    )


@pytest.mark.parametrize("change", ["formula", "coefficient", "ion_mass"])
def test_altered_identity_remains_unreviewed(change: str) -> None:
    ingredient = CALCIUM_CHLORIDE_DIHYDRATE
    calcium, chloride = ingredient.ion_stoichiometry
    if change == "formula":
        ingredient = replace(ingredient, formula="Na2CO3")
    else:
        chloride = (
            replace(chloride, coefficient=1)
            if change == "coefficient"
            else replace(chloride, molar_mass=chloride.molar_mass + Q_(1e-9, "g/mol"))
        )
        ingredient = replace(ingredient, ion_stoichiometry=(calcium, chloride))
    result = calculate_forward_water(
        (
            ForwardWaterSource(
                _source("Source", Alkalinity.mg_per_liter_as_caco3(50)), Q_(10, "L")
            ),
        ),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(TreatmentAddition(ingredient, Q_(1, "g")),),
    )
    assert result.alkalinity_balance.final.unresolved_treatment_indices == (0,)
    assert result.final_alkalinity is None
