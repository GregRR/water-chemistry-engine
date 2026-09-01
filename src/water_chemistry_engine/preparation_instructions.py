"""Structured, human-readable instructions for deterministic water preparation.

This module turns an already-calculated fixed blend and treatment result into
straightforward preparation instructions.  It does not recalculate chemistry or
change any source, blend, or treatment semantics.

Instruction quantities use stable canonical units (liters and grams) so every
caller receives deterministic text.  The structured quantities are retained
alongside that text so a UI can localize or reformat them without parsing prose.
Zero-volume sources and zero-mass additions are valid no-ops in the underlying
calculation, but they are omitted from actionable instructions.
"""

from dataclasses import dataclass

from fermunits import Q_, Quantity

from water_chemistry_engine._workflow_validation import (
    require_treatment_matches_blend,
)
from water_chemistry_engine.blending import WaterBlendResult
from water_chemistry_engine.treatment_application import (
    TreatmentAddition,
    TreatmentApplicationResult,
)


def _format_magnitude(value: float) -> str:
    """Format a canonical instruction magnitude without gratuitous float noise."""
    return format(value, ".12g")


def _format_liters(volume: Quantity[float]) -> str:
    liters = float(volume.to("liter").magnitude)
    return f"{_format_magnitude(liters)} L"


def _format_grams(mass: Quantity[float]) -> str:
    grams = float(mass.to("gram").magnitude)
    return f"{_format_magnitude(grams)} g"


@dataclass(frozen=True, slots=True)
class SourceVolumeInstruction:
    """One positive-volume source used in the actionable fixed blend."""

    source_index: int
    source_name: str
    volume: Quantity[float]
    fraction: float

    @property
    def text(self) -> str:
        """Return a standalone measurement instruction for this source."""
        return f"Measure {_format_liters(self.volume)} of {self.source_name}."


@dataclass(frozen=True, slots=True)
class BlendPreparationInstruction:
    """Actionable source-water blend instruction."""

    sources: tuple[SourceVolumeInstruction, ...]
    total_volume: Quantity[float]

    @property
    def text(self) -> str:
        """Return a concise human-readable description of the fixed blend."""
        if len(self.sources) == 1:
            source = self.sources[0]
            return (
                f"Use {_format_liters(source.volume)} of {source.source_name} "
                "as the starting water."
            )

        source_text = " + ".join(
            f"{_format_liters(source.volume)} of {source.source_name}"
            for source in self.sources
        )
        return (
            f"Combine {source_text} to make {_format_liters(self.total_volume)} "
            "of blended water."
        )


@dataclass(frozen=True, slots=True)
class TreatmentPreparationInstruction:
    """One positive-mass mineral addition in requested treatment order."""

    treatment_index: int
    addition: TreatmentAddition
    mass: Quantity[float]

    @property
    def text(self) -> str:
        """Return a concise human-readable mineral-addition instruction."""
        ingredient = self.addition.ingredient
        return (
            f"Add {_format_grams(self.mass)} of {ingredient.name} "
            f"({ingredient.formula})."
        )


@dataclass(frozen=True, slots=True)
class WaterPreparationInstructions:
    """Structured fixed-blend and treatment instructions for one calculation."""

    blend: BlendPreparationInstruction
    treatments: tuple[TreatmentPreparationInstruction, ...]

    @property
    def lines(self) -> tuple[str, ...]:
        """Return deterministic plain-text instructions in execution order."""
        return (self.blend.text,) + tuple(
            treatment.text for treatment in self.treatments
        )


def build_preparation_instructions(
    blend_result: WaterBlendResult,
    treatment_result: TreatmentApplicationResult,
) -> WaterPreparationInstructions:
    """Build actionable instructions from existing calculation-stage results.

    The supplied treatment must start from the supplied blend.  Positive-volume
    sources are retained in blend order.  Positive-mass treatments are retained
    in requested order.  Valid zero-volume and zero-mass no-ops remain present in
    the underlying audit results but are omitted from instructions because they
    require no physical action.
    """
    require_treatment_matches_blend(blend_result, treatment_result)

    source_instructions = tuple(
        SourceVolumeInstruction(
            source_index=source_index,
            source_name=source.name,
            volume=source.volume.to("liter"),
            fraction=source.fraction,
        )
        for source_index, source in enumerate(blend_result.sources)
        if source.fraction > 0.0
    )

    treatment_instructions = tuple(
        TreatmentPreparationInstruction(
            treatment_index=treatment_index,
            addition=applied_treatment.addition,
            mass=Q_(
                float(applied_treatment.addition.mass.to("gram").magnitude),
                "gram",
            ),
        )
        for treatment_index, applied_treatment in enumerate(
            treatment_result.applied_treatments
        )
        if float(applied_treatment.addition.mass.to("gram").magnitude) > 0.0
    )

    return WaterPreparationInstructions(
        blend=BlendPreparationInstruction(
            sources=source_instructions,
            total_volume=blend_result.total_volume.to("liter"),
        ),
        treatments=treatment_instructions,
    )
