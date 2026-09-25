"""Source-backed validation cases from published brewing-water examples.

These tests use a few narrowly scoped calculations from Palmer and Kaminski,
*Water: A Comprehensive Guide for Brewers* (2013), Chapter 7. They validate
generic Engine behavior; they do not install the book's style recommendations
as an Engine-owned profile catalog or implement its mash-specific models.
"""

import pytest
from fermunits import Q_

import water_chemistry_engine as wce

REPORTED_ONLY = wce.SourceResolutionPolicy(allow_exact_range_midpoints=False)
CHAPTER_7 = wce.SourceDocumentMetadata(
    publisher="Brewers Publications",
    title="Water: A Comprehensive Guide for Brewers (2013)",
    page_reference="Chapter 7, pp. 156-167",
    notes="John Palmer and Colin Kaminski; only the publication year is recorded.",
)


def _concentrations(**values: float) -> tuple[wce.IonConcentration, ...]:
    return tuple(
        wce.IonConcentration.mg_per_liter(wce.Ion(ion_name), value)
        for ion_name, value in values.items()
    )


def _mg_per_liter(state: wce.AqueousChemicalState, ion: wce.Ion) -> float:
    concentration = state.concentration_for(ion)
    assert concentration is not None
    return float(concentration.to("milligram / liter").magnitude)


def test_chapter_7_ro_blend_and_gypsum_case_matches_published_rounding() -> None:
    """Reproduce the pp. 161-165 pale-ale blend and gypsum example."""
    source = wce.SourceWaterProfile(
        name="Palmer and Kaminski American pale ale example",
        concentrations=_concentrations(
            calcium=70.0,
            magnesium=15.0,
            sodium=35.0,
            chloride=55.0,
            sulfate=110.0,
        ),
        ph=wce.ReportedPH.exact(7.8),
        source_document=CHAPTER_7,
        alkalinity=wce.Alkalinity.mg_per_liter_as_caco3(125.0),
    )
    explicit_zero_ro = wce.SourceWaterProfile(
        name="Explicit zero-mineral RO test source",
        concentrations=_concentrations(
            calcium=0.0,
            magnesium=0.0,
            sodium=0.0,
            chloride=0.0,
            sulfate=0.0,
        ),
        alkalinity=wce.Alkalinity.mg_per_liter_as_caco3(0.0),
    )
    target = wce.TargetWaterProfile(
        name="Chapter 7 medium pale ale recommendation",
        concentrations=(
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.CALCIUM,
                minimum=50.0,
                maximum=150.0,
            ),
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.SULFATE,
                minimum=100.0,
                maximum=400.0,
            ),
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.CHLORIDE,
                minimum=0.0,
                maximum=100.0,
            ),
        ),
        alkalinity=wce.Alkalinity.mg_per_liter_as_caco3_range(40.0, 120.0),
        style_associations=("American Pale Ale", "American IPA"),
        notes="Published recommendation and experimentation starting point, not an optimum.",
        provenance=wce.TargetProfileProvenance(
            classification=wce.TargetProfileClassification.STYLE_RECOMMENDATION,
            source_document=CHAPTER_7,
            profile_key="palmer-kaminski-2013-medium-ale-pale-assertive",
            profile_version="2013",
        ),
    )

    result = wce.calculate_forward_water(
        (
            wce.ForwardWaterSource(source, Q_(1.0, "gallon")),
            wce.ForwardWaterSource(explicit_zero_ro, Q_(1.0, "gallon")),
        ),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(wce.TreatmentAddition(wce.GYPSUM, Q_(2.0, "gram")),),
        target_profile=target,
    )

    assert _mg_per_liter(result.blend_state, wce.Ion.CALCIUM) == pytest.approx(35.0)
    assert _mg_per_liter(result.blend_state, wce.Ion.MAGNESIUM) == pytest.approx(7.5)
    assert _mg_per_liter(result.blend_state, wce.Ion.SODIUM) == pytest.approx(17.5)
    assert _mg_per_liter(result.blend_state, wce.Ion.CHLORIDE) == pytest.approx(27.5)
    assert _mg_per_liter(result.blend_state, wce.Ion.SULFATE) == pytest.approx(55.0)
    assert result.blended_alkalinity is not None
    assert result.blended_alkalinity.concentration.magnitude == pytest.approx(62.5)

    calcium_contribution = _mg_per_liter(
        result.final_state, wce.Ion.CALCIUM
    ) - _mg_per_liter(result.blend_state, wce.Ion.CALCIUM)
    sulfate_contribution = _mg_per_liter(
        result.final_state, wce.Ion.SULFATE
    ) - _mg_per_liter(result.blend_state, wce.Ion.SULFATE)
    assert calcium_contribution == pytest.approx(61.5, abs=0.1)
    assert sulfate_contribution == pytest.approx(147.4, abs=0.1)
    assert _mg_per_liter(result.final_state, wce.Ion.CALCIUM) == pytest.approx(
        97.0,
        abs=0.51,
    )
    assert _mg_per_liter(result.final_state, wce.Ion.SULFATE) == pytest.approx(
        202.0,
        abs=0.51,
    )
    assert result.final_alkalinity is not None
    assert result.final_alkalinity.concentration.magnitude == pytest.approx(62.5)
    assert result.final_target_comparison is not None
    assert (
        result.final_target_comparison.status
        is wce.TargetProfileComparisonStatus.SATISFIED
    )


def test_chapter_7_calcium_chloride_case_preserves_practical_rounding() -> None:
    """Reproduce the pp. 166-167 dihydrate water-build calculation."""
    explicit_zero_source = wce.SourceWaterProfile(
        name="Explicit zero-mineral water-build source",
        concentrations=_concentrations(
            calcium=0.0,
            magnesium=0.0,
            chloride=0.0,
            sulfate=0.0,
        ),
        source_document=CHAPTER_7,
        alkalinity=wce.Alkalinity.mg_per_liter_as_caco3(0.0),
    )
    published_recommendation = wce.TargetWaterProfile(
        name="Chapter 7 light pale lager recommendation",
        concentrations=(
            wce.IonConcentrationLowerBound.mg_per_liter(
                wce.Ion.CALCIUM,
                50.0,
            ),
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.SULFATE,
                minimum=0.0,
                maximum=50.0,
            ),
            wce.IonConcentrationRange.mg_per_liter(
                wce.Ion.CHLORIDE,
                minimum=50.0,
                maximum=100.0,
            ),
        ),
        alkalinity=wce.Alkalinity.mg_per_liter_as_caco3_range(0.0, 40.0),
        style_associations=("Pilsner",),
        notes=(
            "Published starting-point recommendation; the worked example "
            "deliberately tempers its calcium minimum."
        ),
        provenance=wce.TargetProfileProvenance(
            classification=wce.TargetProfileClassification.STYLE_RECOMMENDATION,
            source_document=CHAPTER_7,
            profile_key="palmer-kaminski-2013-light-lager-pale",
            profile_version="2013",
        ),
    )

    exact_result = wce.calculate_forward_water(
        (wce.ForwardWaterSource(explicit_zero_source, Q_(10.0, "gallon")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(
            wce.TreatmentAddition(
                wce.CALCIUM_CHLORIDE_DIHYDRATE,
                Q_(4.17, "gram"),
            ),
        ),
        target_profile=published_recommendation,
    )
    practical_result = wce.calculate_forward_water(
        (wce.ForwardWaterSource(explicit_zero_source, Q_(10.0, "gallon")),),
        source_resolution_policy=REPORTED_ONLY,
        treatment_additions=(
            wce.TreatmentAddition(
                wce.CALCIUM_CHLORIDE_DIHYDRATE,
                Q_(4.2, "gram"),
            ),
        ),
        target_profile=published_recommendation,
    )

    assert _mg_per_liter(exact_result.final_state, wce.Ion.CALCIUM) == pytest.approx(
        30.0,
        abs=0.05,
    )
    assert _mg_per_liter(
        practical_result.final_state,
        wce.Ion.CHLORIDE,
    ) == pytest.approx(53.5, abs=0.1)
    assert _mg_per_liter(
        practical_result.final_state,
        wce.Ion.CALCIUM,
    ) > _mg_per_liter(exact_result.final_state, wce.Ion.CALCIUM)
    assert practical_result.final_alkalinity is not None
    assert practical_result.final_alkalinity.concentration.magnitude == 0.0
    assert practical_result.final_target_comparison is not None
    assert (
        practical_result.final_target_comparison.status
        is wce.TargetProfileComparisonStatus.NOT_SATISFIED
    )
    calcium_comparison = practical_result.final_target_comparison.comparison_for(
        wce.Ion.CALCIUM
    )
    chloride_comparison = practical_result.final_target_comparison.comparison_for(
        wce.Ion.CHLORIDE
    )
    assert calcium_comparison is not None
    assert chloride_comparison is not None
    assert calcium_comparison.status is wce.TargetIonComparisonStatus.BELOW_TARGET
    assert chloride_comparison.status is wce.TargetIonComparisonStatus.WITHIN_TARGET
