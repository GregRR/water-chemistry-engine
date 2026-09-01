# Consumer API

## Status

The supported package-root facade described here is under development for
Water Chemistry Engine 0.3.0. It is available from the current source tree but
is not part of the published 0.2.0 distribution.

Released 0.2.x consumers should continue using their tested module-level
imports and pinning the engine version. Once 0.3.0 is released, ordinary
consumers should prefer imports from `water_chemistry_engine` as documented
here.

## Supported boundary

The package root exposes the supported deterministic forward-calculation
surface through its explicit `__all__`. It includes:

- `calculate_forward_water`, `ForwardWaterSource`, and the structured forward
  result and audit types needed to interpret source resolution, blending,
  treatment contributions, contribution matrices, and preparation
  instructions;
- `SourceWaterProfile`, `SourceResolutionPolicy`, `TargetWaterProfile`, and
  the ion concentration/report forms required to build inputs without erasing
  ranges, bounds, or `ND`;
- `Ion`, `TreatmentAddition`, and the supported simple mineral ingredients;
- target-comparison status/result types; and
- `ForwardCalculationNotice`, `ForwardNoticeCode`, and `ForwardNoticeLevel`
  for machine-readable assumptions and limitations.

More specialized modules remain importable during pre-1.0 development, but
their complete contents are not automatically part of the supported facade.
Applications should isolate any direct module-level imports that are not
exported from the package root.

The built-in treatment constants are the supported ingredient identities for
this facade. The current `TreatmentIngredient` and `IonStoichiometry` authoring
types are deliberately not root exports: their present structure does not yet
cover the composition evidence, purity, use limits, and other requirements of
the planned reusable treatment-ingredient contract.

The facade also supports the complete source-report construction graph retained
by `SourceWaterProfile`: reported pH and disinfectants, source-document
metadata, water and physical-source identity, observation/result context,
reported statistics, alkalinity, hardness, TDS, and conductivity. Exporting
these representation types does not make them automatic forward-calculation
inputs. Only explicitly modeled ion concentrations currently enter source
resolution.

The exact initial facade is:

<!-- public-api-inventory-start -->

- entry point and primary results: `calculate_forward_water`,
  `ForwardWaterSource`, `ForwardSourceResult`, and
  `ForwardWaterCalculationResult`;
- derived calculation states: `AqueousChemicalState` and
  `DerivedIonConcentration`;
- source-resolution audit: `SourceProfileResolutionResult`,
  `SourceIonResolution`, `ResolvedSourceIon`, `UnresolvedSourceIon`,
  `SourceIonResolutionMethod`, and `UnresolvedSourceIonReason`;
- fixed-blend audit: `WaterBlendResult`, `BlendedSource`,
  `BlendIonResolution`, `ResolvedBlendIon`, `UnresolvedBlendIon`,
  `BlendIonContribution`, and `UnresolvedBlendIonReason`;
- treatment audit: `TreatmentApplicationResult`, `AppliedTreatment`,
  `TreatmentIonResolution`, `ResolvedTreatmentIon`,
  `UnresolvedTreatmentIon`, `TreatmentIonContribution`, `IonContribution`,
  and `UnresolvedTreatmentIonReason`;
- contribution-matrix interpretation: `WaterContributionMatrix`,
  `IonContributionMatrixRow`, `SourceContributionColumn`,
  `SourceContributionCell`, `SourceContributionCellStatus`,
  `TreatmentContributionColumn`, `TreatmentContributionCell`, and
  `TreatmentContributionCellStatus`;
- preparation-instruction interpretation: `WaterPreparationInstructions`,
  `BlendPreparationInstruction`, `SourceVolumeInstruction`, and
  `TreatmentPreparationInstruction`;
- source and target inputs: `SourceWaterProfile`, `SourceResolutionPolicy`,
  and `TargetWaterProfile`;
- source reporting and provenance: `SourceDocumentMetadata`, `WaterIdentity`,
  `WaterType`, `PhysicalWaterSource`, `PhysicalSourceType`,
  `ObservationPeriod`, `ReportedResultContext`, `ResultCoverage`, `WaterStage`,
  `ReportedStatistic`, `ReportedStatisticKind`, `ReportedPH`,
  `ReportedDisinfectant`, `DisinfectantKind`, `Alkalinity`, `TotalHardness`,
  `TotalDissolvedSolids`, `Conductivity`, and `ReportingBasis`;
- ions and reported concentration forms: `Ion`, `IonConcentration`,
  `IonConcentrationRange`, `IonConcentrationUpperBound`,
  `IonConcentrationLowerBound`, `IonConcentrationNotDetected`,
  `IonConcentrationValue`, `ExactConcentrationEndpoint`,
  `UpperBoundConcentrationEndpoint`, `LowerBoundConcentrationEndpoint`,
  `NotDetectedConcentrationEndpoint`, and `ConcentrationRangeEndpoint`;
- treatment inputs: `TreatmentAddition`, `CALCIUM_CHLORIDE_DIHYDRATE`,
  `GYPSUM`, `EPSOM_SALT`, `SODIUM_CHLORIDE`, `SODIUM_BICARBONATE`,
  `POTASSIUM_CHLORIDE`, and `SIMPLE_MINERAL_INGREDIENTS`;
- comparison interpretation: `TargetIonComparison`,
  `TargetIonComparisonStatus`, `UnsupportedTargetIonReason`,
  `TargetPHComparison`, `TargetPHComparisonStatus`,
  `TargetProfileComparison`, and `TargetProfileComparisonStatus`;
- notice interpretation: `ForwardCalculationNotice`, `ForwardNoticeCode`, and
  `ForwardNoticeLevel`; and
- package identity: `__version__`.

<!-- public-api-inventory-end -->

FermUnits remains the measurement boundary. Construct masses and volumes with
`fermunits.Q_`; the engine does not re-export the unit registry. Construct
target pH and direct `ReportedPH` fields with `fermunits.PHValue`. The
`ReportedPH.exact()`, `.range()`, and `.average()` helpers accept finite numeric
values and normalize them to `PHValue`.

Chemical pH must not be represented as `Q_(value, "pH")`, because Pint may
interpret that symbol as picohenry. `PHValue` deliberately permits any finite
pH rather than imposing a universal 0-through-14 restriction. This
representation change does not add calculated working-water pH: target pH
comparison remains explicitly `NOT_CALCULATED` until a validated reusable
aqueous model exists.

The engine imports both quantity construction and the public `Quantity` type
through FermUnits 0.1.3 or later. Pint remains FermUnits' physical-unit engine
and is installed transitively; ordinary engine consumers do not need a direct
Pint dependency merely to use the quantities returned by this API.

## Source reporting and provenance example

This example preserves source identity, report provenance, result context,
reported pH, alkalinity, and total chlorine without treating the supporting
properties as calculated ions:

```python
from datetime import date

from fermunits import PHValue, Q_

from water_chemistry_engine import (
    Alkalinity,
    DisinfectantKind,
    Ion,
    IonConcentration,
    ObservationPeriod,
    PhysicalSourceType,
    PhysicalWaterSource,
    ReportedDisinfectant,
    ReportedPH,
    ReportedResultContext,
    ResultCoverage,
    SourceDocumentMetadata,
    SourceWaterProfile,
    WaterIdentity,
    WaterStage,
    WaterType,
)

period = ObservationPeriod(
    start=date(2025, 1, 1),
    end=date(2025, 12, 31),
)
context = ReportedResultContext(
    observation_period=period,
    coverage=ResultCoverage.OBSERVATION_PERIOD_SUMMARY,
    water_stage=WaterStage.TREATMENT_PLANT_OUTPUT,
    sample_location="Example Treatment Plant",
)

source = SourceWaterProfile(
    name="Example Municipal Water",
    concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 42.0),),
    ph=ReportedPH(
        minimum=PHValue(7.2),
        maximum=PHValue(7.8),
        reported_average=PHValue(7.5),
        result_context=context,
    ),
    observation_period=period,
    identity=WaterIdentity(
        provider="Example Water Utility",
        water_type=WaterType.MUNICIPAL_WATER,
        physical_sources=(
            PhysicalWaterSource(
                source_type=PhysicalSourceType.RESERVOIR,
                name="Example Reservoir",
            ),
        ),
    ),
    source_document=SourceDocumentMetadata(
        publisher="Example Water Utility",
        title="2025 Water Quality Report",
        source_url="https://example.com/water-report.pdf",
    ),
    alkalinity=Alkalinity(
        value=Q_(105.0, "milligram / liter"),
        result_context=context,
    ),
    disinfectants=(
        ReportedDisinfectant.mg_per_liter(
            DisinfectantKind.TOTAL_CHLORINE,
            0.5,
            result_context=context,
        ),
    ),
)
```

## Complete forward-calculation example

This example resolves two exact source profiles, blends equal volumes, applies
a supported gypsum addition, and compares the final state with a calcium
target:

```python
from fermunits import Q_

from water_chemistry_engine import (
    ForwardWaterSource,
    GYPSUM,
    Ion,
    IonConcentration,
    IonConcentrationRange,
    SourceResolutionPolicy,
    SourceWaterProfile,
    TargetWaterProfile,
    TreatmentAddition,
    calculate_forward_water,
)

source_a = SourceWaterProfile(
    name="Source A",
    concentrations=(
        IonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),
        IonConcentration.mg_per_liter(Ion.SULFATE, 20.0),
    ),
)
source_b = SourceWaterProfile(
    name="Source B",
    concentrations=(
        IonConcentration.mg_per_liter(Ion.CALCIUM, 80.0),
        IonConcentration.mg_per_liter(Ion.SULFATE, 40.0),
    ),
)
target = TargetWaterProfile(
    name="Calcium target",
    concentrations=(
        IonConcentrationRange.mg_per_liter(
            Ion.CALCIUM,
            minimum=65.0,
            maximum=75.0,
        ),
    ),
)

result = calculate_forward_water(
    (
        ForwardWaterSource(source_a, Q_(10, "liter")),
        ForwardWaterSource(source_b, Q_(10, "liter")),
    ),
    source_resolution_policy=SourceResolutionPolicy(
        allow_exact_range_midpoints=False,
    ),
    treatment_additions=(TreatmentAddition(GYPSUM, Q_(0.5, "gram")),),
    target_profile=target,
)

calcium = result.final_state.concentration_for(Ion.CALCIUM)
assert calcium is not None
print(calcium)
print(result.final_target_comparison.status)

for notice in result.notices:
    print(notice.level, notice.code, notice.message)

calcium_row = result.contribution_matrix.row_for(Ion.CALCIUM)
print(calcium_row.known_source_contribution_sum)
print(calcium_row.known_treatment_contribution_sum)

for line in result.preparation_instructions.lines:
    print(line)
```

The expected final calcium concentration is approximately
`65.81975 milligram / liter`, and the final target status is `satisfied`.
The positive gypsum addition also produces a
`treatment_complete_dissolution_model` assumption notice.

The result graph is intended to be consumed through the same facade. For
example, callers can use `isinstance` with `ResolvedSourceIon` versus
`UnresolvedSourceIon`, `ResolvedBlendIon` versus `UnresolvedBlendIon`, and
`ResolvedTreatmentIon` versus `UnresolvedTreatmentIon` without importing their
defining modules. The corresponding reason and method enums are also root
exports. Contribution-cell status enums provide the same explicit
interpretation boundary for presentation code.

## Validation, unknowns, and notices

Invalid request objects fail at their construction or calculation boundary
with an actionable `ValueError` or `TypeError`. Examples include an empty
profile name, incompatible units, negative or non-finite concentrations,
negative or non-finite treatment mass, and an empty source tuple. Consumers
should present these as invalid input rather than as a calculation result.

Missing, bounded, `ND`, or otherwise unresolved chemistry is different from
invalid input. The calculation normally succeeds while preserving that ion as
unknown. Target comparison may therefore be `indeterminate`, and the result
contains structured notices explaining relevant unresolved inputs and
limitations. Consumers must not replace those unknown values with zero.

Notices are part of a successful result and do not imply an exception. A
consumer should:

1. interpret `notice.code` for stable program behavior;
2. use `notice.level` to choose presentation severity;
3. retain the structured context fields when logging or persisting a result;
4. display or localize the message appropriately; and
5. tolerate additional notice codes in later compatible releases rather than
   assuming the current set is exhaustive.

## Pre-1.0 compatibility expectations

The 0.3 package-root facade is the preferred consumer boundary, but the project
remains pre-1.0:

- patch releases in the 0.3 line will not intentionally remove or rename the
  documented root imports;
- correctness fixes may change scientifically incorrect output and will be
  documented;
- later minor releases may evolve request/result structures, with changelog
  and migration guidance and deprecation where practical;
- consumers should construct dataclasses and call functions with keyword
  arguments where supported rather than depending on positional field order;
- consumers should not serialize dataclass internals or assume enum/notice sets
  are closed; and
- applications should pin and test the engine version range they deploy.

The facade remains framework-neutral. It returns Python domain objects and
FermUnits/Pint quantities, never HTML, ORM records, database handles, or
product-specific persistence state.

During development, the source tree continues to report the most recently
released distribution version, currently `0.2.0`. The project changes version
metadata only at its deliberate release-version gate. Therefore `__version__`
is distribution identity, not a capability probe for an unreleased Git
checkout. Consumers must not depend directly on `main`; use a released,
explicitly pinned distribution or an exact commit while testing unreleased
work.
