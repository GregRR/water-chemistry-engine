# Water Chemistry Engine Design

**Document:** `docs/WATER_CHEM_DESIGN.md`  
**Status:** Working design — active implementation  
**Revision:** 2026-08-29
**Project:** Water Chemistry Engine
**Engine distribution:** `water-chemistry-engine`
**Engine import package:** `water_chemistry_engine`
**License:** Mozilla Public License 2.0  
**Initial audience:** Brewers, meadmakers, distillers, application developers, and other validated water-treatment consumers

## 1. Purpose

The Water Chemistry Engine is a reusable, scientifically grounded system for analyzing source water and designing practical water blends and treatment plans.

It is not intended merely to reproduce traditional brewing-water calculators that require callers to manually trial salt additions until displayed ions look close to a target. The engine should accept source-water chemistry, a target/reference profile, available water sources, permitted treatments, and practical constraints, then calculate and rank useful treatment plans automatically as those capabilities are implemented.

The engine remains independent of web frameworks, databases, graphical interfaces, operating systems, and hardware. It should be usable by:

- separately maintained web/API applications;
- Mechani-Brew;
- Python scripts and notebooks;
- third-party software and automation;
- recipe and batch-planning workflows;
- future alternative-language implementations that conform to versioned contracts and test vectors.

## 2. Product goals

The project should make sophisticated water treatment reusable and explainable without hiding the underlying chemistry or source attribution.

The engine should:

1. Model source water, target/reference water, blends, treatment additions, and resulting water as distinct concepts.
2. Preserve the difference between reported, measured, inferred, estimated, and calculated data.
3. Preserve exact values, ranges, qualified bounds, `ND`/not-detected states, reporting bases, named reported statistics, original units, and source-document metadata.
4. Blend two or more waters by volume.
5. Determine practical mineral additions automatically.
6. Optimize water proportions and treatment additions jointly when appropriate.
7. Produce several meaningfully different ranked solutions instead of claiming one universal optimum.
8. Explain why each solution was selected, where it compromises, and why some targets are infeasible.
9. Preserve each source water and treatment ingredient's contribution to every modeled ion.
10. Support dated source-water profiles so an earlier successful treatment can be reproduced from changed current water.
11. Use FermUnits for dimensional quantities while retaining water-chemistry semantics in this engine.
12. Support BeerJSON 1.0 as the current brewing interchange boundary and richer FermentationJSON interchange when its water schemas are ready.
13. Provide a small structured consumer API while keeping all scientific logic out of consuming product layers.
14. Remain suitable for future conforming implementations in Swift, Kotlin, Dart, JavaScript, or other languages.
15. Preserve water identity, sampling stage/context, and result-specific timing when reports distinguish them.
16. Keep regulatory or advisory limits separate from measured or reported water chemistry.
17. Preserve source-reported disinfectants and other relevant analytes even when the current optimizer does not use them, beginning with chlorine and chloramine reporting.
18. Treat intended water use as calculation/request context rather than an intrinsic property of a source-water profile.

## 3. Non-goals

The initial project is not intended to be:

- a universal industrial water-treatment package;
- a municipal treatment-plant simulator;
- a general geochemistry platform;
- an inventory-management or purchasing system;
- an accounting system;
- a laboratory information-management system;
- a replacement for qualified laboratory analysis;
- a claim that matching an ion profile guarantees flavor or product quality;
- dependent on Mechani-Brew, a database, or any particular application framework.

The architecture may permit later use outside brewing, but Version 1 should optimize for beer, mead, distilling, and closely related fermentation uses.

## 4. Engineering principles

1. **Keep chemistry separate from consumer presentation.** No equations, conversion rules, or optimization policies belong only in application views, handlers, database models, or other product layers.
2. **Use explicit quantities.** Dimensional inputs and outputs use FermUnits/Pint quantities or are converted into them at a boundary.
3. **Preserve meaning as well as magnitude.** `mg/L as CaCO3`, bicarbonate concentration, alkalinity, hardness, conductivity, TDS, and pH are not interchangeable merely because numerical conversions can be written.
4. **Preserve source attribution and document metadata.** Water identity, publisher, analysis provider when explicitly known, report title/date, observation timing, retrieval date, source URL, page/table reference, and notes must remain attachable without conflating the water itself with the document that reported it.
5. **Preserve reported data exactly.** A value explicitly reported by a source must never be silently replaced by a calculated substitute.
6. **Keep derived data derived.** Values that can be recalculated from stored source data should normally be calculated on demand rather than persisted as though they were independent measurements.
7. **Do not disguise estimates as measurements.** Calculated, inferred, representative, bounded, censored, not-detected, and measured values remain distinguishable.
8. **Preserve censoring and detection semantics.** `ND`, `<X`, `>X`, and qualified range endpoints must not be coerced into ordinary numeric values without an explicit calculation policy.
9. **Separate chemistry from regulatory references.** MCLs, MCLGs, action levels, treatment techniques, notification limits, and similar thresholds are reference metadata, not source-water concentrations.
10. **Prefer deterministic and reproducible behavior.** Identical versioned inputs and solver settings should produce identical results within documented numerical tolerances.
11. **Explain infeasibility.** The engine must say why a requested target cannot be reached under supplied constraints.
12. **Rank tradeoffs rather than claim one universal optimum.** Users may reasonably prefer accuracy, simplicity, lower dilution, fewer products, or lower total additions.
13. **Make model versions visible.** Saved plans should identify the chemistry, optimization, and reference-data versions that produced them.
14. **Validate against independent reference data.** Legacy calculator code can inform the project but is never authoritative by itself.
15. **Avoid premature abstraction.** Shared calculator infrastructure should be extracted only after concrete duplication demonstrates a stable shared requirement.
16. **Preserve before modeling.** A source report may contain chemically or operationally relevant analytes that the current optimizer cannot yet use. Preserve supported reported data faithfully rather than discarding it merely because no calculation consumes it today.
17. **Keep intended use contextual.** The same source water may be used for brewing liquor, dilution, spirit proofing, coffee brewing, or another purpose. Intended use belongs to the calculation or application context and must not mutate the identity or reported chemistry of the source water.

## 5. System architecture and dependency direction

```text
FermUnits
    │
    ▼
water-chemistry-engine
    │
    ├── external web/API applications
    ├── Mechani-Brew
    ├── Python/automation consumers
    ├── alternative conforming implementations
    └── test and research tooling

BeerJSON 1.0 ───────┐
                    ├── boundary adapters ── water-chemistry-engine domain models
FermentationJSON ───┘
```

Responsibilities are intentionally separated:

- **FermUnits** supplies quantity representation, dimensional validation, unit conversion, equivalent chemistry conversions, and explicit unit definitions. Its planned M4 API also supplies a semantic pH value and the exact definitional transform between pH and dimensionless hydrogen-ion activity; that API is not yet part of the FermUnits 0.1.x version consumed by this engine.
- **Water Chemistry Engine** supplies water-chemistry semantics, reported-value semantics, blending, stoichiometry, comparison, optimization, warnings, and structured results.
- **BeerJSON/FermentationJSON adapters** translate external interchange documents to and from engine boundary/domain models.
- **Consumer applications** supply persistence, users, forms, visual presentation, document ingestion/review workflows, and product-specific interaction.

The shared water representation and deterministic water-chemistry capabilities must not acquire coffee-, bread-, or other domain-specific sensory assumptions merely because products may later use the same engine. Future domain capabilities should depend on the shared water core rather than forcing the core to depend on a particular product domain.

When real application use exposes a missing chemistry, water-domain interpretation, validation, optimization, or calculation-semantic capability, that capability belongs in the engine. Presentation, persistence, authentication, workflow, and interaction state remain application responsibilities.

The engine never imports a consumer application, database ORM, or product-specific presentation framework.

## 6. Tooling decisions

### 6.1 Python and package management

- Python 3.11 is the minimum supported runtime; CI tests Python 3.11 through 3.14.
- `uv` for Python installation, dependency resolution, environments, and locking.
- `uv_build` for the pure-Python engine distribution.
- A standard single-project `src/` package layout.
- Tooling should remain as consistent as practical with FermUnits, Mechani-Brew, and the other Calculators projects.

### 6.2 Current and planned core libraries

- **FermUnits 0.1.x:** required by `water-chemistry-engine`; resolved from PyPI with the supported `>=0.1.2,<0.2.0` dependency range. FermUnits 0.1.2 is the minimum release that shares the Python 3.11 compatibility floor.
- **Pint:** transitive quantity implementation through FermUnits.
- **NumPy:** planned for vector/matrix work when the calculation implementation actually requires it.
- **SciPy:** planned for continuous and mixed-integer optimization when optimization work begins.
- **Pydantic:** planned for validation/serialization at engine API and interchange boundaries where justified.
- **Frozen dataclasses / simple immutable domain objects:** preferred for internal scientific models where serialization behavior is unnecessary.

NumPy, SciPy, and other substantial dependencies should not be added merely because they are expected eventually; add them when an implemented feature needs them.

### 6.3 Consumer applications and boundaries

Consumer products are maintained outside this repository. They may use web frameworks, native frameworks, command-line interfaces, APIs, or other presentation stacks without changing the engine architecture.

The engine should expose framework-neutral structured inputs, outputs, errors, notices, and eventually versioned request/result contracts. Application persistence and presentation-technology decisions are deliberately outside the engine design.

The first known consumer is a separate web-application project, but its stack is not an engine dependency and is documented outside this repository.

### 6.4 Quality tooling

- `pytest` for unit, integration, regression, and reference tests.
- `Hypothesis` for property-based testing.
- Ruff for linting and formatting.
- mypy for static type checking.
- GitHub Actions for CI.
- Coverage reporting as a diagnostic, not as a substitute for meaningful tests.

## 7. Repository and packaging strategy

The repository is public and engine-only. End-user web, native, and other product implementations are separate projects.

```text
water-chemistry-engine/
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   └── water_chemistry_engine/
├── tests/
├── docs/
│   ├── WATER_CHEM_DESIGN.md
│   ├── WATER_CHEM_REFERENCES.md
│   ├── PROJECT_STRUCTURE.md
│   ├── ROADMAP.md
│   ├── decisions/
│   └── research/
├── reference-data/
│   └── water/
├── schemas/
│   └── water/
├── test-vectors/
│   └── water/
├── scripts/
├── CHANGELOG.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── LICENSE
└── README.md
```

`water-chemistry-engine` is the only installable distribution in this
repository. The repository root is the Python project root, and the importable
package lives under `src/water_chemistry_engine/`. The former monorepo-style
`packages/` wrapper is unnecessary now that consumer applications are separate
projects.

No shared calculator-core package should be introduced until at least two concrete projects demonstrate a stable requirement that is genuinely shared and does not belong in this engine.

## 8. Current engine package structure

The 0.2 engine remains a flat package while the domain boundaries are still
small enough to be understandable without premature subpackages. Major module
groups are:

- reported/source semantics: `concentrations`, `reported_values`,
  `reported_properties`, `reported_statistics`, `reported_disinfectants`,
  `reporting_context`, `source_document`, `water_identity`, and `profiles`;
- calculation-ready state and resolution: `chemical_state` and
  `source_resolution`;
- deterministic water construction: `blending`, `treatment_ingredients`,
  `treatment_stoichiometry`, and `treatment_application`;
- result interpretation/presentation data: `target_profiles`,
  `target_comparison`, `contribution_matrix`, `preparation_instructions`,
  `forward_notices`, and `forward_calculator`;
- internal cross-stage validation: `_workflow_validation`;
- reusable supporting semantics: `ions`, `alkalinity_conversions`, and
  `quantity_types`.

Data-driven real-report fixtures live under `test-vectors/water/reports/` rather
than inside the engine package.

The package may be reorganized into subpackages when real code size and import
boundaries justify it. The design document intentionally avoids maintaining an
exhaustive file-by-file tree that can drift from the repository.

## 9. Core domain model

### 9.1 Canonical ion identifiers

Initial canonical ions are represented by stable string-backed identifiers:

- calcium;
- magnesium;
- sodium;
- potassium;
- chloride;
- sulfate;
- bicarbonate;
- carbonate.

Additional analytes should be added deliberately and should not require redesigning the entire profile model.

### 9.2 Exact ion concentration

An exact reported ion concentration contains:

- an ion identifier;
- a FermUnits/Pint quantity convertible to mass per volume.

Canonical comparison calculations may normalize to mg/L, but the supplied quantity and its unit semantics must remain available at the appropriate boundary.

### 9.3 Ranged ion concentration

The current implementation supports linear ranges whose endpoints can themselves preserve source qualifiers. Each endpoint is one of:

- exact numeric value;
- upper bound such as `<X`;
- lower bound such as `>X`;
- `ND` / not detected, with an optional explicitly supplied detection limit.

A range may also carry an independently reported ordinary average.

For an ordinary **linear concentration** whose two endpoints are exact numeric values, calculation behavior is explicit:

```text
reported_average exists                    → use reported_average
policy allows exact-range midpoint         → derive midpoint(minimum, maximum)
otherwise                                  → remain unresolved
```

There is no default midpoint substitution. A caller must supply a
`SourceResolutionPolicy` with `allow_exact_range_midpoints=True` before an
exact-ended range without a reported average becomes calculation-ready. The
midpoint is derived data; it is not stored as `reported_average` and must never
be presented as though the source reported it.

A `reported_average` field may be populated only when the source explicitly identifies the value as an ordinary average. When a reported average accompanies a reported range, the reported average takes precedence over the mathematical midpoint. For example, a source may report calcium as average `51 mg/L`, range `50–53 mg/L`; calculations use the reported `51 mg/L`, not the midpoint `51.5 mg/L`.

A qualified range without an independently reported average has no automatic representative calculation value under the current policy.

### 9.4 Bounds, `ND`, and qualified range endpoints

The engine now represents these source-reported concentration forms directly:

- exact numeric value;
- exact or qualified range;
- upper bound such as `<0.3`;
- lower bound such as `>X`;
- `ND` / not detected;
- ranges such as `ND–11.1` or `<3–14`.

`ND` is a first-class source-reported state:

```text
ND ≠ 0
ND ≠ automatically <X
```

If a report says `ND` but does not publish the applicable detection/reporting limit for that result, the engine must not invent one. If the source explicitly reports a numerical detection limit, it can be retained on the not-detected result/endpoint.

When both endpoints of a reported range carry explicit numeric thresholds—including exact values, upper/lower bounds, or an `ND` endpoint with a supplied detection limit—the minimum endpoint threshold must not exceed the maximum endpoint threshold. This validation catches internally reversed extracted/report data without turning either qualified endpoint into a calculation value. An `ND` endpoint without a reported detection limit remains nonnumeric and does not participate in this threshold-order check.

Bounds, `ND`, and qualified endpoints do not automatically receive a representative calculation value. Any policy that substitutes a numeric value must be explicit, domain-specific, reproducible, and surfaced in assumptions/warnings.

Reported statistic and result-context metadata may accompany exact, bounded, not-detected, and ranged concentration results without changing their source-reported result form.

### 9.5 Reported water properties

Some water-report properties are important but are not ordinary ion concentrations. Initial structured properties are:

- alkalinity;
- total hardness;
- total dissolved solids (TDS);
- electrical conductivity.

These support exact values and, for linear quantities, reported ranges and independently reported ordinary averages.

Alkalinity and total hardness currently use an explicit reporting basis, initially:

- `as CaCO3`.

`as CaCO3` is a chemical reporting basis, not merely a unit label. The engine must preserve it semantically. The model should be extensible to other explicitly reported bases such as bicarbonate alkalinity reported as HCO3 without hiding the basis in an opaque unit string.

Conductivity may carry a reference temperature when the source provides one. A reference temperature must remain optional; the engine must not infer 25 °C or another temperature merely because that is common practice.

#### 9.5.1 Reported disinfectants and non-optimization analytes

Water reports may contain constituents that are important to product quality, treatment decisions, or later domain modules even though they are not part of the current canonical brewing-ion optimization panel. The source-report model and import path must be able to preserve such values without pretending that the optimizer already models their effects.

The first required disinfectant/reporting concepts are:

- unqualified chlorine when the source itself reports only `chlorine` and does not identify a more specific residual/fraction;
- free chlorine, when explicitly reported;
- total chlorine, when explicitly reported;
- combined chlorine, when explicitly reported;
- chloramine or a named chloramine species, using the source's terminology when explicitly reported;
- chlorine dioxide, when explicitly reported.

The original reporting basis or analytical label should be retained when supplied, for example `mg/L as Cl2`. **Chloride (`Cl-`) is chemically and semantically distinct from chlorine, total chlorine, and chloramine and must never be used as a substitute for them.**

The engine/importer must not automatically calculate chloramine or combined chlorine by subtracting free chlorine from total chlorine unless a documented analytical rule for that specific representation supports the derivation. Any such result would be derived data, not a reported measurement.

The initial engine representation is intentionally focused: `ReportedDisinfectant` carries a stable disinfectant concept, source label, optional reporting basis, source-result context/statistic, and exact/range/reported-average concentration semantics. Named chloramine species preserve the source species name without requiring a universal analyte framework. More general analyte abstractions or additional qualified disinfectant result forms should be introduced only when real reports require them.

The same preserve-before-modeling principle may later apply to iron, manganese, nitrate, nitrite, silica, dissolved oxygen, hydrogen sulfide, trihalomethanes, and other report analytes. Adding a reported analyte must not automatically make it an optimization variable or imply that the engine has a validated treatment model for it.

### 9.6 Alkalinity and bicarbonate are not interchangeable

A reported total alkalinity value must remain total alkalinity. The engine must not silently derive or overwrite bicarbonate from total alkalinity.

For example:

```text
Reported: total alkalinity = 108 mg/L as CaCO3
```

must remain that reported measurement.

The engine does, however, support a narrower and chemically different normalization: when a source explicitly identifies a result as **bicarbonate alkalinity** but expresses that bicarbonate result on a CaCO3 mass basis, the equivalent-mass basis can be converted to an HCO3 mass concentration. This is a reporting-basis normalization of an explicitly identified bicarbonate result, not an inference that total alkalinity equals bicarbonate.

Likewise, if a source directly reports a result as `mg/L HCO3`, that value can be represented as the existing bicarbonate ion concentration while preserving its source statistic/context. Niagara's report fixture exercises this case separately from its reported total alkalinity.

Any future model that derives carbonate species from total alkalinity, pH, dissolved inorganic carbon, or other equilibrium inputs must label those species **derived**, retain the assumptions/model version, and coexist with—not replace—the reported alkalinity.

### 9.7 pH is a logarithmic scientific invariant

pH requires behavior different from linear water properties.

The fundamental relationship is:

```text
pH = -log10(a_H+)
```

where `a_H+` is hydrogen-ion activity. A concentration-based `[H+]` treatment is an approximation and must be documented as such when used.

FermUnits 0.1.3 owns the finite semantic `PHValue` and the exact bidirectional
activity transform represented by this definition. It does not define `pH` as
a Pint unit: `Q_(7.0, "pH")` must not be used for chemical pH because Pint can
interpret that symbol as picohenry. The type and transform are now available
through this project's supported dependency range, but migrating the engine's
reported and target pH contracts remains a deliberate later integration slice
rather than an incidental dependency update.

The definition-level transform does not make activity interchangeable with
hydrogen-ion concentration. Converting between activity and concentration
requires an explicit activity coefficient and therefore a selected activity
model and sufficient chemical state. Those choices, along with acid/base and
carbonate equilibria, ionic-strength behavior, temperature-dependent chemistry,
blending/treatment effects, prediction, and application-specific targets,
remain responsibilities of this engine. Any ideal-solution approximation such
as an activity coefficient of 1 must be explicit and versioned here rather than
hidden in FermUnits.

The implemented `ReportedPH` model preserves:

```text
value              # exact reported pH
minimum            # reported lower endpoint
maximum            # reported upper endpoint
reported_average   # ONLY when the source explicitly reports an average
```

The following rules are mandatory and enforced by tests:

1. **Never compute an arithmetic midpoint or arithmetic mean directly in pH space.**
2. If an exact pH is reported, it may be used as that exact reported value.
3. If a source explicitly supplies a reported average pH, preserve and use that reported average when a representative value is required.
4. If only a minimum and maximum pH are reported, preserve the range but do **not** invent an average or generic calculation value.
5. A minimum/maximum range alone is insufficient to reconstruct the mean of the underlying observations.
6. Averaging only the two range endpoints in hydrogen-ion space would produce an endpoint-derived representative, not the true average of the observations that generated the range; it must not be labeled an average.
7. If individual pH observations are available and an aggregate is intentionally calculated, convert each observation to linear hydrogen-ion activity (or an explicitly documented concentration approximation), perform the specified weighted or unweighted averaging in that linear space, and convert back to pH:

```text
a_i = 10^(-pH_i)
mean_a = sum(w_i * a_i) / sum(w_i)
derived_pH = -log10(mean_a)
```

8. Any such aggregate is **derived pH**, never `reported_average`.
9. Measurement temperature and activity-model assumptions should be retained when known and when material to the calculation.

FermUnits 0.1.3 validates the mathematical domain of its semantic pH
representation (finite pH) and activity transform (finite activity greater than
zero), without imposing a supposedly universal 0-through-14 pH range. The
engine must own any narrower validation as an explicit domain or application
policy. The current `ReportedPH` and `TargetWaterProfile` models still enforce
that range; the existing behavior must be reviewed deliberately before adopting
`PHValue` rather than being mistaken for a FermUnits or thermodynamic invariant.

#### 9.7.1 Reusable calculated-pH capability

`ReportedPH` describes only what a source actually reported. Calculated pH is a separate **derived engine result**.

The engine should expose one reusable aqueous pH capability, conceptually:

```python
result = calculate_ph(chemical_state)
```

The pH algorithm must not be duplicated for source water, blended water, and treated water. The calculation receives a normalized aqueous chemical state and should not care how that state was produced. A chemically equivalent state should therefore yield the same result whether it came from one source profile, several blended sources, or a blend plus treatment additions.

A chemical state may represent useful checkpoints such as:

```text
source-water state
        │
        ├── blend one or more sources ──► blended-water state
        │                                      │
        │                                      └── apply additions ──► final treated-water state
        │
        └──────────────── each state may be passed to calculate_ph(...)
```

Calculated pH must obey these rules:

1. It never overwrites or populates `ReportedPH`.
2. It is returned as derived result data associated with the chemical state being evaluated.
3. It identifies the chemistry model/version, assumptions, relevant temperature/reference conditions, source fields used, and warnings/approximation status where applicable.
4. If the supplied state is scientifically insufficient for the selected model, return an explicit insufficient-data result rather than guessing.
5. Changing composition, temperature, or other model-relevant inputs invalidates the previously calculated pH for that state.
6. The calculation must not imply precision unsupported by the model or inputs.
7. The reusable pH capability belongs in `water-chemistry-engine`; consumer applications only construct/select the state and request the calculation.

Working-water pH is distinct from **recipe-aware mash-pH prediction**. Mash pH additionally depends on grain buffering and mash-specific chemistry and remains a later advanced feature even though it may ultimately reuse lower-level acid/base or equilibrium components.

### 9.8 Reported statistic semantics

Real reports use several statistically distinct summary concepts. At minimum the source/report model must be capable of distinguishing:

- single observation;
- ordinary reported average;
- running annual average (RAA);
- locational running annual average (LRAA);
- percentile result such as a 90th percentile;
- highest result;
- lowest result;
- other explicitly named statistics.

`reported_average` remains narrowly defined: it means an ordinary average explicitly reported by the source. It must not become a generic bucket for RAA, LRAA, percentile, highest/lowest, or other named statistics.

The implemented `ReportedStatistic` / `ReportedStatisticKind` model preserves these meanings without forcing every statistic into a separate top-level property. A percentile retains its percentile value, while `OTHER` requires an explicit label.

### 9.9 Observation timing and data coverage

Timing exists at more than one level.

A `SourceWaterProfile` currently supports either:

- a single `observed_on` date; or
- an inclusive `ObservationPeriod(start, end)`.

Those two profile-level forms are mutually exclusive.

Real annual reports also demonstrate that individual constituents may have their own dates or periods that differ from the overall report/profile period. The implemented `ReportedResultContext` therefore supports:

```text
profile/report observation period
+
optional result-specific observation date or period
```

When result-level timing is present, it is the more specific timing for that result.

The implemented `ResultCoverage` model represents **coverage semantics** such as:

- single observation;
- observation-period summary;
- typical/representative analysis;
- historical/reference profile.

A source profile must not be forced to invent a precise sample date when a commercial report supplies only a "Typical Analysis" or a utility supplies only an annual summary.

### 9.10 Water identity and sampling context

Real bottled and municipal reports show that these concepts are distinct and should not be collapsed into one `provider` string:

- provider/company;
- brand;
- product or water type;
- physical source/source system;
- treatment plant or facility where relevant.

Similarly, the chemistry may describe different stages/locations:

- raw source water;
- treated/finished water;
- treatment-plant output;
- distribution system;
- customer tap;
- bottled finished product.

The implemented `WaterIdentity`, `PhysicalWaterSource`, and `WaterStage` models preserve these distinctions. Chemistry from different stages is not interchangeable, and a stage must not be inferred when the source does not say.

### 9.11 Regulatory and advisory references are not source chemistry

Water-quality tables often place measured results beside regulatory/reference values such as:

- MCL;
- MCLG;
- MRDL;
- MRDLG;
- action level;
- treatment technique;
- FDA Standard of Quality;
- notification/advisory limits.

These values are useful metadata for interpreting a report but they are **not measurements of the source-water profile**. Importers must never map them into ion/property concentrations merely because they appear in the same table row.

If retained, regulatory/reference thresholds must live in a separate structure from reported chemistry.

### 9.12 SourceDocumentMetadata

`SourceDocumentMetadata` identifies the document that reported the water-quality data. It is intentionally separate from `WaterIdentity`, which identifies the supplied/produced water itself.

The current immutable metadata object supports:

- `publisher`;
- optional `analysis_provider` when the report explicitly identifies one;
- title;
- publication date;
- source URL;
- retrieval date;
- page/section reference;
- notes.

`publisher` means the organization issuing the document. `analysis_provider` means the laboratory or other analysis provider only when that role is explicit. Neither field should be guessed from the other. Physical source identity, brand/product identity, sampling location, water stage, and observation timing belong in their own domain concepts rather than being hidden inside source-document metadata.

### 9.13 SourceWaterProfile

A source-water profile represents measured or reported chemistry for water that is actually available for blending or treatment.

The current `SourceWaterProfile` supports:

- a human-readable name;
- one reported concentration entry per modeled ion;
- optional `ReportedPH`;
- mutually exclusive profile-level `observed_on` or `observation_period`;
- optional `WaterIdentity`;
- optional `SourceDocumentMetadata`;
- optional alkalinity;
- optional total hardness;
- optional TDS;
- optional conductivity;
- no duplicate ion entries.

Individual reported results may additionally carry `ReportedStatistic` and `ReportedResultContext`, allowing result-specific timing, coverage, water stage, and sample location without forcing those details into the whole profile.

The source-report representation must also be extensible to reported disinfectants and other supported analytes outside the canonical optimization-ion panel. Preserving such a reported value does not make it an optimizer variable or imply a validated treatment model for it.

Only the profile's explicit modeled-ion `concentrations` are automatically resolved into the current derived ion state. Alkalinity, total hardness, TDS, conductivity, pH, and disinfectants remain preserved reported properties unless a caller deliberately invokes a separately documented conversion or future validated model. In particular, total alkalinity is not silently converted to bicarbonate.

A source-water profile describes the water and its provenance. It must not encode the downstream purpose for which a particular calculation happens to use that water.

Source-water profile types may include:

- municipal;
- well;
- spring;
- bottled;
- purified;
- reverse-osmosis;
- distilled;
- laboratory-prepared;
- process water;
- user-measured water.

A report year is not automatically an observation date. If a source gives only an annual reporting period, aggregate year, or typical analysis, preserve that semantics rather than inventing a date such as January 1.

### 9.14 TargetWaterProfile and matchable reference profiles

A matchable target/reference profile represents desired or reference chemistry, not an incoming water supply. The calculation machinery may try to reproduce either one, but the metadata must preserve the scientific distinction between **a desired target** and **a reference profile being reproduced**.

Current target profiles support:

- name;
- exact or ranged ion concentrations;
- optional pH target;
- style associations;
- notes;
- duplicate-ion protection.

Near-term generic target/reference semantics may add:

- stable profile identifier/version;
- source/reference attribution;
- evidentiary/profile classification;
- preferred value within an acceptable range;
- hard minimum and maximum;
- optimization weight;
- additional supported generic water properties such as alkalinity, hardness, TDS, or disinfectant criteria when concrete standards require them.

Matchable profile classifications may include:

- custom/user target;
- previous successful treated-water result;
- published standard;
- published recommendation;
- style recommendation;
- published brewery/practitioner reference;
- treated point-of-use reference;
- experimental reference water;
- historical city or regional reference;
- experimentally or analytically optimized target.

These labels describe evidence, not merely intended use. A documented New York City analysis may be a regional reference that a user chooses to reproduce for dough; it is not thereby an "optimal pizza water" target. Likewise, water used in a published bread experiment is an experimental reference unless the experiment actually establishes an optimum.

Historical brewing-city tables such as Pilsen, Burton-on-Trent, Dublin, Munich, London, Dortmund, Edinburgh, Vienna, Antwerp, and Cologne are **target/reference profiles**, not claims about present-day municipal source water. Each published version must retain its own source/reference attribution; conflicting published profiles should not be silently merged into one supposedly canonical city profile.

Well-sourced coffee, tea, bread, sourdough, or pizza target/reference **data** may therefore be added before complete domain-specific scientific engines. Domain-specific prediction or sensory/process guidance remains a separate later capability.

### 9.15 WaterBlend

A blend records actual source-water volumes or fractions. Actual volumes should be retained whenever known; fractions can be derived.

The implemented fixed-blend boundary operates on exact derived `AqueousChemicalState` inputs rather than directly on reported source results. Callers may provide fixed source volumes, or fixed fractions together with the total physical blend volume needed by later treatment calculations. The result retains normalized source volumes and fractions plus per-source ion contributions. A zero-volume/zero-fraction source has no chemical effect.

For a conservative linear constituent, the basic blend relation is:

```text
C_blend = sum(V_i * C_i) / sum(V_i)
```

This formula does not apply blindly to pH or to censored/not-detected values that lack an explicit numeric calculation policy. Source-report resolution therefore occurs before blending. For each supported ion, a fixed blend concentration is produced only when every positive-volume source has a known derived concentration for that ion. If any contributing source is unknown, the final blend concentration remains unknown; known partial source contributions are retained for audit but are not presented as the total. An explicitly known zero remains a known value rather than being confused with missing data.

The current fixed-blend implementation also applies this linear relation to bicarbonate and carbonate as a **first-order approximation**. Mixing waters can shift carbonate speciation through pH-dependent equilibrium, CO2 exchange, and precipitation, so those species are not assumed to be rigorously conservative. Before reusable calculated-pH work or optimization begins relying materially on carbonate species, the engine must either surface this approximation as a structured assumption/warning or replace it with an equilibrium-aware treatment appropriate to that capability.

### 9.16 Future TreatmentIngredient

Treatment ingredients must separate chemical identity from application inventory.

Required information will include:

- stable identifier;
- display name;
- chemical formula/composition;
- hydration state;
- purity or solution concentration;
- ion yield per mass or volume;
- optional density for liquid treatments;
- validated use limits;
- evidence/source for composition.

Hydration states such as calcium chloride anhydrous vs. dihydrate are chemical identities, not unit conversions.

### 9.17 Future TreatmentPlan

A complete plan should contain:

- source-water volumes and fractions;
- treatment additions;
- predicted final profile;
- per-source and per-treatment contribution matrix;
- objective and component scores;
- target deviations;
- constraint outcomes;
- warnings and explanation codes;
- assumptions;
- solver status/tolerances;
- chemistry, solver, and reference-data versions.

### 9.18 Intended water use is calculation context

The same physical source water can be evaluated or treated differently depending on what the user intends to do with it. Brewery examples include brewing liquor, dilution water, spirit-proofing water, and other validated process uses. Future domains may add contexts such as coffee brewing without changing the source-water representation.

The design should therefore leave room for a lightweight `IntendedWaterUse` or equivalent request-context concept. It may select applicable questions, targets, limits, warnings, or calculation models, but it is not part of `SourceWaterProfile` and it must not alter reported source chemistry.

Version 1 does **not** require a generalized cross-domain suitability-criteria framework. Only intended-use distinctions with concrete, validated behavior should be implemented. Additional brewery purposes and future domain-specific criteria can be added when their requirements are established by actual use cases and evidence.

## 10. Reported, representative, and derived data policy

The engine must enforce a strict distinction between what a source said and what the engine calculated, selected, normalized, or inferred.

### 10.1 Exact reported value

An exact value is stored as reported. It is used directly when the scientific model treats it as representative.

### 10.2 Reported statistic

A report may label a result with a statistic such as ordinary average, RAA, LRAA, percentile, highest, or lowest. That label is part of the source data and must be preserved.

The engine must not assume that every table column named "average" represents the same statistical operation, and adapters must not map a named regulatory statistic into `reported_average` merely because it contains the word "average".

### 10.3 `reported_average`

The field name is specifically **`reported_average`**. It may be populated only when the source itself reports an ordinary average or when a documented importer maps a source concept that is explicitly equivalent to that meaning.

It is not a convenience cache for:

- a midpoint;
- a selected representative value;
- a reconstructed mean;
- RAA/LRAA;
- a percentile;
- highest/lowest results;
- another derived statistic.

### 10.4 Linear numeric range without reported average

For linear quantities such as ion concentration, alkalinity, hardness, TDS, and conductivity, a midpoint may be derived on demand **only when both endpoints are exact numeric values and the calculation policy permits a midpoint representative**:

```text
minimum + maximum stored
midpoint calculated on demand when needed
midpoint not persisted as reported data
```

### 10.5 Linear numeric range with reported average

Store all three independently:

```text
minimum
maximum
reported_average
```

The reported average is used for representative calculations even if it differs from the range midpoint.

### 10.6 Qualified ranges, bounds, and `ND`

A range such as `ND–11.1` or `<3–14` is not an ordinary numeric interval. A midpoint must not be calculated unless an explicit policy first resolves each qualified endpoint into a justified numeric value.

Likewise:

- `ND` has no implicit numeric value;
- `<X` is not automatically `X`;
- `>X` is not automatically `X`;
- detection/reporting limits must remain separate when provided.

Any numeric substitution policy must be explicit and must produce **derived** data with assumptions/warnings.

The implemented source-profile resolution boundary requires a caller-supplied `SourceResolutionPolicy`. Exact reported values and independently reported averages remain directly usable, but a range-only linear reported quantity has no default `calculation_value`. Ion concentrations, alkalinity, total hardness, TDS, conductivity, and reported disinfectant concentrations expose policy-controlled resolution for an exact numeric range, and derive a midpoint only when `allow_exact_range_midpoints` is explicitly enabled. This prevents later comparison or optimization code from silently opting into midpoint substitution merely by reading a convenience property. Bounds, `ND`, and qualified ion ranges without an independently reported average remain unresolved and are omitted from the derived aqueous state rather than treated as zero. Each reported ion receives a structured resolved/unresolved outcome so the calculation method or unresolved reason remains auditable.

### 10.7 Nonlinear quantities

A generic midpoint policy must never be applied automatically to nonlinear/logarithmic quantities such as pH. Each such quantity requires its own scientifically justified aggregation semantics.

### 10.8 Derived values

Derived values should carry or be reproducibly associated with:

- model/version;
- assumptions;
- source fields used;
- calculation method;
- warning/approximation status where applicable.

The deterministic calculation layer uses an exact derived aqueous chemical state with canonical float concentrations in mg/L. An ion omitted from that state is **unknown/not represented**, not zero. Forward treatment application records a structured per-ion resolved/unresolved outcome. A known treatment contribution to an omitted ion remains available for audit, including the treatment index and requested addition that produced it, but it is not called the final total concentration unless the starting state explicitly contains a known value (including an explicit zero when zero is genuinely known).

Canonical unit normalization is not permission to erase original reporting semantics. Derived or normalized values must not overwrite source measurements.

## 11. Source versus target semantics

Source and target profiles are deliberately separate types because they answer different questions.

A **source profile** says:

> This is what this available water source was measured or reported to contain.

A **target profile** says:

> This is the chemistry we would like the treated water to approach or satisfy.

Consequences:

- source profiles emphasize source-document metadata, water identity, dates, plants/locations, report semantics, averages, ranges, and detection limits;
- target profiles emphasize desired values, acceptable ranges, weights, hard limits, and use context;
- historical city profiles belong under target/reference data unless there is a specific historical source-water analysis being represented;
- an achieved treated liquor from a prior successful batch may later be saved as a target for reproduction without pretending it was the original source water.

The deterministic comparison boundary operates on an exact derived `AqueousChemicalState`. Exact target values are closed point criteria; ordinary exact-ended target ranges are inclusive; and standalone numeric upper/lower bounds are one-sided criteria. Signed deviation is negative below a criterion, positive above it, and zero when the criterion is satisfied. A missing state ion remains indeterminate rather than becoming zero. Qualified source-style ranges and `ND` target records remain representable for provenance but are explicitly unsupported for numeric matching until a concrete target semantics exists. A target pH is likewise retained as not calculated until the reusable working-water pH model is implemented; reported source pH is never substituted for derived working-water pH.

## 12. Reference data and real-world fixtures

Reference data is version-controlled and is never accepted merely because it appeared in an old calculator or an uncited table.

### 12.1 Real-report pressure-test corpus

A cross-project review with FermentationJSON examined recent municipal and bottled-water reports from:

- San Francisco;
- Bend;
- Santa Cruz;
- California Water Service / Chico;
- Boulder;
- Asheville;
- Niagara Bottling;
- Primo Water / Sparkletts.

This corpus exposed reporting patterns that must shape the calculator model rather than being treated as parser edge cases: `ND`, explicit bounds, censored range endpoints, several kinds of reported statistics, result-specific timing, typical-analysis coverage, distinct water identities, multiple sampling stages, and regulatory limits adjacent to measured results.

These reports should remain a standing pressure-test corpus for both the calculator and FermentationJSON schemas.

### 12.2 Source-water fixtures

The repository currently contains five data-driven real-report fixtures under `test-vectors/water/reports/`:

- **Santa Cruz 2025** — multiple treatment-plant profiles, exact numeric ranges, independently reported averages, pH ranges, and no invented bicarbonate from alkalinity;
- **Niagara 2024 / 2023 analysis** — bottled finished-product context, multi-facility reported averages, explicit conductivity reference temperature, and directly reported `mg/L HCO3` normalized to the existing bicarbonate ion field while total alkalinity remains separate;
- **Primo / Sparkletts 2023** — Typical Analysis coverage, sulfate `ND–11.1 mg/L`, ordinary ranges, range-only pH, and conductivity without an invented reference temperature;
- **California Water Service / Chico 2025** — qualified potassium range `ND–4.2` with an independently reported average, plus several ordinary ranges/averages;
- **Bend 2025** — result-specific observation timing, including sodium reported in the later annual report from a 2023 sample.

Other reviewed reports—including San Francisco, Boulder, Asheville, Portland, and additional municipal/bottled-water examples—remain useful pressure-test material but do not need fixtures unless they expose a genuinely new semantic or scientific requirement.

Fixtures must retain water/report identity, reporting period or coverage type, source URL, page/table location, original units/bases, statistic labels, sampling context when reported, and the original result form.

### 12.3 Target fixtures

Historical city and brewery profiles may be useful targets but must retain source/reference attribution. A source that publishes one Burton profile and another source that publishes a different Burton profile should produce two independently attributable records, not an undocumented average.

### 12.4 Reference-data format policy

The repository may use internal version-controlled fixtures that are richer than BeerJSON when necessary to test engine semantics such as ranges, qualified endpoints, reported averages/statistics, `ND`, detection limits, result-level timing, sample context, and source-document metadata.

Such fixtures are **test/reference formats**, not a new public interchange standard.

Public brewing interchange should use BeerJSON 1.0 where its schema can represent the data, and FermentationJSON once its richer water model is available.

## 13. BeerJSON and FermentationJSON interoperability

### 13.1 BeerJSON 1.0 is the current compatibility boundary

Until FermentationJSON water schemas are ready, BeerJSON 1.0 should be supported as the established brewing interchange format wherever its model is sufficient.

The engine's internal domain model must not be limited to BeerJSON's capabilities.

BeerJSON 1.0 water concentration fields represent a single concentration value. They do not natively preserve the richer semantics now required by this engine, including:

- min/max concentration ranges;
- independently reported averages;
- upper-bound/detection-limit semantics;
- detailed source-document metadata and attribution;
- richer alkalinity/hardness reporting metadata.

### 13.2 BeerJSON import

BeerJSON-defined water information should be imported without loss of information that BeerJSON itself contains.

Adapters should preserve original BeerJSON values/units at the boundary where practical while producing valid engine domain objects.

### 13.3 BeerJSON export

Export from the richer engine model may be lossy.

When a richer measurement must be represented as BeerJSON's single value, the export policy must be explicit and deterministic. A likely representative-value precedence for linear quantities is:

```text
exact value
or, for a range:
    reported_average if present
    otherwise derived midpoint if export of a representative value is explicitly permitted
```

Any discarded range, bound, source-document metadata, attribution, or reporting semantics must be surfaced in a structured export-loss report. The adapter must never silently imply that an exported representative value was the only value originally known.

For pH, a range-only measurement has no automatically invented representative value and therefore must not be exported as an averaged pH unless an explicit, scientifically valid policy provides one.

### 13.4 FermentationJSON

FermentationJSON is intended to become the richer portable interchange/archive representation for:

- source-water profiles;
- target-water profiles;
- treated brewing liquor;
- water blends;
- water treatment plans;
- exact/range/bound/not-detected/uncertainty semantics;
- qualified range endpoints;
- named reported statistics such as ordinary average, RAA, LRAA, percentile, highest, and lowest;
- canonical and original reported quantities;
- reporting bases;
- measurement/reference conditions such as conductivity temperature;
- profile-level and result-level observation timing;
- water identity and sample/water stage;
- source-document metadata, attribution, and citations;
- regulatory/reference thresholds kept separate from chemistry;
- model assumptions and warnings.

A likely conceptual FermentationJSON reported-result structure is:

```text
reported result
├── result form (exact/range/bound/not detected)
├── reported statistic
├── unit
├── reporting basis
├── reference/measurement conditions
├── optional detection/reporting limits
├── observation date/period
├── sampling context / water stage
└── source-document metadata / attribution
```

Canonicalized values and calculator-derived representative values sit outside the immutable description of what the report actually said.

The engine models and FermentationJSON schemas should be semantically compatible but need not be structurally identical. Serialization remains an adapter responsibility.

FermentationJSON should maintain lossless import of all BeerJSON 1.0-defined information and report losses when richer FermentationJSON data is exported back to BeerJSON.

## 14. External report-ingestion boundary

Document parsing, OCR/AI extraction, confidence scoring, user review, and persistence are consumer-application responsibilities and are not engine dependencies.

The engine receives structured candidate data only after the consumer has established the intended source/report identity and measurement interpretation. Engine-domain validation must then preserve the same scientific contracts used for manually constructed profiles, including ranges, qualified/censored values, `ND`, reported statistics, pH semantics, alkalinity/hardness basis, chlorine/chloramine identity, timing/context, and source-document metadata.

An ingestion workflow must never rely on the engine to invent missing report facts or silently reinterpret ambiguous values. Reusable deterministic import helpers may be added later only when multiple concrete consumers demonstrate a stable engine-level boundary.

## 15. Calculation pipeline

```text
Validate inputs and domain semantics
        │
        ▼
Normalize dimensional quantities with FermUnits
        │
        ▼
Resolve representative values only under explicit measurement rules
        │
        ▼
Construct available source-water blend space
        │
        ▼
Calculate fixed or candidate blends
        │
        ▼
Construct derived blended-water chemical state
        │
        ▼
Apply treatment-ingredient stoichiometry
        │
        ▼
Construct final treated-water chemical state and contribution matrix
        │
        ├────────► calculate_ph(state) when explicitly requested or required
        │          by a calculation policy, using the same reusable pH engine
        ▼
Evaluate hard constraints and target deviations
        │
        ▼
Optimize under named policies
        │
        ▼
Generate distinct candidate plans
        │
        ▼
Rank, explain, and return structured results
```

Blending and treatment remain distinct operations internally even when optimized jointly. The blend state and final treated-water state are useful calculation checkpoints, but they are not separate chemistry engines.

Reported/derived semantics are resolved before a calculation uses a representative value. The calculation layer must never guess silently.

The pH capability is reusable and state-based. Any consumer may request pH for a source, blended-water, or final treated-water state when the model's input contract is satisfied; the engine exposes one calculation rather than product-specific variants.

## 16. Version 1.0 scope and release sequence

Version 1.0 is the stable reusable engine, not an end-user application release. Consumer products may begin earlier against pinned pre-1.0 engine versions and should feed integration findings back into the engine deliberately.

The release sequence is incremental:

- **0.2:** deterministic source -> fixed blend -> mineral additions -> result -> target/reference path;
- **0.3:** supported consumer-facing Python API around the proven forward path;
- **0.4:** curated and classified target/reference data;
- **0.5:** first automatic treatment optimizer;
- **0.6:** ranked practical treatment strategies;
- **0.7:** reusable working-water pH and richer diagnostics if scientifically ready;
- **0.8:** BeerJSON/FermentationJSON interchange, versioned contracts, conformance work, and 1.0 hardening;
- **1.0:** stable documented engine and conformance boundary.

### 16.1 Version 1 engine capabilities

1. **Reported source-water representation** preserving exact/ranged/bounded/`ND` values, statistics, pH, reporting bases, identity, timing/context, provenance, and supported disinfectants.
2. **Target/reference semantics** that distinguish desired targets from sourced references and preserve evidentiary classification/provenance.
3. **Deterministic forward treatment** through explicit source resolution, fixed multi-source blending, supported mineral additions, derived blend/final states, contribution accounting, preparation instructions, notices, and target comparison.
4. **Automatic optimization** for supported blends/additions with explicit feasibility/compromise diagnostics, practical rounding, and ranked named policies.
5. **Reusable working-water pH** only if a defensible state-based model, minimum-input contract, reference cases, and limitations are validated. Missing support remains explicit rather than guessed.
6. **Interchange and conformance** through BeerJSON/FermentationJSON adapters where appropriate, versioned result/request contracts, reference data, and portable test vectors.
7. **Supported consumer API** that remains framework-neutral and does not return HTML, ORM objects, or product-specific state.

### 16.2 Consumer-facing API milestone (0.3)

The published 0.2 module APIs are sufficient for pinned early consumers, but
that release's `water_chemistry_engine.__init__` exports only `__version__`.
Release 0.3 establishes a bounded documented facade around the proven
forward-calculation boundary, provides integration examples, defines pre-1.0
compatibility expectations, and adds tests for the supported surface.

The first 0.3 implementation slice now establishes that package-root facade on
the development branch. Its explicit `__all__` includes the forward entry
point, request/input models, the complete nested source/blend/treatment audit
graph, contribution matrices, preparation instructions, comparison types,
notice codes, and supported simple treatment ingredients required for a
complete workflow.
`docs/CONSUMER_API.md` defines the supported boundary and compatibility policy;
API-level tests exercise a complete calculation, its audit and instruction
outputs, and conservative unknown propagation using only root imports. The
facade delegates to the existing 0.2 workflow and does not duplicate scientific
logic.

The first external review of this slice identified that exporting only the
outer forward-result types left their nested audit unions outside the declared
compatibility boundary. Those nested result types are therefore part of the
facade. This does not automatically make every transitive domain model a root
export: richer `SourceWaterProfile` provenance/property fields and generalized
treatment-ingredient authoring require separate, explicit contract decisions.

Convenience helpers should be driven by real consumer friction. They must not erase reported-value semantics, silently choose representative values, or move scientific/domain policy into an application.

### 16.3 Version 1 reference data

- Validated treatment-ingredient definitions.
- Curated beer, mead, and distilling targets with explicit source/reference attribution.
- Historical-city profiles clearly identified as references rather than silently canonicalized.
- RO and distilled profiles represented explicitly rather than assumed silently.
- Real municipal/bottled-water fixtures with source-document metadata and report semantics.
- Independently calculated stoichiometric reference cases.
- Well-sourced cross-domain target/reference data may be added before Version 1 when it can use the generic water machinery without requiring a new scientific engine.

Coffee is the strongest early candidate because formal published water standards and scientific reference material exist. Tea follows evidence. Bread/pizza entries may include regional, practitioner, point-of-use, or experimental reference waters, but must not be labeled optimal unless the evidence actually establishes an optimum.

### 16.4 Deliberately deferred from the Version 1 critical path

- recipe-dependent mash-pH prediction;
- grain buffering models;
- acid and alkali optimization;
- recipe-aware separate mash/sparge optimization;
- general-purpose geochemical equilibrium, precipitation, and solubility modeling beyond focused validated needs;
- robust uncertainty propagation through optimization;
- sophisticated cost or multi-batch planning beyond reusable caller-supplied constraints;
- a generalized non-additive `TreatmentOperation` framework for activated carbon, ion exchange, modeled reverse osmosis, deaeration, softening, and similar processes.

Product-owned document extraction/review, persistence, accounts, and user-interface milestones are outside the engine roadmap.

## 17. Version 2.0 — advanced brewing-water chemistry

Version 2 adds capabilities that require deeper chemistry models or materially different optimization constraints:

- acid additions;
- alkali additions;
- alkalinity neutralization;
- recipe-aware separate mash and sparge treatment;
- recipe-aware mash-pH prediction;
- deeper carbonate/bicarbonate chemistry beyond the focused working-water pH capability;
- precipitation and solubility considerations where practical;
- uncertainty propagation;
- optimization using uncertain or ranged source-water reports;
- sensitivity and worst-case plans;
- Pareto-front exploration;
- optional treatment-cost inputs;
- optional inventory integration;
- expanded brewery-scale workflows.

Purpose-aware brewery guidance may begin in an early post-1.0 release using existing validated treatment capabilities; deeper recipe-aware chemistry remains Version 2 work.

Mash-pH prediction must clearly separate predicted, calculated, and measured pH and use versioned validated models.

## 18. Version 3.0 — domain-specific food and beverage applications

Version 3 is reserved for genuine domain-specific scientific models, not merely for adding well-sourced target/reference data to the generic calculator. Potential independently validated modules include:

- coffee extraction/sensory guidance;
- tea infusion/extraction guidance;
- bread;
- sourdough;
- pizza dough;
- alkaline noodles;
- ramen/kansui;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages.

These modules may share source-water composition, blending, source-attribution metadata, treatment, target/reference, and optimization infrastructure while retaining their own constituents, targets, treatment rules, sensory/process priorities, warnings, references, and validation suites. Consumer applications may expose whichever validated domains they need without forcing domain-specific assumptions into the shared water core.

The project must not imply that one generic ion-matching score predicts sensory quality across all foods or beverages.

A generalized non-additive `TreatmentOperation` abstraction may be introduced when concrete validated brewing, coffee, or other workflows demonstrate the need. It should not be built merely to anticipate filtration, dechlorination, reverse osmosis, ion exchange, softening, or deaeration.

## 19. Version 4.0 — selected industrial applications

Selected non-food process-water modules may be considered only after dedicated safety, regulatory, materials-compatibility, treatment, and validation research.

Possible areas include laboratory preparation water, cleaning/rinsing, boiler/steam feedwater, cooling water, and selected manufacturing processes.

Industrial support must not be created by simply relabeling the food-oriented optimizer.

## 20. Optimization design

### 20.1 Decision variables

Version 1 decision variables may include:

- volume or fraction of each source water;
- mass of each solid treatment;
- optional binary variable indicating whether a treatment product is used;
- practical rounded amount where discrete dosing is required.

### 20.2 Constraints

- Source fractions sum to the required volume.
- Source amounts remain within availability bounds.
- Treatment quantities remain within validated limits.
- Hard target limits are respected when feasible.
- Decision variables cannot be negative.
- User-excluded waters and ingredients remain unused.

### 20.3 Objective components

Objective components should be calculated separately rather than hidden in one undocumented score:

- weighted ion deviation;
- hard-constraint violation penalty;
- number of treatment products;
- total treatment mass;
- dilution-water usage;
- deviation introduced by dose rounding;
- optional application-provided cost.

### 20.4 Named policies

Named policies map to documented objective weights and constraints and must be versioned.

Examples:

- closest match;
- fewest products;
- lowest total addition;
- least dilution;
- no dilution;
- water-only;
- permitted ingredients only.

The engine should generate multiple candidate plans, remove duplicates/operational equivalents, then rank the meaningful alternatives.

### 20.5 Result exactness language

Results must distinguish:

- exact within declared numerical tolerance;
- all target ranges satisfied;
- closest feasible under constraints;
- mathematically feasible but operationally impractical;
- infeasible with supplied sources/treatments;
- solver failure or indeterminate result.

## 21. Units and localization

### 21.1 Recommended canonical calculation units

- volume: liter;
- solid mass: gram;
- liquid treatment volume: milliliter;
- ion concentration: milligram per liter;
- molar concentration: mole or millimole per liter;
- equivalent concentration: milliequivalent per liter;
- temperature: degree Celsius;
- density: kilogram per liter or gram per milliliter;
- conductivity: microsiemens per centimeter where used canonically.

### 21.2 Consumer input and display units

Consumer boundaries may accept or display quantities such as:

- liters, milliliters, hectoliters;
- US liquid gallons, quarts, pints, fluid ounces;
- Imperial gallons, quarts, pints, fluid ounces;
- kilograms, grams, milligrams, micrograms;
- ounces, pounds, grains;
- mg/L, µg/L, g/L;
- ppm/ppb only under documented assumptions;
- mol/L, mmol/L;
- eq/L, mEq/L;
- hardness/alkalinity reporting units;
- brewing addition rates such as g/L, g/US gal, g/hL, and lb/US beer barrel.

The engine should normalize dimensional quantities without conflating unit conversion with chemical reporting semantics. Locale and product presentation are consumer concerns and must never change stored/scientific meaning.

### 21.3 FermUnits boundary

FermUnits handles physical quantities and conversions. Version 0.1.3 also owns
a non-Pint semantic `PHValue` and the exact pH-to-hydrogen-ion-activity
transform. It does not own an activity model, concentration/activity
conversion, calculated water pH, or measurement-result metadata.

The engine imports `Q_` and the public generic `Quantity` type from FermUnits,
not directly from Pint. Pint remains the underlying physical-unit
implementation and its genuine quantity objects cross the boundary, but
FermUnits owns the dependency, supported version range, registry, and public
typing surface used here.

The water engine retains semantic information and chemistry policy that is not
merely dimensional, including:

- analyte identity;
- `as CaCO3` basis;
- reported vs. derived status;
- reported versus calculated pH, ranges/statistics, measurement context, and
  every model-dependent pH operation;
- treatment ingredient identity/hydration state;
- source-document/reference attribution metadata;
- source/target semantics.

Reported/source quantities preserve supported scalar magnitude representations
(`int`, `float`, `Decimal`, or `Fraction`) rather than erasing Pint's magnitude
type with `Any` or coercing source data to binary floating point. Derived
engineering calculations may deliberately normalize to `float` at a documented
calculation boundary. Array/vectorized quantities remain out of scope until an
implemented feature requires them.

## 22. Public API direction

Release 0.3 establishes a deliberately bounded supported Python facade. The public API accepts framework-neutral structured requests/domain objects and returns structured results plus stable warning/explanation codes.

The 0.2 implementation already exposes the forward workflow through module-level APIs such as `ForwardWaterSource`, `SourceResolutionPolicy`, `TreatmentAddition`, and `calculate_forward_water(...)`. Those paths are usable by pinned pre-1.0 consumers but are not yet the final top-level facade.

The implemented package-root direction is:

```python
from water_chemistry_engine import calculate_forward_water

result = calculate_forward_water(...)
```

The supported result graph includes the derived state, source-resolution,
fixed-blend, treatment-application, contribution-matrix,
preparation-instruction, comparison, and notice types needed to interpret the
complete forward result without importing their defining modules. Root export
does not imply that every transitive source-report or future ingredient model
is already a stable authoring contract; those boundaries are documented and
added deliberately.

Future capabilities such as `calculate_ph(...)` and `optimize_treatment(...)` should join the public facade only when their scientific contracts are implemented and validated.

The public API must not return HTML or depend on application database objects. Convenience APIs must not silently hide source-resolution policy, unknowns, or scientific assumptions.

## 23. Cross-platform conformance strategy

The Python engine is the reference implementation, not necessarily the runtime used by every future consumer.

The engine should:

1. stabilize behavior and domain contracts;
2. publish versioned request/result schemas where a platform-neutral contract is justified;
3. publish portable conformance vectors;
4. require alternative implementations to pass the shared vectors before claiming equivalent behavior.

This preserves calculation consistency without making the engine repository own any particular native/mobile product.

## 24. Testing and validation strategy

### 24.1 Unit tests

- domain validation;
- ion/concentration behavior;
- range and reported-average semantics;
- `ND`, upper/lower bound, and qualified range-endpoint semantics;
- named reported-statistic preservation;
- profile-level and result-level timing precedence;
- sample/water-stage preservation;
- regulatory-reference separation from chemistry;
- reporting-basis preservation;
- pH nonlinear semantics;
- stoichiometric contribution for each treatment ingredient;
- unit conversions and dimensional rejection;
- target deviation/range logic;
- practical rounding;
- warning/explanation codes.

### 24.2 Required pH tests

Tests must prove that:

- a reported average pH is preserved exactly;
- a pH range without a reported average does not yield an arithmetic midpoint;
- range-only pH does not pretend to have a representative average;
- individual-observation aggregation, if implemented, occurs in linear hydrogen-ion activity/concentration space under an explicit model;
- any calculated pH aggregate is marked derived, not reported;
- `calculate_ph(...)` never mutates or populates `ReportedPH`;
- chemically equivalent states produce equivalent pH regardless of whether the state originated as a single source, blend, or treated-water result;
- insufficient chemical state produces an explicit insufficient-data outcome rather than a guessed pH;
- calculated pH results retain the selected model/version and material assumptions/reference conditions;
- changing a model-relevant input invalidates/requires recalculation of the previously derived pH at the application/result-state boundary.

### 24.3 Property-based tests

- blend fractions sum correctly;
- blended concentration remains within source extrema for conservative linear constituents;
- reordering source waters does not change a blend result;
- equivalent unit inputs produce equivalent canonical results;
- zero additions leave blend chemistry unchanged;
- no negative decision-variable volumes/additions are returned;
- adding a zero-volume source has no effect.

### 24.4 Reference tests

- official utility/laboratory water reports;
- published analytical examples where licensing permits;
- independently calculated stoichiometric examples;
- cross-checks against trusted brewing references;
- legacy BrewSession calculator outputs only after verifying their formulas and assumptions.

### 24.5 Optimizer tests

- known exact solutions;
- known infeasible problems;
- source-ion-above-target diagnostics;
- ingredient coupling cases;
- discrete weighing increments;
- deterministic candidate ranking;
- distinct-plan generation.

### 24.6 Cross-platform conformance vectors

Portable versioned request/result pairs should allow Swift, Kotlin, Dart, JavaScript, or other implementations to demonstrate conformance with the reference engine.

## 25. Safety and scientific-integrity considerations

- Treat acids and alkalis as hazardous once supported.
- Include practical-dose limits and clear warning codes.
- Never infer missing concentration, purity, hydration state, or reporting basis without exposing the assumption.
- Never silently replace reported data with calculated data.
- Never silently convert alkalinity to bicarbonate.
- Never arithmetic-average pH.
- Never coerce `ND` to zero or an unspecified detection limit.
- Never treat a regulatory/advisory threshold as a measured concentration.
- Never confuse chloride with chlorine, total chlorine, or chloramine; preserve the source's disinfectant terminology and reporting basis.
- Keep source citations, report periods, and data dates visible.
- Prevent malformed units and impossible values from reaching optimizers.
- Put critical calculation limits in the engine, not only in consumer-side validation.
- Do not present target matching as a guarantee of flavor, fermentation performance, or safety.
- Externally extracted report values require deterministic engine validation before they are treated as normal source-profile data; interactive review policy belongs to the consuming product.

## 26. Current implementation status

As of this revision, the engine repository supports Python 3.11 through 3.14, with Python 3.11 as the compatibility baseline, plus uv, Ruff, mypy, pytest, Hypothesis, GitHub Actions, the installable `water-chemistry-engine` distribution, and FermUnits 0.1.2 from PyPI. CI executes the runtime test suite across Python 3.11, 3.12, 3.13, and 3.14, while Ruff and mypy are configured against Python 3.11 language semantics. The reproducible project gate synchronizes the engine and development dependencies before running formatting, linting, strict typing, tests, and the engine distribution build.

Implemented and tested domain work includes:

- canonical ion identifiers;
- exact ion concentrations;
- exact and qualified concentration ranges;
- exact, upper-bound, lower-bound, and not-detected range endpoints;
- standalone upper-bound, lower-bound, and not-detected concentration results;
- independently reported ordinary averages for linear ranges;
- derived midpoint-on-demand behavior only for exact numeric linear ranges without a reported average;
- explicit refusal to invent a representative value for qualified ranges without a reported average;
- controlled reported-statistic semantics including single observation, ordinary average, RAA, LRAA, percentile, highest, lowest, and explicitly labeled other statistics;
- reusable result context for result-specific timing, coverage semantics, water stage, and sample location;
- `WaterIdentity` and physical-source identity separate from source-document metadata;
- `SourceDocumentMetadata` with publisher vs. optional explicit analysis provider, title/date/URL/retrieval/page-reference/notes;
- source-water profiles with mutually exclusive single observation dates and observation periods;
- target-water profiles;
- alkalinity with explicit `as CaCO3` basis;
- total hardness with explicit `as CaCO3` basis;
- TDS;
- conductivity with optional reference temperature;
- structured `ReportedPH` with exact/range/reported-average semantics and enforced prohibition on arithmetic midpoint/mean behavior for range-only pH;
- bicarbonate-alkalinity reporting-basis conversion for an explicitly identified bicarbonate result without treating total alkalinity as bicarbonate;
- five data-driven real-report fixtures: Santa Cruz, Niagara, Primo/Sparkletts, Cal Water/Chico, and Bend;
- focused reported-disinfectant preservation, including unqualified chlorine, free/total/combined chlorine, chloramine/named chloramine species, chlorine dioxide, source labels/bases, and result context/statistics.

The full project gate is maintained with Ruff formatting/lint checks, strict mypy, and pytest. Hypothesis property tests exercise core blend, contribution-accounting, and target-comparison invariants in addition to the example-based suite.

The real-report pressure-test phase has served its immediate purpose. Additional reports should be added only when they expose a genuinely new semantic or scientific requirement rather than simply increasing fixture count.

First-class source-report preservation of chlorine/chloramine and related disinfectant reporting is now implemented. The Santa Cruz 2025 fixture pressure-tests an unqualified distribution-system `Chlorine` result as its own reported disinfectant rather than inferring free chlorine or mapping the result to chloride. Treatment/removal modeling remains deliberately out of scope for this representation layer.

Release 0.2 completes the **deterministic forward treatment calculation** boundary. Validated simple treatment-ingredient identities, generic stoichiometric ion contributions, exact derived aqueous chemical states, forward application of one or more additions to a known water volume, explicit source-profile-to-derived-state resolution, fixed source-water blending by volume or fraction, structured target/reference comparison, and end-to-end orchestration across those boundaries are implemented. The forward-calculator result retains every source-resolution result, the normalized fixed-blend result, treatment-application result, explicit blend/final states, and optional source/blend/final target comparisons rather than flattening the workflow into final numbers. Blend and treatment results both preserve structured per-ion resolution outcomes and contribution detail while keeping unknown totals unknown. Target comparison preserves exact/range/bound satisfaction and signed deviation, keeps missing state ions indeterminate, refuses to reinterpret qualified ranges or `ND` as numeric targets, and retains target pH as explicitly not calculated until a validated working-water pH model exists. Boundary classification uses a 1e-9 mg/L absolute tolerance solely to suppress floating-point representation noise from otherwise exact deterministic arithmetic; this tolerance is not a chemical, sensory, or user-facing "close enough" policy. A combined row-per-ion contribution matrix now reshapes the existing blend and treatment audit records for presentation without recalculating chemistry. It preserves each source and treatment as a stable column, distinguishes positive-volume unknown source chemistry from zero-volume sources, distinguishes noncontributing treatment ingredients from unknown data, and retains known partial source/treatment contribution subtotals without presenting them as complete totals when the blend or final concentration is unresolved. Structured preparation instructions now transform those already-calculated blend/treatment results into deterministic human-readable actions while retaining canonical quantities for consumer reformatting. Zero-volume sources and zero-mass treatment rows remain in the calculation/audit results but are omitted from actionable instruction text because they require no physical action. Forward-result notices now surface calculation assumptions and result limitations that consumers should not have to reconstruct from nested audit records: midpoint use, unresolved contributing source results, first-order carbonate-species blending, the complete-dissolution treatment model, unknown final-target actuals, unsupported final-target criteria, and deferred final-target-pH comparison. Source- and blend-stage target comparisons remain available on their own structured results rather than duplicating target notices at every stage. These notices do not change chemistry and preserve structured codes/context alongside deterministic English messages. That completes the deterministic 0.2 forward-result boundary; the next engine focus is a deliberate supported consumer-facing API around these proven capabilities.

## 27. Development milestones

### Milestone 0 — repository foundation — substantially complete

- public repository and MPL-2.0 license;
- single-project uv/`src` packaging;
- engine package skeleton;
- Ruff, mypy, pytest, Hypothesis, CI;
- core design and roadmap documents.

### Milestone 1 — FermUnits and measurement semantics — substantially complete

Completed:

- FermUnits dependency;
- ion identifiers;
- exact/range/bound/`ND`/qualified-endpoint semantics;
- ordinary reported-average and named reported-statistic semantics;
- source profiles and target profiles;
- source-document metadata, water identity, physical source, observation timing, coverage, and water-stage context;
- alkalinity/hardness/TDS/conductivity;
- structured reported-pH semantics;
- bicarbonate-alkalinity basis normalization for explicitly identified bicarbonate results;
- five data-driven real-report fixtures exercising the implemented semantics;
- reported disinfectant preservation beginning with chlorine/chloramine.

### Milestone 2 / release 0.2 — deterministic forward calculator — complete

Completed:

- validated simple treatment-ingredient identities, including hydration state;
- generic stoichiometric ion-contribution calculation;
- exact derived aqueous ion-state representation;
- forward application of zero or more simple mineral additions to a known water volume with per-treatment contribution detail;
- explicit source-profile-to-derived-state resolution under a caller-supplied representative-value policy, including auditable unresolved reasons;
- fixed one-, two-, and multi-source blending by volume or fraction with auditable per-source ion contributions and conservative unknown propagation;
- target/reference profile comparison for exact values, exact-ended ranges, and one-sided numeric bounds, including signed deviation and explicit indeterminate/unsupported outcomes;
- end-to-end forward orchestration from reported source profiles through source resolution, fixed blending, mineral additions, explicit blend/final states, and optional source/blend/final target comparison;
- combined source/treatment contribution matrices built from existing audit records without a second chemistry calculation;
- structured human-readable preparation instructions built from the fixed blend and treatment results without a second chemistry calculation;
- structured forward-result notices for material calculation assumptions, unresolved contributing source values, treatment-model assumptions, target limitations, and deferred target-pH comparison;
- Python 3.11–3.14 runtime support with Python 3.11 as the compatibility baseline.

### Milestone 3 / release 0.3 — supported consumer API

- documented top-level/public forward-calculation facade;
- integration examples around the 0.2 workflow;
- API-level compatibility tests;
- explicit pre-1.0 request/result evolution policy;
- application-driven convenience improvements only where they preserve scientific semantics.

### Milestone 4 / release 0.4 — curated target/reference data

- generic target/reference classification and provenance enhancements;
- brewing/mead/distilling profiles;
- well-sourced coffee profiles/standards;
- tea profiles where evidence permits;
- defensible regional, practitioner, point-of-use, or experimental dough/bread/pizza references;
- reference-data validation/versioning.

### Milestone 5 / releases 0.5–0.6 — optimization

- continuous closest-match blend/mineral optimizer;
- constraints and diagnostics;
- practical dose rounding/re-evaluation;
- ranked named policies;
- mixed-integer support only where concrete policies require it.

### Milestone 6 / release 0.7 — reusable working-water pH and diagnostics

- scientifically validated `calculate_ph(chemical_state)` capability if ready;
- explicit insufficient-data results;
- model/version/assumption reporting;
- same capability reusable for source, blend, and final treated states.

A weak pH approximation is not a release requirement; unsupported derived pH may remain unknown.

### Milestone 7 / release 0.8 — interchange and 1.0 hardening

- BeerJSON import/export with explicit loss reporting;
- FermentationJSON adapters when its water schema is ready;
- stable calculation/result contracts;
- expanded authoritative reference tests and conformance vectors;
- chemistry model, package, optimizer, and reference-data versioning.

### Milestone 8 — Version 1.0 release

- stable end-to-end manual and optimized engine workflow;
- stable supported consumer API;
- documented assumptions, operating limits, and unsupported calculations;
- complete release/conformance gate.

### Early post-1.0

- purpose-aware brewery-water guidance using request context;
- additional treatment chains as concrete validated requirements justify them.

## 28. Open design questions

1. Exact boundary between frozen dataclasses and Pydantic boundary models.
2. Exact supported top-level API surface for release 0.3 and which current module paths remain public.
3. Whether SciPy's MILP support is sufficient for all Version 1 discrete policies.
4. First authoritative composition sources for each included treatment ingredient.
5. Redistribution/licensing policy for historical city, brewery, and style targets.
6. Exact BeerJSON water adapter behavior and structured loss-report schema.
7. Exact FermentationJSON water-profile and treatment-plan adapter contract once its schema is stable enough to implement.
8. Whether additional alkalinity normalization belongs partly in FermUnits or entirely in engine semantics.
9. How target-match scores should be normalized and explained.
10. Whether charge-balance diagnostics should only warn or may optionally suggest likely missing information without altering source data.
11. How regulatory/reference thresholds should be represented when preserved for report fidelity without contaminating chemistry models.
12. Exact aqueous equilibrium/activity model, validated reference data, and minimum chemical-state inputs for the reusable `calculate_ph(...)` capability.
13. Exact reusable representation for reported disinfectants and other non-optimization analytes once chlorine/chloramine support expands beyond the first concrete cases.
14. First validated set of intended-water-use values for early post-1.0 purpose-aware guidance versus deeper Version 2 models.
15. Exact generic metadata vocabulary for target versus reference profile classification without overfitting to coffee, tea, or dough.

## 29. Versioning policy

Version independently where appropriate:

- Python package releases;
- chemistry-model revisions;
- measurement-semantics revisions;
- optimization-policy revisions;
- bundled reference datasets;
- BeerJSON adapter compatibility;
- FermentationJSON adapter/schema compatibility;
- cross-platform conformance-vector versions.

A consumer-application-only change should not imply that chemistry results were produced by a new engine model. Conversely, a change to stoichiometric data, representative-value policy, pH aggregation, or scoring semantics must be traceable even if the public Python API remains source-compatible.

## 30. Summary decision

The repository is now explicitly the open-source Water Chemistry Engine rather than a combined engine-and-application project. Release 0.2 completes deterministic source -> blend -> treatment -> result -> target/reference calculations and establishes Python 3.11 as the compatibility baseline. Release 0.3 will make those capabilities easier and safer for external products to consume through a deliberate supported API.

Consumer applications may begin now against pinned 0.2 APIs. Their development is expected to pressure-test the engine and reveal useful improvements, but the ownership boundary is strict: chemistry, water-domain interpretation, validation, optimization, calculation semantics, and scientific notices belong in the engine; presentation, persistence, authentication, workflow, and interaction state belong in the application.

Version 1 will provide a reusable, explainable water-chemistry engine for supported beer, mead, and distilling workflows while keeping the underlying water core generic. It preserves real-world source-report semantics—including exact values, ranges, bounds, `ND`, qualified endpoints, named statistics, reporting bases, timing, water identity, sampling context, source-document metadata, and source-reported disinfectants such as chlorine/chloramine—while supporting multiple sources, exact and ranged targets/references, practical mineral additions, final-state comparison, automatic and ranked treatment plans, contribution data, source/reference attribution, and stable consumer contracts. Intended water use remains calculation/request context rather than part of source-water identity.

The engine deliberately distinguishes reported from derived chemistry. Linear ranges may use an on-demand midpoint only when no reported average exists, both endpoints are exact, and the caller explicitly enables midpoint resolution through `SourceResolutionPolicy`. Qualified ranges do not receive an automatic representative value. pH is explicitly excluded from generic linear averaging because it is logarithmic: range endpoints are preserved, reported averages are trusted only when actually reported, and any derived pH calculation uses an explicit scientifically documented aqueous model. A missing derived-pH model must not block otherwise valid forward treatment calculations.

Well-sourced coffee, tea, bread, sourdough, or pizza target/reference data may be added early when the generic water machinery can represent it. This does not imply that a complete domain-specific predictive engine exists. Regional, historical, practitioner, experimental, standard, and optimized profiles must retain distinct evidentiary classifications.

BeerJSON and FermentationJSON adapters are intentionally later engine milestones so they do not block the supported forward-calculation API. FermentationJSON remains the intended richer long-term interchange representation without constraining the internal engine model or diminishing BeerJSON compatibility. Product-owned AI/document extraction and review workflows remain outside the engine repository.
