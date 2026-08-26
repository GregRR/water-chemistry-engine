# Water Treatment Calculator Roadmap

This roadmap prioritizes useful product increments while preserving the project's
scientific and architectural contracts. Release contents may change as research,
validation, and implementation reveal new requirements.

The immediate product goal is a genuinely usable web application. Advanced
optimization, interchange adapters, report ingestion, and deeper domain-specific
science should not block the first complete source-to-result workflow.

## Current state

The repository already has the core source-report semantics and the beginning of
deterministic treatment calculations needed for the next product increment.
Implemented foundations include:

- source-water and target-water domain models;
- `SourceDocumentMetadata` and `SourceWaterProfile.source_document`;
- physical water identity and result/sampling context kept separate from document metadata;
- exact, ranged, bounded, qualified, `ND`, and named reported-statistic semantics;
- logarithmically correct reported-pH handling with no arithmetic midpoint/mean behavior;
- alkalinity and hardness reporting bases;
- chlorine/chloramine preservation distinct from chloride;
- real municipal/bottled-water report fixtures;
- validated simple treatment-ingredient identities and hydration states;
- generic stoichiometric ion contributions;
- exact derived aqueous ion states;
- forward application of one or more supported mineral additions while preserving unknown values as unknown;
- explicit source-profile resolution into calculation-ready ion states, with exact-range midpoints allowed only by a caller-supplied policy and unresolved values preserved as unknown;
- fixed volume- or fraction-based blending of one or more derived source states, with actual volumes/fractions and per-source ion contributions preserved and unknown source concentrations propagated as unknown.

The current implementation focus is target/reference comparison and the remaining deterministic forward path.

## 0.2 — Deterministic Forward Calculator

Complete the reusable engine path needed to answer:

> Given this source water, this fixed blend, and these mineral additions, what
> water did I make and how does it compare with my target?

### Required work

- Apply supported mineral additions to the blended state.
- Produce explicit blended-water and final treated-water states.
- Compare source/blend/final states with exact or ranged targets.
- Produce contribution detail spanning source waters and treatment ingredients.
- Return structured treatment/result information suitable for a UI.
- Generate straightforward human-readable treatment instructions.
- Surface insufficient/unknown inputs explicitly rather than treating them as zero.

### Not required for 0.2

- automatic optimization;
- ranked treatment strategies;
- BeerJSON adapters;
- FermentationJSON adapters;
- AI-assisted report ingestion;
- recipe-aware mash pH;
- a generalized non-additive treatment-operation framework.

Calculated working-water pH is also not a blocker for this milestone. Reported
pH remains visible exactly as reported, and derived pH remains unknown until a
validated reusable aqueous model has sufficient inputs.

## 0.3 — First Usable Web Application

Build the smallest complete web interface around the deterministic forward
calculator. This is the earliest milestone intended for routine real-world use.

### User workflow

1. Enter a source-water profile or select a built-in profile.
2. Select or enter a target/reference profile.
3. See source-versus-target differences.
4. Optionally blend with RO, distilled, or another characterized source.
5. Enter supported mineral additions.
6. See what each source and treatment contributes.
7. See the resulting water profile and remaining target deviations.
8. Receive clear treatment/blending instructions.

### Required interface capabilities

- Responsive server-rendered web interface with HTMX where useful.
- Manual source-water entry.
- Built-in RO/distilled profiles and a small validated source/reference set.
- Target/reference selection and user-entered targets.
- Fixed blend amounts.
- Supported mineral-addition rows.
- Batch volume and explicit unit controls.
- Source, blend, result, and target comparison tables.
- Treatment instructions and contribution details.
- Clear display of unknown, unavailable, and not-calculated values.
- No account required for basic calculations.

The first usable UI does not wait for automatic optimization, interchange
adapters, or AI report ingestion.

## 0.4 — Curated Target and Reference Profiles

Expand the useful profile library after the first working UI without requiring
complete coffee-, tea-, bread-, or pizza-specific calculation engines.

### Generic profile/data work

Add enough generic metadata to distinguish the evidentiary meaning of matchable
profiles. The representation should be able to distinguish concepts such as:

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
- Published specialty-coffee standards and well-supported coffee-water targets/references.
- Tea target/reference profiles when defensible data exist.
- Regional-reference dough waters such as documented New York City water.
- Measured or otherwise well-supported bakery/pizzeria point-of-use waters.
- Published experimental bread/pizza water profiles where the study actually reports the water used.

Do not:

- turn a regional water analysis into an "optimal" bread/pizza profile;
- average conflicting historical profiles into a manufactured canonical profile;
- turn a mechanistic coffee paper into a universal optimum it did not establish.

Some standards include properties beyond the current ion target model, such as
TDS, hardness, alkalinity, chlorine, odor, or color. Add generic target-property
semantics only where the requirement is concrete and scientifically clear; do
not build a universal sensory-property framework merely to make every historic
standard field machine-optimizable immediately.

## 0.5 — First Automatic Treatment Optimizer

After the manual calculator is useful, let the engine answer:

> What practical blend and supported additions should I use?

### Initial optimizer scope

- Continuous closest-match blending and mineral additions.
- Source availability and maximum-volume constraints.
- User-permitted water sources and treatment ingredients.
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
- user-selected products only;
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
- retain model/version, assumptions, relevant temperature/reference conditions, and warnings.

This milestone is working-water pH only, not recipe-aware mash-pH prediction.
If a sufficiently defensible model is not ready, Version 1 may continue to show
derived pH as unsupported/unknown rather than ship a weak approximation.

## 0.8 — Interchange, Persistence, and 1.0 Hardening

Do the integration work that is useful once the web calculator itself works.

### Interchange

- BeerJSON 1.0 adapters for information BeerJSON can represent.
- Explicit structured loss reporting when richer internal semantics cannot be represented in BeerJSON.
- FermentationJSON adapters when the corresponding schemas are stable enough for dependable round trips.
- Cross-format/reference conformance tests.

BeerJSON and FermentationJSON are intentionally **after the first usable UI**.
They must not delay 0.3.

### Release hardening

- Versioned calculation-result contracts.
- Versioned bundled reference datasets.
- Saved local/user profiles and results where useful.
- Stable warning and explanation codes.
- Accessibility and responsive-layout review.
- Expanded reference and conformance vectors.
- Documentation of operating limits and unsupported calculations.
- Public API cleanup and compatibility review.

## 1.0 — Stable General-Purpose Water Treatment Application

Version 1.0 will provide a reusable, explainable water-treatment system and a
stable web application for supported brewing/fermentation uses, while remaining
generic enough for additional validated target/reference data.

A user can:

- characterize one or more source waters;
- select a supported target or reference profile;
- calculate a fixed blend;
- apply supported mineral additions;
- see source, blend, and final chemistry;
- compare results with the target/reference;
- obtain practical automatic treatment recommendations;
- compare useful ranked alternatives;
- understand contributions, assumptions, unknowns, compromises, and infeasibility;
- use versioned curated profile/reference data;
- perform the workflow through a responsive web application.

### Version 1 scientific/architectural invariants

- pH is logarithmic and is never arithmetic-averaged.
- Reported pH values/ranges remain exactly reported.
- A reported average pH is used only when the source actually reports it.
- Unknown measurements remain unknown; `ND` is not zero.
- Source/report provenance is first-class.
- `SourceDocumentMetadata` and `SourceWaterProfile.source_document` remain the document/report metadata contract.
- Physical source identity and sampling/result context remain separate from document metadata.
- Chlorine/chloramine remain distinct from chloride.
- Historical/regional profiles are not silently merged into canonical averages.
- Source, target/reference, derived calculation state, and measured treated-water result remain distinct concepts.
- The generic water engine contains no coffee-, tea-, bread-, or pizza-specific sensory assumptions.

## 1.1 — AI-Assisted Water-Report Ingestion

AI-assisted PDF/report ingestion is valuable but is a separate product workflow
and does not block the calculator or Version 1.0 chemistry.

Build a reviewable pipeline for municipal, bottled-water, and laboratory reports:

```text
report/document
    -> extraction
    -> candidate measurements and metadata
    -> unit/basis/statistic/context interpretation
    -> ambiguity/confidence reporting
    -> user review/correction
    -> deterministic validation
    -> SourceWaterProfile
```

The ingestion workflow must preserve the existing source-report contracts,
including ranges, qualifiers, `ND`, dates/periods, named statistics, pH semantics,
chlorine/chloramine, alkalinity/hardness basis, water identity, sampling/result
context, and document provenance. It must never silently merge distinct sources,
locations, reporting periods, or treatment stages.

Document parsing and AI extraction remain outside `water-treatment-engine`.

## 1.2 — Purpose-Aware Water Guidance

Add purpose-aware evaluation where validated without mutating source-water
identity. Candidate early contexts include mash liquor and sparge liquor, then
other materially distinct brewery/process uses as evidence supports them.

- Carry intended water use as calculation/request context.
- Explain relevant limits, warnings, and treatment implications for that use.
- Reuse only already validated treatment capabilities.
- Keep this distinct from deeper recipe-aware mash-pH chemistry.

## Version 2.0 — Advanced Brewing-Water Chemistry

Add capabilities that require materially deeper scientific models or optimization:

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
- optional treatment-cost inputs;
- optional inventory integration;
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
suites. The project must not imply that one generic ion-matching score predicts
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

Longer-term ideas that are useful but would clutter the active release path are
retained in `docs/FUTURE_CAPABILITIES.md`. Moving an item there means
"preserved for later evaluation," not "rejected."

## Development principle

Prioritize complete user-visible increments. Preserve data and architecture now
when losing them would make later work scientifically or structurally harder,
but do not introduce large abstractions, interchange layers, predictive models,
or ingestion systems before a concrete product capability needs them.

Features must not be advertised until their calculations, operating ranges,
references, and validation tests are implemented and documented.
