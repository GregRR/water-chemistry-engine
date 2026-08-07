from dataclasses import dataclass
from enum import StrEnum

from fermunits import Q_
from pint import Quantity


class ReportingBasis(StrEnum):
    AS_CACO3 = "as_caco3"


def _validate_quantity(
    value: Quantity,
    *,
    canonical_unit: str,
    label: str,
    dimension_label: str,
) -> None:
    try:
        value.to(canonical_unit)
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to {dimension_label}.") from exc


def _validate_reported_values(
    *,
    value: Quantity | None,
    minimum: Quantity | None,
    maximum: Quantity | None,
    reported_average: Quantity | None,
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


def _calculation_value(
    *,
    value: Quantity | None,
    minimum: Quantity | None,
    maximum: Quantity | None,
    reported_average: Quantity | None,
) -> Quantity:
    if reported_average is not None:
        return reported_average

    if value is not None:
        return value

    if minimum is not None and maximum is not None:
        return (minimum + maximum) / 2

    raise RuntimeError("Validated reported quantity has no calculation value.")


@dataclass(frozen=True, slots=True)
class Alkalinity:
    """Reported alkalinity with explicit reporting semantics and basis."""

    value: Quantity | None = None
    minimum: Quantity | None = None
    maximum: Quantity | None = None
    reported_average: Quantity | None = None
    basis: ReportingBasis = ReportingBasis.AS_CACO3

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
    def calculation_value(self) -> Quantity:
        return _calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
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

    value: Quantity | None = None
    minimum: Quantity | None = None
    maximum: Quantity | None = None
    reported_average: Quantity | None = None
    basis: ReportingBasis = ReportingBasis.AS_CACO3

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
    def calculation_value(self) -> Quantity:
        return _calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
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

    value: Quantity | None = None
    minimum: Quantity | None = None
    maximum: Quantity | None = None
    reported_average: Quantity | None = None

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
    def calculation_value(self) -> Quantity:
        return _calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
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

    value: Quantity | None = None
    minimum: Quantity | None = None
    maximum: Quantity | None = None
    reported_average: Quantity | None = None
    reference_temperature_celsius: float | None = None

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

    @property
    def calculation_value(self) -> Quantity:
        return _calculation_value(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
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
