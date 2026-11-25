from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import TypeAlias

from fermunits import Q_

from water_chemistry_engine.ions import Ion
from water_chemistry_engine.quantity_types import ScalarQuantity
from water_chemistry_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)
from water_chemistry_engine.reported_values import (
    SourceResolutionPolicy,
    linear_calculation_value,
)
from water_chemistry_engine.reporting_context import ReportedResultContext


def _validate_mass_concentration(value: ScalarQuantity) -> None:
    """Require a finite, non-negative quantity convertible to mass per volume."""
    try:
        normalized = value.to("milligram / liter")
    except Exception as exc:
        raise ValueError(
            "Ion concentration must be convertible to mass per volume."
        ) from exc

    magnitude = float(normalized.magnitude)
    if not isfinite(magnitude):
        raise ValueError("Ion concentration must be finite.")
    if magnitude < 0:
        raise ValueError("Ion concentration cannot be negative.")


@dataclass(frozen=True, slots=True)
class ExactConcentrationEndpoint:
    """Exact numeric endpoint of a reported concentration range."""

    value: ScalarQuantity

    def __post_init__(self) -> None:
        _validate_mass_concentration(self.value)

    @classmethod
    def mg_per_liter(cls, value: float) -> ExactConcentrationEndpoint:
        return cls(value=Q_(value, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class UpperBoundConcentrationEndpoint:
    """Range endpoint reported as less than a numerical limit."""

    limit: ScalarQuantity

    def __post_init__(self) -> None:
        _validate_mass_concentration(self.limit)
        if self.limit.magnitude <= 0:
            raise ValueError(
                "A strictly upper-bounded concentration endpoint needs a positive limit."
            )

    @classmethod
    def mg_per_liter(cls, limit: float) -> UpperBoundConcentrationEndpoint:
        return cls(limit=Q_(limit, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class LowerBoundConcentrationEndpoint:
    """Range endpoint reported as greater than a numerical limit."""

    limit: ScalarQuantity

    def __post_init__(self) -> None:
        _validate_mass_concentration(self.limit)

    @classmethod
    def mg_per_liter(cls, limit: float) -> LowerBoundConcentrationEndpoint:
        return cls(limit=Q_(limit, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class NotDetectedConcentrationEndpoint:
    """Range endpoint explicitly reported as not detected."""

    detection_limit: ScalarQuantity | None = None

    def __post_init__(self) -> None:
        if self.detection_limit is not None:
            _validate_mass_concentration(self.detection_limit)
            if self.detection_limit.magnitude <= 0:
                raise ValueError("A not-detected endpoint needs a positive limit.")

    @classmethod
    def with_detection_limit_mg_per_liter(
        cls,
        detection_limit: float,
    ) -> NotDetectedConcentrationEndpoint:
        return cls(
            detection_limit=Q_(detection_limit, "milligram / liter"),
        )


ConcentrationRangeEndpoint: TypeAlias = (
    ExactConcentrationEndpoint
    | UpperBoundConcentrationEndpoint
    | LowerBoundConcentrationEndpoint
    | NotDetectedConcentrationEndpoint
)


def _validate_ion(ion: Ion) -> None:
    if not isinstance(ion, Ion):
        raise TypeError("Ion concentration requires an Ion identifier.")


def _validate_endpoint_order(
    minimum: ConcentrationRangeEndpoint,
    maximum: ConcentrationRangeEndpoint,
    message: str,
) -> None:
    """Reject endpoint constraints that cannot admit a minimum <= maximum."""
    if isinstance(minimum, ExactConcentrationEndpoint):
        lower = minimum.value
    elif isinstance(minimum, LowerBoundConcentrationEndpoint):
        lower = minimum.limit
    else:
        return

    if isinstance(maximum, ExactConcentrationEndpoint):
        upper = maximum.value
    elif isinstance(maximum, UpperBoundConcentrationEndpoint):
        upper = maximum.limit
    elif (
        isinstance(maximum, NotDetectedConcentrationEndpoint)
        and maximum.detection_limit is not None
    ):
        upper = maximum.detection_limit
    else:
        return

    unit = "milligram / liter"
    lo = lower.to(unit).magnitude
    hi = upper.to(unit).magnitude
    strict = isinstance(minimum, LowerBoundConcentrationEndpoint) or not isinstance(
        maximum, ExactConcentrationEndpoint
    )
    if lo > hi or (strict and lo == hi):
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class IonConcentration:
    """Exact reported concentration of a single ion."""

    ion: Ion
    value: ScalarQuantity
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_ion(self.ion)
        _validate_mass_concentration(self.value)

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return the value to use for calculations."""
        return self.value

    @classmethod
    def mg_per_liter(cls, ion: Ion, value: float) -> IonConcentration:
        """Construct an exact ion concentration reported in mg/L."""
        return cls(ion=ion, value=Q_(value, "milligram / liter"))


@dataclass(frozen=True, slots=True)
class IonConcentrationRange:
    """Reported concentration range whose endpoints may themselves be qualified."""

    ion: Ion
    minimum: ConcentrationRangeEndpoint
    maximum: ConcentrationRangeEndpoint
    reported_average: ScalarQuantity | None = None
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None
    reported_statistic_value: ScalarQuantity | None = None

    def __post_init__(self) -> None:
        _validate_ion(self.ion)
        if self.reported_statistic is not None and not isinstance(
            self.reported_statistic, ReportedStatistic
        ):
            raise TypeError(
                "Ion concentration range requires ReportedStatistic metadata."
            )
        named_statistic = (
            self.reported_statistic is not None
            and self.reported_statistic.kind != ReportedStatisticKind.REPORTED_AVERAGE
        )
        if self.reported_statistic_value is not None:
            if not named_statistic:
                raise ValueError(
                    "A separate statistic value requires a named non-average statistic."
                )
            _validate_mass_concentration(self.reported_statistic_value)
        elif named_statistic and self.reported_average is not None:
            # Older callers supplied the labeled statistic in the only numeric
            # summary field. Its explicit label determines its meaning.
            _validate_mass_concentration(self.reported_average)
            object.__setattr__(self, "reported_statistic_value", self.reported_average)
            object.__setattr__(self, "reported_average", None)

        if not isinstance(self.minimum, ConcentrationRangeEndpoint) or not isinstance(
            self.maximum, ConcentrationRangeEndpoint
        ):
            raise TypeError("Ion concentration range requires reported endpoints.")
        _validate_endpoint_order(
            self.minimum,
            self.maximum,
            "Ion concentration range minimum cannot exceed maximum or contradict an endpoint qualifier.",
        )

        if self.reported_average is not None:
            average = ExactConcentrationEndpoint(self.reported_average)
            message = "Ion concentration reported average must fall within the reported range."
            _validate_endpoint_order(self.minimum, average, message)
            _validate_endpoint_order(average, self.maximum, message)

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return only a representative value actually reported by the source."""
        if self.reported_average is not None:
            return self.reported_average

        if self._has_exact_endpoints():
            raise ValueError(
                "An exact concentration range alone has no representative "
                "calculation value. Use calculation_value_with_policy() to "
                "authorize a derived midpoint."
            )

        raise ValueError(
            "A qualified concentration range has no automatic representative "
            "calculation value."
        )

    def _has_exact_endpoints(self) -> bool:
        """Return whether both range endpoints are exact reported values."""
        return isinstance(self.minimum, ExactConcentrationEndpoint) and isinstance(
            self.maximum,
            ExactConcentrationEndpoint,
        )

    def calculation_value_with_policy(
        self,
        policy: SourceResolutionPolicy,
    ) -> ScalarQuantity:
        """Return a reported average or a policy-authorized exact-range midpoint."""
        if self.reported_average is not None:
            return self.reported_average

        if isinstance(self.minimum, ExactConcentrationEndpoint) and isinstance(
            self.maximum,
            ExactConcentrationEndpoint,
        ):
            return linear_calculation_value(
                value=None,
                minimum=self.minimum.value,
                maximum=self.maximum.value,
                reported_average=None,
                policy=policy,
                label="Ion concentration",
            )

        raise ValueError(
            "A qualified concentration range has no automatic representative "
            "calculation value."
        )

    @classmethod
    def mg_per_liter(
        cls,
        ion: Ion,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
    ) -> IonConcentrationRange:
        """Construct an ordinary exact-endpoint concentration range in mg/L."""
        return cls(
            ion=ion,
            minimum=ExactConcentrationEndpoint.mg_per_liter(minimum),
            maximum=ExactConcentrationEndpoint.mg_per_liter(maximum),
            reported_average=(
                None
                if reported_average is None
                else Q_(reported_average, "milligram / liter")
            ),
        )


@dataclass(frozen=True, slots=True)
class IonConcentrationUpperBound:
    """Reported ion concentration known only to be below an upper bound."""

    ion: Ion
    maximum: ScalarQuantity
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_ion(self.ion)
        _validate_mass_concentration(self.maximum)

    @classmethod
    def mg_per_liter(
        cls,
        ion: Ion,
        maximum: float,
    ) -> IonConcentrationUpperBound:
        return cls(
            ion=ion,
            maximum=Q_(maximum, "milligram / liter"),
        )


@dataclass(frozen=True, slots=True)
class IonConcentrationLowerBound:
    """Reported ion concentration known only to exceed a lower bound."""

    ion: Ion
    minimum: ScalarQuantity
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_ion(self.ion)
        _validate_mass_concentration(self.minimum)

    @classmethod
    def mg_per_liter(
        cls,
        ion: Ion,
        minimum: float,
    ) -> IonConcentrationLowerBound:
        return cls(
            ion=ion,
            minimum=Q_(minimum, "milligram / liter"),
        )


@dataclass(frozen=True, slots=True)
class IonConcentrationNotDetected:
    """Ion result explicitly reported as not detected."""

    ion: Ion
    detection_limit: ScalarQuantity | None = None
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_ion(self.ion)
        if self.detection_limit is not None:
            _validate_mass_concentration(self.detection_limit)

    @classmethod
    def with_detection_limit_mg_per_liter(
        cls,
        ion: Ion,
        detection_limit: float,
    ) -> IonConcentrationNotDetected:
        return cls(
            ion=ion,
            detection_limit=Q_(detection_limit, "milligram / liter"),
        )


IonConcentrationValue: TypeAlias = (
    IonConcentration
    | IonConcentrationRange
    | IonConcentrationUpperBound
    | IonConcentrationLowerBound
    | IonConcentrationNotDetected
)
