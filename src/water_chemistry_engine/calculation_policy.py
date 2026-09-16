"""Operation-specific scientific support boundaries for modeled ions.

Chemical identity does not imply that every calculation family can interpret a
species.  The current engine can preserve and formally account for carbonate-
system species, but it does not solve their aqueous equilibrium distribution.
"""

from dataclasses import dataclass

from water_chemistry_engine.ions import Ion


@dataclass(frozen=True, slots=True)
class IonCalculationCapabilities:
    """Scientific support granted to one ion for each calculation family."""

    reported_source: bool
    linear_blend: bool
    manual_treatment_contribution: bool
    ordinary_target_comparison: bool
    optimizer_target: bool
    optimizer_material_contribution: bool
    equilibrium_speciation: bool


_CONSERVATIVE_ION_CAPABILITIES = IonCalculationCapabilities(
    reported_source=True,
    linear_blend=True,
    manual_treatment_contribution=True,
    ordinary_target_comparison=True,
    optimizer_target=True,
    optimizer_material_contribution=True,
    equilibrium_speciation=False,
)

_CARBONATE_SYSTEM_CAPABILITIES = IonCalculationCapabilities(
    reported_source=True,
    linear_blend=True,
    manual_treatment_contribution=True,
    ordinary_target_comparison=False,
    optimizer_target=False,
    optimizer_material_contribution=False,
    equilibrium_speciation=False,
)

# Exhaustiveness is deliberate: a new Ion cannot silently become eligible for
# target comparison or optimization merely by joining the enum.
ION_CALCULATION_CAPABILITIES = {
    Ion.CALCIUM: _CONSERVATIVE_ION_CAPABILITIES,
    Ion.MAGNESIUM: _CONSERVATIVE_ION_CAPABILITIES,
    Ion.SODIUM: _CONSERVATIVE_ION_CAPABILITIES,
    Ion.POTASSIUM: _CONSERVATIVE_ION_CAPABILITIES,
    Ion.CHLORIDE: _CONSERVATIVE_ION_CAPABILITIES,
    Ion.SULFATE: _CONSERVATIVE_ION_CAPABILITIES,
    Ion.BICARBONATE: _CARBONATE_SYSTEM_CAPABILITIES,
    Ion.CARBONATE: _CARBONATE_SYSTEM_CAPABILITIES,
}

if frozenset(ION_CALCULATION_CAPABILITIES) != frozenset(Ion):
    raise RuntimeError("Every Ion requires an explicit calculation-capability policy.")


CARBONATE_SYSTEM_IONS = frozenset((Ion.BICARBONATE, Ion.CARBONATE))


def capabilities_for(ion: Ion) -> IonCalculationCapabilities:
    """Return the explicit operation-specific capabilities for ``ion``."""
    try:
        return ION_CALCULATION_CAPABILITIES[ion]
    except KeyError as exc:
        raise ValueError(f"Unsupported ion calculation policy: {ion!r}") from exc
