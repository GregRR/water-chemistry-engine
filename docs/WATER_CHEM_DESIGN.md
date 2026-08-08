# Water Treatment Engineering Engine Design

**Document:** `docs/WATER_CHEM_DESIGN.md`  
**Status:** Working design — active implementation  
**Revision:** 2026-08-07  
**Project:** Water Treatment Calculator / Calculators  
**Repository:** `water-treatment-calculator`  
**Engine distribution:** `water-treatment-engine`  
**Engine import package:** `water_treatment_engine`  
**Standalone web distribution:** `water-treatment-web`  
**License:** Mozilla Public License 2.0  
**Initial audience:** Homebrewers, meadmakers, craft distillers, and small breweries/distilleries

## 1. Purpose

The Water Treatment Engineering Engine is a reusable, scientifically grounded system for analyzing source water and designing practical water blends and treatment plans.

It is not intended merely to reproduce traditional brewing-water calculators that require users to manually trial salt additions until the displayed ions look close to a target. The engine should accept source-water chemistry, a target profile, available water sources, permitted treatments, and practical constraints, then calculate and rank useful treatment plans automatically.

The engine must remain independent of web frameworks, databases, graphical interfaces, operating systems, and hardware. It should be usable by:

- the standalone calculator web application;
- Mecha-Brew;
- future native mobile and desktop applications;
- Python scripts and notebooks;
- APIs and third-party software;
- automated recipe and batch-planning workflows.

## 2. Product goals

The project should make sophisticated water treatment approachable without hiding the underlying chemistry or provenance.

The system should:

1. Model source water, target water, blends, treatment additions, and resulting brewing liquor as distinct concepts.
2. Preserve the difference between reported, measured, inferred, estimated, and calculated data.
3. Preserve exact values, ranges, qualified bounds, `ND`/not-detected states, reporting bases, named reported statistics, original units, and provenance.
4. Blend two or more waters by volume.
5. Determine practical mineral additions automatically.
6. Optimize water proportions and treatment additions jointly when appropriate.
7. Produce several meaningfully different ranked solutions instead of claiming one universal optimum.
8. Explain why each solution was selected, where it compromises, and why some targets are infeasible.
9. Show each source water and treatment ingredient's contribution to every modeled ion.
10. Support dated source-water profiles so an earlier successful brewing liquor can be reproduced from changed current water.
11. Use FermUnits for dimensional quantities while retaining water-chemistry semantics in this engine.
12. Support BeerJSON 1.0 as the current brewing interchange boundary and richer FermentationJSON interchange when its water schemas are ready.
13. Provide a polished browser interface while keeping all scientific logic outside the interface layer.
14. Remain suitable for future conforming implementations in Swift, Kotlin, Dart, JavaScript, or other languages.
15. Preserve water identity, sampling stage/context, and result-specific timing when reports distinguish them.
16. Keep regulatory or advisory limits separate from measured or reported water chemistry.

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
- dependent on Mecha-Brew, Django, a database, or any particular application framework.

The architecture may permit later use outside brewing, but Version 1 should optimize for beer, mead, distilling, and closely related fermentation uses.

## 4. Engineering principles

1. **Keep chemistry separate from presentation.** No equations, conversion rules, or optimization policies belong in templates, browser handlers, or mobile views.
2. **Use explicit quantities.** Dimensional inputs and outputs use FermUnits/Pint quantities or are converted into them at a boundary.
3. **Preserve meaning as well as magnitude.** `mg/L as CaCO3`, bicarbonate concentration, alkalinity, hardness, conductivity, TDS, and pH are not interchangeable merely because numerical conversions can be written.
4. **Preserve provenance.** Provider, report title, report date, observation date, retrieval date, source URL, page/table reference, and notes must remain attachable to source data.
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

## 5. System architecture and dependency direction

```text
FermUnits
    │
    ▼
water-treatment-engine
    │
    ├── water-treatment-web
    ├── Mecha-Brew
    ├── future native applications
    ├── Python/API consumers
    └── test and research tooling

BeerJSON 1.0 ───────┐
                    ├── boundary adapters ── water-treatment-engine domain models
FermentationJSON ───┘
```

Responsibilities are intentionally separated:

- **FermUnits** supplies quantity representation, dimensional validation, unit conversion, equivalent chemistry conversions, and explicit unit definitions.
- **Water Treatment Engine** supplies water-chemistry semantics, reported-value semantics, blending, stoichiometry, comparison, optimization, warnings, and structured results.
- **BeerJSON/FermentationJSON adapters** translate external interchange documents to and from engine boundary/domain models.
- **Applications** supply persistence, users, forms, visual presentation, import workflows, and product-specific behavior.

The engine must never import the web application, Mecha-Brew, a database ORM, or a platform-specific UI framework.

## 6. Tooling decisions

### 6.1 Python and package management

- Python 3.14.
- `uv` for Python installation, dependency resolution, environments, locking, and workspace management.
- `uv_build` for the current pure-Python workspace packages.
- Standard `src/` package layouts.
- A non-installable root workspace project.
- Tooling should remain as consistent as practical with FermUnits, Mecha-Brew, and the other Calculators projects.

### 6.2 Current and planned core libraries

- **FermUnits 0.1.x:** required by `water-treatment-engine`; currently sourced from the released GitHub `v0.1.0` tag until the dependency strategy is intentionally changed.
- **Pint:** transitive quantity implementation through FermUnits.
- **NumPy:** planned for vector/matrix work when the calculation implementation actually requires it.
- **SciPy:** planned for continuous and mixed-integer optimization when optimization work begins.
- **Pydantic:** planned for validation/serialization at application, API, and interchange boundaries.
- **Frozen dataclasses / simple immutable domain objects:** preferred for internal scientific models where serialization behavior is unnecessary.

NumPy, SciPy, and other substantial dependencies should not be added merely because they are expected eventually; add them when an implemented feature needs them.

### 6.3 Web application

- Server-rendered HTML.
- HTMX for dynamic form fragments, recalculation, profile selection, ranked results, and progressive disclosure.
- Minimal vanilla JavaScript only where browser-only behavior genuinely requires it.
- No mandatory React or Node build pipeline for Version 1.
- Exact Python ASGI framework remains deliberately undecided until the web implementation requires a concrete choice.

The standalone web application is an adapter around the engine. Mecha-Brew will import the same engine directly and render its own seamless interface.

### 6.4 Quality tooling

- `pytest` for unit, integration, regression, and reference tests.
- `Hypothesis` for property-based testing.
- Ruff for linting and formatting.
- mypy for static type checking.
- GitHub Actions for CI.
- Coverage reporting as a diagnostic, not as a substitute for meaningful tests.

## 7. Repository and packaging strategy

The water-treatment project is a public repository. The commercially sensitive draft-system project is a separate private repository. They share conventions, not a repository.

```text
water-treatment-calculator/
├── .github/
│   └── workflows/
│       └── ci.yml
├── apps/
│   └── water-treatment-web/
├── packages/
│   └── water-treatment-engine/
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
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── LICENSE
└── README.md
```

The engine and web application are independently installable workspace members. The web package depends on the engine; the engine does not depend on the web package.

No `calculators-common` package should be introduced until at least two calculator projects demonstrate a stable concrete need that is genuinely shared.

## 8. Current engine package structure

The package is intentionally still small while the domain contracts stabilize.

```text
packages/water-treatment-engine/
├── pyproject.toml
├── README.md
├── src/
│   └── water_treatment_engine/
│       ├── __init__.py
│       ├── py.typed
│       ├── ions.py
│       ├── concentrations.py
│       ├── profiles.py
│       ├── provenance.py
│       ├── target_profiles.py
│       └── reported_properties.py
└── tests/
    ├── test_engine_package.py
    ├── test_ions.py
    ├── test_concentrations.py
    ├── test_profiles.py
    ├── test_provenance.py
    ├── test_target_profiles.py
    └── test_reported_properties.py
```

As blending, stoichiometry, optimization, comparison, serialization, and explanations grow, the package may be reorganized into subpackages. That restructuring should happen when it improves real code organization, not merely to satisfy an early hypothetical directory tree.

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

The current implementation supports numeric linear ranges containing:

- `minimum`;
- `maximum`;
- optional `reported_average`.

For an ordinary **linear concentration** whose two endpoints are exact numeric values, calculation behavior is:

```text
reported_average exists  → use reported_average
otherwise                → derive midpoint(minimum, maximum) on demand
```

The midpoint is derived data. It is not stored as `reported_average` and must never be presented as though the source reported it.

A `reported_average` field may be populated only when the source explicitly identifies the value as an ordinary average. When a reported average accompanies a reported range, the reported average takes precedence over the mathematical midpoint. For example, a source may report calcium as average `51 mg/L`, range `50–53 mg/L`; calculations use the reported `51 mg/L`, not the midpoint `51.5 mg/L`.

Real reports also demonstrate that range endpoints may themselves be censored or non-numeric. Therefore the current numeric-endpoint range type is an implementation subset, not the final general reported-result model.

### 9.4 Bounds, `ND`, and qualified range endpoints

Real water reports require at least these reported result forms:

- exact numeric value;
- numeric range;
- upper bound such as `<0.3`;
- lower bound such as `>X`;
- `ND` / not detected;
- a range whose endpoints are themselves qualified, such as `ND–11.1` or `<3–14`.

The engine currently implements exact values, exact numeric ranges, and numeric upper bounds. It must evolve to represent the remaining forms without coercing them into ordinary numbers.

`ND` is a first-class source-reported state:

```text
ND ≠ 0
ND ≠ automatically <X
```

If a report says `ND` but does not publish the applicable detection/reporting limit for that result, the engine must not invent one. If a source separately reports a numerical limit, that limit may be retained explicitly as source metadata.

Qualified range endpoints mean a future generic range cannot assume `minimum: float` and `maximum: float`. Each endpoint may need the same exact/bound/not-detected semantics as a standalone result.

Bounds, `ND`, and qualified endpoints do not automatically receive a representative calculation value. Any policy that substitutes a numeric value must be explicit, domain-specific, reproducible, and surfaced in assumptions/warnings.

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

### 9.6 Alkalinity and bicarbonate are not interchangeable

A reported alkalinity value must remain alkalinity. The engine must not silently derive or overwrite bicarbonate from alkalinity.

For example:

```text
Reported: total alkalinity = 108 mg/L as CaCO3
```

must remain that reported measurement.

If a later chemistry model calculates a bicarbonate-equivalent concentration from alkalinity under explicit assumptions, that result must be labeled **derived**, retain the assumptions/model version, and coexist with—not replace—the original reported alkalinity.

### 9.7 pH is a logarithmic scientific invariant

pH requires behavior different from linear water properties.

The fundamental relationship is:

```text
pH = -log10(a_H+)
```

where `a_H+` is hydrogen-ion activity. A concentration-based `[H+]` treatment is an approximation and must be documented as such when used.

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

The engine may later introduce a controlled `reported_statistic` concept so imported data can retain the source's statistical meaning without forcing every statistic into a separate top-level property.

### 9.9 Observation timing and data coverage

Timing exists at more than one level.

A `SourceWaterProfile` currently supports either:

- a single `observed_on` date; or
- an inclusive `ObservationPeriod(start, end)`.

Those two profile-level forms are mutually exclusive.

Real annual reports also demonstrate that individual constituents may have their own dates or periods that differ from the overall report/profile period. The model must therefore be prepared for:

```text
profile/report observation period
+
optional result-specific observation date or period
```

When result-level timing is present, it takes precedence for that result.

The source model should also be able to represent **coverage semantics** such as:

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

The engine should preserve a controlled `sample_context` / `water_stage` concept when importing data because chemistry from these stages is not interchangeable.

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

Source-water provenance is an immutable object that may contain:

- provider;
- report title;
- report date;
- source URL;
- retrieval date;
- page or table reference;
- notes.

Future provenance fields may include laboratory, analytical method, sampling location, treatment plant, report edition, source-water origin, extraction confidence, brand/product identity, and report/table context.

### 9.13 SourceWaterProfile

A source-water profile represents water that is actually available for blending or treatment.

It must support:

- a human-readable name;
- one concentration entry per ion;
- optional pH/report properties;
- single observation date or observation period when genuinely known;
- provenance;
- no duplicate ion entries.

As the model evolves it should also support or reference:

- richer water identity;
- data-coverage semantics;
- sample/water stage;
- optional result-specific timing;
- richer reported-result/statistic semantics.

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

### 9.14 TargetWaterProfile

A target profile represents desired or reference chemistry, not an incoming water supply.

Current target profiles support:

- name;
- exact or ranged ion concentrations;
- optional pH target;
- style associations;
- notes;
- duplicate-ion protection.

Future target semantics may add:

- preferred value within an acceptable range;
- hard minimum and maximum;
- optimization weight;
- flavor priority;
- mash-chemistry priority;
- provenance and target type.

Target types include:

- previous successful batch;
- custom target;
- style recommendation;
- published brewery profile;
- historical city or regional profile;
- application-provided recommendation.

Historical brewing-city tables such as Pilsen, Burton-on-Trent, Dublin, Munich, London, Dortmund, Edinburgh, Vienna, Antwerp, and Cologne are **target/reference profiles**, not claims about present-day municipal source water. Each published version must retain its own provenance; conflicting published profiles should not be silently merged into one supposedly canonical city profile.

### 9.15 Future WaterBlend

A blend records actual source-water volumes or fractions. Actual volumes should be retained whenever known; fractions can be derived.

For a conservative linear constituent, the basic blend relation is:

```text
C_blend = sum(V_i * C_i) / sum(V_i)
```

This formula does not apply blindly to pH or to censored/not-detected values that lack an explicit numeric calculation policy.

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

### 10.7 Nonlinear quantities

A generic midpoint policy must never be applied automatically to nonlinear/logarithmic quantities such as pH. Each such quantity requires its own scientifically justified aggregation semantics.

### 10.8 Derived values

Derived values should carry or be reproducibly associated with:

- model/version;
- assumptions;
- source fields used;
- calculation method;
- warning/approximation status where applicable.

Canonical unit normalization is not permission to erase original reporting semantics. Derived or normalized values must not overwrite source measurements.

## 11. Source versus target semantics

Source and target profiles are deliberately separate types because they answer different questions.

A **source profile** says:

> This is what this available water source was measured or reported to contain.

A **target profile** says:

> This is the chemistry we would like the treated water to approach or satisfy.

Consequences:

- source profiles emphasize provenance, dates, plants/locations, report semantics, averages, ranges, and detection limits;
- target profiles emphasize desired values, acceptable ranges, weights, hard limits, and use context;
- historical city profiles belong under target/reference data unless there is a specific historical source-water analysis being represented;
- an achieved treated liquor from a prior successful batch may later be saved as a target for reproduction without pretending it was the original source water.

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

Candidate source fixtures currently include:

- City of Santa Cruz, California, 2025 Water Quality Report, including distinct treatment-plant profiles and reported average/range data;
- Niagara Bottling Water Quality Report 2024, whose relevant chemistry includes separate finished-water products and 2023 aggregate analysis;
- San Francisco Public Utilities Commission 2025 water-quality report;
- Bend water-quality reporting reviewed with FermentationJSON;
- California Water Service / Chico 2025 report;
- Boulder water-quality reporting reviewed with FermentationJSON;
- Asheville water-quality reporting reviewed with FermentationJSON;
- Primo Water / Sparkletts report, including Typical Analysis data and `ND`/qualified range examples;
- Portland 2026 Drinking Water Quality Report;
- additional laboratory or utility reports as they become useful.

Fixtures must retain provider/report identity, reporting period or coverage type, source URL, page/table location, original units/bases, statistic labels, sampling context when reported, and the original result form.

### 12.3 Target fixtures

Historical city and brewery profiles may be useful targets but must retain provenance. A source that publishes one Burton profile and another source that publishes a different Burton profile should produce two independently attributable records, not an undocumented average.

### 12.4 Reference-data format policy

The repository may use internal version-controlled fixtures that are richer than BeerJSON when necessary to test engine semantics such as ranges, qualified endpoints, reported averages/statistics, `ND`, detection limits, result-level timing, sample context, and provenance.

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
- detailed report provenance;
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

Any discarded range, bound, provenance, or reporting semantics must be surfaced in a structured export-loss report. The adapter must never silently imply that an exported representative value was the only value originally known.

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
- provenance and citations;
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
└── provenance
```

Canonicalized values and calculator-derived representative values sit outside the immutable description of what the report actually said.

The engine models and FermentationJSON schemas should be semantically compatible but need not be structurally identical. Serialization remains an adapter responsibility.

FermentationJSON should maintain lossless import of all BeerJSON 1.0-defined information and report losses when richer FermentationJSON data is exported back to BeerJSON.

## 14. AI-assisted PDF water-report import

AI-assisted report import is a planned web-application feature, not an engine dependency.

### 14.1 User workflow

1. User uploads a municipal, bottled-water, or laboratory water-quality PDF.
2. The application extracts document text/tables and identifies candidate water chemistry and metadata.
3. AI-assisted extraction produces structured candidate fields, not final trusted engine data.
4. Deterministic validation checks units, ranges, reporting bases, and value consistency.
5. FermUnits normalizes accepted dimensional quantities.
6. The UI shows the extracted values for user review and correction before saving.
7. Accepted data becomes a `SourceWaterProfile` with provenance.

### 14.2 Required extraction behavior

The importer should attempt to preserve:

- calcium, magnesium, sodium, potassium;
- chloride, sulfate, bicarbonate only when actually reported;
- pH;
- alkalinity with explicit reporting basis;
- hardness with explicit reporting basis;
- TDS;
- conductivity and reference temperature;
- exact values;
- ranges, including qualified/censored endpoints;
- ordinary reported averages and other named reported statistics;
- upper and lower bounds;
- `ND` / not-detected states;
- detection/reporting limits when actually supplied;
- units and reporting bases;
- provider/report title/date;
- profile/report sample or analysis period;
- result-specific sample date/period when present;
- provider, brand, product/water type, and physical source when distinguishable;
- sampling context/water stage;
- page/table/section location;
- extraction confidence where useful.

### 14.3 Prohibited behavior

The AI/import layer must not:

- silently convert alkalinity to bicarbonate;
- replace reported values with inferred values;
- invent dates that are not present;
- treat a range midpoint as a reported average;
- arithmetic-average pH values;
- save extracted values without a user-review opportunity in the normal interactive workflow;
- coerce `ND` to zero;
- treat a regulatory/advisory limit as the measured result;
- collapse RAA, LRAA, percentile, highest/lowest, or another named statistic into an ordinary `reported_average`.

Document parsing and AI extraction remain outside `water-treatment-engine`; the engine receives validated structured data.

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
Apply treatment-ingredient stoichiometry
        │
        ▼
Calculate resulting profile and contribution matrix
        │
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

Blending and treatment remain distinct operations internally even when optimized jointly.

Reported/derived semantics are resolved before a calculation uses a representative value. The calculation layer must never guess silently.

## 16. Version 1.0 scope

Version 1.0 should be a useful end-to-end product rather than only a chemistry-library demonstration. It supports beer, mead, and distilling water where the underlying treatment model is valid. Distilling must distinguish mash/fermentation/process water from spirit-proofing water.

### 16.1 Required engine features

1. **Water-profile modeling**
   - Source and target profiles.
   - Dated and period-based provenance, with result-specific timing where reports require it.
   - Exact, ranged, bounded, not-detected, qualified-endpoint, and reported-statistic semantics.
   - Explicit alkalinity/hardness bases.
   - Correct nonlinear pH semantics.
   - Water identity and sampling-stage/context preservation.
   - Regulatory/reference thresholds kept separate from chemistry.

2. **Forward water blending**
   - Blend two or more source waters by volume.
   - Calculate resulting conservative ion concentrations.
   - Report each source's contribution.
   - Support fixed user-entered blends.
   - Do not apply linear averaging blindly to pH.

3. **Optimized blending**
   - Solve source-water proportions against a target.
   - Support source availability and maximum-volume constraints.
   - Support water-only solutions.

4. **Common mineral additions**
   - Calcium chloride in explicitly identified hydration form.
   - Calcium sulfate in explicitly identified form.
   - Magnesium sulfate heptahydrate.
   - Sodium chloride.
   - Sodium bicarbonate.
   - Other salts only after composition and use are validated.

5. **Joint blend-and-mineral optimization**
   - Optimize water proportions and mineral quantities together.
   - Do not lock in a water-only optimum when a slightly different blend produces a better complete treatment plan.

6. **Ranked solution policies**
   - exact match when feasible;
   - closest practical match;
   - fewest different treatment products;
   - lowest total mineral addition;
   - least dilution/RO usage;
   - no dilution;
   - no mineral additions / water-only blend;
   - user-selected ingredients only.

7. **Practical dosing**
   - configurable weighing precision;
   - minimum meaningful addition;
   - maximum validated addition rate;
   - recalculation after practical rounding.

8. **Explainability and diagnostics**
   - machine-readable warning/explanation codes;
   - unreachable-target explanations;
   - source ion already above target;
   - multi-ion salt coupling;
   - explicit assumptions and representative-value choices.

9. **Contribution matrix**
   - initial source contribution;
   - effect of blending;
   - contribution from each mineral;
   - final total for each modeled ion.

10. **Profile comparison**
    - raw differences;
    - range satisfaction;
    - weighted normalized score;
    - hard-limit violations;
    - charge-balance diagnostic when enough data exists.

11. **Interchange**
    - BeerJSON 1.0 water import/export for representable information;
    - explicit export-loss reporting for richer engine data;
    - FermentationJSON adapter when the relevant schema stabilizes;
    - versioned calculation/test-vector representation.

12. **Localization readiness**
    - canonical calculations independent of display locale;
    - explicit US, Imperial, and metric identifiers;
    - user-selectable input/display units;
    - no persisted ambiguous `gallon` or `fluid ounce` identifiers.

### 16.2 Required standalone web features

- Responsive desktop, tablet, and phone layouts.
- Manual source-water entry.
- Saved and built-in profiles.
- Multiple source-water rows.
- Fixed-blend calculation.
- Target entry using exact values and ranges.
- Selection of permitted salts.
- Batch volume and unit selection.
- Ranked treatment-plan cards.
- Detailed contribution tables.
- Plain-language warnings and explanations.
- BeerJSON import/export.
- FermentationJSON import/export when available.
- AI-assisted PDF water-report import after the source-report model is stable.
- Review/correction of AI-extracted water-report data before saving.
- Dated saved reports so source-water changes can be compared over time.
- No account required for basic calculations.

### 16.3 Version 1 reference data

- Validated treatment-ingredient definitions.
- Curated beer, mead, and distilling targets with provenance.
- Historical-city profiles clearly identified as reference targets.
- RO and distilled profiles represented explicitly rather than assumed silently.
- Real municipal/bottled-water fixtures with provenance and report semantics.
- Independently calculated stoichiometric reference cases.

### 16.4 Deliberately deferred from Version 1 core chemistry

- recipe-dependent mash-pH prediction;
- grain buffering models;
- acid and alkali optimization;
- separate mash- and sparge-water optimization;
- detailed precipitation/equilibrium treatment;
- robust uncertainty propagation through optimization;
- detailed inventory/purchasing/package management;
- sophisticated cost optimization;
- multi-batch production planning.

AI-assisted PDF extraction may be developed in the Version 1 web application, but it remains an ingestion workflow and must not force unvalidated chemistry into the engine.

## 17. Version 2.0 — advanced brewing-water chemistry

Version 2 should add features that require deeper chemistry models or materially different optimization constraints:

- acid additions;
- alkali additions;
- alkalinity neutralization;
- separate mash and sparge treatment;
- recipe-aware mash-pH prediction;
- deeper carbonate/bicarbonate chemistry;
- precipitation and solubility considerations where practical;
- uncertainty propagation;
- optimization using uncertain or ranged source-water reports;
- sensitivity and worst-case plans;
- Pareto-front exploration;
- optional treatment cost inputs;
- optional Mecha-Brew inventory integration;
- expanded brewery-scale workflows.

Mash-pH prediction must clearly separate predicted, calculated, and measured pH and use versioned validated models.

## 18. Version 3.0 — broader food and beverage applications

Potential independently validated domain modules include:

- coffee;
- tea;
- bread;
- sourdough;
- pizza dough;
- alkaline noodles;
- ramen/kansui;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages.

These modules may share source-water composition, blending, provenance, and optimization infrastructure while retaining their own constituents, targets, treatment rules, sensory/process priorities, warnings, references, and validation suites.

The project must not imply that one generic ion-matching score predicts sensory quality across all foods or beverages.

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

### 21.2 Input and display units

The interface may accept and display:

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

Locale selects defaults only. It must never change the meaning of stored data.

### 21.3 FermUnits boundary

FermUnits handles physical quantities and conversions. The water engine retains semantic information that is not merely dimensional, including:

- analyte identity;
- `as CaCO3` basis;
- reported vs. derived status;
- pH/logarithmic behavior;
- treatment ingredient identity/hydration state;
- provenance;
- source/target semantics.

## 22. Public API direction

The eventual public API should accept platform-neutral structured requests and return structured results and stable warning/explanation codes.

Illustrative direction only:

```python
from water_treatment_engine import blend_waters, optimize_treatment

blend_result = blend_waters(...)
optimization_result = optimize_treatment(...)
```

The public API must not return HTML or depend on application database objects.

Request/result schemas should be versioned independently enough that future native clients can conform without embedding Python.

## 23. Mobile and cross-platform strategy

The Python engine is the reference implementation, not necessarily the runtime used by every future client.

For mobile/offline use:

1. stabilize engine behavior and domain contracts;
2. publish versioned request/result schemas and conformance vectors;
3. build the web product;
4. implement native or cross-platform clients as product needs justify;
5. require alternative implementations to pass shared conformance vectors.

This avoids coupling future iOS/Android products to an embedded Python runtime while preserving calculation consistency.

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
- any calculated pH aggregate is marked derived, not reported.

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
- Keep source citations, report periods, and data dates visible.
- Prevent malformed units and impossible values from reaching optimizers.
- Put critical calculation limits in the engine, not only in UI validation.
- Do not present target matching as a guarantee of flavor, fermentation performance, or safety.
- AI-extracted report values require deterministic validation and user review before normal persistence.

## 26. Current implementation status

As of this revision, the repository foundation is operational with Python 3.14, uv, Ruff, mypy, pytest, GitHub Actions, independently installable engine/web packages, and FermUnits 0.1.0 integration.

Implemented and tested domain work includes:

- canonical ion identifiers;
- exact ion concentrations;
- numeric ranged ion concentrations;
- independently reported ordinary averages for linear ranges;
- derived midpoint-on-demand behavior for exact numeric linear ranges without a reported average;
- numeric upper-bound ion concentrations;
- source-water profiles;
- source-water provenance;
- mutually exclusive single observation dates and observation periods;
- target-water profiles;
- alkalinity with explicit `as CaCO3` basis;
- total hardness with explicit `as CaCO3` basis;
- TDS;
- conductivity with optional reference temperature;
- structured `ReportedPH` with exact/range/reported-average semantics;
- enforced prohibition on arithmetic midpoint/mean behavior for range-only pH.

The most recent clean test gate before this design revision reported **68 passing tests**.

The FermentationJSON real-report review has identified the next source-report semantics that should be implemented before serious fixture ingestion:

1. `ND` / not-detected as a first-class result state;
2. lower bounds and a generalized bound representation;
3. qualified/censored range endpoints such as `ND–11.1` and `<3–14`;
4. controlled reported-statistic semantics beyond ordinary `reported_average`;
5. optional result-specific observation date/period;
6. water identity fields beyond provider alone;
7. sample/water-stage context;
8. strict separation of regulatory/reference thresholds from chemistry.

Real Santa Cruz, Niagara, Primo/Sparkletts, and other source fixtures should be added only after the subset of these semantics required by each fixture can be represented faithfully.

## 27. Development milestones

### Milestone 0 — repository foundation — substantially complete

- public repository and MPL-2.0 license;
- uv workspace;
- engine and web package skeletons;
- Ruff, mypy, pytest, CI;
- core design and roadmap documents.

### Milestone 1 — FermUnits and measurement semantics — in progress

Completed or underway:

- FermUnits dependency;
- ion identifiers;
- exact/range/bound semantics;
- reported-average semantics;
- provenance;
- source profiles;
- target profiles;
- alkalinity/hardness/TDS/conductivity;
- structured pH semantics implemented and tested;
- profile observation periods implemented;
- `ND`, qualified endpoints, richer statistics, result timing, identity/context next;
- real report fixtures after required source-report semantics are representable;
- BeerJSON water adapter after the profile contracts settle sufficiently.

### Milestone 2 — deterministic forward calculations

- two- and multi-source blending;
- validated mineral stoichiometry;
- contribution matrices;
- profile comparison.

### Milestone 3 — optimization core

- continuous closest-match blending/additions;
- constraints and diagnostics;
- named policies;
- mixed-integer support where needed for fewest-product solutions;
- practical dose rounding/re-evaluation.

### Milestone 4 — web application

- HTMX profile-entry/blending workflows;
- ranked results and contribution tables;
- localization-ready quantity controls;
- BeerJSON import/export;
- FermentationJSON adapters when ready;
- AI-assisted PDF report extraction/review.

### Milestone 5 — validation and Version 1 release

- expanded authoritative reference tests;
- documented assumptions and limitations;
- accessibility/responsive review;
- chemistry model, package, optimizer, and reference-data versioning;
- stable conformance vectors.

## 28. Open design questions

1. Exact boundary between frozen dataclasses and Pydantic boundary models.
2. Exact ASGI framework for `water-treatment-web`.
3. Whether SciPy's MILP support is sufficient for all Version 1 discrete policies.
4. First authoritative composition sources for each included treatment ingredient.
5. Redistribution/licensing policy for historical city, brewery, and style targets.
6. Exact BeerJSON water adapter behavior and structured loss-report schema.
7. Exact FermentationJSON water-profile and treatment-plan adapter contract.
8. Whether additional alkalinity normalization belongs partly in FermUnits or entirely in engine semantics.
9. How target-match scores should be normalized and explained.
10. Which ions/properties belong in the default UI panel vs. advanced display.
11. Whether charge-balance diagnostics should only warn or may optionally suggest likely missing information without altering source data.
12. Exact generalized representation for lower/upper bounds, `ND`, and qualified/censored range endpoints.
13. Controlled vocabulary and payload for reported statistics such as ordinary average, RAA, LRAA, percentile, highest, and lowest.
14. Whether result-level timing belongs directly on every reported result or through a reusable measurement-context object.
15. Controlled vocabulary for water identity/product type and sample/water stage.
16. How regulatory/reference thresholds should be represented when preserved for report fidelity without contaminating chemistry models.
17. Whether pH aggregation should use activity directly, a concentration approximation, or model-selectable behavior when raw observations are supplied.
18. Long-term source for FermUnits dependency after GitHub-tag development use.

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

A UI-only patch should not imply that saved chemistry results were produced by a new model. Conversely, a change to stoichiometric data, representative-value policy, pH aggregation, or scoring semantics must be traceable even if the public Python API remains source-compatible.

## 30. Summary decision

Version 1 will provide a reusable, explainable water-treatment engineering system for beer, mead, and distilling users, especially home producers and small commercial operations. It will preserve real-world source-report semantics—including exact values, ranges, bounds, `ND`, qualified endpoints, named statistics, reporting bases, timing, water identity, and sampling context—while supporting multiple water sources, exact and ranged targets, practical mineral additions, ranked plans, contribution tables, provenance, BeerJSON compatibility, localization, and a responsive HTMX web interface.

The engine deliberately distinguishes reported from derived chemistry. Linear ranges may use an on-demand midpoint only when no reported average exists. pH is explicitly excluded from that generic behavior because it is logarithmic: range endpoints are preserved, reported averages are trusted only when actually reported, and any derived pH aggregation requires an explicit scientifically documented linear-space method.

FermentationJSON is expected to become the richer long-term interchange representation without constraining the internal engine model or diminishing BeerJSON compatibility.
