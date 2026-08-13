# Water Treatment Engineering Engine Design

**Document:** `docs/WATER_CHEM_DESIGN.md`  
**Status:** Working design — active implementation  
**Revision:** 2026-08-09
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

The project should make sophisticated water treatment approachable without hiding the underlying chemistry or source attribution.

The system should:

1. Model source water, target water, blends, treatment additions, and resulting brewing liquor as distinct concepts.
2. Preserve the difference between reported, measured, inferred, estimated, and calculated data.
3. Preserve exact values, ranges, qualified bounds, `ND`/not-detected states, reporting bases, named reported statistics, original units, and source-document metadata.
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
17. Preserve source-reported disinfectants and other relevant analytes even when the current optimizer does not use them, beginning with chlorine and chloramine reporting.
18. Treat intended water use as calculation/application context rather than an intrinsic property of a source-water profile.

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

The shared water representation and deterministic water-chemistry capabilities must not acquire coffee-, bread-, or other domain-specific sensory assumptions merely because those applications may later use the same code base. Future domain capabilities should depend on the shared water core rather than forcing the core to depend on a particular product domain. The standalone web application may expose several calculators over time, while downstream applications should consume only the domain capabilities they need; for example, Mecha-Brew should integrate the beer, mead, distilling, and related fermentation-water capabilities without depending on future coffee or bread modules.

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

- **FermUnits 0.1.x:** required by `water-treatment-engine`; currently sourced from the released GitHub `v0.1.1` tag until the dependency strategy is intentionally changed.
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

The package is intentionally still small while the domain contracts stabilize. The current implemented structure is:

```text
packages/water-treatment-engine/
├── pyproject.toml
├── README.md
├── src/
│   └── water_treatment_engine/
│       ├── __init__.py
│       ├── py.typed
│       ├── alkalinity_conversions.py
│       ├── concentrations.py
│       ├── ions.py
│       ├── profiles.py
│       ├── reported_properties.py
│       ├── reported_statistics.py
│       ├── reporting_context.py
│       ├── source_document.py
│       ├── target_profiles.py
│       └── water_identity.py
└── tests/
    ├── test_alkalinity_conversions.py
    ├── test_concentrations.py
    ├── test_engine_package.py
    ├── test_ions.py
    ├── test_profiles.py
    ├── test_real_report_fixtures.py
    ├── test_reported_properties.py
    ├── test_reported_statistics.py
    ├── test_reporting_context.py
    ├── test_source_document.py
    ├── test_target_profiles.py
    └── test_water_identity.py
```

Data-driven real-report fixtures live under `test-vectors/water/reports/` rather than inside the engine package.

As blending, stoichiometry, aqueous-state calculation, optimization, comparison, serialization, and explanations grow, the package may be reorganized into subpackages. That restructuring should happen when it improves real code organization, not merely to satisfy an early hypothetical directory tree.

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

For an ordinary **linear concentration** whose two endpoints are exact numeric values, calculation behavior is:

```text
reported_average exists  → use reported_average
otherwise                → derive midpoint(minimum, maximum) on demand
```

The midpoint is derived data. It is not stored as `reported_average` and must never be presented as though the source reported it.

A `reported_average` field may be populated only when the source explicitly identifies the value as an ordinary average. When a reported average accompanies a reported range, the reported average takes precedence over the mathematical midpoint. For example, a source may report calcium as average `51 mg/L`, range `50–53 mg/L`; calculations use the reported `51 mg/L`, not the midpoint `51.5 mg/L`.

A qualified range without an independently reported average has no automatic representative calculation value.

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

The main product use case is calculating pH for the **working water** after the user has selected source water(s), blending proportions, and treatment additions. The web UI should expose a single **Calc pH** action for that workflow. One click may evaluate every meaningful current checkpoint and update both the blend pH and final treated-water pH when both states exist. These are two results from the same engine capability, not two different pH algorithms or necessarily two different buttons. If there is no chemically distinct intermediate state, the UI should avoid presenting duplicate values.

A source report that omits pH may optionally offer a separately labeled **Estimate pH** action when sufficient chemistry is present. It must call the same `calculate_ph(...)` capability. Missing source pH is allowed to remain unknown; the engine must never manufacture a value merely to fill a report field.

Calculated pH must obey these rules:

1. It never overwrites or populates `ReportedPH`.
2. It is stored/returned as derived result data associated with the chemical state being evaluated.
3. It identifies the chemistry model/version, assumptions, relevant temperature/reference conditions, source fields used, and warnings/approximation status where applicable.
4. If the supplied state is scientifically insufficient for the selected model, return an explicit insufficient-data result rather than guessing.
5. Changing source composition, blend fractions, treatment additions, temperature, or other model-relevant inputs invalidates the previously calculated pH for that state.
6. The calculation should not display precision unsupported by the model or inputs.
7. The reusable pH capability belongs in `water-treatment-engine`; HTMX handlers and other clients only construct/select the state and request the calculation.

This working-water calculation is distinct from **recipe-aware mash-pH prediction**. Mash pH additionally depends on grain buffering and mash-specific chemistry and remains a later advanced feature even though it may ultimately reuse lower-level acid/base or equilibrium components.

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
- source/reference attribution and target type.

Target types include:

- previous successful batch;
- custom target;
- style recommendation;
- published brewery profile;
- historical city or regional profile;
- application-provided recommendation.

Historical brewing-city tables such as Pilsen, Burton-on-Trent, Dublin, Munich, London, Dortmund, Edinburgh, Vienna, Antwerp, and Cologne are **target/reference profiles**, not claims about present-day municipal source water. Each published version must retain its own source/reference attribution; conflicting published profiles should not be silently merged into one supposedly canonical city profile.

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

- source profiles emphasize source-document metadata, water identity, dates, plants/locations, report semantics, averages, ranges, and detection limits;
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

## 14. AI-assisted PDF water-report import

AI-assisted report import is a planned web-application feature, not an engine dependency.

### 14.1 User workflow

1. User uploads a municipal, bottled-water, or laboratory water-quality PDF.
2. The application extracts document text/tables and identifies candidate water chemistry and metadata.
3. AI-assisted extraction produces structured candidate fields, not final trusted engine data.
4. Deterministic validation checks units, ranges, reporting bases, and value consistency.
5. FermUnits normalizes accepted dimensional quantities.
6. The UI shows the extracted values for user review and correction before saving.
7. Accepted data becomes a `SourceWaterProfile` with explicit water identity and source-document metadata.

### 14.2 Required extraction behavior

The importer should attempt to preserve:

- calcium, magnesium, sodium, potassium;
- chloride, sulfate, bicarbonate only when actually reported;
- free chlorine, total chlorine, combined chlorine, chloramine/named chloramine species, and chlorine dioxide when actually reported;
- supported reported analytes that are relevant to later quality or treatment decisions even when the current optimizer does not consume them;
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
- collapse RAA, LRAA, percentile, highest/lowest, or another named statistic into an ordinary `reported_average`;
- confuse chloride with chlorine/chloramine or map one into the other;
- derive combined chlorine or chloramine from total and free chlorine without an explicit, documented analytical rule and derived-data label.

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

The pH capability is reusable and state-based. The web application's **Calc pH** action may request pH for both the blended-water and final treated-water states in one interaction, while a source-profile **Estimate pH** action may pass a source state to the same engine capability.

## 16. Version 1.0 scope

Version 1.0 should be a useful end-to-end product rather than only a chemistry-library demonstration. It supports beer, mead, and distilling water where the underlying treatment model is valid. Distilling must distinguish mash/fermentation/process water from spirit-proofing water.

### 16.1 Required engine features

1. **Water-profile modeling**
   - Source and target profiles.
   - Dated and period-based source-document/report context, with result-specific timing where reports require it.
   - Exact, ranged, bounded, not-detected, qualified-endpoint, and reported-statistic semantics.
   - Explicit alkalinity/hardness bases.
   - Correct nonlinear pH semantics.
   - Water identity and sampling-stage/context preservation.
   - Regulatory/reference thresholds kept separate from chemistry.
   - Preservation of source-reported disinfectants and other supported non-optimization analytes, beginning with chlorine/chloramine reporting.

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

5. **Reusable working-water pH calculation**
   - One engine capability accepts a normalized aqueous chemical state rather than a UI-specific source/blend/final-water request.
   - The same capability can evaluate source, blended, and final treated-water states when the selected model has sufficient inputs.
   - Calculated pH is derived data and never overwrites `ReportedPH`.
   - Insufficient chemistry returns an explicit insufficient-data result rather than a guessed value.
   - Results retain model/version, assumptions, relevant temperature/reference conditions, and warnings.
   - This is working-water pH, not recipe-aware mash-pH prediction.

6. **Joint blend-and-mineral optimization**
   - Optimize water proportions and mineral quantities together.
   - Do not lock in a water-only optimum when a slightly different blend produces a better complete treatment plan.

7. **Ranked solution policies**
   - exact match when feasible;
   - closest practical match;
   - fewest different treatment products;
   - lowest total mineral addition;
   - least dilution/RO usage;
   - no dilution;
   - no mineral additions / water-only blend;
   - user-selected ingredients only.

8. **Practical dosing**
   - configurable weighing precision;
   - minimum meaningful addition;
   - maximum validated addition rate;
   - recalculation after practical rounding.

9. **Explainability and diagnostics**
   - machine-readable warning/explanation codes;
   - unreachable-target explanations;
   - source ion already above target;
   - multi-ion salt coupling;
   - explicit assumptions and representative-value choices.

10. **Contribution matrix**
   - initial source contribution;
   - effect of blending;
   - contribution from each mineral;
   - final total for each modeled ion.

11. **Profile comparison**
    - raw differences;
    - range satisfaction;
    - weighted normalized score;
    - hard-limit violations;
    - charge-balance diagnostic when enough data exists.

12. **Interchange**
    - BeerJSON 1.0 water import/export for representable information;
    - explicit export-loss reporting for richer engine data;
    - FermentationJSON adapter when the relevant schema stabilizes;
    - versioned calculation/test-vector representation.

13. **Localization readiness**
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
- A single **Calc pH** action for working water that can update every meaningful current derived pH checkpoint, including blend pH and final treated-water pH when both states exist.
- Optional **Estimate pH** for a source profile with missing reported pH only when the reusable pH model has sufficient chemistry; otherwise pH remains unknown.
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
- Carry intended water use as request/application context wherever a supported calculation or warning depends on that distinction; do not infer intended use from the source-water profile itself.
- No account required for basic calculations.

### 16.3 Version 1 reference data

- Validated treatment-ingredient definitions.
- Curated beer, mead, and distilling targets with explicit source/reference attribution.
- Historical-city profiles clearly identified as reference targets.
- RO and distilled profiles represented explicitly rather than assumed silently.
- Real municipal/bottled-water fixtures with source-document metadata and report semantics.
- Independently calculated stoichiometric reference cases.

### 16.4 Deliberately deferred from Version 1 core chemistry

- recipe-dependent mash-pH prediction;
- grain buffering models;
- acid and alkali optimization;
- separate mash- and sparge-water optimization;
- general-purpose geochemical equilibrium, precipitation, and solubility modeling beyond the focused validated aqueous chemistry required by Version 1 features;
- robust uncertainty propagation through optimization;
- detailed inventory/purchasing/package management;
- sophisticated cost optimization;
- multi-batch production planning;
- a generalized non-additive `TreatmentOperation` framework for activated-carbon treatment, ion exchange, modeled reverse-osmosis removal, deaeration, softening, and similar processes.

AI-assisted PDF extraction may be developed in the Version 1 web application, but it remains an ingestion workflow and must not force unvalidated chemistry into the engine.

## 17. Version 2.0 — advanced brewing-water chemistry

Version 2 should add features that require deeper chemistry models or materially different optimization constraints:

- acid additions;
- alkali additions;
- alkalinity neutralization;
- separate mash and sparge treatment;
- recipe-aware mash-pH prediction;
- deeper carbonate/bicarbonate chemistry beyond the focused working-water pH capability;
- precipitation and solubility considerations where practical;
- uncertainty propagation;
- optimization using uncertain or ranged source-water reports;
- sensitivity and worst-case plans;
- Pareto-front exploration;
- optional treatment cost inputs;
- optional Mecha-Brew inventory integration;
- purpose-aware brewing/brewery-water guidance where validated, using intended-water-use context rather than changing source-water identity;
- expanded brewery-scale workflows.

Mash-pH prediction must clearly separate predicted, calculated, and measured pH and use versioned validated models.

## 18. Version 3.0 — broader food and beverage applications

Potential independently validated domain modules include:

- coffee, the preferred first non-brewing domain once the brewing-water foundation is stable;
- tea;
- bread;
- sourdough;
- pizza dough;
- alkaline noodles;
- ramen/kansui;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages.

These modules may share source-water composition, blending, source-attribution metadata, and optimization infrastructure while retaining their own constituents, targets, treatment rules, sensory/process priorities, warnings, references, and validation suites. The standalone web application may host several such calculators over the shared engine, while other applications consume only the domains they need.

A generalized non-additive `TreatmentOperation` abstraction may be introduced in this stage if concrete brewing or coffee requirements justify it. It should not be pre-built in Version 1 merely to anticipate filtration, dechlorination, reverse osmosis, ion exchange, softening, or deaeration workflows.

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
- source-document/reference attribution metadata;
- source/target semantics.

Reported/source quantities preserve supported scalar magnitude representations
(`int`, `float`, `Decimal`, or `Fraction`) rather than erasing Pint's magnitude
type with `Any` or coercing source data to binary floating point. Derived
engineering calculations may deliberately normalize to `float` at a documented
calculation boundary. Array/vectorized quantities remain out of scope until an
implemented feature requires them.

## 22. Public API direction

The eventual public API should accept platform-neutral structured requests and return structured results and stable warning/explanation codes.

Illustrative direction only:

```python
from water_treatment_engine import blend_waters, calculate_ph, optimize_treatment

blend_result = blend_waters(...)
ph_result = calculate_ph(chemical_state)
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
- Put critical calculation limits in the engine, not only in UI validation.
- Do not present target matching as a guarantee of flavor, fermentation performance, or safety.
- AI-extracted report values require deterministic validation and user review before normal persistence.

## 26. Current implementation status

As of this revision, the repository foundation is operational with Python 3.14, uv, Ruff, mypy, pytest, Hypothesis, GitHub Actions, independently installable engine/web packages, and FermUnits 0.1.1 integration. The reproducible workspace gate uses `uv run --all-packages` so engine, web, FermUnits, and transitive dependencies are present regardless of prior environment state.

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

The latest clean gate before the reported-disinfectant implementation reported **189 passing tests**, with Ruff, Ruff format check, and strict mypy also passing.

The real-report pressure-test phase has served its immediate purpose. Additional reports should be added only when they expose a genuinely new semantic or scientific requirement rather than simply increasing fixture count.

First-class source-report preservation of chlorine/chloramine and related disinfectant reporting is now implemented. The Santa Cruz 2025 fixture pressure-tests an unqualified distribution-system `Chlorine` result as its own reported disinfectant rather than inferring free chlorine or mapping the result to chloride. Treatment/removal modeling remains deliberately out of scope for this representation layer.

The next implementation focus moves from source-report representation into **deterministic forward treatment calculations**: validated treatment-ingredient identities, generic stoichiometric ion contributions, derived working-water states, blending, and later the reusable aqueous pH capability documented above.

## 27. Development milestones

### Milestone 0 — repository foundation — substantially complete

- public repository and MPL-2.0 license;
- uv workspace;
- engine and web package skeletons;
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
- five data-driven real-report fixtures exercising the implemented semantics.

Still expected at the boundary as needed:

- reported disinfectant/analyte preservation beginning with chlorine/chloramine;
- BeerJSON water adapter once the profile contracts are sufficiently settled;
- FermentationJSON adapter when its water schema is ready.

### Milestone 2 — deterministic forward calculations — next

- validated treatment-ingredient identities, including hydration state;
- generic stoichiometric ion-contribution calculation;
- forward application of one or more additions to a known water volume;
- two- and multi-source blending;
- explicit derived blended-water and final treated-water chemical states;
- contribution matrices;
- profile comparison;
- reusable `calculate_ph(chemical_state)` capability once a scientifically validated aqueous model and minimum-input contract are established;
- one working-water **Calc pH** action may evaluate both blend and final treated-water checkpoints through that same capability.

### Milestone 3 — optimization core

- continuous closest-match blending/additions;
- constraints and diagnostics;
- named policies;
- mixed-integer support where needed for fewest-product solutions;
- practical dose rounding/re-evaluation.

### Milestone 4 — web application

- HTMX profile-entry/blending/treatment workflows;
- working-water **Calc pH** action backed only by the reusable engine capability;
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
12. How regulatory/reference thresholds should be represented when preserved for report fidelity without contaminating chemistry models.
13. Exact aqueous equilibrium/activity model, validated reference data, and minimum chemical-state inputs for the reusable `calculate_ph(...)` capability.
14. Whether optional source-profile **Estimate pH** belongs in the Version 1 UI or should wait until the working-water pH workflow is validated.
15. Long-term source for FermUnits dependency after GitHub-tag development use.
16. Exact reusable representation for reported disinfectants and other non-optimization analytes once chlorine/chloramine support expands beyond the first concrete cases.
17. First validated set of intended-water-use values and which belong in Version 1 versus later brewery/domain modules.

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

Version 1 will provide a reusable, explainable water-treatment engineering system for beer, mead, and distilling users, especially home producers and small commercial operations. It will preserve real-world source-report semantics—including exact values, ranges, bounds, `ND`, qualified endpoints, named statistics, reporting bases, timing, water identity, sampling context, source-document metadata, and source-reported disinfectants such as chlorine/chloramine—while supporting multiple water sources, exact and ranged targets, practical mineral additions, ranked plans, contribution tables, source/reference attribution, BeerJSON compatibility, localization, and a responsive HTMX web interface. Intended water use remains calculation/application context rather than part of source-water identity.

The engine deliberately distinguishes reported from derived chemistry. Linear ranges may use an on-demand midpoint only when no reported average exists and both endpoints are exact. Qualified ranges do not receive an automatic representative value. pH is explicitly excluded from generic linear averaging because it is logarithmic: range endpoints are preserved, reported averages are trusted only when actually reported, and any derived pH calculation uses an explicit scientifically documented aqueous model.

Calculated working-water pH is one reusable engine capability, conceptually `calculate_ph(chemical_state)`. Source, blended, and final treated-water states may all use that same capability. The standalone UI should normally expose one **Calc pH** action that can refresh every meaningful current working-water pH checkpoint in one interaction; a separately labeled source **Estimate pH** may reuse the same engine only when scientifically sufficient inputs exist. Calculated pH never overwrites `ReportedPH`.

FermentationJSON is expected to become the richer long-term interchange representation without constraining the internal engine model or diminishing BeerJSON compatibility.
