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
  result types;
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

The exact initial facade is:

- entry point and primary results: `calculate_forward_water`,
  `ForwardWaterSource`, `ForwardSourceResult`, and
  `ForwardWaterCalculationResult`;
- source and target inputs: `SourceWaterProfile`, `SourceResolutionPolicy`,
  and `TargetWaterProfile`;
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

FermUnits remains the dimensional boundary. Construct masses and volumes with
`fermunits.Q_`; the engine does not re-export the unit registry. Chemical pH
must not be represented as `Q_(value, "pH")`, because Pint may interpret that
symbol as picohenry. Reported pH and future calculated-pH contracts remain
separate from ordinary dimensional quantities.

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
```

The expected final calcium concentration is approximately
`65.81975 milligram / liter`, and the final target status is `satisfied`.
The positive gypsum addition also produces a
`treatment_complete_dissolution_model` assumption notice.

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
