import pytest
from fermunits import Q_

from water_chemistry_engine.optimization import (
    OptimizerBlendPolicy,
    OptimizerRequest,
    OptimizerSource,
)
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.treatment_ingredients import GYPSUM
from water_chemistry_engine.treatment_materials import ExactMassDosedTreatmentMaterial


def _source(name: str = "Source") -> OptimizerSource:
    return OptimizerSource(SourceWaterProfile(name, ()), Q_(1, "liter"), Q_(2, "liter"))


def test_optimizer_request_preserves_explicit_blend_authority() -> None:
    request = OptimizerRequest(
        total_volume=Q_(2, "liter"),
        sources=(_source(),),
        permitted_materials=(),
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


def test_optimizer_request_rejects_duplicate_material_keys() -> None:
    material = ExactMassDosedTreatmentMaterial(
        "gypsum", "Gypsum", GYPSUM, Q_(0.1, "gram")
    )
    with pytest.raises(ValueError, match="duplicate material keys"):
        OptimizerRequest(
            Q_(1, "liter"),
            (_source(),),
            (material, material),
            SourceResolutionPolicy(False),
            OptimizerBlendPolicy.FIXED,
        )
