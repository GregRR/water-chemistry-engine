"""Presentation-ready notices for deterministic forward calculations.

The calculation stages already preserve detailed audit records.  This module
selects the subset of assumptions, unresolved inputs, and unsupported target
criteria that a caller should be able to surface directly without reverse-
engineering those nested records.

Notices do not change calculation outcomes.  Machine-readable codes and fields
allow a web or native client to localize presentation while the deterministic
English ``message`` remains useful to scripts and simple interfaces.  Target
notices are intentionally scoped to the final treated-water comparison; source
and blend target comparisons remain available on their own structured results.
"""

from dataclasses import dataclass
from enum import StrEnum

from water_chemistry_engine.blending import WaterBlendResult
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.source_resolution import (
    ResolvedSourceIon,
    SourceIonResolutionMethod,
    SourceProfileResolutionResult,
    UnresolvedSourceIon,
)
from water_chemistry_engine.target_comparison import (
    TargetIonComparisonStatus,
    TargetPHComparisonStatus,
    TargetProfileComparison,
)
from water_chemistry_engine.treatment_application import TreatmentApplicationResult


class ForwardNoticeLevel(StrEnum):
    """Presentation severity for one forward-calculation notice."""

    INFORMATION = "information"
    ASSUMPTION = "assumption"
    WARNING = "warning"


class ForwardNoticeCode(StrEnum):
    """Machine-readable notice codes for the deterministic forward workflow."""

    SOURCE_RANGE_MIDPOINT_USED = "source_range_midpoint_used"
    SOURCE_ION_UNRESOLVED = "source_ion_unresolved"
    CARBONATE_BLEND_APPROXIMATION = "carbonate_blend_approximation"
    TREATMENT_COMPLETE_DISSOLUTION_MODEL = "treatment_complete_dissolution_model"
    TARGET_ACTUAL_UNKNOWN = "target_actual_unknown"
    TARGET_CRITERION_UNSUPPORTED = "target_criterion_unsupported"
    TARGET_PH_NOT_CALCULATED = "target_ph_not_calculated"


@dataclass(frozen=True, slots=True)
class ForwardCalculationNotice:
    """One structured user-facing notice produced by the forward workflow."""

    code: ForwardNoticeCode
    level: ForwardNoticeLevel
    message: str
    ion: Ion | None = None
    source_index: int | None = None
    source_name: str | None = None
    reason: str | None = None


def _source_notices(
    source_resolutions: tuple[SourceProfileResolutionResult, ...],
    blend_result: WaterBlendResult,
) -> tuple[ForwardCalculationNotice, ...]:
    if len(source_resolutions) != len(blend_result.sources):
        raise ValueError(
            "Source-resolution count must match the supplied blend source count."
        )

    notices: list[ForwardCalculationNotice] = []
    for source_index, (resolution_result, blended_source) in enumerate(
        zip(source_resolutions, blend_result.sources, strict=True)
    ):
        if (
            resolution_result.source_profile.name != blended_source.name
            or resolution_result.state != blended_source.state
        ):
            raise ValueError(
                "Source-resolution entries must correspond to blend sources "
                "in the same order."
            )

        if blended_source.fraction == 0.0:
            continue

        for resolution in resolution_result.ion_resolutions:
            if isinstance(resolution, ResolvedSourceIon):
                if (
                    resolution.method
                    is SourceIonResolutionMethod.DERIVED_EXACT_RANGE_MIDPOINT
                ):
                    notices.append(
                        ForwardCalculationNotice(
                            code=ForwardNoticeCode.SOURCE_RANGE_MIDPOINT_USED,
                            level=ForwardNoticeLevel.ASSUMPTION,
                            message=(
                                f"{blended_source.name} {resolution.ion.value} uses "
                                "the midpoint of an exact reported range under the "
                                "supplied source-resolution policy."
                            ),
                            ion=resolution.ion,
                            source_index=source_index,
                            source_name=blended_source.name,
                            reason=resolution.method.value,
                        )
                    )
                continue

            if isinstance(resolution, UnresolvedSourceIon):
                notices.append(
                    ForwardCalculationNotice(
                        code=ForwardNoticeCode.SOURCE_ION_UNRESOLVED,
                        level=ForwardNoticeLevel.WARNING,
                        message=(
                            f"{blended_source.name} {resolution.ion.value} could not "
                            "be resolved for calculation "
                            f"({resolution.reason.value})."
                        ),
                        ion=resolution.ion,
                        source_index=source_index,
                        source_name=blended_source.name,
                        reason=resolution.reason.value,
                    )
                )

    return tuple(notices)


def _carbonate_blend_notice(
    blend_result: WaterBlendResult,
) -> ForwardCalculationNotice | None:
    positive_source_count = sum(
        source.fraction > 0.0 for source in blend_result.sources
    )
    if positive_source_count <= 1:
        return None

    modeled_carbonate_species = tuple(
        ion
        for ion in (Ion.BICARBONATE, Ion.CARBONATE)
        if blend_result.state.concentration_for(ion) is not None
    )
    if not modeled_carbonate_species:
        return None

    species_text = "/".join(ion.value for ion in modeled_carbonate_species)
    return ForwardCalculationNotice(
        code=ForwardNoticeCode.CARBONATE_BLEND_APPROXIMATION,
        level=ForwardNoticeLevel.ASSUMPTION,
        message=(
            f"Blended {species_text} uses the current first-order linear blend "
            "approximation; carbonate speciation may shift after mixing."
        ),
    )


def _treatment_model_notice(
    treatment_result: TreatmentApplicationResult,
) -> ForwardCalculationNotice | None:
    has_positive_addition = any(
        float(applied.addition.mass.to("gram").magnitude) > 0.0
        for applied in treatment_result.applied_treatments
    )
    if not has_positive_addition:
        return None

    return ForwardCalculationNotice(
        code=ForwardNoticeCode.TREATMENT_COMPLETE_DISSOLUTION_MODEL,
        level=ForwardNoticeLevel.ASSUMPTION,
        message=(
            "Mineral additions use the current theoretical complete-dissolution "
            "mass-balance model; solubility, precipitation, and aqueous reactions "
            "are not solved."
        ),
    )


def _target_notices(
    final_target_comparison: TargetProfileComparison | None,
) -> tuple[ForwardCalculationNotice, ...]:
    if final_target_comparison is None:
        return ()

    notices: list[ForwardCalculationNotice] = []
    for comparison in final_target_comparison.ion_comparisons:
        if comparison.status is TargetIonComparisonStatus.ACTUAL_UNKNOWN:
            notices.append(
                ForwardCalculationNotice(
                    code=ForwardNoticeCode.TARGET_ACTUAL_UNKNOWN,
                    level=ForwardNoticeLevel.WARNING,
                    message=(
                        f"Final {comparison.ion.value} cannot be compared with the "
                        "target because the actual concentration is unknown."
                    ),
                    ion=comparison.ion,
                    reason=comparison.status.value,
                )
            )
            continue

        if comparison.status is TargetIonComparisonStatus.TARGET_UNSUPPORTED:
            reason = (
                comparison.unsupported_reason.value
                if comparison.unsupported_reason is not None
                else comparison.status.value
            )
            notices.append(
                ForwardCalculationNotice(
                    code=ForwardNoticeCode.TARGET_CRITERION_UNSUPPORTED,
                    level=ForwardNoticeLevel.WARNING,
                    message=(
                        f"Target {comparison.ion.value} is represented but is not "
                        f"numerically comparable ({reason})."
                    ),
                    ion=comparison.ion,
                    reason=reason,
                )
            )

    ph_comparison = final_target_comparison.ph_comparison
    if (
        ph_comparison is not None
        and ph_comparison.status is TargetPHComparisonStatus.NOT_CALCULATED
    ):
        notices.append(
            ForwardCalculationNotice(
                code=ForwardNoticeCode.TARGET_PH_NOT_CALCULATED,
                level=ForwardNoticeLevel.INFORMATION,
                message=(
                    "Target pH is retained, but final working-water pH is not "
                    "calculated by the current engine."
                ),
                reason=ph_comparison.status.value,
            )
        )

    return tuple(notices)


def build_forward_notices(
    source_resolutions: tuple[SourceProfileResolutionResult, ...],
    blend_result: WaterBlendResult,
    treatment_result: TreatmentApplicationResult,
    final_target_comparison: TargetProfileComparison | None,
) -> tuple[ForwardCalculationNotice, ...]:
    """Build presentation notices from existing forward-stage results.

    Zero-volume sources are excluded because their unresolved report values do
    not affect the calculated blend.  Source notices preserve midpoint-policy
    assumptions and unresolved reported values.  A multi-source blend that
    actually computes bicarbonate or carbonate receives the documented linear-
    blending approximation notice.  Positive mineral additions surface the
    current complete-dissolution mass-balance assumption.  Final-target notices
    surface unknown actual values, unsupported criteria, and deferred working-
    water pH explicitly.  Source- and blend-stage target comparisons deliberately
    keep their outcomes on those stage results rather than duplicating notices.
    """
    notices = list(_source_notices(source_resolutions, blend_result))

    carbonate_notice = _carbonate_blend_notice(blend_result)
    if carbonate_notice is not None:
        notices.append(carbonate_notice)

    treatment_notice = _treatment_model_notice(treatment_result)
    if treatment_notice is not None:
        notices.append(treatment_notice)

    notices.extend(_target_notices(final_target_comparison))
    return tuple(notices)
