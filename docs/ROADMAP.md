# Water Chemistry Engine Roadmap

This roadmap describes the reusable engine's development path. End-user web,
mobile, and other product roadmaps live in their own projects and may advance in
parallel against released or deliberately pinned pre-1.0 engine versions.

Application development is expected to inform this roadmap by exposing awkward
APIs, missing domain operations, and result-shape problems. When a need is
scientific or domain-specific, it belongs in this engine rather than in a
consumer application's presentation or persistence layer.

## Current state

Release 0.2 completes the deterministic source-to-result path needed by real
consumer applications. Implemented foundations include:

- source-water and target-water domain models;
- `SourceDocumentMetadata` and `SourceWaterProfile.source_document`;
- physical water identity and result/sampling context kept separate from
  document metadata;
- exact, ranged, bounded, qualified, `ND`, and named reported-statistic
  semantics;
- logarithmically correct reported-pH handling with no arithmetic midpoint/mean
  behavior;
- alkalinity and hardness reporting bases;
- chlorine/chloramine preservation distinct from chloride;
- real municipal/bottled-water report fixtures;
- validated simple treatment-ingredient identities and hydration states;
- generic stoichiometric ion contributions;
- exact derived aqueous ion states;
- forward application of supported mineral additions while preserving unknowns;
- explicit source-profile resolution under caller-supplied policy;
- fixed volume/fraction blending with source attribution and conservative
  unknown propagation;
- deterministic target/reference comparison;
- end-to-end forward orchestration through source resolution, blending,
  treatment, and comparison;
- combined source/treatment contribution matrices;
- structured preparation instructions;
- machine-readable notices for assumptions, unresolved inputs, model limits,
  target limitations, and deferred target-pH calculation;
- Python 3.11 through 3.14 support with 3.11 as the compatibility baseline.

The next engine milestone is a deliberate consumer-facing API boundary. The
existing 0.2 module APIs are already usable by pinned applications, but the
published 0.2 package root exports only `__version__`. Development for 0.3 now
exposes the important consumer operations through an intentional supported
surface while the full milestone remains in progress.

## 0.2 — Deterministic Forward Calculator

**Status: complete.**

The reusable engine answers:

> Given this source water, this fixed blend, and these mineral additions, what
> water did I make and how does it compare with my target?

### Completed work

- Apply supported mineral additions to the blended state.
- Produce explicit blended-water and final treated-water states.
- Compare source/blend/final states with exact or ranged targets.
- Produce contribution detail spanning source waters and treatment ingredients.
- Return structured treatment/result information for arbitrary consumers.
- Generate straightforward human-readable preparation instructions while
  retaining canonical quantities.
- Surface insufficient/unknown inputs explicitly rather than treating them as
  zero.
- Return structured notices for assumptions and result limitations.

### Deliberately not required for 0.2

- automatic optimization;
- ranked treatment strategies;
- BeerJSON adapters;
- FermentationJSON adapters;
- document/AI report extraction;
- recipe-aware mash pH;
- a generalized non-additive treatment-operation framework.

Calculated working-water pH is also not a blocker. Reported pH remains visible
exactly as reported, and derived pH remains unknown until a validated reusable
aqueous model has sufficient inputs.

## 0.3 — Supported Consumer API

**Status: in progress.**

Establish a bounded, documented Python facade around the capabilities already
proven in 0.2 rather than requiring applications to depend indefinitely on
internal module layout.

The first implementation slice establishes an explicit package-root export
contract, API-level integration tests, and `docs/CONSUMER_API.md`. It preserves
the existing scientific workflow rather than wrapping it in a second
calculation layer. Version and release metadata remain at 0.2.0 until the full
0.3 release gate is ready.

The first independent 0.3 review found that the initial facade returned rich
nested audit objects without exporting the types needed to interpret them. The
remediation expands the supported boundary across source resolution, blending,
treatment application, contribution matrices, and preparation instructions,
and adds consumer-level checks for those paths. This is API-completeness work;
it does not change the underlying calculations.

A focused external follow-up independently verified all four original findings
as closed at commit `c8518550b11487fe2ca6ab2b6840e3947666230c`, found no new
defect, and cleared this first consumer-facade checkpoint. The remaining 0.3
work below is deliberately separate from that reviewed result boundary.

The next bounded slice exposes the complete source-reporting and provenance
construction graph preserved by `SourceWaterProfile`. It also adopts FermUnits
`PHValue` for reported and target pH rather than publishing the earlier
unsupported universal 0-through-14 restriction as part of the consumer
contract. This is representation and validation work; calculated working-water
pH remains unsupported.

### Required work

- Define and document the supported top-level consumer imports for the current
  forward workflow.
- Keep request/result objects structured and framework-neutral.
- Provide concise integration examples for source creation, fixed blending,
  target comparison, and supported additions.
- Document validation/error and notice-handling expectations.
- Define compatibility expectations for pre-1.0 result/request evolution.
- Keep all dimensional inputs/outputs explicit through FermUnits/Pint.
- Add API-level tests so refactors cannot silently break the documented
  consumer surface.
- Keep the public source-input graph cohesive across reported pH,
  disinfectants, source documents, water identity, result context/statistics,
  and supporting reported properties.
- Replace the current built-in-only treatment-ingredient facade only after a
  reusable authoring contract includes composition evidence, purity, use
  limits, and the other requirements recorded in the design.
- Identify any convenience constructors/helpers justified by real application
  use without duplicating chemistry or hiding reported-data semantics.

Consumer applications do not need to wait for this milestone to begin. During
0.2/0.3 co-development they should isolate current module-level imports behind a
small adapter and pin a tested engine version.

## 0.4 — Curated Target and Reference Profiles

Expand the useful profile library without requiring complete coffee-, tea-,
bread-, or pizza-specific predictive engines.

### Generic profile/data work

Add enough generic metadata to distinguish the evidentiary meaning of matchable
profiles, including concepts such as:

- source water;
- treated point-of-use water;
- regional reference water;
- historical reference water;
- published standard;
- published recommendation;
- practitioner reference;
- experimental reference;
- experimentally/analytically optimized target;
- user target;
- previously achieved treated water.

A reference profile may be selectable as something to reproduce without being
presented as scientifically optimal.

### Near-term profile additions

- Curated brewing, mead, and distilling profiles with explicit provenance.
- Published specialty-coffee standards and well-supported coffee-water
  targets/references.
- Tea target/reference profiles when defensible data exist.
- Regional-reference dough waters such as documented New York City water.
- Measured or otherwise well-supported bakery/pizzeria point-of-use waters.
- Published experimental bread/pizza water profiles where the study actually
  reports the water used.

Do not:

- turn a regional water analysis into an "optimal" bread/pizza profile;
- average conflicting historical profiles into a manufactured canonical
  profile;
- turn a mechanistic coffee paper into a universal optimum it did not establish.

Some standards include properties beyond the current ion target model, such as
TDS, hardness, alkalinity, chlorine, odor, or color. Add generic target-property
semantics only where the requirement is concrete and scientifically clear; do
not build a universal sensory-property framework merely to make every historic
standard field machine-optimizable immediately.

## 0.5 — First Automatic Treatment Optimizer

Let the engine answer:

> What practical blend and supported additions should I use?

### Initial optimizer scope

- Continuous closest-match blending and mineral additions.
- Source availability and maximum-volume constraints.
- Caller-permitted water sources and treatment ingredients.
- Hard target constraints where supported.
- Explicit infeasibility and compromise diagnostics.
- Practical dose rounding followed by full recalculation.
- A structured recommended treatment plan.

Do not require every future ranking policy before the first optimizer is useful.

## 0.6 — Ranked Practical Treatment Strategies

Expand optimization to provide materially distinct plans and explain tradeoffs.
Candidate policies include:

- closest practical match;
- water-only blend;
- no-dilution treatment;
- least dilution/RO water;
- lowest total mineral addition;
- fewest treatment products;
- caller-selected products only;
- other policies only after their objectives and constraints are documented.

Add mixed-integer optimization only when a concrete policy requires it. Continue
to recalculate chemistry after operational rounding and report whether a plan is
exact, within all target ranges, closest feasible, impractical, infeasible, or
indeterminate.

## 0.7 — Reusable Working-Water pH and Richer Diagnostics

Add a validated state-based aqueous pH capability when the scientific model,
minimum-input contract, reference cases, and limits are established.

Conceptually:

```text
calculate_ph(chemical_state)
```

The same capability may evaluate source, blended, or final treated-water states.
It must:

- never overwrite `ReportedPH`;
- never arithmetic-average pH;
- return insufficient-data status instead of guessing;
- retain model/version, assumptions, relevant temperature/reference conditions,
  and warnings.

The semantic representation prerequisite is complete: FermUnits 0.1.3 is in
the supported dependency range, and reported and target pH use its finite
`PHValue` rather than an artificial universal 0-through-14 range. Before or as
part of calculated working-water pH:

- never represent chemical pH as `Q_(value, "pH")`, because FermUnits will not
  redefine Pint's existing interpretation of that symbol as picohenry;
- keep activity-coefficient selection, concentration/activity conversion,
  equilibria, ionic strength, and all prediction policy in this engine.

This milestone is working-water pH only, not recipe-aware mash-pH prediction.
If a sufficiently defensible model is not ready, Version 1 may continue to
return derived pH as unsupported/unknown rather than ship a weak approximation.

## 0.8 — Interchange, Conformance, and 1.0 Hardening

### Interchange

- BeerJSON 1.0 adapters for information BeerJSON can represent.
- Explicit structured loss reporting when richer internal semantics cannot be
  represented in BeerJSON.
- FermentationJSON adapters when the corresponding schemas are stable enough
  for dependable round trips.
- Cross-format/reference conformance tests.

### Release hardening

- Versioned calculation-result contracts.
- Versioned bundled reference datasets.
- Stable warning and explanation codes.
- Expanded reference and cross-platform conformance vectors.
- Documentation of operating limits and unsupported calculations.
- Public API cleanup and compatibility review.
- Extend property-based invariants to forward orchestration, notices, and
  preparation instructions where they materially improve coverage.

## 1.0 — Stable General-Purpose Water Chemistry Engine

Version 1.0 will provide a reusable, explainable, stable engine for supported
brewing/fermentation water-treatment workflows while remaining generic enough
for additional validated target/reference data and consumer products.

A consumer can:

- characterize one or more source waters;
- select or construct a supported target/reference profile;
- calculate a fixed blend;
- apply supported mineral additions;
- inspect source, blend, and final chemistry;
- compare results with a target/reference;
- obtain practical automatic treatment recommendations;
- compare useful ranked alternatives;
- inspect contributions, assumptions, unknowns, compromises, and infeasibility;
- use versioned curated profile/reference data;
- integrate through documented stable Python/request-result contracts.

### Version 1 scientific/architectural invariants

- pH is logarithmic and is never arithmetic-averaged.
- Reported pH values/ranges remain exactly reported.
- A reported average pH is used only when the source actually reports it.
- Unknown measurements remain unknown; `ND` is not zero.
- Source/report provenance is first-class.
- `SourceDocumentMetadata` and `SourceWaterProfile.source_document` remain the
  document/report metadata contract.
- Physical source identity and sampling/result context remain separate from
  document metadata.
- Chlorine/chloramine remain distinct from chloride.
- Historical/regional profiles are not silently merged into canonical averages.
- Source, target/reference, derived calculation state, and measured treated-water
  result remain distinct concepts.
- The generic water core contains no coffee-, tea-, bread-, or pizza-specific
  sensory assumptions.
- Critical scientific/domain rules live in the engine, not in consumer
  applications.

## 1.1 — Purpose-Aware Water Guidance

Add purpose-aware evaluation where validated without mutating source-water
identity. Candidate early contexts include mash liquor and sparge liquor, then
other materially distinct brewery/process uses as evidence supports them.

- Carry intended water use as calculation/request context.
- Return relevant limits, warnings, and treatment implications for that use.
- Reuse only already validated treatment capabilities.
- Keep this distinct from deeper recipe-aware mash-pH chemistry.

## Version 2.0 — Advanced Brewing-Water Chemistry

Add capabilities that require materially deeper scientific models or
optimization:

- acid additions;
- alkali additions;
- alkalinity neutralization;
- recipe-aware separate mash/sparge treatment;
- recipe-aware mash-pH prediction;
- deeper carbonate/bicarbonate chemistry;
- precipitation and solubility considerations where practical;
- uncertainty propagation;
- optimization using uncertain/ranged source reports;
- sensitivity and worst-case plans;
- Pareto-front exploration;
- optional caller-supplied treatment cost/availability constraints;
- expanded brewery-scale workflows.

Mash-pH prediction must distinguish predicted, calculated, and measured pH and
use versioned validated models.

## Version 3.0 — Domain-Specific Food and Beverage Models

Early cross-domain target/reference **data** does not require these modules.
Version 3 is reserved for genuinely new domain-specific predictive or guidance
models, such as:

- coffee extraction/sensory guidance;
- tea infusion/extraction guidance;
- bread, sourdough, and pizza-dough process models;
- alkaline noodles and kansui;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages.

These modules may share source-water composition, blending, provenance,
treatment, target/reference, and optimization infrastructure while retaining
their own scientific models, constituents, warnings, references, and validation
suites. The engine must not imply that one generic ion-matching score predicts
sensory quality across all foods and beverages.

A generalized non-additive `TreatmentOperation` abstraction may be introduced
when concrete validated workflows such as activated carbon, dechlorination,
reverse osmosis, ion exchange, softening, or deaeration demonstrate the needed
abstraction. Do not build it solely in anticipation of future domains.

## Version 4.0 — Selected Industrial Applications

Possible future modules may address selected non-food process-water uses only
after their safety, regulatory, materials-compatibility, treatment, and
validation requirements have been researched and documented.

## Preserved future work

Longer-term engine ideas that would clutter the active release path are retained
in `docs/FUTURE_CAPABILITIES.md`. Moving an item there means "preserved for
later evaluation," not "rejected."

## Development principle

Prioritize complete reusable engine capabilities and let real consumers pressure
test them early. Preserve data and architecture now when losing them would make
later work scientifically or structurally harder, but do not introduce large
abstractions, interchange layers, predictive models, or treatment frameworks
before a concrete capability needs them.

Features must not be advertised until their calculations, operating ranges,
references, and validation tests are implemented and documented.
