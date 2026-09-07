"""Typed boundary for the first practical treatment optimizer.

The request model is intentionally separate from solving.  It records the
authority a caller grants over source volumes and rejects ambiguous material
inputs before a numerical method can treat unknown chemistry as zero.
"""

from dataclasses import dataclass
from enum import StrEnum
from math import fsum, isclose, isfinite

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


class OptimizerInputSupportStatus(StrEnum):
    """Whether the request uses only implemented models and semantics."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    INDETERMINATE = "indeterminate"


class OptimizerFeasibilityStatus(StrEnum):
    """Whether a plan satisfies the request's hard physical constraints."""

    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    INDETERMINATE = "indeterminate"


class OptimizerTargetFitStatus(StrEnum):
    """Whether final chemistry satisfies all supported target criteria."""

    WITHIN_TARGET = "within_target"
    OUTSIDE_TARGET = "outside_target"
    NOT_EVALUATED = "not_evaluated"
    INDETERMINATE = "indeterminate"


class OptimizerPracticalityStatus(StrEnum):
    """Whether a feasible plan satisfies operational dosing policy."""

    PRACTICAL = "practical"
    IMPRACTICAL = "impractical"
    NOT_EVALUATED = "not_evaluated"
    INDETERMINATE = "indeterminate"


_VOLUME_REL_TOL = 1e-12
_VOLUME_ABS_TOL_LITERS = 1e-12


def _nonnegative_volume(value: ScalarQuantity, *, label: str) -> Quantity[float]:
    try:
        normalized = value.to("liter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to volume.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude < 0:
        raise ValueError(f"{label} must be finite and nonnegative.")
    return Q_(magnitude, "liter")


def _positive_volume(value: ScalarQuantity, *, label: str) -> Quantity[float]:
    normalized = _nonnegative_volume(value, label=label)
    if normalized.magnitude == 0:
        raise ValueError(f"{label} must be greater than zero.")
    return normalized


def _positive_mass(value: ScalarQuantity, *, label: str) -> Quantity[float]:
    try:
        normalized = value.to("gram")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass.") from exc
    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude) or magnitude <= 0:
        raise ValueError(f"{label} must be finite and greater than zero.")
    return Q_(magnitude, "gram")


@dataclass(frozen=True, slots=True)
class OptimizerSource:
    """One caller-permitted source and its current/available quantities."""

    source_profile: SourceWaterProfile
    current_volume: ScalarQuantity
    maximum_volume: ScalarQuantity

    def __post_init__(self) -> None:
        if not isinstance(self.source_profile, SourceWaterProfile):
            raise TypeError("Optimizer source_profile must be SourceWaterProfile.")
        current = _nonnegative_volume(
            self.current_volume, label="Optimizer source volume"
        )
        maximum = _positive_volume(
            self.maximum_volume, label="Optimizer source maximum"
        )
        if maximum.magnitude < current.magnitude:
            raise ValueError(
                "Optimizer source maximum volume cannot be below current volume."
            )


@dataclass(frozen=True, slots=True)
class OptimizerMaterialConstraint:
    """One permitted exact material and its caller-declared batch limit.

    ``maximum_mass`` is an explicit operational constraint for this request. It
    prevents an unbounded recommendation but is not represented as a universal
    safety, sensory, solubility, or regulatory limit.
    """

    material: ExactMassDosedTreatmentMaterial
    maximum_mass: ScalarQuantity

    def __post_init__(self) -> None:
        if not isinstance(self.material, ExactMassDosedTreatmentMaterial):
            raise TypeError(
                "Optimizer material constraint requires an exact mass-dosed material."
            )
        _positive_mass(
            self.maximum_mass,
            label="Optimizer material maximum mass",
        )


@dataclass(frozen=True, slots=True)
class OptimizerRequest:
    """Declared inputs and authority for an optimizer invocation.

    Existing manual additions are absent by design.  A proportional-dilution
    request must identify its diluent explicitly.  A real RO water therefore
    carries its characterized source profile; an ideal distilled/deionized
    profile must likewise be supplied deliberately and is never inferred as
    zero chemistry by this boundary.
    """

    total_volume: ScalarQuantity
    sources: tuple[OptimizerSource, ...]
    material_constraints: tuple[OptimizerMaterialConstraint, ...]
    source_resolution_policy: SourceResolutionPolicy
    blend_policy: OptimizerBlendPolicy
    target_profile: TargetWaterProfile | None = None
    request_no_dilution_plan: bool = False
    diluent_source: OptimizerSource | None = None

    def __post_init__(self) -> None:
        total = _positive_volume(self.total_volume, label="Optimizer total volume")
        if not isinstance(self.source_resolution_policy, SourceResolutionPolicy):
            raise TypeError(
                "Optimizer source_resolution_policy must be SourceResolutionPolicy."
            )
        if not isinstance(self.blend_policy, OptimizerBlendPolicy):
            raise TypeError("Optimizer blend_policy must be OptimizerBlendPolicy.")
        if self.target_profile is not None and not isinstance(
            self.target_profile, TargetWaterProfile
        ):
            raise TypeError("Optimizer target_profile must be TargetWaterProfile.")
        if not isinstance(self.request_no_dilution_plan, bool):
            raise TypeError("Optimizer request_no_dilution_plan must be a boolean.")
        if self.diluent_source is not None and not isinstance(
            self.diluent_source, OptimizerSource
        ):
            raise TypeError("Optimizer diluent_source must be OptimizerSource.")
        if not self.sources:
            raise ValueError("Optimizer request requires at least one source.")
        if any(not isinstance(source, OptimizerSource) for source in self.sources):
            raise TypeError(
                "Optimizer sources must contain only OptimizerSource values."
            )
        if any(
            not isinstance(constraint, OptimizerMaterialConstraint)
            for constraint in self.material_constraints
        ):
            raise TypeError(
                "Optimizer material_constraints must contain only "
                "OptimizerMaterialConstraint values."
            )
        keys = [constraint.material.key for constraint in self.material_constraints]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "Optimizer request cannot contain duplicate material keys."
            )

        current_total = fsum(
            float(source.current_volume.to("liter").magnitude)
            for source in self.sources
        )
        if self.blend_policy is OptimizerBlendPolicy.FIXED:
            if self.diluent_source is not None:
                raise ValueError(
                    "A fixed-blend request cannot specify a diluent source."
                )
            if not isclose(
                current_total,
                float(total.magnitude),
                rel_tol=_VOLUME_REL_TOL,
                abs_tol=_VOLUME_ABS_TOL_LITERS,
            ):
                raise ValueError(
                    "Fixed-blend source volumes must sum to optimizer total volume."
                )
        elif self.blend_policy is OptimizerBlendPolicy.PROPORTIONAL_DILUTION:
            if self.diluent_source is None:
                raise ValueError(
                    "A proportional-dilution request requires an explicit diluent source."
                )
            if self.diluent_source in self.sources:
                raise ValueError(
                    "A proportional-dilution diluent cannot also be an ordinary source."
                )
            if self.diluent_source.current_volume.to("liter").magnitude != 0:
                raise ValueError(
                    "A proportional-dilution diluent must have zero current volume."
                )
            if current_total <= 0:
                raise ValueError(
                    "A proportional-dilution request requires a positive current blend."
                )
        elif self.diluent_source is not None:
            raise ValueError(
                "A source-volume request includes diluent water among ordinary sources."
            )
