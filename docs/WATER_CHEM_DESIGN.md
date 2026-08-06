# Water Treatment Engineering Engine Design

**Document:** `WATER_CHEM_DESIGN.md`  
**Status:** Working design draft — repository foundation  
**Project:** Calculators  
**Primary package:** `water-treatment-calculator`  
**Initial audience:** Homebrewers, meadmakers, craft distillers, and small breweries/distilleries

## 1. Purpose

The Water Treatment Engineering Engine is a reusable, scientifically grounded system for designing brewing-water blends and treatment plans.

It is not intended merely to reproduce traditional water-profile calculators that require users to experiment manually with salt additions. The engine should accept source-water chemistry, a target profile, available water sources, permitted treatment ingredients, and practical constraints, then calculate and rank useful treatment plans automatically.

The engine must remain independent of web frameworks, databases, graphical interfaces, operating systems, and hardware. It should be usable by:

- the standalone calculator web application;
- Mecha-Brew;
- future mobile and desktop applications;
- Python scripts and notebooks;
- APIs and third-party software;
- automated recipe and batch-planning workflows.

## 2. Product goals

The project should make sophisticated water treatment approachable without hiding the underlying chemistry.

The system should:

1. Model source water, target water, blends, additions, and resulting brewing liquor as distinct concepts.
2. Blend two or more waters by volume.
3. Determine practical mineral additions automatically.
4. Produce several meaningfully different ranked solutions.
5. Explain why each solution was selected and where it compromises.
6. Show each water source and treatment ingredient's contribution to every modeled ion.
7. Preserve units, reporting bases, provenance, ranges, and assumptions.
8. Support dated source-water profiles so earlier successful brewing liquor can be reproduced from current water.
9. Integrate cleanly with FermUnits and FermentationJSON.
10. Provide a polished browser interface while keeping all scientific logic outside the interface layer.

## 3. Non-goals

The initial project is not intended to be:

- a universal industrial water-treatment package;
- a municipal treatment-plant simulator;
- a general geochemistry platform;
- an inventory-management or purchasing system;
- an accounting system;
- a laboratory information-management system;
- a replacement for qualified laboratory analysis;
- dependent on Mecha-Brew, Django, or any particular application.

The architecture may permit later use outside brewing, but initial decisions should optimize for beer, mead, distilling, and closely related fermentation uses.

## 4. Engineering principles

1. **Keep chemistry separate from presentation.** No equations or optimization rules belong in templates, JavaScript form handlers, or mobile views.
2. **Use explicit quantities.** Every dimensional input and result must carry a FermUnits quantity or be converted into one at the boundary.
3. **Preserve meaning as well as magnitude.** `mg/L as CaCO3`, bicarbonate concentration, total alkalinity, hardness, pH, and mass fractions are not interchangeable merely because numerical conversions exist.
4. **Preserve provenance.** Reported values, source documents, dates, assumptions, and inferred values must remain distinguishable.
5. **Prefer deterministic and reproducible behavior.** Identical versioned inputs and solver settings should produce identical results within documented numerical tolerances.
6. **Explain infeasibility.** The engine must say why a requested target cannot be reached under the supplied constraints.
7. **Do not disguise estimates as measurements.** Calculated, inferred, nominal, bounded, and measured values must remain distinguishable.
8. **Rank tradeoffs rather than claim one universal optimum.** A brewer may reasonably prefer simplicity, lower dilution, closer ion matching, or fewer products.
9. **Make model versions visible.** Saved plans should identify the chemistry and optimization model versions that produced them.
10. **Validate against independent reference data.** Legacy calculator code can inform the project but must not be accepted as authoritative without tests and source verification.

## 5. Project relationship

```text
FermUnits
    │
    ▼
Water Treatment Engineering Engine
    │
    ├── standalone web calculator
    ├── Mecha-Brew adapter
    ├── future mobile/desktop apps
    ├── Python API
    └── optional command-line tools

FermentationJSON
    ├── import/export of water profiles
    ├── import/export of blends
    └── import/export of treatment plans
```

FermUnits supplies quantity representation, dimensional validation, and unit conversion. The water engine supplies chemical semantics and calculations. FermentationJSON supplies a portable archival and interchange representation. Applications supply storage, user accounts, visual presentation, and workflow integration.

## 6. Tooling decisions

The tooling should remain as consistent as practical with FermUnits, the draft-system calculator, and Mecha-Brew.

### 6.1 Python and package management

- Python 3.14 as the development target.
- `uv` for Python installation, dependency resolution, environments, locking, commands, and workspace management.
- A `uv` workspace at the Calculators repository root.
- Standard `pyproject.toml` metadata for every independently installable package.
- Source layouts (`src/<package_name>/`) for installable Python packages.
- The same build backend used across the calculator packages unless a specific package requires an exception.

### 6.2 Core libraries

- **FermUnits:** all public dimensional inputs and outputs.
- **NumPy:** vector and matrix operations used by contribution and optimization calculations.
- **SciPy:** continuous optimization and mixed-integer optimization where suitable.
- **Pydantic:** validation and serialization models at application, API, and file boundaries.
- **Frozen dataclasses or similarly simple domain models:** internal chemistry objects where runtime serialization behavior is unnecessary.

Pydantic should not become the chemistry architecture. Boundary models may convert to immutable domain objects before calculation.

### 6.3 Web application

- Server-rendered HTML.
- HTMX for dynamic form fragments, recalculation, ranked-result panels, profile selection, and progressive disclosure.
- Jinja templates.
- A small Python ASGI application layer, initially FastAPI/Starlette-compatible.
- Minimal vanilla JavaScript only where browser-only behavior genuinely requires it.
- No React or mandatory Node build pipeline for version 1.

The standalone web application is an adapter around the engine. Mecha-Brew may use its own application framework and templates while importing the same engine package.

### 6.4 Quality tooling

- `pytest` for unit, integration, regression, and reference tests.
- `Hypothesis` for property-based tests, especially conservation, blending, bounds, and unit invariance.
- Ruff for linting and formatting.
- mypy for static type checking.
- GitHub Actions for CI.
- Coverage reporting as a diagnostic, not as a substitute for meaningful tests.

### 6.5 Documentation and data

- Markdown design and reference documents.
- Version-controlled JSON or YAML reference datasets where humans need to review data.
- FermentationJSON adapters for standard interchange when the relevant schemas are stable.
- SQLite may be used by the standalone web app for user-created profiles, but the engine must not import or require SQLite.

## 7. Repository and packaging strategy

The broader **Calculators** effort is one coordinated product family, but repository boundaries must respect licensing and commercial plans. The water-treatment project is public, while the draft-system project remains private. They therefore should not begin in one Git monorepo.

The water project will use its own public repository while following shared standards established for the calculator family: Python, uv, Ruff, mypy, pytest, HTMX, explicit units, versioned calculation contracts, and compatible result/warning conventions.

Within the water repository, the scientific engine and standalone web interface remain independently installable workspace members:

```text
water-treatment-calculator/
├── pyproject.toml                 # uv workspace and shared development config
├── uv.lock
├── .python-version
├── .gitignore
├── README.md
├── LICENSE                       # MPL-2.0
├── docs/
│   ├── WATER_CHEM_DESIGN.md
│   ├── WATER_CHEM_REFERENCES.md
│   ├── PROJECT_STRUCTURE.md
│   ├── ROADMAP.md
│   ├── decisions/
│   └── research/
├── packages/
│   └── water-treatment-engine/
├── apps/
│   └── water-treatment-web/
├── reference-data/
│   └── water/
├── schemas/
│   └── water/
├── test-vectors/
│   └── water/
└── scripts/
```

The engine distribution can be installed without the web application. The web application depends on the engine, but the engine never depends on the web application. Mecha-Brew will import the engine directly and render it through Mecha-Brew's own interface.

No shared `calculators-common` package should be created yet. Cross-repository code should only be extracted after at least two calculator engines demonstrate a stable, concrete shared need.

## 8. Water package directory structure

```text
packages/water-treatment-engine/
├── pyproject.toml
├── README.md
├── src/
│   └── water_treatment/
│       ├── __init__.py
│       ├── py.typed
│       ├── api.py
│       ├── models/
│       │   ├── profiles.py
│       │   ├── measurements.py
│       │   ├── targets.py
│       │   ├── ingredients.py
│       │   ├── blends.py
│       │   ├── constraints.py
│       │   ├── plans.py
│       │   └── results.py
│       ├── chemistry/
│       │   ├── ions.py
│       │   ├── composition.py
│       │   ├── stoichiometry.py
│       │   ├── blending.py
│       │   ├── contributions.py
│       │   ├── alkalinity.py
│       │   └── charge_balance.py
│       ├── optimization/
│       │   ├── problem.py
│       │   ├── objectives.py
│       │   ├── constraints.py
│       │   ├── continuous.py
│       │   ├── mixed_integer.py
│       │   ├── ranking.py
│       │   └── diagnostics.py
│       ├── comparison/
│       │   ├── deviations.py
│       │   ├── scoring.py
│       │   └── feasibility.py
│       ├── explanations/
│       │   ├── codes.py
│       │   ├── messages.py
│       │   └── builder.py
│       ├── serialization/
│       │   ├── pydantic_models.py
│       │   ├── fermentation_json.py
│       │   └── test_vectors.py
│       ├── data/
│       │   ├── salts/
│       │   └── built_in_profiles/
│       └── exceptions.py
└── tests/
    ├── unit/
    ├── integration/
    ├── property/
    ├── reference/
    └── regression/
```

The structure is deliberately layered. It allows acids, mash-pH models, and alternate optimizers to be added without rewriting the water-profile or result contracts.

## 9. Core domain model

### 9.1 Measurement

A chemistry measurement must be able to represent:

- exact value;
- nominal or representative value;
- minimum and maximum range;
- upper or lower bound;
- uncertainty;
- detection limit;
- missing or not reported;
- measured, reported, inferred, estimated, or calculated status;
- original unit and reporting basis;
- optional canonical value.

### 9.2 WaterProfile

Common chemistry and metadata shared by source, target, and resulting profiles.

Initial principal constituents:

- calcium;
- magnesium;
- sodium;
- potassium;
- chloride;
- sulfate;
- bicarbonate;
- carbonate where reported;
- alkalinity with explicit basis;
- pH with measurement temperature where known.

Additional constituents should be extensible without breaking existing documents or APIs.

### 9.3 SourceWaterProfile

Represents incoming water available for blending or treatment.

Metadata should include:

- name and stable identifier;
- water type: municipal, well, spring, purified, RO, distilled, bottled, laboratory-prepared, or other;
- provider or brand;
- product and region where relevant;
- sample date, report date, or effective period;
- source citation;
- analytical method where known;
- notes and provenance;
- whether values are single measurements, averages, or ranges.

### 9.4 TargetWaterProfile

Represents desired brewing liquor rather than an incoming supply.

Each target constituent may contain:

- preferred value;
- acceptable range;
- hard minimum or maximum;
- optimization weight;
- flavor priority;
- mash-chemistry priority;
- provenance and target type.

Target types include:

- previous successful batch;
- custom profile;
- style recommendation;
- published brewery profile;
- historical city or regional profile;
- application-provided recommendation.

### 9.5 WaterBlend

Records actual volumes or fractions of source waters. Actual volumes should be retained whenever known; fractions are derived.

### 9.6 TreatmentIngredient

Separates chemical identity from user inventory.

Required information includes:

- stable identifier;
- display name;
- chemical formula or composition;
- hydration state;
- purity or concentration;
- ion yield per mass or volume;
- permitted use limits;
- optional density for liquid treatments;
- evidence or source for composition.

### 9.7 TreatmentConstraint

Examples:

- allowed and disallowed waters;
- maximum available amount of a water source;
- required use of an existing fixed volume;
- allowed and disallowed treatments;
- maximum addition rate;
- target-ion hard limits;
- minimum practical weighing increment;
- maximum dilution fraction;
- maximum number of treatment products;
- require whole bottle or container increments where requested.

### 9.8 TreatmentPlan

A complete result containing:

- water-source volumes and fractions;
- treatment additions;
- final predicted profile;
- per-source and per-treatment ion contribution matrix;
- objective and component scores;
- target deviations;
- constraint outcomes;
- warnings and explanation codes;
- assumptions;
- solver status and tolerances;
- model and data versions.

## 10. Calculation pipeline

```text
Validate inputs and units
        │
        ▼
Normalize measurements and reporting bases
        │
        ▼
Construct available source-water blend space
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
Optimize under named policy
        │
        ▼
Generate distinct candidate plans
        │
        ▼
Rank, explain, and return structured results
```

Blending and treatment should remain distinct operations internally even when optimized together.

## 11. Version 1.0 scope

Version 1.0 should be a useful end-to-end product rather than only a chemistry library demonstration. It will explicitly support beer, mead, and distilling profiles where the treatment model is the same. Distilling use must distinguish process water used for mashing or fermentation from water used to proof finished spirits.

### 11.1 Required engine features

1. **Water-profile modeling**
   - Source, target, and resulting profiles.
   - Dated profiles and provenance.
   - Exact values, preferred values, ranges, and hard limits.
   - Explicit alkalinity and reporting bases.

2. **Forward water blending**
   - Blend two or more source waters by volume.
   - Calculate the resulting ion profile.
   - Report each source's contribution.
   - Support fixed user-entered blends such as 2 gallons municipal plus 8 gallons bottled water.

3. **Optimized blending**
   - Solve source-water proportions against a target.
   - Support source availability and maximum-volume constraints.
   - Support water-only solutions.

4. **Common brewing mineral additions**
   - Calcium chloride in explicitly identified form.
   - Calcium sulfate in explicitly identified form.
   - Magnesium sulfate heptahydrate.
   - Sodium chloride.
   - Sodium bicarbonate.
   - Other salts only after composition and use are validated.

5. **Joint blend-and-mineral optimization**
   - Optimize water proportions and mineral quantities together.
   - Do not lock in the best water-only blend if a slightly different blend produces a better complete plan.

6. **Ranked solution policies**
   - Exact match when feasible.
   - Closest practical match.
   - Fewest different treatment products.
   - Lowest total mineral addition.
   - Least dilution or purchased low-mineral water.
   - No mineral additions.
   - User-selected ingredients only.

7. **Practical dosing**
   - Configurable weighing precision.
   - Minimum meaningful addition.
   - Maximum addition rate.
   - Recalculate the final profile after rounding to practical doses.

8. **Explainability and diagnostics**
   - Machine-readable warning and explanation codes.
   - Explain unreachable targets.
   - Identify ions already above target.
   - Identify coupling caused by multi-ion salts.
   - Show compromises and sensitivity to constraints.

9. **Contribution matrix**
   - Initial source contribution.
   - Effect of blending.
   - Contribution from each mineral.
   - Final total for each ion.

10. **Profile comparison**
    - Raw differences.
    - Range satisfaction.
    - Weighted normalized score.
    - Hard-limit violations.
    - Charge-balance diagnostic where enough data is available.

11. **Serialization and interchange**
    - Stable Pydantic boundary models.
    - Versioned JSON test-vector format.
    - FermentationJSON adapter aligned with its water-profile schemas.
    - Preserve original reported units and values where available.

12. **Localization readiness**
    - Canonical calculations independent of display locale.
    - Explicit US, Imperial, and metric unit identifiers.
    - User-selectable input and display units.
    - No persisted ambiguous `gallon` or `fluid ounce` identifiers.

### 11.2 Required standalone web features

- Responsive desktop, tablet, and phone layouts.
- Manual source-water entry.
- Selection of saved and built-in profiles.
- Multiple source-water rows.
- Fixed-blend calculation.
- Target entry using exact values or ranges.
- Selection of allowed salts.
- Batch volume and unit selection.
- Ranked plan cards.
- Detailed contribution table.
- Plain-language warnings and explanation panels.
- Import and export of supported profile and plan documents.
- No account required for basic calculations.

### 11.3 Required reference data

- Validated definitions for included salts.
- Curated beer, mead, and distilling target profiles, each with domain and use-stage metadata.
- Distilling profiles must identify whether they apply to mash/fermentation water, process water, or proofing water.
- A small curated set of example targets.
- RO and distilled reference profiles represented appropriately rather than assumed silently.
- Test fixtures based on authoritative or independently calculated examples.

Historical city and brewery profiles may be included only with provenance and clear descriptions of what the published figures represent. A historical municipal analysis must not be presented as though it were necessarily the brewery's treated brewing liquor.

### 11.4 Version 1.0 exclusions

The following are deliberately deferred rather than partially implemented:

- mash-pH prediction;
- grain buffering and recipe-dependent pH;
- acid and alkali optimization;
- separate mash and sparge treatment optimization;
- precipitation, solubility, and equilibrium modeling beyond documented practical limits;
- treatment order effects;
- robust uncertainty propagation through optimization;
- automatic extraction of chemistry from arbitrary reports;
- inventory, purchasing, package tracking, or supplier management;
- detailed cost optimization;
- multi-batch production planning;
- accounts, synchronization, and collaboration inside the engine package.

## 12. Version 2.0 scope

Version 2.0 should add features that require deeper chemistry models or materially different optimization constraints.

### 12.1 Acid, alkali, and alkalinity treatment

- Lactic, phosphoric, sulfuric, hydrochloric, and other supported acids with explicit concentration bases.
- Calcium hydroxide and other validated alkalinity additions.
- Neutralization and alkalinity calculations.
- Acid concentration, density, and purity handling.
- Safety and practical-dose limits.

### 12.2 Mash and sparge workflows

- Separate treatment locations and volumes.
- Strike, infusion, and sparge-water plans.
- Recipe-linked grain bill and liquor-to-grist ratio.
- Sparge-water alkalinity and pH guidance.
- Full-batch treatment schedules.

### 12.3 Mash-pH prediction

- Versioned prediction models.
- Malt and adjunct buffering data.
- Acidulated malt and direct acid additions.
- Model uncertainty and confidence indicators.
- Validation against measured mash datasets.
- Clear separation of predicted and measured pH.

### 12.4 More sophisticated chemistry

- Better carbonate-system treatment.
- Precipitation and solubility warnings.
- Temperature-sensitive properties where material.
- Additional ions and brewing-relevant constituents.
- Charge-balance reconciliation options that never overwrite reported values silently.

### 12.5 Robust optimization

- Optimization against uncertain source-water ranges.
- Worst-case and sensitivity plans.
- Pareto-front exploration.
- Additional mixed-integer operational constraints.
- More advanced plan diversity controls.

### 12.6 Optional operational features

These belong mainly in applications but require engine inputs or outputs:

- optional ingredient cost per unit mass or volume;
- lowest-cost ranking;
- ingredient availability from Mecha-Brew inventory;
- saved favorite treatment policies;
- brewery-scale addition instructions;
- multi-user review and approval in Mecha-Brew.


## 13. Version 3.0 scope — broader food and beverage domains

Version 3.0 may extend the shared water-composition and optimization architecture to additional food and beverage uses without weakening the brewing-first design of earlier releases. Candidate modules include:

- coffee extraction and brewing water;
- tea brewing water;
- bread, sourdough, and pizza dough;
- alkaline noodles, ramen, and kansui systems;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages.

Each new domain must define its own constituents, target semantics, treatment ingredients, sensory or process priorities, warnings, references, and validation suite. The project must not imply that one generic ion-matching score predicts sensory quality across all foods.

Future food modules may require support for trace constituents, dissolved gases, total dissolved solids, sensory-risk annotations, and interactions between water chemistry and food ingredients. These features should be added only where supported by credible evidence and must distinguish measured effects from heuristic guidance.

## 14. Version 4.0 scope — selected non-food industrial uses

Version 4.0 may add selected non-food process-water modules. Possible areas include laboratory preparation water, cleaning and rinsing, boiler or steam feedwater, cooling water, and selected manufacturing processes.

Industrial modules require separate safety, materials-compatibility, regulatory, and validation work. They must not be enabled merely by relabeling the food-oriented optimizer.

## 15. Optimization design

### 13.1 Decision variables

Version 1 decision variables may include:

- volume or fraction of each source water;
- mass of each solid treatment;
- optional binary variable indicating whether a treatment product is used;
- practical rounded amount where discrete dosing is required.

### 13.2 Constraints

- Source fractions sum to the required volume.
- Source amounts remain within availability bounds.
- Treatment quantities remain within configured limits.
- Hard ion limits are respected when feasible.
- Variables cannot be negative.
- User-excluded waters and ingredients remain unused.

### 13.3 Objective components

The optimizer should calculate objective components separately rather than burying them in one undocumented score:

- weighted ion deviation;
- hard-constraint violation penalty;
- number of treatment products;
- total treatment mass;
- dilution-water usage;
- deviation introduced by practical rounding;
- optional application-provided cost.

### 13.4 Named policies

Named user policies map to documented objective weights and constraints. They must be versioned.

The engine should generate several candidate plans independently, then remove duplicate or operationally equivalent plans before ranking.

### 13.5 Exactness

The result language must distinguish:

- exact within declared numerical tolerance;
- target ranges fully satisfied;
- closest feasible under constraints;
- mathematically feasible but operationally impractical;
- infeasible with supplied sources and treatments;
- solver failure or indeterminate result.

## 16. Units and localization

### 14.1 Canonical calculation units

Recommended canonical forms include:

- volume: liter;
- solid mass: gram;
- liquid treatment volume: milliliter;
- ion concentration: milligram per liter;
- molar concentration: mole or millimole per liter;
- equivalent concentration: milliequivalent per liter;
- temperature: degree Celsius;
- density: kilogram per liter or gram per milliliter.

### 14.2 Display and input units

The interface may accept and display:

- liters, milliliters, hectoliters;
- US liquid gallons, quarts, pints, and fluid ounces;
- Imperial gallons, pints, and fluid ounces;
- grams, milligrams, kilograms, ounces, and pounds;
- grams per liter, grams per gallon, grams per hectoliter, and pounds per US beer barrel;
- mg/L, ppm where the documented assumption is applicable, mmol/L, and mEq/L;
- relevant hardness and alkalinity reporting units.

Locale selects defaults. It must never change the meaning of already stored data.

### 14.3 FermUnits requirements

Before implementing the engine, audit FermUnits for:

- explicit US and Imperial volume units;
- concentration and amount-of-substance units;
- equivalent concentration;
- density and solution fractions;
- hardness units;
- brewing-scale addition rates;
- representation or conversion support for values reported `as CaCO3` without erasing the reporting basis;
- preservation of exact, range, and bound semantics at higher model layers.

## 17. FermentationJSON integration

FermentationJSON should eventually represent:

- source water profiles;
- target water profiles;
- treated brewing liquor;
- water blends;
- water treatment plans.

The adapter should preserve:

- canonical quantities;
- original reported quantities;
- reporting bases;
- profile dates and effective periods;
- provenance and citations;
- exact, range, uncertainty, and detection-limit semantics;
- water-source identities and blend volumes;
- treatments, assumptions, warnings, and model versions.

The engine's Python models and the FermentationJSON schemas should be compatible but need not be structurally identical. Serialization is an adapter responsibility.

## 18. Public API direction

Illustrative API only:

```python
from water_treatment import (
    BlendRequest,
    OptimizationRequest,
    blend_waters,
    optimize_treatment,
)

blend_result = blend_waters(
    BlendRequest(
        sources=(municipal, sparkletts, bottled_water),
        required_volume=Q_(10, "US_liquid_gallon"),
    )
)

optimization_result = optimize_treatment(
    OptimizationRequest(
        sources=(municipal, sparkletts, bottled_water),
        target=target,
        required_volume=Q_(10, "US_liquid_gallon"),
        permitted_treatments=(gypsum, calcium_chloride),
        policies=("closest_match", "fewest_products", "least_dilution"),
    )
)
```

The public API should return structured objects and stable codes. It must not return HTML or depend on application database objects.

## 19. Testing strategy

### 17.1 Unit tests

- Stoichiometric contribution for every treatment ingredient.
- Volume-weighted blending.
- Unit conversions and dimensional rejection.
- Target deviation and range logic.
- Rounding and practical-dose behavior.
- Explanation and warning codes.

### 17.2 Property-based tests

- Blend fractions sum correctly.
- Blended concentration remains within source extrema for conservative constituents.
- Reordering source waters does not change results.
- Equivalent unit inputs produce equivalent canonical results.
- Zero additions leave blend chemistry unchanged.
- No negative volumes or additions are returned.
- Adding a source with zero volume has no effect.

### 17.3 Reference tests

- Published analytical examples where licensing permits use.
- Independently calculated stoichiometric examples.
- Cross-checks against trusted brewing references.
- Legacy calculator outputs only after verifying their formulas and assumptions.

### 17.4 Optimizer tests

- Known exact solutions.
- Known infeasible problems.
- Source-ion-above-target diagnostics.
- Ingredient coupling cases.
- Discrete weighing increments.
- Deterministic candidate ranking.
- Distinct-plan generation.

### 17.5 Cross-platform test vectors

Portable JSON request/result pairs should allow future Swift, Kotlin, Dart, JavaScript, or other implementations to demonstrate conformance with the reference engine.

## 20. Security and safety considerations

- Treat acids and alkalis as potentially hazardous once supported.
- Include maximum practical dosing limits and clear warning codes.
- Never infer missing concentration or purity without exposing the assumption.
- Do not present target-profile matching as a guarantee of beer quality.
- Keep source citations and data dates visible.
- Prevent malformed units or impossible values from reaching the optimizer.
- Place calculation limits in the engine, not only in the browser form.

## 21. Open design questions

These should be resolved before implementation reaches the corresponding area:

1. Final public distribution and import names.
2. Exact boundary between dataclasses and Pydantic models.
3. Whether SciPy's built-in MILP support is sufficient for all version 1 policies.
4. The first authoritative ingredient-composition sources.
5. Which historical or style targets may be redistributed and under what licenses.
6. The exact FermentationJSON water-profile schema and adapter contract.
7. Whether alkalinity normalization belongs partly in FermUnits or entirely in the engine semantics.
8. How target match scores should be normalized and explained to users.
9. Which ions qualify for the version 1 default panel versus advanced display.
10. Whether charge-balance diagnostics should merely warn or optionally infer a likely missing ion.

## 22. Initial development milestones

### Milestone 0 — Repository foundation

- Create the public `water-treatment-calculator` repository as a separate Git repository coordinated within the broader Calculators project.
- Use the Mozilla Public License 2.0 unless that licensing decision is revised before publication.
- Initialize the uv workspace.
- Add package and web-app skeletons.
- Add Ruff, mypy, pytest, and CI.
- Add this design document and decision records.

### Milestone 1 — FermUnits and chemistry semantics

- Audit required units.
- Define ion identifiers and measurement bases.
- Define immutable profile and measurement models.
- Establish serialization test vectors.

### Milestone 2 — Deterministic forward calculations

- Implement two- and multi-source blending.
- Implement validated mineral stoichiometry.
- Produce contribution matrices.
- Implement profile comparison.

### Milestone 3 — Optimization core

- Implement continuous closest-match blending and additions.
- Add constraints and diagnostics.
- Add named optimization policies.
- Add mixed-integer support for fewest-product solutions.
- Add practical dose rounding and re-evaluation.

### Milestone 4 — Web application

- Build HTMX profile-entry and blending workflows.
- Add ranked results and contribution tables.
- Add localization-ready quantity controls.
- Add import/export.

### Milestone 5 — Validation and 1.0 release

- Expand reference tests.
- Document assumptions and limitations.
- Complete accessibility and responsive-interface review.
- Publish model version, package version, and reference-data version.

## 23. Versioning policy

The project should version independently:

- Python package releases;
- chemistry-model revisions;
- optimization-policy revisions;
- bundled reference datasets;
- FermentationJSON adapter/schema compatibility.

A patch release that fixes UI text should not imply that saved chemistry results were produced by a new model. Conversely, a change to stoichiometric data or scoring semantics must be traceable even if the public Python API remains source-compatible.

## 24. Summary decision

Version 1.0 will provide a complete blending and mineral-treatment system for beer, mead, and distilling users, particularly home producers and small commercial operations. It includes multiple source waters, target ranges, practical constraints, ranked plans, contribution tables, explanations, localization, and a responsive HTMX web interface.

Acid/base chemistry, mash and sparge separation, mash-pH prediction, robust uncertainty optimization, and operational inventory/cost features are deferred to version 2.0 because they require deeper models and should not be implemented superficially. Version 3.0 broadens the engine into carefully validated food and beverage modules. Version 4.0 may add selected non-food industrial modules with distinct safety and regulatory requirements.
