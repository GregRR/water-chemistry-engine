"""Conservative-equivalent total-alkalinity accounting.

This named model carries report-native total alkalinity through source
resolution and additive-volume blending, then adds only specifically reviewed
treatment contributions.  It does not calculate carbonate speciation, pH,
precipitation, dissolution, carbon-dioxide exchange, or unmodeled reactions.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from math import fsum, isfinite, ulp
from typing import TypeAlias

from fermunits import Q_, Quantity

from water_chemistry_engine._workflow_validation import (
    require_treatment_matches_blend,
)
from water_chemistry_engine.alkalinity_conversions import (
    CACO3_EQUIVALENT_MASS_G_PER_EQ,
)
from water_chemistry_engine.blending import WaterBlendResult
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.reported_properties import (
    Alkalinity,
    AlkalinityResultIdentity,
    ReportingBasis,
)
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    TreatmentApplicationResult,
)
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_ANHYDROUS,
    CALCIUM_CHLORIDE_DIHYDRATE,
    EPSOM_SALT,
    GYPSUM,
    POTASSIUM_CHLORIDE,
    SODIUM_BICARBONATE,
    SODIUM_CHLORIDE,
    TreatmentIngredient,
)

# Admit each ingredient explicitly. Extending the stoichiometry catalog alone
# does not establish a zero effect in the conservative alkalinity model.
_REVIEWED_RULES = {
    ingredient.key: (ingredient, equivalents)
    for ingredient, equivalents in (
        (SODIUM_BICARBONATE, 1.0),
        (GYPSUM, 0.0),
        (EPSOM_SALT, 0.0),
        (SODIUM_CHLORIDE, 0.0),
        (POTASSIUM_CHLORIDE, 0.0),
        (CALCIUM_CHLORIDE_ANHYDROUS, 0.0),
        (CALCIUM_CHLORIDE_DIHYDRATE, 0.0),
    )
}


def _matches_molar_mass(actual: ScalarQuantity, reviewed: ScalarQuantity) -> bool:
    """Allow round-off from unit conversion at the catalog mass's precision."""
    expected = float(reviewed.to("g/mol").magnitude)
    measured = float(actual.to("g/mol").magnitude)
    return abs(measured - expected) <= 4 * ulp(expected)


def reviewed_alkalinity_equivalents_per_mole(
    ingredient: TreatmentIngredient,
) -> float | None:
    """Return the model rule for a verified identity, independent of its label."""
    rule = _REVIEWED_RULES.get(ingredient.key)
    if rule is None:
        return None
    reviewed, equivalents = rule
    if ingredient is reviewed:
        return equivalents
    if (
        ingredient.formula != reviewed.formula
        or len(ingredient.ion_stoichiometry) != len(reviewed.ion_stoichiometry)
        or not _matches_molar_mass(ingredient.molar_mass, reviewed.molar_mass)
    ):
        return None
    reviewed_ions = {entry.ion: entry for entry in reviewed.ion_stoichiometry}
    for actual in ingredient.ion_stoichiometry:
        expected = reviewed_ions.get(actual.ion)
        if (
            expected is None
            or actual.coefficient != expected.coefficient
            or not _matches_molar_mass(actual.molar_mass, expected.molar_mass)
        ):
            return None
    return equivalents


CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL = "conservative_equivalent_alkalinity_v1"

# CaCO3 formula mass 100.0869 g/mol divided by valence 2.  This constant is a
# reporting-equivalent mass, not a claim that CaCO3 is dissolved in the water.
CACO3_EQUIVALENT_MASS_MG = CACO3_EQUIVALENT_MASS_G_PER_EQ * 1000.0


class AlkalinityModelLimitation(StrEnum):
    """Stable exclusions from the conservative-equivalent calculation model."""

    COMPLETE_DISSOLUTION_ASSUMED = "complete_dissolution_assumed"
    PRECIPITATION_DISSOLUTION_NOT_CALCULATED = (
        "precipitation_dissolution_not_calculated"
    )
    UNMODELED_REACTIONS_NOT_CALCULATED = "unmodeled_reactions_not_calculated"
    CARBONATE_SPECIATION_NOT_CALCULATED = "carbonate_speciation_not_calculated"
    WORKING_WATER_PH_NOT_CALCULATED = "working_water_ph_not_calculated"
    LABORATORY_TITRATION_NOT_SIMULATED = "laboratory_titration_not_simulated"


CONSERVATIVE_EQUIVALENT_ALKALINITY_LIMITATIONS = (
    AlkalinityModelLimitation.COMPLETE_DISSOLUTION_ASSUMED,
    AlkalinityModelLimitation.PRECIPITATION_DISSOLUTION_NOT_CALCULATED,
    AlkalinityModelLimitation.UNMODELED_REACTIONS_NOT_CALCULATED,
    AlkalinityModelLimitation.CARBONATE_SPECIATION_NOT_CALCULATED,
    AlkalinityModelLimitation.WORKING_WATER_PH_NOT_CALCULATED,
    AlkalinityModelLimitation.LABORATORY_TITRATION_NOT_SIMULATED,
)


class SourceAlkalinityResolutionMethod(StrEnum):
    """How reported source alkalinity became a modeled numeric input."""

    REPORTED_VALUE = "reported_value"
    REPORTED_AVERAGE = "reported_average"
    DERIVED_EXACT_RANGE_MIDPOINT = "derived_exact_range_midpoint"


class UnresolvedSourceAlkalinityReason(StrEnum):
    """Why source total alkalinity is unavailable to the model."""

    NOT_REPORTED = "not_reported"
    EXACT_RANGE_MIDPOINT_NOT_PERMITTED = "exact_range_midpoint_not_permitted"
    LOWER_BOUND = "lower_bound"
    UPPER_BOUND = "upper_bound"
    ACID_NEUTRALIZING_CAPACITY_UNSUPPORTED = "acid_neutralizing_capacity_unsupported"


@dataclass(frozen=True, slots=True)
class ModeledAlkalinity:
    """Calculated total alkalinity kept distinct from a reported measurement."""

    concentration: Quantity[float]
    basis: ReportingBasis = ReportingBasis.AS_CACO3
    model: str = CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL

    def __post_init__(self) -> None:
        try:
            normalized = self.concentration.to("milligram / liter")
        except Exception as exc:
            raise ValueError(
                "Modeled alkalinity must be convertible to mass per volume."
            ) from exc
        magnitude = float(normalized.magnitude)
        if not isfinite(magnitude):
            raise ValueError("Modeled alkalinity must be finite.")
        if self.basis is not ReportingBasis.AS_CACO3:
            raise ValueError(
                "The alkalinity model currently requires an as-CaCO3 basis."
            )
        if self.model != CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL:
            raise ValueError("Unsupported alkalinity calculation model.")
        object.__setattr__(
            self,
            "concentration",
            Q_(magnitude, "milligram / liter"),
        )

    @classmethod
    def mg_per_liter_as_caco3(cls, value: float) -> "ModeledAlkalinity":
        return cls(Q_(value, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class ResolvedSourceAlkalinity:
    """One report-native alkalinity result resolved for calculation."""

    source_result: Alkalinity
    alkalinity: ModeledAlkalinity
    method: SourceAlkalinityResolutionMethod


@dataclass(frozen=True, slots=True)
class UnresolvedSourceAlkalinity:
    """One source whose total alkalinity remains unknown."""

    source_result: Alkalinity | None
    reason: UnresolvedSourceAlkalinityReason


SourceAlkalinityResolution: TypeAlias = (
    ResolvedSourceAlkalinity | UnresolvedSourceAlkalinity
)


@dataclass(frozen=True, slots=True)
class SourceAlkalinityContribution:
    """Known contribution from one source to blended total alkalinity."""

    source_index: int
    source_name: str
    source_alkalinity: ModeledAlkalinity
    weighted_contribution: Quantity[float]


@dataclass(frozen=True, slots=True)
class BlendedAlkalinityResult:
    """Modeled blend alkalinity plus complete source audit detail."""

    alkalinity: ModeledAlkalinity | None
    source_contributions: tuple[SourceAlkalinityContribution, ...]
    missing_source_indices: tuple[int, ...]
    missing_source_names: tuple[str, ...]
    model: str = CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL

    @property
    def is_resolved(self) -> bool:
        return self.alkalinity is not None


@dataclass(frozen=True, slots=True)
class TreatmentAlkalinityContribution:
    """One reviewed treatment's signed alkalinity contribution."""

    treatment_index: int
    addition: TreatmentAddition
    equivalents_per_mole: float
    concentration: Quantity[float]
    model: str = CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL


@dataclass(frozen=True, slots=True)
class FinalAlkalinityResult:
    """Modeled final alkalinity and auditable treatment contributions."""

    initial_alkalinity: ModeledAlkalinity | None
    treatment_contributions: tuple[TreatmentAlkalinityContribution, ...]
    alkalinity: ModeledAlkalinity | None
    model: str = CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL
    unresolved_treatment_indices: tuple[int, ...] = ()

    @property
    def is_resolved(self) -> bool:
        return self.alkalinity is not None


@dataclass(frozen=True, slots=True)
class AlkalinityBalanceResult:
    """Complete source, blend, treatment, and final alkalinity result graph."""

    source_resolutions: tuple[SourceAlkalinityResolution, ...]
    blend: BlendedAlkalinityResult
    final: FinalAlkalinityResult
    model: str = CONSERVATIVE_EQUIVALENT_ALKALINITY_MODEL
    limitations: tuple[AlkalinityModelLimitation, ...] = (
        CONSERVATIVE_EQUIVALENT_ALKALINITY_LIMITATIONS
    )
    _workflow: tuple[WaterBlendResult, TreatmentApplicationResult] | None = field(
        default=None, kw_only=True, repr=False, compare=False
    )

    def require_matching_stages(
        self,
        blend_result: WaterBlendResult,
        treatment_result: TreatmentApplicationResult,
    ) -> None:
        """Check the original stage instances before joining positional audit records."""
        if (
            self._workflow is None
            or self._workflow[0] is not blend_result
            or self._workflow[1] is not treatment_result
        ):
            raise ValueError(
                "Alkalinity balance must come from the supplied blend and treatment results."
            )


def resolve_source_alkalinity(
    source_profile: SourceWaterProfile,
    *,
    policy: SourceResolutionPolicy,
) -> SourceAlkalinityResolution:
    """Resolve report-native total alkalinity under the source policy."""
    reported = source_profile.alkalinity
    if reported is None:
        return UnresolvedSourceAlkalinity(
            source_result=None,
            reason=UnresolvedSourceAlkalinityReason.NOT_REPORTED,
        )

    if (
        reported.analytical_context is not None
        and reported.analytical_context.result_identity
        is AlkalinityResultIdentity.ACID_NEUTRALIZING_CAPACITY
    ):
        return UnresolvedSourceAlkalinity(
            source_result=reported,
            reason=(
                UnresolvedSourceAlkalinityReason.ACID_NEUTRALIZING_CAPACITY_UNSUPPORTED
            ),
        )

    if reported.value is not None:
        value = reported.value
        method = SourceAlkalinityResolutionMethod.REPORTED_VALUE
    elif reported.reported_average is not None:
        value = reported.reported_average
        method = SourceAlkalinityResolutionMethod.REPORTED_AVERAGE
    elif reported.minimum is not None and reported.maximum is None:
        return UnresolvedSourceAlkalinity(
            source_result=reported,
            reason=UnresolvedSourceAlkalinityReason.LOWER_BOUND,
        )
    elif reported.maximum is not None and reported.minimum is None:
        return UnresolvedSourceAlkalinity(
            source_result=reported,
            reason=UnresolvedSourceAlkalinityReason.UPPER_BOUND,
        )
    elif policy.allow_exact_range_midpoints:
        value = reported.calculation_value_with_policy(policy)
        method = SourceAlkalinityResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT
    else:
        return UnresolvedSourceAlkalinity(
            source_result=reported,
            reason=(
                UnresolvedSourceAlkalinityReason.EXACT_RANGE_MIDPOINT_NOT_PERMITTED
            ),
        )

    return ResolvedSourceAlkalinity(
        source_result=reported,
        alkalinity=ModeledAlkalinity(value),
        method=method,
    )


def _blend_alkalinity(
    source_resolutions: tuple[SourceAlkalinityResolution, ...],
    blend_result: WaterBlendResult,
) -> BlendedAlkalinityResult:
    if len(source_resolutions) != len(blend_result.sources):
        raise ValueError(
            "Source-alkalinity resolution count must match blend source count."
        )

    contributions: list[SourceAlkalinityContribution] = []
    missing_indices: list[int] = []
    missing_names: list[str] = []
    for source_index, (resolution, source) in enumerate(
        zip(source_resolutions, blend_result.sources, strict=True)
    ):
        if source.fraction == 0.0:
            continue
        if isinstance(resolution, UnresolvedSourceAlkalinity):
            missing_indices.append(source_index)
            missing_names.append(source.name)
            continue
        source_value = float(resolution.alkalinity.concentration.magnitude)
        contributions.append(
            SourceAlkalinityContribution(
                source_index=source_index,
                source_name=source.name,
                source_alkalinity=resolution.alkalinity,
                weighted_contribution=Q_(
                    source_value * source.fraction,
                    "milligram / liter",
                ),
            )
        )

    blended = None
    if not missing_indices:
        blended = ModeledAlkalinity.mg_per_liter_as_caco3(
            fsum(float(item.weighted_contribution.magnitude) for item in contributions)
        )
    return BlendedAlkalinityResult(
        alkalinity=blended,
        source_contributions=tuple(contributions),
        missing_source_indices=tuple(missing_indices),
        missing_source_names=tuple(missing_names),
    )


def calculate_treatment_alkalinity_contribution(
    treatment_index: int,
    addition: TreatmentAddition,
    water_volume_liters: float,
) -> TreatmentAlkalinityContribution | None:
    """Return a reviewed conservative-equivalent treatment contribution."""
    equivalents_per_mole = reviewed_alkalinity_equivalents_per_mole(addition.ingredient)
    if equivalents_per_mole is None or equivalents_per_mole == 0.0:
        return None
    mass_grams = float(addition.mass.to("gram").magnitude)
    molar_mass = float(addition.ingredient.molar_mass.to("gram / mole").magnitude)
    concentration = Q_(
        mass_grams
        / molar_mass
        / water_volume_liters
        * equivalents_per_mole
        * CACO3_EQUIVALENT_MASS_MG,
        "milligram / liter",
    )
    return TreatmentAlkalinityContribution(
        treatment_index=treatment_index,
        addition=addition,
        equivalents_per_mole=equivalents_per_mole,
        concentration=concentration,
    )


def calculate_alkalinity_balance(
    source_resolutions: tuple[SourceAlkalinityResolution, ...],
    blend_result: WaterBlendResult,
    treatment_result: TreatmentApplicationResult,
) -> AlkalinityBalanceResult:
    """Calculate the named conservative-equivalent alkalinity balance."""
    require_treatment_matches_blend(blend_result, treatment_result)
    blended = _blend_alkalinity(source_resolutions, blend_result)
    water_volume_liters = float(treatment_result.final_volume.to("liter").magnitude)
    contributions = []
    unresolved_indices = []
    for index, applied in enumerate(treatment_result.applied_treatments):
        addition = applied.addition
        contribution = calculate_treatment_alkalinity_contribution(
            index, addition, water_volume_liters
        )
        if contribution is not None:
            contributions.append(contribution)
        elif (
            addition.mass.magnitude > 0
            and reviewed_alkalinity_equivalents_per_mole(addition.ingredient) is None
        ):
            unresolved_indices.append(index)
    final_alkalinity = None
    if blended.alkalinity is not None and not unresolved_indices:
        final_alkalinity = ModeledAlkalinity.mg_per_liter_as_caco3(
            float(blended.alkalinity.concentration.to("mg/L").magnitude)
            * treatment_result.initial_to_final_volume_ratio
            + fsum(float(item.concentration.magnitude) for item in contributions)
        )
    final = FinalAlkalinityResult(
        initial_alkalinity=blended.alkalinity,
        treatment_contributions=tuple(contributions),
        unresolved_treatment_indices=tuple(unresolved_indices),
        alkalinity=final_alkalinity,
    )
    return AlkalinityBalanceResult(
        source_resolutions=source_resolutions,
        blend=blended,
        final=final,
        _workflow=(blend_result, treatment_result),
    )
