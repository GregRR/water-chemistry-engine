# Consumer API

## Status

This document defines the supported package-root facade for Water Chemistry
Engine 0.5 development. Ordinary consumers should prefer imports from
`water_chemistry_engine` as documented here. Consumers remaining on an earlier
minor release should continue using their tested imports and pinned version
until they deliberately migrate.

### Important 0.4.1 behavior change

This maintenance release is intentionally stricter for carbonate-system inputs.
Applications upgrading from 0.4.0 may now observe these optimizer requests
returning `OptimizerInputSupportStatus.UNSUPPORTED` with no plans:

- a target containing `Ion.BICARBONATE` or `Ion.CARBONATE`, with diagnostic code
  `CARBONATE_SYSTEM_TARGET_UNSUPPORTED`;
- a permitted material that contributes bicarbonate or carbonate (including
  `SODIUM_BICARBONATE`), with diagnostic code
  `CARBONATE_SYSTEM_MATERIAL_UNSUPPORTED`; or
- a target containing total alkalinity, with diagnostic code
  `TARGET_ALKALINITY_UNSUPPORTED`.

This is a deliberate safety boundary, not an input-format error. Manual forward
calculations with sodium bicarbonate remain supported, but their bicarbonate
output is formal inventory accounting and carries a structured
`CARBONATE_SYSTEM_MODEL_LIMITATION` notice. Consumers should handle these
diagnostic and notice codes explicitly rather than assuming every 0.4.0
optimizer input remains admissible.

## Supported boundary

The package root exposes the supported deterministic forward-calculation and
bounded-optimization surface through its explicit `__all__`. It includes:

- `calculate_forward_water`, `ForwardWaterSource`, and the structured forward
  result and audit types needed to interpret source resolution, blending,
  treatment contributions, contribution matrices, and preparation
  instructions;
- `SourceWaterProfile`, `SourceResolutionPolicy`, `TargetWaterProfile`,
  `TargetProfileClassification`, `TargetProfileProvenance`, and the ion
  concentration/report forms required to build inputs without erasing ranges,
  bounds, `ND`, or the evidentiary meaning of a matchable profile;
- `Ion`, `TreatmentAddition`, and the supported simple mineral ingredients;
- target-comparison status/result types; and
- `ForwardCalculationNotice`, `ForwardNoticeCode`, and `ForwardNoticeLevel`
  for machine-readable assumptions and limitations; and
- `optimize_treatment` plus the complete optimizer request, material, status,
  diagnostic, solver-report, plan, and result graph.

More specialized modules remain importable during pre-1.0 development, but
their complete contents are not automatically part of the supported facade.
Applications should isolate any direct module-level imports that are not
exported from the package root.

The built-in treatment constants are idealized supported chemical identities
for this facade. They define formula/hydration-state stoichiometry; they do not
imply that an arbitrary commercial product has the same purity, assay, retained
moisture, physical form, or solution concentration. For example,
`CALCIUM_CHLORIDE_ANHYDROUS` means pure `CaCl2`, while
`CALCIUM_CHLORIDE_DIHYDRATE` means pure `CaCl2·2H2O`; neither means "calcium
chloride flakes" generically.

The current `TreatmentIngredient` and `IonStoichiometry` authoring types are
deliberately not root exports. Their present structure models ideal chemical
identity only and does not yet cover the composition/specification evidence,
material assay or concentration basis, density/reference temperature for
volume dosing, practical-use limits, and other requirements of the planned
reusable treatment-material contract. Release 0.4 instead exposes the narrow
`ExactMassDosedTreatmentMaterial` boundary for caller-named physical materials
that map exactly, mass for mass, to one of the supported built-in chemical
identities. Engine 0.5 also exposes exact and ranged mass-fraction material
types. They retain solid-versus-aqueous-solution form independently from the
chemical identity, and their fractions must be explicitly dimensionless (for
example, `Q_(80, "percent")`). An exact fraction can resolve a measured mass to
an ordinary `TreatmentAddition`; a ranged fraction returns active-chemical mass
bounds and cannot silently select a midpoint or produce an exact addition.
These types support mass dosing only. They do not infer density or permit
volume dosing. Their optional `composition_source` retains manufacturer,
standard, or other specification-document metadata without turning that source
into an assumed universal use limit.

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
  `IonContributionMatrixRow`, `IonContributionCalculationBasis`,
  `SourceContributionColumn`,
  `SourceContributionCell`, `SourceContributionCellStatus`,
  `TreatmentContributionColumn`, `TreatmentContributionCell`, and
  `TreatmentContributionCellStatus`;
- preparation-instruction interpretation: `WaterPreparationInstructions`,
  `BlendPreparationInstruction`, `SourceVolumeInstruction`, and
  `TreatmentPreparationInstruction`;
- source and target inputs: `SourceWaterProfile`, `SourceResolutionPolicy`,
  `TargetWaterProfile`, `TargetProfileClassification`, and
  `TargetProfileProvenance`;
- optimizer entry point and request: `optimize_treatment`, `OptimizerRequest`,
  `OptimizerSource`, `OptimizerMaterialConstraint`,
  `ExactMassDosedTreatmentMaterial`, and `OptimizerBlendPolicy`;
- optimizer results: `OptimizerResult`, `OptimizerPlan`,
  `OptimizerSourceVolume`, `OptimizerMaterialAddition`,
  `OptimizerSolverReport`, `OptimizerDiagnostic`, and
  `OptimizerDiagnosticCode`;
- optimizer interpretation: `OptimizerStrategy`,
  `OptimizerInputSupportStatus`, `OptimizerFeasibilityStatus`,
  `OptimizerTargetFitStatus`, and `OptimizerPracticalityStatus`;
- source reporting and provenance: `SourceDocumentMetadata`, `WaterIdentity`,
  `WaterType`, `PhysicalWaterSource`, `PhysicalSourceType`,
  `ObservationPeriod`, `ReportedResultContext`, `ResultCoverage`, `WaterStage`,
  `ReportedStatistic`, `ReportedStatisticKind`, `ReportedPH`,
  `ReportedDisinfectant`, `DisinfectantKind`, `Alkalinity`, `TotalHardness`,
  `TotalDissolvedSolids`, `Conductivity`, and `ReportingBasis`;
- shared scalar quantity typing: `ScalarQuantity`;
- ions and reported concentration forms: `Ion`, `IonConcentration`,
  `IonConcentrationRange`, `IonConcentrationUpperBound`,
  `IonConcentrationLowerBound`, `IonConcentrationNotDetected`,
  `IonConcentrationValue`, `ExactConcentrationEndpoint`,
  `UpperBoundConcentrationEndpoint`, `LowerBoundConcentrationEndpoint`,
  `NotDetectedConcentrationEndpoint`, and `ConcentrationRangeEndpoint`;
- treatment inputs: `TreatmentAddition`, `CALCIUM_CHLORIDE_ANHYDROUS`,
  `CALCIUM_CHLORIDE_DIHYDRATE`, `GYPSUM`, `EPSOM_SALT`, `SODIUM_CHLORIDE`,
  `SODIUM_BICARBONATE`, `POTASSIUM_CHLORIDE`, and
  `SIMPLE_MINERAL_INGREDIENTS`; plus
  `ExactMassDosedTreatmentMaterial`, `ExactMassFractionTreatmentMaterial`,
  `RangedMassFractionTreatmentMaterial`, `TreatmentMaterialForm`, and
  `TreatmentMaterialActiveMassRange` for physical mass-dosed materials;
- comparison interpretation: `TargetIonComparison`,
  `TargetIonComparisonStatus`, `TargetIonCalculationBasis`,
  `TargetIonClosenessStatus`,
  `TargetComparisonPolicy`, `TargetIonClosenessPolicy`,
  `UnsupportedTargetIonReason`, `TargetAlkalinityComparison`,
  `TargetAlkalinityComparisonStatus`,
  `TargetPHComparison`, `TargetPHComparisonStatus`,
  `TargetProfileComparison`, and `TargetProfileComparisonStatus`;
- modeled total alkalinity: `ModeledAlkalinity`,
  `AlkalinityModelLimitation`,
  `SourceAlkalinityResolution`, `ResolvedSourceAlkalinity`,
  `UnresolvedSourceAlkalinity`, `UnresolvedSourceAlkalinityReason`,
  `SourceAlkalinityResolutionMethod`, `SourceAlkalinityContribution`,
  `BlendedAlkalinityResult`, `TreatmentAlkalinityContribution`,
  `FinalAlkalinityResult`, `AlkalinityBalanceResult`, and
  `AlkalinityContributionMatrixRow`;
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

`ScalarQuantity` is the engine's supported annotation for a FermUnits quantity
whose magnitude is an `int`, `float`, `Decimal`, or `Fraction`. Consumers may
use it to type reported-value fields and return values without reproducing the
engine's scalar-magnitude policy or importing `quantity_types` directly.

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
        reported_average=PHValue(7.4),
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

## Automatic treatment optimizer example

This fixed-blend example asks the engine to select a practical gypsum dose in
whole 0.1 g increments. The batch-specific 2 g maximum is caller policy, not a
universal use or safety limit:

```python
from fermunits import Q_

from water_chemistry_engine import (
    GYPSUM,
    ExactMassDosedTreatmentMaterial,
    Ion,
    IonConcentration,
    IonConcentrationRange,
    OptimizerBlendPolicy,
    OptimizerMaterialConstraint,
    OptimizerRequest,
    OptimizerSource,
    SourceResolutionPolicy,
    SourceWaterProfile,
    TargetWaterProfile,
    optimize_treatment,
)

source = SourceWaterProfile(
    name="Source water",
    concentrations=(
        IonConcentration.mg_per_liter(Ion.CALCIUM, 0.0),
        IonConcentration.mg_per_liter(Ion.SULFATE, 0.0),
    ),
)
target = TargetWaterProfile(
    name="Calcium target",
    concentrations=(
        IonConcentrationRange.mg_per_liter(
            Ion.CALCIUM,
            minimum=23.27,
            maximum=23.29,
        ),
    ),
)
gypsum = ExactMassDosedTreatmentMaterial(
    key="gypsum",
    name="Gypsum",
    ingredient=GYPSUM,
    dose_increment=Q_(0.1, "gram"),
)
request = OptimizerRequest(
    total_volume=Q_(10, "liter"),
    sources=(
        OptimizerSource(
            source_profile=source,
            current_volume=Q_(10, "liter"),
            maximum_volume=Q_(10, "liter"),
        ),
    ),
    material_constraints=(
        OptimizerMaterialConstraint(
            material=gypsum,
            maximum_mass=Q_(2, "gram"),
        ),
    ),
    source_resolution_policy=SourceResolutionPolicy(
        allow_exact_range_midpoints=False,
    ),
    blend_policy=OptimizerBlendPolicy.FIXED,
    target_profile=target,
)

result = optimize_treatment(request)
plan = result.plans[0]

print(plan.material_additions[0].measured_mass)
print(plan.target_fit)
print(plan.calculation.final_state.concentration_for(Ion.CALCIUM))
```

The selected dose is `1.0 gram`. Every accepted plan contains ordinary source
volumes and treatment additions, and its nested forward calculation contains
the final water, signed target deviations, contribution matrix, preparation
instructions, and notices.

`FIXED` preserves the supplied source volumes. `PROPORTIONAL_DILUTION`
preserves the current ordinary-source proportions while optimizing the volume
of a separately supplied, characterized diluent. `SOURCE_VOLUMES` may vary each
permitted source from zero through its declared maximum while enforcing the
requested total volume. The optional no-dilution comparison is valid only for
`PROPORTIONAL_DILUTION`.

The first returned plan is the closest absolute mg/L solution with lower total
measured material mass as its tie-breaker. A second preferred plan appears only
when an equally close solution uses fewer treatment products. A requested,
operationally distinct no-dilution best-effort plan follows those candidates.
Consumers should use the structured strategy and diagnostic enums, not plan
position or English summaries alone, when implementing behavior.

A failure limited to an optional fewest-materials or requested no-dilution
candidate does not invalidate an already postvalidated primary plan. Such a
result remains feasible, retains its primary plans and primary solver report,
and includes a result-level `SOLVER_FAILED` or
`SOLVER_POSTVALIDATION_FAILED` diagnostic identifying the unavailable optional
candidate.

## 0.5 total-alkalinity calculation contract

Engine 0.4.1 preserves report-native source total alkalinity and accepts a
total-alkalinity target separately from bicarbonate and carbonate. Blend,
treatment, and final alkalinity remain `NOT_CALCULATED`, and working-water pH
remains `NOT_CALCULATED`. Consumers may build source/target entry and
presentation against that contract now, but must not calculate alkalinity,
carbonate species, or pH in the application layer.

Engine 0.5 now includes the first public slice of the named
`conservative_equivalent_alkalinity_v1` balance. It returns policy-controlled
source resolution, volume-weighted blending with unknown propagation,
per-source and reviewed per-treatment contributions, modeled final total
alkalinity, exact/range/bound target comparison with signed deviation, and a
contribution-matrix row. Exact, range, lower-bound, and upper-bound alkalinity
targets are supported; one-sided source reports remain unresolved rather than
being treated as exact values. Reported, modeled, and target alkalinity remain
conceptually distinct: `Alkalinity` preserves report/target values while
`ModeledAlkalinity` identifies calculated output and its model. Optimizer
admission is supported when every contributing source alkalinity is resolved
and the target supplies an exact, range, or one-sided alkalinity criterion.
When ion and alkalinity criteria are combined, the
`closest_absolute_mg_per_liter_v1` ranking includes ion deviations in mg/L and
total-alkalinity deviations in mg/L as CaCO3 in the same unweighted absolute-
deviation sum. This is an explicit ranking convenience, not a claim that ion
mass and equivalent-mass alkalinity deviations are scientifically
interchangeable.
`AlkalinityBalanceResult.limitations` supplies stable
`AlkalinityModelLimitation` codes for complete-dissolution, unmodeled-reaction,
precipitation/dissolution, carbonate-speciation, and working-water-pH limits.

Sodium bicarbonate may participate in optimization only when starting
alkalinity is resolved and the request contains an appropriate supported total-
alkalinity criterion. Its sodium contribution remains ordinary ion chemistry;
its one-equivalent-per-mole alkalinity rule is specific to the named model and
its complete-dissolution/no-reaction assumptions. Any retained bicarbonate
quantity remains formal carbonate inventory rather than a claim about final
equilibrium bicarbonate concentration. Bicarbonate and carbonate targets remain
unsupported optimizer inputs, and meeting an alkalinity target never implies
that a particular pH was achieved.

Every optimized rounded dose must be replayed through the ordinary forward
calculation so the engine—not the consumer—proves that the plan reproduces its
reported modeled final alkalinity.

This admission applies to fixed blends, proportional dilution, and bounded
source-volume selection. Unknown source or diluent alkalinity produces an
explicit indeterminate optimizer result rather than an assumed zero. A sodium-
bicarbonate material remains unsupported when no alkalinity criterion is
present, and bicarbonate/carbonate species targets remain unsupported.

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

### Carbonate-system repair in 0.4.1

Explicit source bicarbonate, carbonate, and total alkalinity remain separate.
The engine never converts total alkalinity to bicarbonate automatically.
Forward bicarbonate/carbonate values use formal linear inventory accounting and
carry `FORMAL_CARBONATE_INVENTORY` result metadata plus structured model-
limitation notices. A numerical carbonate-species target comparison is retained
only for reference reproducibility and makes the overall comparison
`INDETERMINATE`. A total-alkalinity target is preserved separately and reports
`NOT_CALCULATED`.

The 0.4.1 optimizer rejects bicarbonate and carbonate targets and rejects any
automatically selectable material that contributes those species. In
particular, sodium bicarbonate cannot be selected to satisfy a sodium target
while its unmodeled alkalinity effect is ignored. It remains supported for an
explicit manual `TreatmentAddition`; consumers must surface the returned
carbonate-system limitation.

Notices are part of a successful result and do not imply an exception. A
consumer should:

1. interpret `notice.code` for stable program behavior;
2. use `notice.level` to choose presentation severity;
3. retain the structured context fields when logging or persisting a result;
4. display or localize the message appropriately; and
5. tolerate additional notice codes in later compatible releases rather than
   assuming the current set is exhaustive.

## Migrating pH code from 0.2.0

Water Chemistry Engine 0.2.0 exposed float-based pH fields through its
module-level models. The 0.3 consumer contract uses FermUnits `PHValue` so
chemical pH cannot be confused with an ordinary dimensional quantity.

The `ReportedPH.exact()`, `.range()`, and `.average()` constructors remain
source-compatible and still accept finite numeric arguments:

```python
reported_ph = ReportedPH.exact(7.2)
```

The stored fields and `calculation_value` now return `PHValue`. Code that needs
the underlying numeric magnitude for display or an explicit serialization
adapter should read `.value` from that semantic object:

```python
numeric_ph = reported_ph.calculation_value.value
```

Direct `ReportedPH` field construction must wrap each pH value:

```python
from fermunits import PHValue

reported_ph = ReportedPH(value=PHValue(7.2))
```

`TargetWaterProfile.ph` has no numeric convenience constructor, so 0.2 code
must change from `ph=7.0` to `ph=PHValue(7.0)`:

```python
target = TargetWaterProfile(
    name="Example target",
    concentrations=(),
    ph=PHValue(7.0),
)
```

`PHValue` is not implicitly float-convertible or JSON-serializable. Consumers
should keep it semantic inside their domain boundary and perform deliberate
display or interchange adaptation at the application edge.

## Pre-1.0 compatibility expectations

The 0.4 package-root facade is the preferred consumer boundary, but the project
remains pre-1.0:

- patch releases in the 0.4 line will not intentionally remove or rename the
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

The 0.5 development source tree reports `0.5.0`; the current public release is
0.4.1. `__version__` is distribution identity, not a capability probe for an
arbitrary Git checkout. Consumers must not depend directly on `main`; use a
released, explicitly pinned distribution. An exact commit or built artifact may
be appropriate while testing unreleased work.
