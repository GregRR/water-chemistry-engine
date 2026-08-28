"""End-to-end deterministic forward water calculation workflow.

This module composes the existing source-resolution, fixed-blending, treatment-
application, and target-comparison boundaries without changing their scientific
semantics.  It is orchestration rather than a second chemistry implementation.

Unknown and unresolved inputs remain unknown throughout the workflow.  The
nested stage results are preserved so callers can explain how source reports
were resolved, how sources contributed to the blend, how treatments contributed
to the final water, and how each calculation checkpoint compares with a target.
"""

from dataclasses import dataclass

from water_treatment_engine.blending import BlendSource, WaterBlendResult, blend_waters
from water_treatment_engine.chemical_state import AqueousChemicalState
from water_treatment_engine.profiles import SourceWaterProfile
from water_treatment_engine.quantity_types import ScalarQuantity
from water_treatment_engine.reported_values import SourceResolutionPolicy
from water_treatment_engine.source_resolution import (
    SourceProfileResolutionResult,
    resolve_source_profile,
)
from water_treatment_engine.target_comparison import (
    TargetProfileComparison,
    compare_state_to_target,
)
from water_treatment_engine.target_profiles import TargetWaterProfile
from water_treatment_engine.treatment_application import (
    TreatmentAddition,
    TreatmentApplicationResult,
    apply_treatment_additions,
)


@dataclass(frozen=True, slots=True)
class ForwardWaterSource:
    """One reported source profile and its requested volume in the fixed blend."""

    source_profile: SourceWaterProfile
    volume: ScalarQuantity


@dataclass(frozen=True, slots=True)
class ForwardSourceResult:
    """One source after policy-controlled resolution and optional comparison."""

    source: ForwardWaterSource
    resolution: SourceProfileResolutionResult
    target_comparison: TargetProfileComparison | None

    @property
    def state(self) -> AqueousChemicalState:
        """Return the exact derived state produced by source resolution."""
        return self.resolution.state


@dataclass(frozen=True, slots=True)
class ForwardWaterCalculationResult:
    """Structured result for the complete deterministic forward workflow."""

    source_resolution_policy: SourceResolutionPolicy
    target_profile: TargetWaterProfile | None
    source_results: tuple[ForwardSourceResult, ...]
    blend_result: WaterBlendResult
    treatment_result: TreatmentApplicationResult
    blend_target_comparison: TargetProfileComparison | None
    final_target_comparison: TargetProfileComparison | None

    @property
    def blend_state(self) -> AqueousChemicalState:
        """Return the explicit fixed-blend state before treatment additions."""
        return self.blend_result.state

    @property
    def final_state(self) -> AqueousChemicalState:
        """Return the explicit final treated-water state."""
        return self.treatment_result.final_state


def _compare_if_requested(
    state: AqueousChemicalState,
    target_profile: TargetWaterProfile | None,
) -> TargetProfileComparison | None:
    if target_profile is None:
        return None
    return compare_state_to_target(state, target_profile)


def calculate_forward_water(
    sources: tuple[ForwardWaterSource, ...],
    *,
    source_resolution_policy: SourceResolutionPolicy,
    treatment_additions: tuple[TreatmentAddition, ...] = (),
    target_profile: TargetWaterProfile | None = None,
) -> ForwardWaterCalculationResult:
    """Run source resolution -> blend -> additions -> optional comparisons.

    Every source report is first resolved under the same explicit caller policy.
    Those exact derived states are blended using the requested source volumes.
    Mineral additions are then applied using the blend's physical total volume.

    When a target/reference profile is supplied, each resolved source state, the
    fixed blend, and the final treated state are compared independently.  The
    original stage results remain nested in the returned result so a UI or other
    caller can surface unknowns, resolution methods, source contributions, and
    treatment contributions without reconstructing them from final numbers.
    """
    if not sources:
        raise ValueError("Forward water calculation requires at least one source.")

    resolved_sources = tuple(
        resolve_source_profile(
            source.source_profile,
            policy=source_resolution_policy,
        )
        for source in sources
    )

    source_results = tuple(
        ForwardSourceResult(
            source=source,
            resolution=resolution,
            target_comparison=_compare_if_requested(
                resolution.state,
                target_profile,
            ),
        )
        for source, resolution in zip(sources, resolved_sources, strict=True)
    )

    blend_result = blend_waters(
        tuple(
            BlendSource(
                name=source.source_profile.name,
                state=resolution.state,
                volume=source.volume,
            )
            for source, resolution in zip(sources, resolved_sources, strict=True)
        )
    )

    treatment_result = apply_treatment_additions(
        blend_result.state,
        blend_result.total_volume,
        treatment_additions,
    )

    return ForwardWaterCalculationResult(
        source_resolution_policy=source_resolution_policy,
        target_profile=target_profile,
        source_results=source_results,
        blend_result=blend_result,
        treatment_result=treatment_result,
        blend_target_comparison=_compare_if_requested(
            blend_result.state,
            target_profile,
        ),
        final_target_comparison=_compare_if_requested(
            treatment_result.final_state,
            target_profile,
        ),
    )
