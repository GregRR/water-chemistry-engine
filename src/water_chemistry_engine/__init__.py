"""Supported consumer API for the reusable Water Chemistry Engine.

The package root is the compatibility boundary for ordinary consumers.  More
specialized modules remain importable during the pre-1.0 development period,
but applications should prefer the names exported here for the deterministic
forward-calculation workflow.
"""

from water_chemistry_engine.blending import (
    BlendedSource,
    BlendIonContribution,
    BlendIonResolution,
    ResolvedBlendIon,
    UnresolvedBlendIon,
    UnresolvedBlendIonReason,
    WaterBlendResult,
)
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.concentrations import (
    ConcentrationRangeEndpoint,
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    IonConcentrationValue,
    LowerBoundConcentrationEndpoint,
    NotDetectedConcentrationEndpoint,
    UpperBoundConcentrationEndpoint,
)
from water_chemistry_engine.contribution_matrix import (
    IonContributionMatrixRow,
    SourceContributionCell,
    SourceContributionCellStatus,
    SourceContributionColumn,
    TreatmentContributionCell,
    TreatmentContributionCellStatus,
    TreatmentContributionColumn,
    WaterContributionMatrix,
)
from water_chemistry_engine.forward_calculator import (
    ForwardSourceResult,
    ForwardWaterCalculationResult,
    ForwardWaterSource,
    calculate_forward_water,
)
from water_chemistry_engine.forward_notices import (
    ForwardCalculationNotice,
    ForwardNoticeCode,
    ForwardNoticeLevel,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.preparation_instructions import (
    BlendPreparationInstruction,
    SourceVolumeInstruction,
    TreatmentPreparationInstruction,
    WaterPreparationInstructions,
)
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_values import SourceResolutionPolicy
from water_chemistry_engine.source_resolution import (
    ResolvedSourceIon,
    SourceIonResolution,
    SourceIonResolutionMethod,
    SourceProfileResolutionResult,
    UnresolvedSourceIon,
    UnresolvedSourceIonReason,
)
from water_chemistry_engine.target_comparison import (
    TargetIonComparison,
    TargetIonComparisonStatus,
    TargetPHComparison,
    TargetPHComparisonStatus,
    TargetProfileComparison,
    TargetProfileComparisonStatus,
    UnsupportedTargetIonReason,
)
from water_chemistry_engine.target_profiles import TargetWaterProfile
from water_chemistry_engine.treatment_application import (
    AppliedTreatment,
    ResolvedTreatmentIon,
    TreatmentAddition,
    TreatmentApplicationResult,
    TreatmentIonContribution,
    TreatmentIonResolution,
    UnresolvedTreatmentIon,
    UnresolvedTreatmentIonReason,
)
from water_chemistry_engine.treatment_ingredients import (
    CALCIUM_CHLORIDE_DIHYDRATE,
    EPSOM_SALT,
    GYPSUM,
    POTASSIUM_CHLORIDE,
    SIMPLE_MINERAL_INGREDIENTS,
    SODIUM_BICARBONATE,
    SODIUM_CHLORIDE,
)
from water_chemistry_engine.treatment_stoichiometry import IonContribution

__version__ = "0.2.0"

__all__ = [
    "CALCIUM_CHLORIDE_DIHYDRATE",
    "EPSOM_SALT",
    "GYPSUM",
    "POTASSIUM_CHLORIDE",
    "SIMPLE_MINERAL_INGREDIENTS",
    "SODIUM_BICARBONATE",
    "SODIUM_CHLORIDE",
    "AppliedTreatment",
    "AqueousChemicalState",
    "BlendIonContribution",
    "BlendIonResolution",
    "BlendPreparationInstruction",
    "BlendedSource",
    "ConcentrationRangeEndpoint",
    "DerivedIonConcentration",
    "ExactConcentrationEndpoint",
    "ForwardCalculationNotice",
    "ForwardNoticeCode",
    "ForwardNoticeLevel",
    "ForwardSourceResult",
    "ForwardWaterCalculationResult",
    "ForwardWaterSource",
    "Ion",
    "IonConcentration",
    "IonConcentrationLowerBound",
    "IonConcentrationNotDetected",
    "IonConcentrationRange",
    "IonConcentrationUpperBound",
    "IonConcentrationValue",
    "IonContribution",
    "IonContributionMatrixRow",
    "LowerBoundConcentrationEndpoint",
    "NotDetectedConcentrationEndpoint",
    "ResolvedBlendIon",
    "ResolvedSourceIon",
    "ResolvedTreatmentIon",
    "SourceContributionCell",
    "SourceContributionCellStatus",
    "SourceContributionColumn",
    "SourceIonResolution",
    "SourceIonResolutionMethod",
    "SourceProfileResolutionResult",
    "SourceResolutionPolicy",
    "SourceVolumeInstruction",
    "SourceWaterProfile",
    "TargetIonComparison",
    "TargetIonComparisonStatus",
    "TargetPHComparison",
    "TargetPHComparisonStatus",
    "TargetProfileComparison",
    "TargetProfileComparisonStatus",
    "TargetWaterProfile",
    "TreatmentAddition",
    "TreatmentApplicationResult",
    "TreatmentContributionCell",
    "TreatmentContributionCellStatus",
    "TreatmentContributionColumn",
    "TreatmentIonContribution",
    "TreatmentIonResolution",
    "TreatmentPreparationInstruction",
    "UnresolvedBlendIon",
    "UnresolvedBlendIonReason",
    "UnresolvedSourceIon",
    "UnresolvedSourceIonReason",
    "UnresolvedTreatmentIon",
    "UnresolvedTreatmentIonReason",
    "UnsupportedTargetIonReason",
    "UpperBoundConcentrationEndpoint",
    "WaterBlendResult",
    "WaterContributionMatrix",
    "WaterPreparationInstructions",
    "__version__",
    "calculate_forward_water",
]
