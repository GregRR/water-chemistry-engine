from dataclasses import dataclass

from fermunits import Q_

from water_treatment_engine.ions import Ion
from water_treatment_engine.quantity_types import ScalarQuantity
from water_treatment_engine.reported_statistics import ReportedStatistic
from water_treatment_engine.reported_values import (
    SourceResolutionPolicy,
    linear_calculation_value,
)
from water_treatment_engine.reporting_context import ReportedResultContext


def _validate_mass_concentration(value: ScalarQuantity) -> None:
    """Require a quantity convertible to mass per volume."""
    try:
        value.to("milligram / liter")
    except Exception as exc:
        raise ValueError(
            "Ion concentration must be convertible to mass per volume."
        ) from exc


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

    @classmethod
    def with_detection_limit_mg_per_liter(
        cls,
        detection_limit: float,
    ) -> NotDetectedConcentrationEndpoint:
        return cls(
            detection_limit=Q_(detection_limit, "milligram / liter"),
        )


type ConcentrationRangeEndpoint = (
    ExactConcentrationEndpoint
    | UpperBoundConcentrationEndpoint
    | LowerBoundConcentrationEndpoint
    | NotDetectedConcentrationEndpoint
)


@dataclass(frozen=True, slots=True)
class IonConcentration:
    """Exact reported concentration of a single ion."""

    ion: Ion
    value: ScalarQuantity
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
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

    def __post_init__(self) -> None:
        if isinstance(self.minimum, ExactConcentrationEndpoint) and isinstance(
            self.maximum,
            ExactConcentrationEndpoint,
        ):
            minimum = self.minimum.value.to("milligram / liter").magnitude
            maximum = self.maximum.value.to("milligram / liter").magnitude

            if minimum > maximum:
                raise ValueError(
                    "Ion concentration range minimum cannot exceed maximum."
                )

            if self.reported_average is not None:
                _validate_mass_concentration(self.reported_average)
                reported_average = self.reported_average.to(
                    "milligram / liter"
                ).magnitude

                if not minimum <= reported_average <= maximum:
                    raise ValueError(
                        "Ion concentration reported average must fall within "
                        "the reported range."
                    )

        elif self.reported_average is not None:
            _validate_mass_concentration(self.reported_average)

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
        _validate_mass_concentration(self.maximum)

        if self.maximum.to("milligram / liter").magnitude < 0:
            raise ValueError("Ion concentration upper bound cannot be negative.")

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
        _validate_mass_concentration(self.minimum)

        if self.minimum.to("milligram / liter").magnitude < 0:
            raise ValueError("Ion concentration lower bound cannot be negative.")

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


type IonConcentrationValue = (
    IonConcentration
    | IonConcentrationRange
    | IonConcentrationUpperBound
    | IonConcentrationLowerBound
    | IonConcentrationNotDetected
)
