from dataclasses import dataclass
from enum import StrEnum

from fermunits import Q_

from water_treatment_engine.quantity_types import ScalarQuantity
from water_treatment_engine.reported_statistics import ReportedStatistic
from water_treatment_engine.reporting_context import ReportedResultContext


class DisinfectantKind(StrEnum):
    """Stable disinfectant concepts preserved from source-water reports."""

    # Some reports label the residual only as "Chlorine".  Do not silently
    # reinterpret that source wording as free, total, or combined chlorine.
    CHLORINE = "chlorine"
    FREE_CHLORINE = "free_chlorine"
    TOTAL_CHLORINE = "total_chlorine"
    COMBINED_CHLORINE = "combined_chlorine"
    CHLORAMINE = "chloramine"
    CHLORINE_DIOXIDE = "chlorine_dioxide"


def _validate_mass_concentration(value: ScalarQuantity, *, label: str) -> None:
    """Require a non-negative quantity convertible to mass per volume."""
    try:
        concentration = value.to("milligram / liter")
    except Exception as exc:
        raise ValueError(f"{label} must be convertible to mass per volume.") from exc

    if concentration.magnitude < 0:
        raise ValueError(f"{label} cannot be negative.")


def _validate_reported_values(
    *,
    value: ScalarQuantity | None,
    minimum: ScalarQuantity | None,
    maximum: ScalarQuantity | None,
    reported_average: ScalarQuantity | None,
) -> None:
    label = "Reported disinfectant concentration"

    if value is not None:
        _validate_mass_concentration(value, label=label)
        if minimum is not None or maximum is not None or reported_average is not None:
            raise ValueError(
                f"{label} exact value cannot be combined with a range or "
                "reported average."
            )
        return

    if (minimum is None) != (maximum is None):
        raise ValueError(f"{label} range requires both minimum and maximum values.")

    if minimum is not None and maximum is not None:
        _validate_mass_concentration(minimum, label=label)
        _validate_mass_concentration(maximum, label=label)

        minimum_value = minimum.to("milligram / liter").magnitude
        maximum_value = maximum.to("milligram / liter").magnitude
        if minimum_value > maximum_value:
            raise ValueError(f"{label} minimum cannot exceed maximum.")

        if reported_average is not None:
            _validate_mass_concentration(reported_average, label=label)
            average_value = reported_average.to("milligram / liter").magnitude
            if not minimum_value <= average_value <= maximum_value:
                raise ValueError(
                    f"{label} reported average must fall within the reported range."
                )
        return

    if reported_average is not None:
        _validate_mass_concentration(reported_average, label=label)
        return

    raise ValueError(
        f"{label} requires an exact value, a reported average, or a complete range."
    )


@dataclass(frozen=True, slots=True)
class ReportedDisinfectant:
    """A disinfectant concentration preserved as the source reported it.

    This is deliberately a focused source-report object rather than a treatment
    model.  Storing chlorine, chloramine, or chlorine dioxide here does not imply
    that the optimizer can yet predict removal, reaction products, or post-
    treatment residuals.

    ``reporting_basis`` and ``reported_label`` are source metadata, not unit
    aliases.  In particular, the engine never assumes an omitted basis such as
    ``as Cl2`` merely because that basis is common in analytical reporting.
    """

    kind: DisinfectantKind
    value: ScalarQuantity | None = None
    minimum: ScalarQuantity | None = None
    maximum: ScalarQuantity | None = None
    reported_average: ScalarQuantity | None = None
    species_name: str | None = None
    reported_label: str | None = None
    reporting_basis: str | None = None
    reported_statistic: ReportedStatistic | None = None
    result_context: ReportedResultContext | None = None

    def __post_init__(self) -> None:
        _validate_reported_values(
            value=self.value,
            minimum=self.minimum,
            maximum=self.maximum,
            reported_average=self.reported_average,
        )

        if self.species_name is not None:
            if not self.species_name.strip():
                raise ValueError("Disinfectant species name cannot be empty.")
            if self.kind is not DisinfectantKind.CHLORAMINE:
                raise ValueError(
                    "A named disinfectant species is currently supported only "
                    "for chloramine results."
                )

        if self.reported_label is not None and not self.reported_label.strip():
            raise ValueError("Disinfectant reported label cannot be empty.")

        if self.reporting_basis is not None and not self.reporting_basis.strip():
            raise ValueError("Disinfectant reporting basis cannot be empty.")

    @property
    def identity_key(self) -> tuple[DisinfectantKind, str | None]:
        """Return the source-profile identity used to reject duplicates."""
        species_name = self.species_name
        return (
            self.kind,
            species_name.strip().casefold() if species_name is not None else None,
        )

    @property
    def calculation_value(self) -> ScalarQuantity:
        """Return a representative linear concentration when one is available."""
        if self.reported_average is not None:
            return self.reported_average

        if self.value is not None:
            return self.value

        if self.minimum is not None and self.maximum is not None:
            # Preserve source magnitudes exactly.  A midpoint is derived data, so
            # normalize units and deliberately enter the float calculation layer.
            unit = self.minimum.units
            minimum = float(self.minimum.magnitude)
            maximum = float(self.maximum.to(unit).magnitude)
            return Q_((minimum + maximum) / 2.0, unit)

        raise RuntimeError("Validated disinfectant result has no calculation value.")

    @classmethod
    def mg_per_liter(
        cls,
        kind: DisinfectantKind,
        value: float,
        *,
        species_name: str | None = None,
        reported_label: str | None = None,
        reporting_basis: str | None = None,
        reported_statistic: ReportedStatistic | None = None,
        result_context: ReportedResultContext | None = None,
    ) -> ReportedDisinfectant:
        """Construct an exact disinfectant result reported in mg/L."""
        return cls(
            kind=kind,
            value=Q_(value, "milligram / liter"),
            species_name=species_name,
            reported_label=reported_label,
            reporting_basis=reporting_basis,
            reported_statistic=reported_statistic,
            result_context=result_context,
        )

    @classmethod
    def mg_per_liter_range(
        cls,
        kind: DisinfectantKind,
        minimum: float,
        maximum: float,
        *,
        reported_average: float | None = None,
        species_name: str | None = None,
        reported_label: str | None = None,
        reporting_basis: str | None = None,
        reported_statistic: ReportedStatistic | None = None,
        result_context: ReportedResultContext | None = None,
    ) -> ReportedDisinfectant:
        """Construct a disinfectant range reported in mg/L."""
        return cls(
            kind=kind,
            minimum=Q_(minimum, "milligram / liter"),
            maximum=Q_(maximum, "milligram / liter"),
            reported_average=(
                None
                if reported_average is None
                else Q_(reported_average, "milligram / liter")
            ),
            species_name=species_name,
            reported_label=reported_label,
            reporting_basis=reporting_basis,
            reported_statistic=reported_statistic,
            result_context=result_context,
        )
