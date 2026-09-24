import pytest
from fermunits import PHValue

from water_chemistry_engine.comparison_policy import (
    TargetComparisonPolicy,
    TargetIonClosenessPolicy,
)
from water_chemistry_engine.concentrations import (
    IonConcentration,
    IonConcentrationRange,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.reported_properties import (
    Alkalinity,
    AlkalinityAnalyticalContext,
    AlkalinityResultIdentity,
)
from water_chemistry_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)
from water_chemistry_engine.source_document import SourceDocumentMetadata
from water_chemistry_engine.target_profiles import (
    TargetProfileClassification,
    TargetProfileProvenance,
    TargetWaterProfile,
)


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


def test_target_profile_preserves_total_alkalinity_separately() -> None:
    alkalinity = Alkalinity.mg_per_liter_as_caco3(40.0)

    profile = TargetWaterProfile(
        name="Total alkalinity target",
        concentrations=(),
        alkalinity=alkalinity,
    )

    assert profile.alkalinity is alkalinity
    assert profile.concentration_for(Ion.BICARBONATE) is None


def test_target_profile_preserves_one_sided_alkalinity_bound() -> None:
    alkalinity = Alkalinity.mg_per_liter_as_caco3_upper_bound(80.0)

    profile = TargetWaterProfile(
        name="Upper alkalinity target",
        concentrations=(),
        alkalinity=alkalinity,
    )

    assert profile.alkalinity is alkalinity
    assert profile.alkalinity.minimum is None
    assert profile.alkalinity.maximum is not None


@pytest.mark.parametrize(
    "alkalinity",
    (
        Alkalinity.mg_per_liter_as_caco3(
            40.0,
            reported_statistic=ReportedStatistic(
                kind=ReportedStatisticKind.REPORTED_AVERAGE
            ),
        ),
        Alkalinity.mg_per_liter_as_caco3(
            40.0,
            analytical_context=AlkalinityAnalyticalContext(
                result_identity=AlkalinityResultIdentity.TOTAL_ALKALINITY,
            ),
        ),
    ),
)
def test_target_profile_rejects_source_only_alkalinity_metadata(
    alkalinity: Alkalinity,
) -> None:
    with pytest.raises(ValueError, match="source-only"):
        TargetWaterProfile(
            name="Invalid alkalinity target",
            concentrations=(),
            alkalinity=alkalinity,
        )


def test_missing_target_ion_returns_none() -> None:
    profile = TargetWaterProfile(
        name="Example Target",
        concentrations=(),
    )

    assert profile.concentration_for(Ion.MAGNESIUM) is None


def test_target_profile_has_no_implicit_evidentiary_classification() -> None:
    profile = TargetWaterProfile(name="Unclassified target", concentrations=())

    assert profile.provenance is None


def test_target_profile_preserves_versioned_historical_provenance() -> None:
    document = SourceDocumentMetadata(
        publisher="Example Historical Archive",
        title="Example City Water Analysis",
        source_url="https://example.com/archive/water-analysis",
    )
    provenance = TargetProfileProvenance(
        classification=TargetProfileClassification.HISTORICAL_REFERENCE,
        source_document=document,
        profile_key="example-city-archive-1901",
        profile_version="1",
    )

    profile = TargetWaterProfile(
        name="Example City, 1901",
        concentrations=(),
        provenance=provenance,
    )

    assert profile.provenance is provenance
    assert profile.provenance.classification is (
        TargetProfileClassification.HISTORICAL_REFERENCE
    )
    assert profile.provenance.source_document is document
    assert profile.provenance.profile_key == "example-city-archive-1901"
    assert profile.provenance.profile_version == "1"


@pytest.mark.parametrize(
    "classification",
    [
        classification
        for classification in TargetProfileClassification
        if classification
        not in {
            TargetProfileClassification.USER_TARGET,
            TargetProfileClassification.PREVIOUSLY_ACHIEVED_TREATED_WATER,
        }
    ],
)
def test_evidence_claiming_classifications_require_document_attribution(
    classification: TargetProfileClassification,
) -> None:
    with pytest.raises(ValueError, match="requires source_document attribution"):
        TargetProfileProvenance(classification=classification)


@pytest.mark.parametrize(
    "classification",
    [
        TargetProfileClassification.USER_TARGET,
        TargetProfileClassification.PREVIOUSLY_ACHIEVED_TREATED_WATER,
    ],
)
def test_user_owned_classifications_do_not_invent_document_attribution(
    classification: TargetProfileClassification,
) -> None:
    provenance = TargetProfileProvenance(classification=classification)

    assert provenance.source_document is None


@pytest.mark.parametrize(
    ("profile_key", "profile_version"),
    [("example", None), (None, "1")],
)
def test_versioned_profile_identity_requires_key_and_version_together(
    profile_key: str | None,
    profile_version: str | None,
) -> None:
    with pytest.raises(ValueError, match="must be provided together"):
        TargetProfileProvenance(
            classification=TargetProfileClassification.USER_TARGET,
            profile_key=profile_key,
            profile_version=profile_version,
        )


@pytest.mark.parametrize("field", ["profile_key", "profile_version"])
def test_target_profile_provenance_rejects_empty_identity_fields(field: str) -> None:
    values = {"profile_key": "example", "profile_version": "1"}
    values[field] = "   "

    with pytest.raises(ValueError, match=rf"{field} cannot be empty"):
        TargetProfileProvenance(
            classification=TargetProfileClassification.USER_TARGET,
            **values,
        )


def test_target_profile_provenance_rejects_raw_classification_string() -> None:
    with pytest.raises(TypeError, match="TargetProfileClassification"):
        TargetProfileProvenance(
            classification="user_target",  # type: ignore[arg-type]
        )


def test_target_profile_provenance_rejects_wrong_document_type() -> None:
    with pytest.raises(TypeError, match="SourceDocumentMetadata"):
        TargetProfileProvenance(
            classification=TargetProfileClassification.PUBLISHED_STANDARD,
            source_document="citation",  # type: ignore[arg-type]
        )


def test_target_profile_rejects_wrong_provenance_type() -> None:
    with pytest.raises(TypeError, match="TargetProfileProvenance"):
        TargetWaterProfile(
            name="Example target",
            concentrations=(),
            provenance="historical",  # type: ignore[arg-type]
        )


def test_target_profile_preserves_comparison_policy() -> None:
    comparison_policy = TargetComparisonPolicy(
        key="example-bands",
        version="1",
        description="Example absolute closeness bands.",
        ion_policies=(
            TargetIonClosenessPolicy.mg_per_liter(
                Ion.CALCIUM,
                maximum_below_deviation=5.0,
                maximum_above_deviation=10.0,
            ),
        ),
    )
    profile = TargetWaterProfile(
        name="Calcium target",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
        comparison_policy=comparison_policy,
    )

    assert profile.comparison_policy is comparison_policy


def test_target_profile_rejects_policy_for_absent_ion() -> None:
    comparison_policy = TargetComparisonPolicy(
        key="absent-ion",
        version="1",
        description="Invalid policy for an absent target ion.",
        ion_policies=(
            TargetIonClosenessPolicy.mg_per_liter(
                Ion.SULFATE,
                maximum_below_deviation=5.0,
                maximum_above_deviation=5.0,
            ),
        ),
    )

    with pytest.raises(ValueError, match="ions absent.*sulfate"):
        TargetWaterProfile(
            name="Calcium target",
            concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
            comparison_policy=comparison_policy,
        )


def test_target_profile_rejects_wrong_comparison_policy_type() -> None:
    with pytest.raises(TypeError, match="TargetComparisonPolicy"):
        TargetWaterProfile(
            name="Calcium target",
            concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
            comparison_policy="close",  # type: ignore[arg-type]
        )


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


@pytest.mark.parametrize("value", [-0.1, 14.1])
def test_target_ph_does_not_impose_a_universal_zero_to_fourteen_range(
    value: float,
) -> None:
    profile = TargetWaterProfile(
        name="Example Target",
        concentrations=(),
        ph=PHValue(value),
    )

    assert profile.ph == PHValue(value)


def test_target_ph_requires_semantic_ph_value() -> None:
    with pytest.raises(TypeError, match="fermunits.PHValue"):
        TargetWaterProfile(
            name="Example Target",
            concentrations=(),
            ph=7.0,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("invalid", [-1.0, float("nan"), float("inf"), float("-inf")])
def test_invalid_target_concentration_is_rejected(invalid: float) -> None:
    with pytest.raises(ValueError, match="finite|negative"):
        TargetWaterProfile(
            name="Invalid Target",
            concentrations=(IonConcentration.mg_per_liter(Ion.SODIUM, invalid),),
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
