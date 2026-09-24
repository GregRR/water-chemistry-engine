import pytest
from fermunits import PHValue

from water_chemistry_engine.concentrations import IonConcentration
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.reported_properties import Alkalinity
from water_chemistry_engine.source_document import SourceDocumentMetadata
from water_chemistry_engine.target_profile_catalog import TargetProfileCatalog
from water_chemistry_engine.target_profiles import (
    TargetProfileClassification,
    TargetProfileProvenance,
    TargetWaterProfile,
)


def _curated_profile(
    *,
    profile_key: str = "example-reference",
    profile_version: str = "1",
    name: str = "Example reference",
) -> TargetWaterProfile:
    return TargetWaterProfile(
        name=name,
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
        provenance=TargetProfileProvenance(
            classification=TargetProfileClassification.PUBLISHED_RECOMMENDATION,
            source_document=SourceDocumentMetadata(
                publisher="Example standards organization",
                title="Example water recommendation",
            ),
            profile_key=profile_key,
            profile_version=profile_version,
        ),
    )


def test_catalog_preserves_versions_and_requires_exact_lookup() -> None:
    first = _curated_profile(profile_version="1", name="First version")
    second = _curated_profile(profile_version="2", name="Second version")
    catalog = TargetProfileCatalog(
        catalog_key="example-water-references",
        catalog_version="2026.1",
        profiles=(first, second),
    )

    assert catalog.profile_for("example-reference", "1") is first
    assert catalog.profile_for("example-reference", "2") is second
    assert catalog.profile_for("example-reference", "3") is None
    assert not hasattr(catalog, "latest")


@pytest.mark.parametrize("field", ("catalog_key", "catalog_version"))
def test_catalog_rejects_empty_identity(field: str) -> None:
    values = {
        "catalog_key": "example-water-references",
        "catalog_version": "2026.1",
    }
    values[field] = "   "

    with pytest.raises(ValueError, match="cannot be empty"):
        TargetProfileCatalog(
            profiles=(_curated_profile(),),
            **values,
        )


@pytest.mark.parametrize("field", ("catalog_key", "catalog_version"))
def test_catalog_rejects_untyped_identity(field: str) -> None:
    values: dict[str, object] = {
        "catalog_key": "example-water-references",
        "catalog_version": "2026.1",
    }
    values[field] = 1

    with pytest.raises(TypeError, match="must be text"):
        TargetProfileCatalog(  # type: ignore[arg-type]
            profiles=(_curated_profile(),),
            **values,
        )


def test_catalog_requires_at_least_one_profile() -> None:
    with pytest.raises(ValueError, match="at least one profile"):
        TargetProfileCatalog("example", "1", ())


def test_catalog_requires_tuple_profiles() -> None:
    with pytest.raises(TypeError, match="must use a tuple"):
        TargetProfileCatalog(
            "example",
            "1",
            [_curated_profile()],  # type: ignore[arg-type]
        )


def test_catalog_rejects_wrong_profile_type() -> None:
    with pytest.raises(TypeError, match="only TargetWaterProfile"):
        TargetProfileCatalog(
            "example",
            "1",
            ("profile",),  # type: ignore[arg-type]
        )


def test_catalog_requires_profile_provenance() -> None:
    with pytest.raises(ValueError, match="require provenance"):
        TargetProfileCatalog(
            "example",
            "1",
            (
                TargetWaterProfile(
                    "Unclassified",
                    (IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
                ),
            ),
        )


@pytest.mark.parametrize(
    "classification",
    (
        TargetProfileClassification.USER_TARGET,
        TargetProfileClassification.PREVIOUSLY_ACHIEVED_TREATED_WATER,
    ),
)
def test_catalog_rejects_application_owned_profile_classifications(
    classification: TargetProfileClassification,
) -> None:
    profile = TargetWaterProfile(
        name="Application-owned target",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
        provenance=TargetProfileProvenance(
            classification=classification,
            profile_key="application-owned",
            profile_version="1",
        ),
    )

    with pytest.raises(ValueError, match="user-owned or previously-achieved"):
        TargetProfileCatalog("example", "1", (profile,))


def test_catalog_requires_versioned_profile_identity() -> None:
    profile = TargetWaterProfile(
        name="Unversioned recommendation",
        concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 50.0),),
        provenance=TargetProfileProvenance(
            classification=TargetProfileClassification.PUBLISHED_RECOMMENDATION,
            source_document=SourceDocumentMetadata(publisher="Example publisher"),
        ),
    )

    with pytest.raises(ValueError, match="require profile_key and profile_version"):
        TargetProfileCatalog("example", "1", (profile,))


def test_catalog_rejects_duplicate_profile_identity() -> None:
    first = _curated_profile(name="First interpretation")
    conflicting = _curated_profile(name="Conflicting interpretation")

    with pytest.raises(ValueError, match="duplicate profile key/version"):
        TargetProfileCatalog("example", "1", (first, conflicting))


def test_catalog_requires_at_least_one_represented_target_criterion() -> None:
    empty_profile = TargetWaterProfile(
        name="Metadata-only profile",
        concentrations=(),
        provenance=TargetProfileProvenance(
            classification=TargetProfileClassification.PUBLISHED_RECOMMENDATION,
            source_document=SourceDocumentMetadata(publisher="Example publisher"),
            profile_key="metadata-only",
            profile_version="1",
        ),
    )

    with pytest.raises(ValueError, match="represented target criterion"):
        TargetProfileCatalog("example", "1", (empty_profile,))


def test_catalog_accepts_ph_and_alkalinity_as_represented_criteria() -> None:
    document = SourceDocumentMetadata(publisher="Example publisher")
    ph_profile = TargetWaterProfile(
        name="pH recommendation",
        concentrations=(),
        ph=PHValue(7.0),
        provenance=TargetProfileProvenance(
            classification=TargetProfileClassification.PUBLISHED_RECOMMENDATION,
            source_document=document,
            profile_key="ph-recommendation",
            profile_version="1",
        ),
    )
    alkalinity_profile = TargetWaterProfile(
        name="Alkalinity recommendation",
        concentrations=(),
        alkalinity=Alkalinity.mg_per_liter_as_caco3_range(30.0, 50.0),
        provenance=TargetProfileProvenance(
            classification=TargetProfileClassification.PUBLISHED_RECOMMENDATION,
            source_document=document,
            profile_key="alkalinity-recommendation",
            profile_version="1",
        ),
    )

    catalog = TargetProfileCatalog(
        "example",
        "1",
        (ph_profile, alkalinity_profile),
    )

    assert catalog.profile_for("ph-recommendation", "1") is ph_profile
    assert catalog.profile_for("alkalinity-recommendation", "1") is alkalinity_profile


@pytest.mark.parametrize("field", ("profile_key", "profile_version"))
def test_catalog_lookup_rejects_empty_identity(field: str) -> None:
    catalog = TargetProfileCatalog("example", "1", (_curated_profile(),))
    values = {"profile_key": "example-reference", "profile_version": "1"}
    values[field] = " "

    with pytest.raises(ValueError, match="cannot be empty"):
        catalog.profile_for(**values)
