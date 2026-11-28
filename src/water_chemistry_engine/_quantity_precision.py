"""Unit conversion for the optimizer's strict volume and dose constraints."""

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
def _rational_registry() -> "UnitRegistry[Fraction]":
    # Parse the same unit definitions with rational conversion factors. For
    # example, the US gallon's factor includes the cube of the inch length.
    registry = type(ureg)(non_int_type=Fraction)
    vessels = files("fermunits.definitions").joinpath("vessels.txt")
    with as_file(vessels) as path:
        registry.load_definitions(path)
    return registry


def capacity_liters(volume: ScalarQuantity) -> Fraction:
    """Keep the declared magnitude exact when changing volume units."""
    return _canonical_magnitude(volume, "liter")


def dose_grams(mass: ScalarQuantity) -> Fraction:
    """Keep the declared magnitude exact when changing dose units."""
    return _canonical_magnitude(mass, "gram")


def _canonical_magnitude(quantity: ScalarQuantity, target: str) -> Fraction:
    value = quantity.magnitude
    magnitude = Fraction(str(value)) if isinstance(value, float) else Fraction(value)
    unit = str(quantity.units)
    if unit == target:
        return magnitude

    # Retain caller-defined units and conversion scales. Use the rational
    # definition for standard units when it agrees to conversion precision.
    native_scale = (1 * quantity.units).to(target).magnitude
    registry = _rational_registry()
    if unit in registry and registry.Unit(unit).is_compatible_with(target):
        exact_scale = registry.convert(Fraction(1), unit, target)
        if isclose(float(exact_scale), float(native_scale), rel_tol=1e-15):
            return magnitude * Fraction(exact_scale)
    return magnitude * Fraction(str(native_scale))
