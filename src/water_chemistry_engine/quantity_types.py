"""Shared scalar Pint quantity types used by the Water Chemistry Engine.

Pint's ``Quantity`` generic parameter describes the Python type of the
quantity's magnitude, not its physical dimensionality.  Reported water data may
legitimately preserve several scalar numeric representations, so the engine
accepts those concrete ``Quantity`` specializations rather than erasing the
magnitude type with ``Quantity[Any]``.

Arrays and complex magnitudes are intentionally outside this alias.  The
current engine models scalar measurements and scalar engineering calculations;
vectorized calculation can be introduced deliberately if a real use case
requires it later.
"""

from decimal import Decimal
from fractions import Fraction
from typing import TypeAlias

from fermunits import Quantity

ScalarQuantity: TypeAlias = (
    Quantity[int] | Quantity[float] | Quantity[Decimal] | Quantity[Fraction]
)
