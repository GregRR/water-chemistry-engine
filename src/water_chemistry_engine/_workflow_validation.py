"""Shared structural validation for linked forward-calculation stage results."""

from math import isclose

from water_chemistry_engine.blending import WaterBlendResult
from water_chemistry_engine.treatment_application import TreatmentApplicationResult

_VOLUME_REL_TOL = 1e-12
_VOLUME_ABS_TOL_LITERS = 1e-12


def require_treatment_matches_blend(
    blend_result: WaterBlendResult,
    treatment_result: TreatmentApplicationResult,
) -> None:
    """Require a treatment result to originate from the supplied blend result.

    The volume comparison tolerates only floating-point representation noise;
    it is not a domain-level allowance for treating different batch volumes as
    equivalent.
    """
    if treatment_result.initial_state != blend_result.state:
        raise ValueError(
            "Treatment result initial state must match the supplied blend state."
        )

    treatment_liters = float(treatment_result.water_volume.to("liter").magnitude)
    blend_liters = float(blend_result.total_volume.to("liter").magnitude)
    if not isclose(
        treatment_liters,
        blend_liters,
        rel_tol=_VOLUME_REL_TOL,
        abs_tol=_VOLUME_ABS_TOL_LITERS,
    ):
        raise ValueError(
            "Treatment result water volume must match the supplied blend volume."
        )
