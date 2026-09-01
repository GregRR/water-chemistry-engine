from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from fermunits import Q_, PHValue

from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.reported_values import (
    SourceResolutionPolicy,
    linear_calculation_value,
)
from water_chemistry_engine.reporting_context import ReportedResultContext


class ReportingBasis(StrEnum):
    AS_CACO3 = "as_caco3"


def _validate_quantity(
    value: ScalarQuantity,
    *,
    canonical_unit: str,
    label: str,
    dimension_label: str,
) -> None:
    try:
        value.to(canonical_unit)
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to {dimension_label}.") from exc

    magnitude = float(value.to(canonical_unit).magnitude)
    if not isfinite(magnitude):
        raise ValueError(f"{label} must be finite.")
    if magnitude < 0:
        raise ValueError(f"{label} cannot be negative.")


def _validate_reported_values(
    *,
    value: ScalarQuantity | None,
    minimum: ScalarQuantity | None,
    maximum: ScalarQuantity | None,
    reported_average: ScalarQuantity | None,
    canonical_unit: str,
    label: str,
    dimension_label: str,
) -> None:
    if value is not None:
        _validate_quantity(
            value,
            canonical_unit=canonical_unit,
            label=label,
            dimension_label=dimension_label,
        )

        if minimum is not None or maximum is not None or reported_average is not None:
            raise ValueError(
                f"{label} exact value cannot be combined with a range or "
                "reported average."
            )

        return

    if (minimum is None) != (maximum is None):
        raise ValueError(f"{label} range requires both minimum and maximum values.")

    if minimum is not None and maximum is not None:
        _validate_quantity(
            minimum,
            canonical_unit=canonical_unit,
            label=label,
            dimension_label=dimension_label,
        )
        _validate_quantity(
            maximum,
            canonical_unit=canonical_unit,
            label=label,
            dimension_label=dimension_label,
        )

        minimum_value = minimum.to(canonical_unit).magnitude
        maximum_value = maximum.to(canonical_unit).magnitude

        if minimum_value > maximum_value:
            raise ValueError(f"{label} minimum cannot exceed maximum.")

        if reported_average is not None:
            _validate_quantity(
                reported_average,
                canonical_unit=canonical_unit,
                label=label,
                dimension_label=dimension_label,
            )
            average_value = reported_average.to(canonical_unit).magnitude

            if not minimum_value <= average_value <= maximum_value:
                raise ValueError(
                    f"{label} reported average must fall within the reported range."
                )

        return

    if reported_average is not None:
        _validate_quantity(
            reported_average,
            canonical_unit=canonical_unit,
            label=label,
            dimension_label=dimension_label,
        )
        return

    raise ValueError(
        f"{label} requires an exact value, a reported average, or a complete range."
    )


@dataclass(frozen=True, slots=True)
class Alkalinity:
    """Reported alkalinity with explicit reporting semantics and basis."""

    value: ScalarQuantity | None = None
    minimum: ScalarQuantity | None = None
    maximum: ScalarQuantity | None = None
    reported_average: ScalarQuantity | None = None
    basis: ReportingBasis = ReportingBasis.AS_CACO3

    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_reported_values(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            canonical_unit="milligram / liter",
            label="Alkalinity",
            dimension_label="mass per volume",
        )

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return only a representative value actually reported by the source."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=None,
            label=type(self).__name__,
        )

    def calculation_value_with_policy(
        self,
        policy: SourceResolutionPolicy,
    ) -> ScalarQuantity:
        """Return a reported value or a policy-authorized range midpoint."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=policy,
            label=type(self).__name__,
        )

    @classmethod
    def mg_per_liter_as_caco3(cls, value: float) -> Alkalinity:
        return cls(value=Q_(value, "milligram / liter"))

    @classmethod
    def mg_per_liter_as_caco3_range(
        cls,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
    ) -> Alkalinity:
        return cls(
            minimum=Q_(minimum, "milligram / liter"),
            maximum=Q_(maximum, "milligram / liter"),
            reported_average=(
                None
                if reported_average is None
                else Q_(reported_average, "milligram / liter")
            ),
        )


@dataclass(frozen=True, slots=True)
class TotalHardness:
    """Reported total hardness with explicit reporting semantics and basis."""

    value: ScalarQuantity | None = None
    minimum: ScalarQuantity | None = None
    maximum: ScalarQuantity | None = None
    reported_average: ScalarQuantity | None = None
    basis: ReportingBasis = ReportingBasis.AS_CACO3

    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_reported_values(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            canonical_unit="milligram / liter",
            label="Total hardness",
            dimension_label="mass per volume",
        )

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return only a representative value actually reported by the source."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=None,
            label=type(self).__name__,
        )

    def calculation_value_with_policy(
        self,
        policy: SourceResolutionPolicy,
    ) -> ScalarQuantity:
        """Return a reported value or a policy-authorized range midpoint."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=policy,
            label=type(self).__name__,
        )

    @classmethod
    def mg_per_liter_as_caco3(cls, value: float) -> TotalHardness:
        return cls(value=Q_(value, "milligram / liter"))

    @classmethod
    def mg_per_liter_as_caco3_range(
        cls,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
    ) -> TotalHardness:
        return cls(
            minimum=Q_(minimum, "milligram / liter"),
            maximum=Q_(maximum, "milligram / liter"),
            reported_average=(
                None
                if reported_average is None
                else Q_(reported_average, "milligram / liter")
            ),
        )


@dataclass(frozen=True, slots=True)
class TotalDissolvedSolids:
    """Reported total dissolved solids."""

    value: ScalarQuantity | None = None
    minimum: ScalarQuantity | None = None
    maximum: ScalarQuantity | None = None
    reported_average: ScalarQuantity | None = None

    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_reported_values(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            canonical_unit="milligram / liter",
            label="Total dissolved solids",
            dimension_label="mass per volume",
        )

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return only a representative value actually reported by the source."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=None,
            label=type(self).__name__,
        )

    def calculation_value_with_policy(
        self,
        policy: SourceResolutionPolicy,
    ) -> ScalarQuantity:
        """Return a reported value or a policy-authorized range midpoint."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=policy,
            label=type(self).__name__,
        )

    @classmethod
    def mg_per_liter(cls, value: float) -> TotalDissolvedSolids:
        return cls(value=Q_(value, "milligram / liter"))

    @classmethod
    def mg_per_liter_range(
        cls,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
    ) -> TotalDissolvedSolids:
        return cls(
            minimum=Q_(minimum, "milligram / liter"),
            maximum=Q_(maximum, "milligram / liter"),
            reported_average=(
                None
                if reported_average is None
                else Q_(reported_average, "milligram / liter")
            ),
        )


@dataclass(frozen=True, slots=True)
class Conductivity:
    """Reported electrical conductivity with optional reference temperature."""

    value: ScalarQuantity | None = None
    minimum: ScalarQuantity | None = None
    maximum: ScalarQuantity | None = None
    reported_average: ScalarQuantity | None = None
    reference_temperature_celsius: float | None = None

    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_reported_values(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            canonical_unit="microsiemens / centimeter",
            label="Conductivity",
            dimension_label="electrical conductivity",
        )
        if self.reference_temperature_celsius is not None and not isfinite(
            self.reference_temperature_celsius
        ):
            raise ValueError("Conductivity reference temperature must be finite.")

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return only a representative value actually reported by the source."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=None,
            label=type(self).__name__,
        )

    def calculation_value_with_policy(
        self,
        policy: SourceResolutionPolicy,
    ) -> ScalarQuantity:
        """Return a reported value or a policy-authorized range midpoint."""
        return linear_calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
            policy=policy,
            label=type(self).__name__,
        )

    @classmethod
    def microsiemens_per_cm(
        cls,
        value: float,
        *,
        reference_temperature_celsius: float | None = None,
    ) -> Conductivity:
        return cls(
            value=Q_(value, "microsiemens / centimeter"),
            reference_temperature_celsius=reference_temperature_celsius,
        )

    @classmethod
    def microsiemens_per_cm_range(
        cls,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
        reference_temperature_celsius: float | None = None,
    ) -> Conductivity:
        return cls(
            minimum=Q_(minimum, "microsiemens / centimeter"),
            maximum=Q_(maximum, "microsiemens / centimeter"),
            reported_average=(
                None
                if reported_average is None
                else Q_(reported_average, "microsiemens / centimeter")
            ),
            reference_temperature_celsius=reference_temperature_celsius,
        )


@dataclass(frozen=True, slots=True)
class ReportedPH:
    """Reported pH with explicit exact, range, and reported-average semantics.

    pH is logarithmic. A minimum/maximum range alone does not provide enough
    information to reconstruct an average pH and must never be reduced to an
    arithmetic midpoint.
    """

    value: PHValue | None = None
    minimum: PHValue | None = None
    maximum: PHValue | None = None
    reported_average: PHValue | None = None

    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        for item in (self.value, self.minimum, self.maximum, self.reported_average):
            if item is not None and not isinstance(item, PHValue):
                raise TypeError("Reported pH values must use fermunits.PHValue.")

        if self.value is not None:
            if (
                self.minimum is not None
                or self.maximum is not None
                or self.reported_average is not None
            ):
                raise ValueError(
                    "Reported pH exact value cannot be combined with a range "
                    "or reported average."
                )
            return

        if (self.minimum is None) != (self.maximum is None):
            raise ValueError(
                "Reported pH range requires both minimum and maximum values."
            )

        if self.minimum is not None and self.maximum is not None:
            if self.minimum.value > self.maximum.value:
                raise ValueError("Reported pH minimum cannot exceed maximum.")

            if (
                self.reported_average is not None
                and not self.minimum.value
                <= self.reported_average.value
                <= self.maximum.value
            ):
                raise ValueError(
                    "Reported pH reported average must fall within the reported range."
                )
            return

        if self.reported_average is not None:
            return

        raise ValueError(
            "Reported pH requires an exact value, a reported average, "
            "or a complete range."
        )

    @property
    def calculation_value(self) -> PHValue:
        """Return a representative pH only when one was actually reported."""
        if self.reported_average is not None:
            return self.reported_average

        if self.value is not None:
            return self.value

        raise ValueError(
            "A pH range alone has no representative calculation value. "
            "Do not calculate an arithmetic midpoint for logarithmic pH data."
        )

    @classmethod
    def exact(cls, value: float) -> ReportedPH:
        """Construct an exact reported pH."""
        return cls(value=PHValue(value))

    @classmethod
    def range(
        cls,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
    ) -> ReportedPH:
        """Construct a reported pH range with an optional reported average."""
        return cls(
            minimum=PHValue(minimum),
            maximum=PHValue(maximum),
            reported_average=(
                None if reported_average is None else PHValue(reported_average)
            ),
        )

    @classmethod
    def average(cls, reported_average: float) -> ReportedPH:
        """Construct a pH explicitly reported by the source as an average."""
        return cls(reported_average=PHValue(reported_average))
