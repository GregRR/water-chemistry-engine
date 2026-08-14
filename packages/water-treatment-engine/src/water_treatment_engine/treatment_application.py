"""Forward application of simple mineral additions to a derived water state.

This layer combines the fixed stoichiometric contributions calculated by
``treatment_stoichiometry`` with an existing exact derived ion inventory.  It
is still a formal mass-balance model rather than an aqueous-equilibrium model.
In particular, it does not consume ions through reactions, enforce solubility,
model precipitation, or redistribute carbonate species.
"""

from dataclasses import dataclass

from fermunits import Q_
from pint import Quantity

from water_treatment_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.quantity_types import ScalarQuantity
from water_treatment_engine.treatment_ingredients import TreatmentIngredient
from water_treatment_engine.treatment_stoichiometry import (
    IonContribution,
    calculate_ion_contributions,
)


@dataclass(frozen=True, slots=True)
class TreatmentAddition:
    """One requested mass addition of a specific treatment ingredient."""

    ingredient: TreatmentIngredient
    mass: ScalarQuantity

    def __post_init__(self) -> None:
        try:
            normalized = self.mass.to("gram")
        except Exception as exc:
            raise ValueError(
                "Treatment addition mass must be convertible to mass."
            ) from exc

        if normalized.magnitude < 0:
            raise ValueError("Treatment addition mass cannot be negative.")


@dataclass(frozen=True, slots=True)
class AppliedTreatment:
    """One treatment addition together with its derived ion contributions."""

    addition: TreatmentAddition
    ion_contributions: tuple[IonContribution, ...]


@dataclass(frozen=True, slots=True)
class TreatmentApplicationResult:
    """Derived final state and auditable contribution detail for a treatment set."""

    initial_state: AqueousChemicalState
    water_volume: Quantity[float]
    applied_treatments: tuple[AppliedTreatment, ...]
    final_state: AqueousChemicalState


def _normalize_water_volume(water_volume: ScalarQuantity) -> Quantity[float]:
    try:
        normalized = water_volume.to("liter")
    except Exception as exc:
        raise ValueError(
            "Treatment water volume must be convertible to volume."
        ) from exc

    magnitude = float(normalized.magnitude)
    if magnitude <= 0:
        raise ValueError("Treatment water volume must be greater than zero.")

    return Q_(magnitude, "liter")


def apply_treatment_additions(
    initial_state: AqueousChemicalState,
    water_volume: ScalarQuantity,
    additions: tuple[TreatmentAddition, ...],
) -> TreatmentApplicationResult:
    """Apply zero or more simple mineral additions to an exact water state.

    Existing known state concentrations and each treatment contribution are
    summed in canonical mg/L units.  A missing ion in ``initial_state`` remains
    unknown: treatment contribution to that ion is recorded, but it is not
    silently promoted to a final total by assuming the unknown starting value
    was zero.  Callers that genuinely know a starting concentration is zero
    should represent that zero explicitly in the derived state.

    The returned per-treatment records preserve how much each requested
    addition contributed.  This is the treatment side of the contribution
    matrix that later blend-and-treatment planning will expose to users.
    """
    normalized_volume = _normalize_water_volume(water_volume)

    concentrations_mg_per_liter = {
        concentration.ion: float(concentration.concentration.magnitude)
        for concentration in initial_state.concentrations
    }

    applied_treatments: list[AppliedTreatment] = []
    for addition in additions:
        contributions = calculate_ion_contributions(
            addition.ingredient,
            addition.mass,
            normalized_volume,
        )
        applied_treatments.append(
            AppliedTreatment(
                addition=addition,
                ion_contributions=contributions,
            )
        )

        for contribution in contributions:
            if contribution.ion in concentrations_mg_per_liter:
                concentrations_mg_per_liter[contribution.ion] += float(
                    contribution.concentration.magnitude
                )

    # Enum declaration order gives the derived state a stable ordering that is
    # independent of dict insertion details or the order in which treatments
    # happened to be supplied.
    final_concentrations = tuple(
        DerivedIonConcentration.mg_per_liter(
            ion,
            concentrations_mg_per_liter[ion],
        )
        for ion in Ion
        if ion in concentrations_mg_per_liter
    )

    return TreatmentApplicationResult(
        initial_state=initial_state,
        water_volume=normalized_volume,
        applied_treatments=tuple(applied_treatments),
        final_state=AqueousChemicalState(concentrations=final_concentrations),
    )
