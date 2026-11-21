"""Capacity arithmetic for the optimizer's strict source-volume constraints."""

from fractions import Fraction
from functools import cache
from importlib.resources import as_file, files
from math import isclose
from typing import TYPE_CHECKING

from fermunits import ureg

from water_chemistry_engine.quantity_types import ScalarQuantity

if TYPE_CHECKING:
    from pint import UnitRegistry


@cache
def _rational_volume_registry() -> "UnitRegistry[Fraction]":
    # Parse the same unit definitions with rational conversion factors. For
    # example, the US gallon's factor includes the cube of the inch length.
    registry = type(ureg)(non_int_type=Fraction)
    vessels = files("fermunits.definitions").joinpath("vessels.txt")
    with as_file(vessels) as path:
        registry.load_definitions(path)
    return registry


def capacity_liters(volume: ScalarQuantity) -> Fraction:
    """Keep the declared magnitude exact when changing volume units."""
    value = volume.magnitude
    magnitude = Fraction(str(value)) if isinstance(value, float) else Fraction(value)
    unit = str(volume.units)
    if unit == "liter":
        return magnitude

    # Retain caller-defined units and conversion scales. Use the rational
    # definition for standard units when it agrees to conversion precision.
    native_scale = (1 * volume.units).to("liter").magnitude
    registry = _rational_volume_registry()
    if unit in registry and registry.Unit(unit).is_compatible_with("liter"):
        exact_scale = registry.convert(Fraction(1), unit, "liter")
        if isclose(float(exact_scale), float(native_scale), rel_tol=1e-15):
            return magnitude * Fraction(exact_scale)
    return magnitude * Fraction(str(native_scale))
