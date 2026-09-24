from dataclasses import dataclass
from enum import StrEnum

from fermunits import PHValue

from water_chemistry_engine.comparison_policy import TargetComparisonPolicy
from water_chemistry_engine.concentrations import IonConcentrationValue
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.reported_properties import Alkalinity
from water_chemistry_engine.source_document import SourceDocumentMetadata


class TargetProfileClassification(StrEnum):
    """Evidentiary meaning explicitly claimed for a matchable profile."""

    USER_TARGET = "user_target"
    PREVIOUSLY_ACHIEVED_TREATED_WATER = "previously_achieved_treated_water"
    PUBLISHED_STANDARD = "published_standard"
    PUBLISHED_RECOMMENDATION = "published_recommendation"
    STYLE_RECOMMENDATION = "style_recommendation"
    PRACTITIONER_REFERENCE = "practitioner_reference"
    TREATED_POINT_OF_USE_REFERENCE = "treated_point_of_use_reference"
    EXPERIMENTAL_REFERENCE = "experimental_reference"
    REGIONAL_REFERENCE = "regional_reference"
    HISTORICAL_REFERENCE = "historical_reference"
    EXPERIMENTALLY_OPTIMIZED_TARGET = "experimentally_optimized_target"
    ANALYTICALLY_OPTIMIZED_TARGET = "analytically_optimized_target"


_DOCUMENTED_CLASSIFICATIONS = frozenset(TargetProfileClassification) - {
    TargetProfileClassification.USER_TARGET,
    TargetProfileClassification.PREVIOUSLY_ACHIEVED_TREATED_WATER,
}


def _validate_optional_text(value: str | None, field_name: str) -> None:
    if value is not None and not value.strip():
        raise ValueError(f"Target profile {field_name} cannot be empty.")


@dataclass(frozen=True, slots=True)
class TargetProfileProvenance:
    """Classification and attribution for a target or reproducible reference.

    ``profile_key`` and ``profile_version`` identify a versioned profile in a
    registry; they are deliberately separate from a document's title or date.
    Classifications that claim published, practitioner, regional, historical,
    experimental, or analytical support require an attributed document.
    """

    classification: TargetProfileClassification
    source_document: SourceDocumentMetadata | None = None
    profile_key: str | None = None
    profile_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.classification, TargetProfileClassification):
            raise TypeError(
                "Target profile classification must use TargetProfileClassification."
            )

        if self.source_document is not None and not isinstance(
            self.source_document,
            SourceDocumentMetadata,
        ):
            raise TypeError(
                "Target profile source_document must use SourceDocumentMetadata."
            )

        _validate_optional_text(self.profile_key, "profile_key")
        _validate_optional_text(self.profile_version, "profile_version")
        if (self.profile_key is None) != (self.profile_version is None):
            raise ValueError(
                "Target profile profile_key and profile_version must be provided "
                "together."
            )

        if (
            self.classification in _DOCUMENTED_CLASSIFICATIONS
            and self.source_document is None
        ):
            raise ValueError(
                f"Target profile classification {self.classification.value!r} "
                "requires source_document attribution."
            )


@dataclass(frozen=True, slots=True)
class TargetWaterProfile:
    """Desired or reference chemistry for treated water.

    ``alkalinity`` is a distinct total-alkalinity criterion. It is preserved
    without being converted into a bicarbonate concentration.
    """

    name: str
    concentrations: tuple[IonConcentrationValue, ...]
    ph: PHValue | None = None
    style_associations: tuple[str, ...] = ()
    notes: str | None = None
    provenance: TargetProfileProvenance | None = None
    alkalinity: Alkalinity | None = None
    comparison_policy: TargetComparisonPolicy | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Target water profile name cannot be empty.")

        ions = [concentration.ion for concentration in self.concentrations]
        if len(ions) != len(set(ions)):
            raise ValueError(
                "Target water profile cannot contain duplicate ion concentrations."
            )

        if self.ph is not None and not isinstance(self.ph, PHValue):
            raise TypeError("Target water profile pH must use fermunits.PHValue.")

        if self.alkalinity is not None and not isinstance(
            self.alkalinity,
            Alkalinity,
        ):
            raise TypeError("Target water profile alkalinity must use Alkalinity.")
        if self.alkalinity is not None and (
            self.alkalinity.reported_statistic is not None
            or self.alkalinity.analytical_context is not None
        ):
            raise ValueError(
                "Target water profile alkalinity cannot carry source-only "
                "reported statistic or analytical context."
            )

        if any(not style.strip() for style in self.style_associations):
            raise ValueError("Target water profile style associations cannot be empty.")

        if self.notes is not None and not self.notes.strip():
            raise ValueError("Target water profile notes cannot be empty.")

        if self.provenance is not None and not isinstance(
            self.provenance,
            TargetProfileProvenance,
        ):
            raise TypeError(
                "Target water profile provenance must use TargetProfileProvenance."
            )

        if self.comparison_policy is not None:
            if not isinstance(self.comparison_policy, TargetComparisonPolicy):
                raise TypeError(
                    "Target water profile comparison_policy must use "
                    "TargetComparisonPolicy."
                )
            target_ions = set(ions)
            policy_ions = {policy.ion for policy in self.comparison_policy.ion_policies}
            if unsupported_ions := policy_ions - target_ions:
                names = ", ".join(sorted(ion.value for ion in unsupported_ions))
                raise ValueError(
                    "Target comparison policy contains ions absent from the target "
                    f"profile: {names}."
                )

    def concentration_for(self, ion: Ion) -> IonConcentrationValue | None:
        """Return the target concentration for an ion, if present."""
        for concentration in self.concentrations:
            if concentration.ion is ion:
                return concentration

        return None
