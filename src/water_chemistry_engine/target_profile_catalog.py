"""Versioned catalog boundary for curated target and reference profiles.

The catalog validates identity and provenance; it does not choose a preferred
version, merge conflicting references, or imply that a listed profile is an
optimum. Consumers select an exact profile key and version deliberately.
"""

from dataclasses import dataclass

from water_chemistry_engine.target_profiles import (
    TargetProfileClassification,
    TargetWaterProfile,
)

_NON_CURATED_CLASSIFICATIONS = frozenset(
    {
        TargetProfileClassification.USER_TARGET,
        TargetProfileClassification.PREVIOUSLY_ACHIEVED_TREATED_WATER,
    }
)


def _validate_required_text(value: str, label: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be text.")
    if not value.strip():
        raise ValueError(f"{label} cannot be empty.")


@dataclass(frozen=True, slots=True)
class TargetProfileCatalog:
    """One explicitly versioned collection of curated target/reference profiles.

    Every member must already carry complete versioned
    :class:`TargetProfileProvenance`. User-owned targets and previously achieved
    treated-water profiles remain application data rather than curated catalog
    entries.
    """

    catalog_key: str
    catalog_version: str
    profiles: tuple[TargetWaterProfile, ...]

    def __post_init__(self) -> None:
        _validate_required_text(self.catalog_key, "Target profile catalog key")
        _validate_required_text(
            self.catalog_version,
            "Target profile catalog version",
        )
        if not isinstance(self.profiles, tuple):
            raise TypeError("Target profile catalog profiles must use a tuple.")
        if not self.profiles:
            raise ValueError("Target profile catalog requires at least one profile.")
        if any(
            not isinstance(profile, TargetWaterProfile) for profile in self.profiles
        ):
            raise TypeError(
                "Target profile catalog profiles must contain only "
                "TargetWaterProfile values."
            )

        identities: list[tuple[str, str]] = []
        for profile in self.profiles:
            if (
                not profile.concentrations
                and profile.ph is None
                and profile.alkalinity is None
            ):
                raise ValueError(
                    "Curated target profile catalog entries require at least one "
                    "represented target criterion."
                )
            provenance = profile.provenance
            if provenance is None:
                raise ValueError(
                    "Curated target profile catalog entries require provenance."
                )
            if provenance.classification in _NON_CURATED_CLASSIFICATIONS:
                raise ValueError(
                    "Curated target profile catalog entries cannot use a "
                    "user-owned or previously-achieved classification."
                )
            if provenance.profile_key is None or provenance.profile_version is None:
                raise ValueError(
                    "Curated target profile catalog entries require profile_key "
                    "and profile_version."
                )
            identities.append(
                (provenance.profile_key, provenance.profile_version),
            )

        if len(identities) != len(set(identities)):
            raise ValueError(
                "Target profile catalog cannot contain duplicate profile key/version "
                "identities."
            )

    def profile_for(
        self,
        profile_key: str,
        profile_version: str,
    ) -> TargetWaterProfile | None:
        """Return one exact version, without inventing a latest-version policy."""
        _validate_required_text(profile_key, "Target profile key")
        _validate_required_text(profile_version, "Target profile version")

        for profile in self.profiles:
            provenance = profile.provenance
            assert provenance is not None
            if (
                provenance.profile_key == profile_key
                and provenance.profile_version == profile_version
            ):
                return profile
        return None
