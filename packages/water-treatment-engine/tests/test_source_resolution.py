from decimal import Decimal
from fractions import Fraction

import pytest
from fermunits import Q_
from water_treatment_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    NotDetectedConcentrationEndpoint,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.profiles import SourceWaterProfile
from water_treatment_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)
from water_treatment_engine.source_resolution import (
    ResolvedSourceIon,
    SourceIonResolutionMethod,
    SourceResolutionPolicy,
    UnresolvedSourceIon,
    UnresolvedSourceIonReason,
    resolve_source_profile,
)

ALLOW_MIDPOINTS = SourceResolutionPolicy(allow_exact_range_midpoints=True)
REPORTED_ONLY = SourceResolutionPolicy(allow_exact_range_midpoints=False)


def _mg_per_liter(result, ion: Ion) -> float | None:
    concentration = result.state.concentration_for(ion)
    if concentration is None:
        return None
    return float(concentration.to("milligram / liter").magnitude)


def test_exact_reported_value_resolves_directly() -> None:
    calcium = IonConcentration(
        ion=Ion.CALCIUM,
        value=Q_(Decimal("0.051"), "gram / liter"),
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(calcium,),
    )

    result = resolve_source_profile(profile, policy=REPORTED_ONLY)

    assert _mg_per_liter(result, Ion.CALCIUM) == pytest.approx(51.0)
    resolution = result.resolution_for(Ion.CALCIUM)
    assert isinstance(resolution, ResolvedSourceIon)
    assert resolution.source_result is calcium
    assert resolution.method is SourceIonResolutionMethod.REPORTED_VALUE
    assert isinstance(resolution.concentration.concentration.magnitude, float)


def test_reported_average_takes_precedence_over_exact_range_midpoint() -> None:
    calcium = IonConcentrationRange.mg_per_liter(
        Ion.CALCIUM,
        minimum=50.0,
        maximum=53.0,
        reported_average=51.0,
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(calcium,),
    )

    result = resolve_source_profile(profile, policy=REPORTED_ONLY)

    assert _mg_per_liter(result, Ion.CALCIUM) == pytest.approx(51.0)
    resolution = result.resolution_for(Ion.CALCIUM)
    assert isinstance(resolution, ResolvedSourceIon)
    assert resolution.method is SourceIonResolutionMethod.REPORTED_AVERAGE


def test_qualified_range_with_reported_average_resolves_to_reported_average() -> None:
    potassium = IonConcentrationRange(
        ion=Ion.POTASSIUM,
        minimum=NotDetectedConcentrationEndpoint(),
        maximum=ExactConcentrationEndpoint.mg_per_liter(4.2),
        reported_average=Q_(1.3, "milligram / liter"),
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(potassium,),
    )

    result = resolve_source_profile(profile, policy=REPORTED_ONLY)

    assert _mg_per_liter(result, Ion.POTASSIUM) == pytest.approx(1.3)
    resolution = result.resolution_for(Ion.POTASSIUM)
    assert isinstance(resolution, ResolvedSourceIon)
    assert resolution.method is SourceIonResolutionMethod.REPORTED_AVERAGE


def test_exact_range_midpoint_requires_explicit_policy_permission() -> None:
    sulfate = IonConcentrationRange.mg_per_liter(
        Ion.SULFATE,
        minimum=50.0,
        maximum=150.0,
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(sulfate,),
    )

    result = resolve_source_profile(profile, policy=REPORTED_ONLY)

    assert result.state.concentration_for(Ion.SULFATE) is None
    resolution = result.resolution_for(Ion.SULFATE)
    assert isinstance(resolution, UnresolvedSourceIon)
    assert (
        resolution.reason
        is UnresolvedSourceIonReason.EXACT_RANGE_MIDPOINT_NOT_PERMITTED
    )


def test_exact_range_midpoint_is_derived_when_policy_allows_it() -> None:
    sulfate = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=ExactConcentrationEndpoint(Q_(50, "milligram / liter")),
        maximum=ExactConcentrationEndpoint(Q_(Fraction(3, 20), "gram / liter")),
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(sulfate,),
    )

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert _mg_per_liter(result, Ion.SULFATE) == pytest.approx(100.0)
    resolution = result.resolution_for(Ion.SULFATE)
    assert isinstance(resolution, ResolvedSourceIon)
    assert resolution.method is SourceIonResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT


def test_qualified_range_without_reported_average_remains_unresolved() -> None:
    sulfate = IonConcentrationRange(
        ion=Ion.SULFATE,
        minimum=NotDetectedConcentrationEndpoint(),
        maximum=ExactConcentrationEndpoint.mg_per_liter(11.1),
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(sulfate,),
    )

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert result.state.concentration_for(Ion.SULFATE) is None
    resolution = result.resolution_for(Ion.SULFATE)
    assert isinstance(resolution, UnresolvedSourceIon)
    assert resolution.reason is UnresolvedSourceIonReason.QUALIFIED_RANGE


@pytest.mark.parametrize(
    ("source_result", "reason"),
    [
        (
            IonConcentrationUpperBound.mg_per_liter(Ion.SODIUM, maximum=5.0),
            UnresolvedSourceIonReason.UPPER_BOUND,
        ),
        (
            IonConcentrationLowerBound.mg_per_liter(Ion.SODIUM, minimum=5.0),
            UnresolvedSourceIonReason.LOWER_BOUND,
        ),
        (
            IonConcentrationNotDetected.with_detection_limit_mg_per_liter(
                Ion.SODIUM,
                detection_limit=0.3,
            ),
            UnresolvedSourceIonReason.NOT_DETECTED,
        ),
    ],
)
def test_bounds_and_not_detected_remain_unresolved(source_result, reason) -> None:
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(source_result,),
    )

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert result.state.concentration_for(Ion.SODIUM) is None
    resolution = result.resolution_for(Ion.SODIUM)
    assert isinstance(resolution, UnresolvedSourceIon)
    assert resolution.source_result is source_result
    assert resolution.reason is reason


def test_missing_ion_is_not_added_as_zero() -> None:
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),),
    )

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert _mg_per_liter(result, Ion.CALCIUM) == pytest.approx(40.0)
    assert result.state.concentration_for(Ion.MAGNESIUM) is None
    assert result.resolution_for(Ion.MAGNESIUM) is None


def test_explicit_reported_zero_remains_known_zero() -> None:
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(IonConcentration.mg_per_liter(Ion.CHLORIDE, 0.0),),
    )

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert _mg_per_liter(result, Ion.CHLORIDE) == pytest.approx(0.0)


def test_derived_state_uses_stable_ion_order() -> None:
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(
            IonConcentration.mg_per_liter(Ion.SULFATE, 80.0),
            IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
            IonConcentration.mg_per_liter(Ion.SODIUM, 10.0),
        ),
    )

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert tuple(item.ion for item in result.state.concentrations) == (
        Ion.CALCIUM,
        Ion.SODIUM,
        Ion.SULFATE,
    )


def test_resolution_audit_preserves_source_result_statistic_metadata() -> None:
    statistic = ReportedStatistic(
        kind=ReportedStatisticKind.REPORTED_AVERAGE,
        label="Average of facility results",
    )
    calcium = IonConcentration(
        ion=Ion.CALCIUM,
        value=Q_(20, "milligram / liter"),
        reported_statistic=statistic,
    )
    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(calcium,),
    )

    result = resolve_source_profile(profile, policy=REPORTED_ONLY)

    resolution = result.resolution_for(Ion.CALCIUM)
    assert isinstance(resolution, ResolvedSourceIon)
    assert resolution.source_result.reported_statistic is statistic


def test_resolution_result_retains_profile_and_policy() -> None:
    profile = SourceWaterProfile(name="Example Water", concentrations=())

    result = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    assert result.source_profile is profile
    assert result.policy is ALLOW_MIDPOINTS
    assert result.state.concentrations == ()
    assert result.ion_resolutions == ()


def test_resolved_state_feeds_treatment_without_promoting_unknown_to_zero() -> None:
    from water_treatment_engine.treatment_application import (
        TreatmentAddition,
        apply_treatment_additions,
    )
    from water_treatment_engine.treatment_ingredients import (
        CALCIUM_CHLORIDE_DIHYDRATE,
    )

    profile = SourceWaterProfile(
        name="Example Water",
        concentrations=(
            IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),
            IonConcentrationUpperBound.mg_per_liter(
                Ion.CHLORIDE,
                maximum=5.0,
            ),
        ),
    )
    resolved = resolve_source_profile(profile, policy=ALLOW_MIDPOINTS)

    treated = apply_treatment_additions(
        resolved.state,
        Q_(10, "liter"),
        (
            TreatmentAddition(
                ingredient=CALCIUM_CHLORIDE_DIHYDRATE,
                mass=Q_(1, "gram"),
            ),
        ),
    )

    calcium = treated.final_state.concentration_for(Ion.CALCIUM)
    assert calcium is not None
    assert calcium.to("milligram / liter").magnitude == pytest.approx(
        77.2625,
        abs=0.001,
    )
    assert treated.final_state.concentration_for(Ion.CHLORIDE) is None
