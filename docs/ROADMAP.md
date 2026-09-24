# Water Chemistry Engine Roadmap

This roadmap describes the reusable engine's development path. End-user web,
mobile, and other product roadmaps live in their own projects and may advance in
parallel against released or deliberately pinned pre-1.0 engine versions.

Application development is expected to inform this roadmap by exposing awkward
APIs, missing reusable chemistry operations, and result-shape problems. A
capability belongs in this engine when it is general water chemistry, treatment
mechanics, measurement semantics, or reusable validation/optimization logic.
Domain-specific interpretation and prediction belong in consumer applications
or separate domain libraries, even when they compose lower-level engine
primitives.

## Current state

Release 0.2 completed the deterministic source-to-result path needed by real
consumer applications. Release 0.3 added the supported package-root boundary
for consuming that path, and release 0.4 added the first bounded automatic
treatment optimizer and practical candidate plans. Implemented foundations
include:

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
- a supported package-root consumer facade with the complete input and result
  graph required for the forward workflow;
- API-level compatibility and integration tests;
- Python 3.11 through 3.14 support with 3.11 as the compatibility baseline.

Release 0.4 completes the first optimizer vertical slice. Its package-root
facade exposes the request, plan, diagnostic, solver-report, and exact
mass-dosed material graph through an intentional supported surface. Curated
profiles, broader treatment-material semantics, and richer target comparison
remain planned for 0.5.

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

**Status: complete.**

Establish a bounded, documented Python facade around the capabilities already
proven in 0.2 rather than requiring applications to depend indefinitely on
internal module layout.

The implementation establishes an explicit package-root export contract,
API-level integration tests, and `docs/CONSUMER_API.md`. It preserves the
existing scientific workflow rather than wrapping it in a second calculation
layer.

The first independent 0.3 review found that the initial facade returned rich
nested audit objects without exporting the types needed to interpret them. The
remediation expands the supported boundary across source resolution, blending,
treatment application, contribution matrices, and preparation instructions,
and adds consumer-level checks for those paths. This is API-completeness work;
it does not change the underlying calculations.

A focused external follow-up independently verified all four original findings
as closed at commit `c8518550b11487fe2ca6ab2b6840e3947666230c`, found no new
defect, and cleared this first consumer-facade checkpoint. The remaining 0.3
source-input work was deliberately reviewed as a separate boundary.

The second bounded slice exposes the complete source-reporting and provenance
construction graph preserved by `SourceWaterProfile`. It also adopts FermUnits
`PHValue` for reported and target pH rather than publishing the earlier
unsupported universal 0-through-14 restriction as part of the consumer
contract. This is representation and validation work; calculated working-water
pH remains unsupported.

Independent discovery and focused reviews found no scientific or runtime
defect in that slice. They identified two API-completeness/documentation gaps:
the public annotations used an unexported `ScalarQuantity` alias, and the
published 0.2.0 float-to-`PHValue` migration needed explicit guidance for both
`ReportedPH` and `TargetWaterProfile.ph`. The remediation exports the alias,
adds the migration guidance, and strengthens the pH example so its reported
average differs from the forbidden arithmetic midpoint.

A focused external follow-up independently verified both findings as closed at
commit `15ff61c36ae30b7a8d09aeaf168492e89f70f0eb`, found no new defect, and
cleared this source-reporting/provenance checkpoint. The same review also found
the subsequent treatment-material documentation scientifically accurate,
internally consistent, and correctly presented as future 0.4 work rather than
an implemented 0.3 capability.

### Completed work

- Defined and documented the supported top-level consumer imports for the current
  forward workflow.
- Kept request/result objects structured and framework-neutral.
- Provided concise integration examples for source creation, fixed blending,
  target comparison, and supported additions.
- Documented validation/error and notice-handling expectations.
- Defined compatibility expectations for pre-1.0 result/request evolution.
- Kept all dimensional inputs/outputs explicit through FermUnits/Pint.
- Added API-level tests so refactors cannot silently break the documented
  consumer surface.
- Kept the public source-input graph cohesive across reported pH,
  disinfectants, source documents, water identity, result context/statistics,
  and supporting reported properties.
- Kept the built-in-only treatment-ingredient facade narrow in 0.3; broader
  treatment authoring remains deferred until the reusable chemical-identity and
  treatment-material contracts are defined with composition evidence, assay or
  concentration semantics, use limits, and the other requirements recorded in
  the design.
- Established the rule that future convenience constructors/helpers must be
  justified by real application use without duplicating chemistry or hiding
  reported-data semantics.

Consumer applications should depend on and pin the 0.4.1 release rather than
depending on the engine repository. Pre-release integration may use an exact
commit or locally built artifact.

## 0.3.1 — FermUnits 1.0 Compatibility

**Status: complete.**

Adopt and verify FermUnits 1.0 without changing the Water Chemistry Engine's
scientific behavior or supported consumer contract. This patch release should:

- verify the dependency and lockfile against the published FermUnits 1.0
  artifacts;
- exercise the complete supported consumer API and representative calculations
  on Python 3.11 through 3.14;
- retain FermUnits as the engine's sole public unit boundary;
- document any compatibility qualification discovered during validation; and
- update release-workflow actions that otherwise rely on forced legacy Node.js
  execution.

## 0.4 — Automatic Treatment Optimizer and Practical Plans

**Status: complete.**

### 0.4.1 carbonate-system safety repair

Release 0.4.1 separates reported carbonate-system identity from calculation
eligibility. It preserves explicitly reported bicarbonate, carbonate, and total
alkalinity, retains manual sodium-bicarbonate formal accounting, and labels
linear bicarbonate/carbonate results as model-limited inventory. Automatic
optimization rejects bicarbonate/carbonate targets and materials that contribute
those species until a named, validated carbonate-system policy exists. Total-
alkalinity targets can be represented but remain explicitly not calculated.

Let the engine answer:

> Given my characterized sources, current blend, target, permitted treatments,
> and practical constraints, what useful treatment plans can I make?

This is a complete first vertical slice, not merely a solver that returns
unnamed numeric decision variables. It includes the minimum treatment-material
semantics required before the engine chooses measured doses for a user.

### Initial inputs and blend policies

- Total preparation volume, one or more characterized source waters, current
  source quantities, and optional target chemistry.
- Caller-permitted source waters and exact-composition, mass-dosed treatment
  materials.
- Source availability and maximum-volume constraints.
- An explicit blend policy that either preserves the current blend, preserves
  its source proportions while adding dilution water, or permits source-volume
  optimization. The engine must never silently change modes.
- An explicit ideal distilled/deionized-water profile when that documented
  model is selected. Real RO water should normally be supplied as a
  characterized source rather than silently assumed to contain zero of every
  analyte.
- Practical dose increments or rounding constraints supported by the engine.
- Existing manual mineral additions are not optimizer inputs in this release.

Unknown or unresolved source chemistry remains unknown. It must not become zero
merely to make an optimization problem solvable.

The initial request boundary now encodes all three blend-policy
identities, nonnegative current and positive maximum source volumes,
exact mass-dosed materials, and the source-resolution policy. Fixed-blend
requests require current source volumes
to equal the requested total. Proportional-dilution requests require an
explicit zero-current-volume diluent profile; neither ideal-zero chemistry nor
the identity of real RO water is inferred by the engine.
Every permitted material also requires a positive caller-declared maximum mass
for the batch that permits at least one whole declared dose increment. This is
an operational optimization bound, not a universal safety, sensory, solubility,
or regulatory limit.

The solver supports all three blend policies with the versioned
`closest_absolute_mg_per_liter_v1` strategy. It minimizes the
unweighted sum of absolute target deviations in canonical mg/L over whole
dose-increment counts and, for proportional dilution, one continuous diluent
volume while preserving the current non-diluent source proportions.
Source-volume optimization instead uses one bounded continuous decision per
caller-permitted source. The solver then
uses lower total measured material mass as a tie-breaker. This is an explicit
mathematical ranking policy, not a sensory or process-equivalence claim across
criteria. When a request combines ion and total-alkalinity criteria, the
unweighted sum includes ion deviations in mg/L and alkalinity deviations in
mg/L as CaCO3. This ranking convenience does not claim that one unit of ion
mass deviation and one unit of equivalent-mass alkalinity deviation are
scientifically interchangeable. Every accepted plan is recalculated through
the ordinary forward path.
An optionally requested no-dilution best-effort plan is independently solved
and returned only when operationally distinct; source limits that make it
impossible are reported explicitly. For source-volume optimization, all
selected volumes sum exactly to the requested total and every target ion must
be resolved independently for every candidate source. Sources remain
positionally distinct even when display names match.

The initial SciPy/HiGHS integration accepts at most 1,000,000 dose increments
per permitted material. Larger integer ranges are reported as unsupported and
are never silently coarsened. This conservative implementation limit is not a
scientific or operational recommendation. Coefficients and bounds outside the
backend's documented numerical range are likewise rejected rather than passed
through as if they were ordinary finite values. The engine independently
validates returned increment counts, reconstructs the primary objective from
those counts, retains the raw solver-reported objective for audit, and compares
its reconstruction with the ordinary forward result before returning a plan.

### Candidate plans and strategies

- Return up to two meaningfully different preferred plans when the supported
  problem admits useful alternatives, rather than numerically trivial variants
  of one recipe.
- Include a small, documented initial strategy set covering closest practical
  match and useful tradeoffs such as less dilution, fewer products, or lower
  total measured addition.
- Support an optionally requested no-dilution best-effort plan.
- Deduplicate operationally equivalent candidates and return deterministic
  results in deterministic order.
- Explain the principal tradeoff or constraint responsible for each candidate.

Do not require every future ranking policy or mixed-integer formulation before
this release is useful.

The implemented bounded strategy set returns the lower-total-mass member of the
closest absolute mg/L solutions first. When a second solution with the same
primary target-deviation optimum uses fewer treatment products, the engine
returns that operationally distinct candidate second and reports the product
count and measured-mass tradeoff. Binary product-use decisions are linked to
whole dose-increment counts, followed by a lower-mass tertiary solve; candidates
that do not actually reduce product count are discarded. An independently
requested no-dilution plan follows those preferred candidates and can therefore
make the result contain up to three plans. If its untreated blend already
exceeds a target maximum, structured diagnostics identify each unavoidable
overshoot and its deviation because the supported treatments are additive and
cannot reduce that starting concentration.

### Structured plan and diagnostics

Each plan should contain, through deliberate public domain types:

- stable strategy identity and result-local plan identity;
- proposed source-water quantities, including any explicit diluent;
- measured treatment-material additions and resolved active chemical amounts;
- calculated blend and final treated-water states;
- per-analyte target outcomes and signed deviations;
- contribution/audit data;
- input-support, feasibility, target-fit, and operational-practicality outcomes
  without collapsing those distinct concepts into one ambiguous status;
- explicit compromise and unavoidable-overshoot diagnostics;
- notices, assumptions, solver status/tolerances, and relevant model/policy
  versions; and
- ranking/summary information sufficient for a consumer to explain why the
  plan was offered.

An optimizer-generated addition must use the same treatment semantics as a
manual addition. Applying an accepted plan through the ordinary blending and
forward-treatment APIs after practical rounding must reproduce the plan's
reported final chemistry. An end-to-end test must enforce that invariant.

### Minimum treatment-material prerequisite

The first optimizer may be deliberately restricted to exact-composition,
mass-dosed materials whose measured dose resolves deterministically to an
active chemical amount. It must preserve the distinction between chemical
identity, including hydration state, and the physical material being dosed.

Ranged or unknown assay, unlabeled concentration percentages, unsupported
liquid-volume dosing, and materials without adequate composition evidence or
use-limit policy must be rejected or reported as unsupported rather than
silently approximated.

### Explicit 0.4 exclusions

- retaining existing manual additions as optimizer inputs;
- pH or mash-chemistry optimization;
- ranged-assay uncertainty optimization;
- arbitrary liquid-volume dosing without either an exact mass-per-volume basis
  or sufficient mass-fraction, density, and applicable-condition information;
- universal close/far or UI color thresholds;
- a large built-in target library;
- arbitrary non-additive treatment operations;
- product-specific persistence, reports, or UI behavior; and
- equilibrium-dependent chalk treatment.

## 0.5 — Total Alkalinity, Treatment Materials, Profiles, and Comparison Expansion

**Status: in progress.**

Expand the useful profile library and practical treatment-material model
without requiring complete coffee-, tea-, bread-, or pizza-specific predictive
engines. The first optimizer's exact-composition material slice expands here to
cover additional practical preparations and evidence-backed policies.

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

The initial 0.5 provenance boundary now supplies an explicit classification,
document attribution, and paired stable key/version for matchable profiles.
Unclassified targets remain unclassified rather than being silently treated as
user targets, and classifications that claim external evidence require an
attributed source document.
Source water remains structurally represented by `SourceWaterProfile`; it is
not inferred from or duplicated in the target/reference classification.

### Conservative-equivalent total-alkalinity balance

Promote total alkalinity from a preserved-only source/target property into the
calculated forward workflow through a named
`conservative_equivalent_alkalinity_v1` model. This is an equivalent balance,
not carbonate speciation, equilibrium chemistry, or pH prediction.

The model must keep reported, calculated, and target alkalinity conceptually
distinct without requiring a breaking replacement of the public `Alkalinity`
type. Its initial assumptions are:

- volumes are additive;
- source alkalinity is resolved under the existing source-resolution policy;
- resolved source alkalinity is volume-weighted during blending;
- reviewed treatment contributions are calculated stoichiometrically in
  equivalents;
- supported contributing ingredients dissolve completely;
- precipitation, mineral dissolution, biological reactions, and unmodeled
  acid/base reactions are not calculated; and
- carbonate redistribution and CO2 exchange do not themselves change total
  alkalinity, while reactions such as calcium-carbonate precipitation can and
  remain explicit limitations.

When a source supplies them, the report-native record should also preserve the
original analyte wording and unit, reported-result identity as total alkalinity
or acid-neutralizing capacity (ANC), reported statistic, analytical method,
titration endpoint or method code, filtered/unfiltered sample state, sampling
context, and document provenance. These are source semantics and must not be
manufactured for calculated or target values.

Before 0.5.0 release, the public source-reporting model must expose enough
optional analytical context to retain those supplied semantics rather than only
the normalized `as CaCO3` value. Missing method, endpoint, sample-state, or
alkalinity/ANC identity remains unknown; the engine must not infer it from the
number alone.

The public representation should keep this optional source-only analytical
metadata cohesive rather than overloading `ReportedResultContext`, whose purpose
is timing and sampling context. Result identity and filtered/unfiltered state
should use explicit controlled values; original analyte/unit wording, method
name, and method code should remain source-faithful text; and an explicitly
reported titration endpoint should use `PHValue`. Reported alkalinity should also
support the existing `ReportedStatistic` concept. Exact public class and field
names remain an implementation decision, but calculated and target alkalinity
must not acquire this source-only metadata.

The supported public API returns:

1. policy-controlled source-alkalinity resolution;
2. volume-weighted blended alkalinity with unknown propagation;
3. structured per-source alkalinity contributions;
4. structured treatment alkalinity contributions;
5. modeled final total alkalinity;
6. exact/range/bound target-alkalinity comparison;
7. signed target deviation and comparison status;
8. contribution-matrix support for total alkalinity;
9. stable calculation-basis and limitation metadata;
10. optimizer support only when final alkalinity is resolvable and an
    appropriate alkalinity criterion is present; and
11. post-rounding forward recalculation proving that an optimized plan
    reproduces its reported final alkalinity.

All eleven items are implemented. Sodium bicarbonate is automatically
selectable only under the named conservative-equivalent model when starting
alkalinity is resolved and a supported total-alkalinity criterion is present.
Every selected dose is replayed through the ordinary forward calculation before
the plan is accepted.

If any positive-volume source has missing or unresolved alkalinity, blended
and final total alkalinity remain unresolved. Known source and treatment
contributions remain auditable, but a known addition must not turn an unknown
starting value into a known final result. A zero-volume unknown source has no
effect, and a source alkalinity of zero is known only when explicitly reported
or otherwise justified by an existing source-resolution contract.

The model must not infer source alkalinity from bicarbonate, carbonate, pH,
hardness, or charge balance. Bicarbonate and carbonate remain unsupported
ordinary optimizer targets. Sodium bicarbonate is optimizer-eligible
only when initial/blended alkalinity is resolved, a supported total-alkalinity
criterion is present, its sodium contribution is included normally, and no
requested behavior requires pH or equilibrium speciation.

For a specifically reviewed material such as sodium bicarbonate, a signed
equivalent-per-mole rule belongs to this named calculation model; it is not a
universally valid intrinsic property required of every chemical identity. The
initial NaHCO3 rule contributes one equivalent of alkalinity per mole under the
model assumptions. Formal bicarbonate inventory remains separately auditable
and must not be presented as equilibrium final bicarbonate concentration.

`conservative_equivalent_alkalinity_v1` is not a simulator for the exact result
of a particular laboratory titration procedure. Analytical endpoint and method
can affect a reported alkalinity result. The calculation contract should expose
that limitation explicitly rather than hard-code an endpoint-specific correction
into the generic equivalent balance.

Consumer applications may proceed against Engine 0.4.1 with report-native
total-alkalinity and pH entry, independent preservation of explicitly reported
bicarbonate/carbonate, and `NOT_CALCULATED` presentation for blend, treatment,
and final alkalinity and working-water pH. Applications must not reconstruct
these calculations from ion data. Field placement, exact labels, layout,
application schema versions, toggles, and temporary material visibility remain
consumer-project decisions rather than engine requirements.

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

### Practical treatment-material work

Preserve the existing distinction between ideal chemical stoichiometry and the
real material a user measures and adds.

- Treat hydration state as part of chemical identity. Calcium chloride
  anhydrous and calcium chloride dihydrate are distinct identities, not unit
  conversions or interchangeable product forms.
- Anhydrous calcium chloride is now a supported chemical identity, distinct
  from calcium chloride dihydrate, with authoritative composition provenance
  and independent formula-mass and ion-yield tests.
- Exact and ranged mass-fraction treatment-material representations now cover
  solid and aqueous-solution preparations without changing the underlying
  chemical stoichiometry. Exact fractions resolve measured mass to active
  chemical mass; ranged fractions preserve active-mass bounds without an
  implicit midpoint.
- Exact mass-fraction materials are eligible optimizer inputs. Dose increments,
  request maximums, and mass ranking remain measured-material quantities while
  chemistry uses resolved active mass. Ranged materials remain optimizer-
  ineligible until an explicit uncertainty policy exists.
- Represent purity/assay separately from chemical hydration state. A commercial
  flake specified as a range such as 77–80% or 83–87% CaCl2 is a material
  specification, not the definition of pure calcium chloride dihydrate.
- Represent solution concentration with an explicit basis; never accept an
  unlabeled percentage whose meaning could be mass fraction, mass/volume, or
  another convention.
- Mass-based dosing of aqueous solutions is supported when an exact mass
  fraction is supplied. Manual volume dosing is supported either when exact
  mass fraction, density, density reference temperature, and a matching
  measurement temperature are supplied, or when an exact active-mass-per-
  solution-volume concentration and matching reference/measurement
  temperatures are supplied. Thermal correction and volume-dose optimization
  remain unsupported.
- Density is retained with its reference temperature and may carry separate
  source-document provenance. The engine never assumes a concentrated aqueous
  treatment solution has density 1 g/mL.
- Preserve reported assay/concentration ranges rather than silently replacing
  them with an arithmetic midpoint. Any representative-value policy used for a
  calculation must be explicit and auditable.
- Retain authoritative composition/specification evidence and validated
  practical-use limits with reusable material definitions.
- Keep the current complete-dissolution model explicit for simple supported
  additions rather than implying that every solid is fully soluble under every
  process condition.

Full equilibrium, precipitation, and dissolution modeling is not required for
0.5. Calcium carbonate/chalk must not be added to the ordinary
complete-dissolution ingredient set merely by assigning fixed Ca2+ and
carbonate contributions; its useful dissolved contribution depends on the
carbonate/CO2 system and remains later chemistry work.

### Richer target-comparison semantics

- Preserve the existing exact/range/bound outcomes and signed deviations.
- Add scientifically and operationally defined comparison policies only where
  their meaning and intended use are explicit.
- Support consumer-facing categories beyond raw difference, such as close/far,
  only when their thresholds are documented rather than inferred by an
  application from a universal percentage.
- Handle zero and very-low targets without percentage-based singularities or
  misleading classifications.

The initial 0.5 comparison-policy boundary uses versioned, described,
per-ion absolute mass-concentration bands. Existing below/within/above status
and signed deviation remain unchanged. Within-target, close, far, and
not-evaluated interpretation is reported separately; without an explicit policy
the engine does not invent a closeness category. Asymmetric absolute bands are
measured from the nearest accepted exact/range/bound boundary and remain defined
for zero and very-low targets without percentage division.

## 0.6 — Optimizer and Contract Hardening

Expand the first useful optimizer without invalidating its plan semantics.
Candidate work includes:

- additional named strategies and caller-selected policy combinations beyond
  the bounded 0.4 set;
- stronger plan snapshot, serialization, and compatibility contracts;
- policy, solver, and model version reporting suitable for saved designs;
- broader practical-material participation as 0.5 semantics permit;
- performance and numerical-conditioning work supported by measurements and
  reference problems; and
- expanded conformance vectors and independent solver/result checks.

Add mixed-integer optimization only when a concrete policy requires it. Continue
to recalculate chemistry after operational rounding and report whether a plan is
exact, within all target ranges, closest feasible, impractical, infeasible, or
indeterminate.

## 0.7 — Reusable Working-Water pH and Richer Diagnostics

Add validated state-based aqueous chemistry and diagnostic capabilities when
the scientific models, minimum-input contracts, reference cases, and limits are
established.

Conceptually, reusable primitives may eventually include operations such as:

```text
calculate_ph(chemical_state)
charge_balance(chemical_state)
reconcile_hardness(chemical_state)
```

The exact public API names are not committed by this roadmap. The important
boundary is that these operations describe water chemistry rather than a beer,
coffee, tea, dough, or other domain process.

This milestone does not establish a general carbonate-speciation or aqueous-
equilibrium solver. Those deeper capabilities remain Version 2 work. A bounded
working-water-pH implementation may use validated internal equilibrium
calculations necessary for that result without publishing a general solver or
claiming broader speciation support.

The same capabilities may evaluate source, blended, or final treated-water
states. They must:

- never overwrite reported measurements;
- never arithmetic-average pH;
- return insufficient-data status instead of guessing;
- retain model/version, assumptions, relevant temperature/reference conditions,
  and warnings;
- keep charge balance diagnostic rather than mutating source data to force
  electroneutrality; and
- distinguish reported total hardness from hardness reconstructed from known
  calcium/magnesium rather than silently substituting one for the other.

The semantic representation prerequisite is complete: FermUnits 0.1.3 remains
the supported floor, FermUnits 1.0.0 is the locked release dependency, and
reported and target pH use their finite `PHValue` rather than an artificial
universal 0-through-14 range. Before or as part of calculated working-water pH:

- never represent chemical pH as `Q_(value, "pH")`, because FermUnits will not
  redefine Pint's existing interpretation of that symbol as picohenry;
- keep activity-coefficient selection, concentration/activity conversion,
  equilibria, ionic strength, and all prediction policy in this engine.

This milestone is working-water chemistry only. Recipe-aware mash-pH prediction,
malt buffering, grain-bill interpretation, and other brewing-specific models
belong in a brewing consumer such as Water Chemistry Designer, which may
compose these lower-level engine results. If a sufficiently defensible aqueous
model is not ready, Version 1 may continue to return derived pH as
unsupported/unknown rather than ship a weak approximation.

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
- The generic water core contains no brewing-, coffee-, tea-, bread-, pizza-,
  or other domain-specific predictive/sensory assumptions.
- Reusable water chemistry and treatment rules live in the engine; domain-
  specific interpretation, prediction, and recommendation logic lives in the
  consuming domain.

## 1.1 — Reusable Process-State and Treatment Context

Add generic process-state context where it is needed to model water treatment
without embedding a particular product domain.

Candidate capabilities include:

- ordered water-state checkpoints before and after treatment steps;
- explicit treatment sequence/order where chemistry depends on order of
  addition;
- target state conditions such as temperature or requested water pH when the
  underlying chemistry is validated; and
- opaque caller-owned purpose/context identifiers when they are useful for
  provenance, without engine-authored brewing or sensory interpretation.

A consumer may label a state as mash liquor, sparge liquor, coffee brew water,
or another purpose. The engine should calculate the reusable chemistry of that
state; the consumer owns the domain-specific recommendation.

## Version 2.0 — Advanced Generic Aqueous and Reactive Chemistry

Add capabilities that require materially deeper scientific models or
optimization while remaining reusable across domains:

- acid and alkali additions as chemistry primitives;
- alkalinity neutralization;
- acid dose to a target **water** pH when a validated model supports it;
- deeper carbonate/bicarbonate and CO2 equilibrium chemistry;
- reusable carbonate speciation and equilibrium-state calculations;
- a general buffer-system/equilibrium solver only if a defensible domain-neutral
  contract can be established;
- precipitation, saturation, solubility, and dissolution behavior where
  practical and validated, including the chemistry needed before chalk can be
  modeled as an actionable treatment;
- order-of-addition and process-state effects where chemically material;
- reaction-time/kinetic behavior only where validated and necessary;
- uncertainty propagation;
- optimization using uncertain/ranged source reports;
- sensitivity and worst-case plans;
- Pareto-front exploration;
- optional caller-supplied treatment cost/availability constraints; and
- broader generic process-water workflows.

Domain models such as malt/grain buffering, Kolbach residual-alkalinity
interpretation, Z-alkalinity mash models, recipe-aware mash-pH prediction,
beer-style recommendations, coffee extraction guidance, and dough behavior are
not Engine features. Consumers such as Water Chemistry Designer may build those
models by composing generic Engine primitives with domain-specific data.

## Version 3.0 — Broader Generic Treatment Models

Add non-additive or reactive treatment models only as concrete validated
workflows establish reusable contracts. Candidates include:

- activated-carbon filtration/dechlorination;
- reverse-osmosis treatment and rejection models;
- ion exchange;
- lime softening and other validated softening/dealkalization methods;
- deaeration; and
- membrane filtration where relevant.

A generalized non-additive `TreatmentOperation` abstraction may be introduced
only after multiple implemented workflows demonstrate the common contract. It
must not be designed around a single brewing, coffee, industrial, or other
consumer workflow.

## Version 4.0 — Advanced Generic Process-Water Modeling

Consider broader process-water calculations only when the chemistry can be
expressed through reusable water-state, treatment, materials-compatibility, and
validation contracts. Safety, regulatory, sensory, production, and
purpose-specific decisions remain responsibilities of the consuming domain.

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
