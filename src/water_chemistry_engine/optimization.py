"""Typed boundary for the first practical treatment optimizer.

The request model is intentionally separate from solving.  It records the
authority a caller grants over source volumes and rejects ambiguous material
inputs before a numerical method can treat unknown chemistry as zero.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from fermunits import Q_, Quantity

from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_materials import ExactMassDosedTreatmentMaterial


class OptimizerBlendPolicy(StrEnum):
    """The permitted way an optimizer may alter source-water quantities."""

    FIXED = "fixed"
    PROPORTIONAL_DILUTION = "proportional_dilution"
    SOURCE_VOLUMES = "source_volumes"


class OptimizerPlanStatus(StrEnum):
    """Non-interchangeable outcomes reported for one proposed plan."""

    WITHIN_TARGET = "within_target"
    CLOSEST_FEASIBLE = "closest_feasible"
    INFEASIBLE = "infeasible"
    OPERATIONALLY_IMPRACTICAL = "operationally_impractical"
    UNSUPPORTED = "unsupported"
    INDETERMINATE = "indeterminate"


def _positive_volume(value: ScalarQuantity, *, label: str) -> Quantity[float]:
    try:
        normalized = value.to("liter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and greater than zero.")
    return Q_(magnitude, "liter")


@dataclass(frozen=True, slots=True)
class OptimizerSource:
    """One caller-permitted source and its current/available quantities."""

    source_profile: SourceWaterProfile
    current_volume: ScalarQuantity
    maximum_volume: ScalarQuantity

    def __post_init__(self) -> None:
        current = _positive_volume(self.current_volume, label="Optimizer source volume")
        maximum = _positive_volume(
            self.maximum_volume, label="Optimizer source maximum"
        )
        if maximum.magnitude < current.magnitude:
            raise ValueError(
                "Optimizer source maximum volume cannot be below current volume."
            )


@dataclass(frozen=True, slots=True)
class OptimizerRequest:
    """Declared inputs and authority for an optimizer invocation.

    Existing manual additions are absent by design.  A real RO source must be
    represented by ``OptimizerSource``; a separately documented ideal diluent
    will be introduced with proportional-dilution solving rather than inferred
    from this request.
    """

    total_volume: ScalarQuantity
    sources: tuple[OptimizerSource, ...]
    permitted_materials: tuple[ExactMassDosedTreatmentMaterial, ...]
    source_resolution_policy: SourceResolutionPolicy
    blend_policy: OptimizerBlendPolicy
    target_profile: TargetWaterProfile | None = None
    request_no_dilution_plan: bool = False

    def __post_init__(self) -> None:
        _positive_volume(self.total_volume, label="Optimizer total volume")
        if not self.sources:
            raise ValueError("Optimizer request requires at least one source.")
        names = [source.source_profile.name for source in self.sources]
        if len(names) != len(set(names)):
            raise ValueError("Optimizer request cannot contain duplicate source names.")
        keys = [material.key for material in self.permitted_materials]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "Optimizer request cannot contain duplicate material keys."
            )
