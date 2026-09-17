import pytest
from fermunits import Q_

from water_chemistry_engine.alkalinity_balance import (
    CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL,
    AlkalinityModelLimitation,
    ResolvedSourceAlkalinity,
    SourceAlkalinityResolutionMethod,
    UnresolvedSourceAlkalinity,
    UnresolvedSourceAlkalinityReason,
)
from water_chemistry_engine.concentrations import IonConcentration
from water_chemistry_engine.forward_calculator import (
    ForwardWaterSource,
    calculate_forward_water,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_properties import Alkalinity
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.target_comparison import (
    TargetAlkalinityComparisonStatus,
    TargetProfileComparisonStatus,
)
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_application import TreatmentAddition
from water_chemistry_engine.treatment_ingredients import GYPSUM, SODIUM_BICARBONATE

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
