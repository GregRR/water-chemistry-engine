import pytest
from fermunits import Q_

from water_chemistry_engine.optimization import (
    OptimizerBlendPolicy,
    OptimizerFeasibilityStatus,
    OptimizerInputSupportStatus,
    OptimizerMaterialConstraint,
    OptimizerPracticalityStatus,
    OptimizerRequest,
    OptimizerSource,
    OptimizerTargetFitStatus,
)
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.treatment_ingredients import GYPSUM
from water_chemistry_engine.treatment_materials import ExactMassDosedTreatmentMaterial


def _source(name: str = "Source") -> OptimizerSource:
    return OptimizerSource(SourceWaterProfile(name, ()), Q_(1, "liter"), Q_(2, "liter"))


def test_optimizer_request_preserves_explicit_blend_authority() -> None:
    request = OptimizerRequest(
        total_volume=Q_(1, "liter"),
        sources=(_source(),),
        material_constraints=(),
        source_resolution_policy=SourceResolutionPolicy(
            allow_exact_range_midpoints=False
        ),
        blend_policy=OptimizerBlendPolicy.FIXED,
    )
    assert request.blend_policy is OptimizerBlendPolicy.FIXED


def test_optimizer_source_rejects_maximum_below_current() -> None:
    with pytest.raises(ValueError, match="below current"):
        OptimizerSource(
            SourceWaterProfile("Source", ()), Q_(2, "liter"), Q_(1, "liter")
        )


@pytest.mark.parametrize(
    "volume",
    [Q_(-1, "liter"), Q_(float("nan"), "liter"), Q_(float("inf"), "liter")],
)
def test_optimizer_source_rejects_invalid_current_volume(volume: object) -> None:
    with pytest.raises(ValueError, match="finite and nonnegative"):
        OptimizerSource(
            SourceWaterProfile("Source", ()),
            volume,  # type: ignore[arg-type]
            Q_(1, "liter"),
        )


def test_optimizer_source_accepts_zero_current_volume() -> None:
    source = OptimizerSource(
        SourceWaterProfile("Available source", ()), Q_(0, "liter"), Q_(1, "liter")
    )

    assert source.current_volume.magnitude == 0


def test_optimizer_source_rejects_wrong_volume_dimension() -> None:
    with pytest.raises(ValueError, match="convertible to volume"):
        OptimizerSource(SourceWaterProfile("Source", ()), Q_(1, "gram"), Q_(1, "liter"))


@pytest.mark.parametrize(
    "volume",
    [
        Q_(0, "liter"),
        Q_(-1, "liter"),
        Q_(float("nan"), "liter"),
        Q_(float("inf"), "liter"),
    ],
)
def test_optimizer_source_rejects_invalid_maximum_volume(volume: object) -> None:
    with pytest.raises(ValueError):
        OptimizerSource(
            SourceWaterProfile("Source", ()),
            Q_(0, "liter"),
            volume,  # type: ignore[arg-type]
        )


def test_optimizer_source_rejects_wrong_maximum_volume_dimension() -> None:
    with pytest.raises(ValueError, match="convertible to volume"):
        OptimizerSource(SourceWaterProfile("Source", ()), Q_(0, "liter"), Q_(1, "gram"))


def test_optimizer_request_rejects_duplicate_material_keys() -> None:
    material = ExactMassDosedTreatmentMaterial(
        "gypsum", "Gypsum", GYPSUM, Q_(0.1, "gram")
    )
    constraint = OptimizerMaterialConstraint(material, Q_(10, "gram"))
    with pytest.raises(ValueError, match="duplicate material keys"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (constraint, constraint),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )


def test_optimizer_request_allows_sources_with_the_same_display_name() -> None:
    request = OptimizerRequest(
        Q_(2, "liter"),
        (_source("Well"), _source("Well")),
        (),
        SourceResolutionPolicy(False),
        OptimizerBlendPolicy.FIXED,
    )

    assert len(request.sources) == 2


def test_optimizer_request_rejects_no_sources() -> None:
    with pytest.raises(ValueError, match="at least one source"):
        OptimizerRequest(
            Q_(1, "liter"),
            (),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )


@pytest.mark.parametrize(
    "volume",
    [
        Q_(0, "liter"),
        Q_(-1, "liter"),
        Q_(float("nan"), "liter"),
        Q_(float("inf"), "liter"),
    ],
)
def test_optimizer_request_rejects_invalid_total_volume(volume: object) -> None:
    with pytest.raises(ValueError):
        OptimizerRequest(
            volume,  # type: ignore[arg-type]
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )


def test_optimizer_request_rejects_wrong_total_volume_dimension() -> None:
    with pytest.raises(ValueError, match="convertible to volume"):
        OptimizerRequest(
            Q_(1, "gram"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )


def test_fixed_blend_requires_current_volumes_to_sum_to_total() -> None:
    with pytest.raises(ValueError, match="must sum"):
        OptimizerRequest(
            Q_(100, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )


def test_fixed_blend_accepts_cross_unit_equivalent_volume_sum() -> None:
    request = OptimizerRequest(
        Q_(1000, "milliliter"),
        (_source(),),
        (),
        SourceResolutionPolicy(False),
        OptimizerBlendPolicy.FIXED,
    )

    assert request.total_volume == Q_(1000, "milliliter")


@pytest.mark.parametrize("invalid_policy", ["fixed", "totally_made_up_policy"])
def test_optimizer_request_rejects_non_enum_blend_policy(
    invalid_policy: object,
) -> None:
    with pytest.raises(TypeError, match="must be OptimizerBlendPolicy"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            invalid_policy,  # type: ignore[arg-type]
        )


def test_optimizer_request_rejects_non_policy_resolution_value() -> None:
    with pytest.raises(TypeError, match="must be SourceResolutionPolicy"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (),
            "midpoints",  # type: ignore[arg-type]
            OptimizerBlendPolicy.FIXED,
        )


def test_proportional_dilution_requires_explicit_zero_volume_diluent() -> None:
    with pytest.raises(ValueError, match="requires an explicit diluent"):
        OptimizerRequest(
            Q_(2, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        )

    diluent = OptimizerSource(
        SourceWaterProfile("Characterized RO", ()), Q_(0, "liter"), Q_(2, "liter")
    )
    request = OptimizerRequest(
        Q_(2, "liter"),
        (_source(),),
        (),
        SourceResolutionPolicy(False),
        OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
        diluent_source=diluent,
    )

    assert request.diluent_source is diluent


def test_proportional_dilution_rejects_nonzero_current_diluent() -> None:
    with pytest.raises(ValueError, match="zero current volume"):
        OptimizerRequest(
            Q_(2, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
            diluent_source=_source("RO"),
        )


def test_proportional_dilution_rejects_diluent_repeated_as_source() -> None:
    diluent = OptimizerSource(
        SourceWaterProfile("RO", ()), Q_(0, "liter"), Q_(2, "liter")
    )
    with pytest.raises(ValueError, match="cannot also be an ordinary source"):
        OptimizerRequest(
            Q_(2, "liter"),
            (_source(), diluent),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
            diluent_source=diluent,
        )


def test_source_volume_policy_rejects_separate_diluent() -> None:
    diluent = OptimizerSource(
        SourceWaterProfile("RO", ()), Q_(0, "liter"), Q_(2, "liter")
    )
    with pytest.raises(ValueError, match="among ordinary sources"):
        OptimizerRequest(
            Q_(2, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.SOURCE_VOLUMES,
            diluent_source=diluent,
        )


@pytest.mark.parametrize(
    "blend_policy, message",
    [
        (OptimizerBlendPolicy.FIXED, "already a no-dilution request"),
        (OptimizerBlendPolicy.SOURCE_VOLUMES, "no separately identified diluent"),
    ],
)
def test_no_dilution_plan_request_requires_proportional_dilution_policy(
    blend_policy: OptimizerBlendPolicy,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            blend_policy,
            request_no_dilution_plan=True,
        )


def test_optimizer_request_rejects_wrong_boundary_types() -> None:
    with pytest.raises(TypeError, match="target_profile"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
            target_profile="target",  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError, match="no_dilution_plan"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
            request_no_dilution_plan=1,  # type: ignore[arg-type]
        )


def test_optimizer_request_rejects_wrong_collection_member_types() -> None:
    with pytest.raises(TypeError, match="only OptimizerSource"):
        OptimizerRequest(
            Q_(1, "liter"),
            ("source",),  # type: ignore[arg-type]
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )
    with pytest.raises(TypeError, match="only OptimizerMaterialConstraint"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            ("gypsum",),  # type: ignore[arg-type]
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )


@pytest.mark.parametrize(
    "maximum",
    [
        Q_(0, "gram"),
        Q_(-1, "gram"),
        Q_(float("nan"), "gram"),
        Q_(float("inf"), "gram"),
    ],
)
def test_optimizer_material_constraint_requires_positive_finite_maximum(
    maximum: object,
) -> None:
    material = ExactMassDosedTreatmentMaterial(
        "gypsum", "Gypsum", GYPSUM, Q_(0.1, "gram")
    )
    with pytest.raises(ValueError, match="finite and greater than zero"):
        OptimizerMaterialConstraint(
            material,
            maximum,  # type: ignore[arg-type]
        )


def test_optimizer_material_constraint_rejects_wrong_dimension() -> None:
    material = ExactMassDosedTreatmentMaterial(
        "gypsum", "Gypsum", GYPSUM, Q_(0.1, "gram")
    )
    with pytest.raises(ValueError, match="convertible to mass"):
        OptimizerMaterialConstraint(material, Q_(1, "liter"))


def test_optimizer_material_constraint_requires_one_usable_increment() -> None:
    material = ExactMassDosedTreatmentMaterial(
        "gypsum", "Gypsum", GYPSUM, Q_(0.1, "gram")
    )
    with pytest.raises(ValueError, match="at least one dose increment"):
        OptimizerMaterialConstraint(material, Q_(0.09, "gram"))


def test_optimizer_request_rejects_wrong_diluent_type() -> None:
    with pytest.raises(TypeError, match="diluent_source"):
        OptimizerRequest(
            Q_(2, "liter"),
            (_source(),),
            (),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.PROPORTIONAL_DILUTION,
            diluent_source="RO",  # type: ignore[arg-type]
        )


def test_optimizer_outcome_dimensions_remain_separate() -> None:
    assert OptimizerInputSupportStatus.UNSUPPORTED.value == "unsupported"
    assert OptimizerFeasibilityStatus.INFEASIBLE.value == "infeasible"
    assert OptimizerTargetFitStatus.OUTSIDE_TARGET.value == "outside_target"
    assert OptimizerPracticalityStatus.IMPRACTICAL.value == "impractical"
