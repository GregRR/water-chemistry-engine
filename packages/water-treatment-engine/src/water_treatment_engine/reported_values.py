"""Shared policy for resolving linear reported values for calculations.

Reported source values may include exact values, independently reported
averages, and ranges.  Exact values and reported averages are source data and
may be used directly.  A midpoint is derived data and is available only when a
caller explicitly opts into that representative-value policy.
"""

from dataclasses import dataclass

from fermunits import Q_

from water_treatment_engine.quantity_types import ScalarQuantity


@dataclass(frozen=True, slots=True)
class SourceResolutionPolicy:
    """Explicit rules for selecting representative linear source values."""

    allow_exact_range_midpoints: bool


def linear_calculation_value(
    *,
    value: ScalarQuantity | None,
    minimum: ScalarQuantity | None,
    maximum: ScalarQuantity | None,
    reported_average: ScalarQuantity | None,
    policy: SourceResolutionPolicy | None,
    label: str,
) -> ScalarQuantity:
    """Return a reported value or a policy-authorized derived midpoint.

    Inputs are expected to have already passed the reporting object's own
    validation.  A source-reported average takes precedence over a range
    midpoint.  An exact source value is likewise usable without policy.  A
    range-only value requires explicit midpoint permission.
    """
    if reported_average is not None:
        return reported_average

    if value is not None:
        return value

    if minimum is not None and maximum is not None:
        if policy is None or not policy.allow_exact_range_midpoints:
            raise ValueError(
                f"{label} range alone has no representative calculation value "
                "without explicit midpoint permission."
            )

        # Preserve source-reported magnitudes as supplied.  A midpoint is
        # derived data, so normalize units and deliberately enter the engine's
        # floating-point calculation layer.
        unit = minimum.units
        minimum_value = float(minimum.magnitude)
        maximum_value = float(maximum.to(unit).magnitude)
        return Q_((minimum_value + maximum_value) / 2.0, unit)

    raise RuntimeError(f"Validated {label.casefold()} has no calculation value.")
