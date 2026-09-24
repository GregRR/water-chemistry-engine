# Water Chemistry Engineering References

**Status:** Initial curated bibliography and research register  
**Project:** Water Chemistry Engine
**Purpose:** Track scientific, technical, historical, and implementation sources used to design, validate, or contextualize the engine.

## 1. Source policy

Sources are not all treated as equally authoritative. Each entry should be classified as one or more of:

- **Primary scientific source:** peer-reviewed paper, standard, official analytical method, or original dataset.
- **Authoritative technical source:** recognized professional organization, government agency, standards body, or established technical manual.
- **Specialist secondary source:** technically informed book, article, or practitioner reference.
- **Introductory source:** useful for explanations and discovery, but not sufficient by itself for formulas, limits, or validation.

For every calculation implemented from a source, record:

- the exact formula, table, or claim used;
- units and reporting basis;
- assumptions and valid range;
- edition, date, DOI, method number, or stable identifier;
- whether redistribution of source data is permitted;
- the tests that verify the implementation.

Where an authoritative ASBC method, table, or formula is known to exist but cannot yet be checked directly, mark the item **ASBC verification pending** and record the method or table identifier when known.

Domain-specific sources may motivate reusable Engine chemistry, but a brewing,
coffee, tea, dough, industrial, or other purpose-specific model should not be
moved into the Engine merely because its chemistry is discussed here. Extract
the domain-neutral primitive and leave interpretation/prediction in the
consumer or separate domain library.

## 2. Foundational brewing-water sources

### Brewer World overview

- **Author:** Abhinav Reddy
- **Title:** The Importance of Water Chemistry in Beer & Brewing
- **Date:** 2021-01-20
- **URL:** https://www.brewer-world.com/the-importance-of-water-chemistry-in-beer-brewing/
- **Type:** Introductory secondary source
- **Relevant topics:** Regional water profiles, brewing ions, iron/off-flavor concerns, and the role of water chemistry in fermentation and flavor.
- **Use in this project:** Background explanation and discovery only; not a formula or target-profile authority.

### Brewers Association water resource hub

- **Title:** Water Resources
- **Publisher:** Brewers Association
- **URL:** https://www.brewersassociation.org/resource-hub/water/
- **Type:** Authoritative technical-source index
- **Relevant topics:** Brewery water quality, treatment methods, equipment, and operational practices.
- **Use in this project:** Research index for professional brewing-water operations and future small-brewery features.

### Brewers Association webinars

- **Titles:** Water Chemistry for Consistent Brewing; Understanding and Adjusting Water Chemistry
- **Publisher:** Brewers Association
- **URLs:**
  - https://www.brewersassociation.org/webinar/water-chemistry-for-consistent-brewing/
  - https://www.brewersassociation.org/webinar/understanding-and-adjusting-water-chemistry/
- **Type:** Authoritative technical education
- **Use in this project:** Practical brewing context and discovery. Some content may require membership access.

### Eumann and Schildbach (2012)

- **Authors:** Michael Eumann; Stefan Schildbach
- **Title:** 125th Anniversary Review: Water sources and treatment in brewing
- **Journal:** *Journal of the Institute of Brewing*, Volume 118, pages 12–21
- **Year:** 2012
- **DOI:** 10.1002/jib.18
- **Type:** Peer-reviewed brewing-science review article
- **Relevant topics:** Distinct brewery water purposes; brewing-water calcium, alkalinity, chloride, sulfate, nitrate, silica, and disinfectant concerns; dechlorination; reverse osmosis; ion exchange; deaeration; other treatment technologies.
- **Design implications:**
  - Intended water use belongs to calculation/application context because brew water, dilution water, service water, and other brewery uses have different requirements.
  - Chlorine and other oxidizing disinfectants can matter independently of chloride concentration and should not be discarded during report ingestion.
  - The review identifies CaSO4 and CaCl2 additions as noncarbonate-hardness treatments and notes practical control problems from the poor solubility of calcium sulfate, supporting explicit treatment-model limits rather than assuming every mineral behaves like highly soluble calcium chloride.
  - The review formulates brewing residual alkalinity from total alkalinity and
    calcium/magnesium hardness on an equivalent basis. This supports total
    alkalinity as the actionable generic Engine calculation axis while keeping
    residual-alkalinity interpretation in a brewing consumer rather than
    treating it as source-water identity or a generic Engine recommendation.
  - Non-additive treatment processes exist, but a generalized treatment-operation abstraction is not required for Version 1.
- **Caution:** The paper's numerical water-requirement tables are the authors' recommendations in an industrial-brewery context; they are not assumed to be universal standards for every brewery or product.

### Palmer and Kaminski (2013)

- **Authors:** John Palmer; Colin Kaminski
- **Title:** *Water: A Comprehensive Guide for Brewers*
- **Publisher:** Brewers Publications
- **Year:** 2013
- **Type:** Specialist technical book from a recognized brewing publisher
- **Reviewed material:** Chapters 3–7 and Appendices B–D.
- **Relevant topics:** Water-report interpretation; alkalinity and hardness;
  carbonate equilibrium; residual alkalinity; malt buffering and mash pH;
  acid/base treatment; salt and acid stoichiometry; phosphoric-acid/calcium
  interactions; charge balance; carbonate-species distribution.
- **Design implications:**
  - Chapter 3 supports preserving report-native analyte/method semantics and
    keeping alkalinity, hardness, bicarbonate, and carbonate as distinct
    concepts rather than interchangeable labels.
  - Chapters 4–6 show why generic aqueous carbonate/acid-base chemistry can be
    reusable while mash-pH prediction also requires malt/grain-specific
    buffering and process inputs. Mash-pH and residual-alkalinity
    interpretation therefore belong in a brewing consumer, not the Engine.
  - Chapter 6 and Appendix B support future generic acid/base, target-water-pH,
    precipitation, and order-of-addition primitives, provided equations and
    numerical constants are independently validated before implementation.
  - Appendix C supports explicit hydration state, mass-fraction, concentration,
    density, and equivalent-basis semantics for treatment materials.
  - Appendix D supports charge balance as a report-quality diagnostic. An
    imbalance may reflect missing ions, reporting basis, speciation, or
    measurement/reporting error; the Engine must not force balance by inventing
    or altering source values.
  - Chapter 7 reinforces coupled-ion treatment constraints and the distinction
    between a published recommendation/reference profile and a scientifically
    established optimum.
- **Verification rule:** OCR is used for navigation/prose only. Equations,
  tables, numerical constants, and any implementation logic must be checked
  against the scanned page; where practical, implementation claims should also
  be cross-checked against an independent authoritative source.
- **Known source cautions:**
  - Appendix D page 275 incorrectly describes the non-bicarbonate share at pH 7
    as carbonate and treats a dissolved-inorganic-carbon species fraction as a
    fraction of total alkalinity. Its own Table 28 on page 277 instead assigns
    that share to carbonic acid and rounds carbonate to zero. Carbonic acid is
    not an alkalinity term, so the illustrated division of bicarbonate by its
    species fraction does not calculate total alkalinity.
  - Appendix C page 269 illustrates estimating dilute-acid density by a simple
    concentration ratio. That shortcut is not accepted as an Engine material
    rule; volume dosing requires an exact supported mass-per-volume basis or
    independently sourced density and applicable-condition data.
  - The verified correction, bounded audit calculation, authoritative
    cross-checks, and future implementation rules are recorded in
    [`docs/research/carbonate-speciation-source-audit.md`](research/carbonate-speciation-source-audit.md).

### Sutea et al. (2025)

- **Authors:** Corina Maria Sutea et al.
- **Title:** Beer Aroma Compounds: Key Odorants, Off-Flavour Compounds and Improvement Proposals
- **Journal:** *Foods*, Volume 14, article 4287
- **Year:** 2025
- **DOI:** 10.3390/foods14244287
- **Type:** Peer-reviewed review article
- **Relevant topics:** Beer odorants and off-flavours, including chlorophenols, metallic flavour, and water-related contamination sources.
- **Design implications:** Supports preserving chlorine/chloramine information from source-water reports because chlorine can participate in chlorophenol formation associated with medicinal off-flavours.
- **Use in this project:** Sensory/mechanistic context and research support; individual thresholds or corrective actions should be verified against primary sources before becoming engine limits.

## 3. Food science and sensory sources

### Sheibani and Mohammadi (2018)

- **Authors:** Ershad Sheibani; Abdorreza Mohammadi
- **Title:** The impacts of water compositions on sensory properties of foods and beverages cannot be underestimated
- **Journal:** *Food Research International*, Volume 108, pages 101–110
- **Year:** 2018
- **DOI:** 10.1016/j.foodres.2018.03.024
- **PMID:** 29735038
- **Type:** Peer-reviewed review article
- **Relevant topics:** Water composition as a source of sensory variation; interactions between minerals and food/beverage constituents; source, treatment, and distribution effects.
- **Design implications:**
  - Preserve source and treatment provenance.
  - Leave room for constituents beyond the initial brewing-ion panel.
  - Keep sensory annotations evidence-based and domain-specific.
  - Do not claim direct prediction of taste from a generic ion-match score.
- **Roadmap:** Supports early generic target/reference data where defensible;
  domain-specific sensory/process modeling belongs in consumers or separate
  domain libraries, with reusable chemistry extracted into the Engine when a
  common primitive emerges.

### Food Science Toolbox overview

- **Author:** Courtney Simons
- **Title:** Why Water Plays a Central Role in Food
- **Date:** 2026-03-16
- **URL:** https://foodsciencetoolbox.com/why-water-plays-a-central-role-in-food/
- **Type:** Introductory food-science source
- **Relevant topics:** Water polarity, solvent behavior, hydration, food reactions, texture, gluten formation, gelatinization, and stability.
- **Use in this project:** Roadmap context and educational framing for later food modules; not a quantitative treatment-model source.

### SCAA specialty-coffee water standard (2009)

- **Title:** SCAA Standard | Water for Brewing Specialty Coffee
- **Publisher:** Specialty Coffee Association of America
- **Revision:** 2009-11-21; version `21NOV2009A`
- **Type:** Historical authoritative industry standard
- **Relevant topics:** Coffee-brewing water target/range concepts for TDS, calcium hardness, alkalinity, pH, sodium, odor/color, and total chlorine.
- **Design implications:**
  - Supports preserving total chlorine as source-water data.
  - Demonstrates that a domain may evaluate water against purpose-specific criteria that are not reducible to a generic ion-distance target.
- **Caution:** Treat these values as a dated SCAA standard, not automatically as the current Specialty Coffee Association standard.

### Hendon, Colonna-Dashwood, and Colonna-Dashwood (2014)

- **Authors:** Christopher H. Hendon; Lesley Colonna-Dashwood; Maxwell Colonna-Dashwood
- **Title:** The Role of Dissolved Cations in Coffee Extraction
- **Journal:** *Journal of Agricultural and Food Chemistry*, Volume 62, pages 4947–4950
- **Year:** 2014
- **DOI:** 10.1021/jf501687c
- **Type:** Primary scientific source
- **Relevant topics:** Modeled interactions of Na+, Mg2+, and Ca2+ with representative coffee compounds; cation-dependent extraction behavior; interaction with bicarbonate buffering.
- **Design implications:** Supports early coffee target/reference data using the generic water engine while reinforcing that a later coffee-specific extraction/sensory model is a separate capability.
- **Caution:** The paper does not establish one universally optimal coffee-water composition; do not turn its relative binding results into a generic "more magnesium is better" scoring rule.

### Daily Coffee News practical water guide (2018)

- **Title:** A Practical Water Guide for Coffee Professionals: Part I
- **Date:** 2018-08-15
- **URL:** https://dailycoffeenews.com/2018/08/15/a-practical-water-guide-for-coffee-professionals-part-i/
- **Type:** Specialist secondary source
- **Relevant topics:** Practical coffee-water composition, hardness/alkalinity, treatment, and distinction between chloride and chlorine-related concerns.
- **Use in this project:** Workflow and terminology research for early coffee target/reference data and later coffee-specific modeling. Quantitative rules should be traced to primary or current authoritative sources before implementation.

### Ferreira et al. (2024)

- **Authors:** Fernanda Ferreira et al.
- **Title:** Harnessing the Power of Natural Mineral Waters in Bread Formulations: Effects on Chemical, Physical, and Physicochemical Properties
- **Journal:** *Applied Sciences*, Volume 14, article 9179
- **Year:** 2024
- **DOI:** 10.3390/app14209179
- **Type:** Primary scientific source
- **Relevant topics:** Effects of different mineral waters on bread mineral composition, pH, texture, and related physicochemical properties.
- **Design implications:** The reported waters are legitimate experimental reference profiles and may be bundled as such if admission rules are met, but the study provides no basis for a universal optimal bread-water target. Deeper bread/sourdough modeling remains future domain work.

### Sourdough Institute tap-water article

- **Title:** The Role of Tap Water in Sourdough Preparation
- **Publisher/site:** Sourdough Institute
- **URL:** https://www.sourdoughinstitute.com/post/the-role-of-tap-water-in-sourdough-preparation
- **Type:** Specialist secondary source / research summary
- **Relevant topics:** Water composition in starter establishment and bread-making context; possible differences between starter creation, mature starter maintenance, and dough use.
- **Use in this project:** Future bread/sourdough research questions and workflow design. Trace scientific claims to the underlying primary study before implementing quantitative models.

### Brot Box water-quality article

- **Title:** How Water Quality Affects Bread Baking
- **Publisher/site:** The Brot Box
- **URL:** https://thebrotbox.com/blogs/news/how-water-quality-affects-bread-baking
- **Type:** Practitioner/introductory secondary source
- **Relevant topics:** Practical discussion of hardness, pH, chlorine/chloramine, yeast, gluten, and bread quality.
- **Use in this project:** Discovery and user-workflow context only; its numerical recommendations are not accepted as authoritative target profiles without stronger validation.

## 4. Authoritative and primary source register and verification gaps

The verified sources and still-pending categories below are required before
the corresponding calculations are considered validated. Items that remain to
be acquired or checked are marked explicitly.

### Brewing chemistry and analytical methods

- ASBC Methods of Analysis: water, alkalinity, hardness, minerals, pH, and related brewing-liquor methods. **ASBC verification pending.**
- European Brewery Convention methods relevant to brewing water. **Verification pending.**
- Current editions of recognized brewing-science texts, including water chemistry, mash chemistry, and mineral-treatment references.
- Government or accredited-laboratory methods for interpreting municipal and bottled-water analyses.

### Chemical composition and stoichiometry

For every included salt, acid, or alkali, distinguish evidence for the ideal
chemical identity from evidence for a real treatment material.

Chemical-identity evidence should cover:

- authoritative molecular formula and molar mass;
- hydration state;
- stoichiometric ion yield;
- authoritative chemical reference.

Treatment-material evidence should cover where applicable:

- purity/assay, preserving reported ranges;
- solution concentration and its explicit basis;
- density and reference temperature/conditions when volume dosing requires it;
- product grade or specification;
- solubility, dissolution, and practical-use limits with their valid conditions;
- safety documentation.

Preferred sources include NIST, PubChem, recognized chemical suppliers' technical specifications, pharmacopeial/food-grade standards, and peer-reviewed chemistry references.

#### Solution concentration terminology

- **IUPAC Compendium of Chemical Terminology (Gold Book), “mass
  concentration,” term M03713**
  - DOI: https://doi.org/10.1351/goldbook.M03713
  - Type: authoritative chemical terminology
  - Relevant definition: mass of a constituent divided by the volume of the
    mixture.
  - Use: supports the exact active-chemical-mass-per-solution-volume material
    basis and the calculation `active mass = mass concentration × measured
    solution volume`.
  - Project policy: the initial engine contract requires the measurement
    temperature to match the stated concentration reference temperature and
    provides no thermal correction. This fail-closed condition is project
    policy; it is not a numerical rule supplied by the IUPAC definition.

#### Calcium chloride identity and material references

- **PubChem CID 5284359 — Calcium chloride (`CaCl2`)**
  - URL: https://pubchem.ncbi.nlm.nih.gov/compound/5284359
  - Type: authoritative government chemical database
  - Relevant data: anhydrous formula and molecular weight (~110.98 g/mol).
  - Use: authoritative identity/reference case for anhydrous calcium chloride.
- **PubChem CID 6093260 — Calcium chloride dihydrate (`CaCl2·2H2O`)**
  - URL: https://pubchem.ncbi.nlm.nih.gov/compound/6093260
  - Type: authoritative government chemical database
  - Relevant data: dihydrate formula and molecular weight (~147.01 g/mol).
  - Use: independent identity/reference case for the existing dihydrate model.
- **Occidental Chemical Corporation (OxyChem), _Calcium Chloride Handbook_**
  - URL: https://www.oxychemcalciumchloride.com/siteassets/documents/guides/calcium-chloride-handbook.pdf
  - Type: authoritative manufacturer technical guide
  - Relevant data: physical properties of CaCl2 hydrates and solutions; the
    guide lists pure dihydrate as 75.49% CaCl2 by composition and distinguishes
    it from commercial-grade products; solution physical properties vary with
    concentration and temperature.
  - Design implication: pure hydrate composition and commercial material assay
    are separate semantics; density used for volume dosing must retain its
    applicable conditions.
- **OxyChem DOWFLAKE Xtra 83–87% Calcium Chloride Flakes**
  - URL: https://www.oxychemcalciumchloride.com/products/dowflake-xtra-83-87-calcium-chloride-flakes/
  - Type: manufacturer product specification
  - Relevant data: example of a commercial solid material specified by a CaCl2
    assay range rather than by pure-hydrate stoichiometry alone.
  - Design implication: preserve material assay ranges instead of treating a
    product label as the definition of a hydrate or silently averaging it.
- **OxyChem LIQUIDOW Food Grade Calcium Chloride Solution**
  - URL: https://www.oxychemcalciumchloride.com/products/liquidow-food-grade-calcium-chloride-solution/
  - Type: manufacturer food-grade product/technical data
  - Relevant data: an example food-grade liquid material specified at
    32.0–33.0% CaCl2 by weight, with certificate-of-analysis support.
  - Design implication: a liquid treatment is a solution/material, not a third
    calcium-chloride hydration state; mass dosing and volume dosing require
    distinct conversion semantics. Density for volume conversion must come from
    a validated source appropriate to the specified concentration and
    conditions.

#### Gypsum solubility references

- **Voigt (2023)**
  - Title: Solubility of anhydrite and gypsum at temperatures below 100°C and
    the gypsum-anhydrite transition temperature in aqueous solutions: a
    re-assessment
  - Journal: *Frontiers in Nuclear Engineering*, Volume 2
  - DOI: 10.3389/fnuen.2023.1208582
  - Type: peer-reviewed scientific reassessment of experimental solubility and
    calorimetric data
  - Relevant topics: temperature-dependent gypsum/anhydrite solubility,
    phase stability, electrolyte effects, and slow anhydrite crystallization
    kinetics; the reassessment places the gypsum-anhydrite transition in water
    near 42°C rather than supporting a universal one-line hot-versus-cold rule.
  - Design implication: do not encode the shorthand that gypsum is simply
    "less soluble in hot water than cold" as a general engine rule.
    Temperature, phase, solution composition, and kinetics belong to any later
    validated solubility model.

#### Carbonate/chalk and dissolution references

- **Parkhurst and Appelo (2013), PHREEQC Version 3**
  - Title: Description of Input and Examples for PHREEQC Version 3—A Computer
    Program for Speciation, Batch-Reaction, One-Dimensional Transport, and
    Inverse Geochemical Calculations
  - DOI: 10.3133/tm6A43
  - URL: https://pubs.usgs.gov/publication/tm6A43
  - Type: authoritative USGS aqueous-geochemistry model documentation
  - Design implication: equilibrium species distributions require a declared
    aqueous/activity model and boundary conditions beyond linear ion inventory.
- **USGS Office of Water Quality Technical Memorandum WQ2012.05**
  - Title: Replacement of the Simple Speciation Method for Computation of
    Carbonate and Bicarbonate Concentrations from Alkalinity Titrations
  - URL: https://water.usgs.gov/water-resources/memos/memo.php?id=2098
  - Type: authoritative government analytical-method policy and rationale
  - Relevant topics: pH, alkalinity/ANC, acid-dissociation constants, activity
    treatment, noncarbonate titratable constituents, and the limitations of
    simplified carbonate/bicarbonate calculations.
  - Design implication: neither total alkalinity nor a fixed pH 8.3 threshold
    supports a universal conversion to bicarbonate/carbonate concentration.
- **Rounds and Wilde (2012), USGS National Field Manual section 6.6**
  - Title: Alkalinity and Acid Neutralizing Capacity
  - DOI: 10.3133/twri09A6.6
  - URL: https://www.usgs.gov/publications/chapter-a6-section-66-alkalinity-and-acid-neutralizing-capacity
  - Type: authoritative government field/analytical method
  - Design implication: alkalinity is acid-neutralizing capacity; carbonate-
    species calculations are separate analytical/model operations.

- **Plummer and Busenberg (1982)**
  - Title: The solubilities of calcite, aragonite and vaterite in CO2-H2O
    solutions between 0 and 90°C, and an evaluation of the aqueous model for
    the system CaCO3-CO2-H2O
  - Journal: *Geochimica et Cosmochimica Acta*, Volume 46, Issue 6, pages
    1011–1040
  - DOI: 10.1016/0016-7037(82)90056-4
  - USGS record: https://pubs.usgs.gov/publication/70011789
  - Type: primary scientific source / USGS-authored research
  - Relevant topics: calcite solubility and CaCO3-CO2-H2O equilibria across
    temperature and CO2 conditions.
  - Design implication: chalk cannot be represented faithfully as a fixed
    complete-dissolution Ca2+/carbonate dose independent of pH/CO2 state.
- **USGS Alkalinity Calculator methods**
  - URL: https://or.water.usgs.gov/alk/methods.html
  - Type: authoritative government analytical-method documentation
  - Relevant topics: carbonate-system titration endpoints and dependence on
    carbonic-acid equilibrium constants.
  - Design implication: pH 8.3/8.4 is not a hard chemical switch at which all
    carbonate universally becomes bicarbonate; future speciation must use an
    explicit equilibrium model.

The specific claim that undissolved brewing chalk remains on grain and later
continues reacting in the kettle or fermenter remains a research question. Do
not encode that process narrative without direct experimental brewing evidence.

### Water quality and reporting semantics

- **Standard Methods 2320 — Alkalinity**
  - DOI: 10.2105/SMWW.2882.023
  - URL: https://www.standardmethods.org/doi/10.2105/SMWW.2882.023
  - Type: recognized authoritative analytical method
  - Relevant topic: alkalinity as acid-neutralizing capacity determined by
    titration.
  - Design implication: total alkalinity is a water property expressed on an
    equivalent basis, not an automatically interchangeable bicarbonate or
    carbonate concentration.
- **USGS National Field Manual, Chapter A6.6 — Alkalinity and Acid
  Neutralizing Capacity**
  - Authors: Stewart A. Rounds; Franceska D. Wilde
  - DOI: 10.3133/twri09A6.6
  - URL: https://pubs.usgs.gov/publication/twri09A6.6
  - Type: authoritative government analytical-method guidance
  - Relevant topics: alkalinity versus acid-neutralizing capacity, filtered
    versus unfiltered samples, titration, carbonate and noncarbonate
    contributors, and method/reporting semantics.
  - Design implication: preserve whether a source result is alkalinity or ANC,
    its sample state, and its analytical/titration method when supplied.
- **USGS Office of Water Quality Technical Memorandum 2012.05**
  - Title: Replacement of the Simple Speciation Method for Computation of
    Carbonate and Bicarbonate Concentrations from Alkalinity Titrations
  - URL: https://water.usgs.gov/water-resources/memos/memo.php?id=2098
  - Type: authoritative government scientific policy and method rationale
  - Relevant topics: additional inputs and assumptions required for carbonate
    speciation; activity, temperature, ionic-strength, hydroxide, and
    noncarbonate-alkalinity limitations.
  - Design implication: never silently convert total alkalinity to bicarbonate
    or carbonate, and keep any future speciation result derived, model-versioned,
    and separate from the reported value.
- **USGS PHREEQC Version 3 `SOLUTION` documentation**
  - URL: https://water.usgs.gov/water-resources/software/PHREEQC/documentation/phreeqc3-html/phreeqc3-48.htm
  - Type: authoritative government geochemical-model documentation
  - Relevant data: alkalinity is converted through gram equivalent weight;
    alkalinity reported as CaCO3 uses approximately 50.04 g/eq.
  - Design implication: use equivalents as the canonical calculation axis and
    retain `as CaCO3` as an explicit reporting basis.
- US EPA drinking-water terminology and reporting guidance.
- WHO drinking-water guidance where relevant.
- Bottled-water regulatory and quality-report requirements.
- Definitions and conversions for alkalinity, hardness, `as CaCO3`, equivalents, detection limits, and uncertainty.

### IUPAC pH definition and measurement recommendations

- **Entry:** pH, IUPAC Compendium of Chemical Terminology (Gold Book), term
  P04524
- **DOI:** 10.1351/goldbook.P04524
- **URL:** https://goldbook.iupac.org/terms/view/P04524
- **Type:** Authoritative chemical terminology
- **Relevant claim:** Defines pH from hydrogen-ion activity as
  `pH = -lg(a(H+))`.
- **Project inference:** The activity-based definition does not itself impose a
  universal numerical 0-through-14 boundary. Any narrower accepted range must
  therefore come from a separately documented domain or application policy.
- **Use in this project:** Supports representing chemical pH with a finite
  semantic value rather than a Pint unit or an unexplained universal range.

- **Authors:** R. P. Buck et al.
- **Title:** Measurement of pH. Definition, Standards, and Procedures (IUPAC
  Recommendations 2002)
- **Journal:** *Pure and Applied Chemistry*, Volume 74, Issue 11, pages
  2169–2200
- **DOI:** 10.1351/pac200274112169
- **NIST record:**
  https://www.nist.gov/publications/measurement-ph-definition-standards-and-procedures-iupac-recommendations-2002
- **Type:** IUPAC recommendation / authoritative primary technical source
- **Relevant topics:** Notional activity-based pH definition, standards,
  measurement procedures, traceability, and uncertainty for dilute aqueous
  solutions.
- **Use in this project:** Governs the semantic distinction between pH,
  hydrogen-ion activity, operational measurement, and future calculated-pH
  models. It does not justify treating activity as concentration or adding a
  derived working-water pH model without further evidence.

### Mead and distilling

Version 1 requires a focused research set for:

- mead fermentation-water guidance;
- distilling mash and fermentation water;
- distillery process water;
- spirit proofing water;
- sensory and stability implications of proofing-water composition.

These use cases must remain distinct. A profile suitable for fermentation is not automatically suitable for proofing finished spirits.

### Numerical optimization backend

- **Entry:** SciPy 1.17 `scipy.optimize.milp` documentation
- **URL:** https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.milp.html
- **Type:** Authoritative library documentation
- **Relevant claims:** Defines SciPy's mixed-integer linear-programming
  interface, integer-variable semantics, bounds and linear constraints, result
  statuses, MIP gap, and deterministic HiGHS backend. Its example explicitly
  demonstrates that rounding a continuous optimum need not produce the correct
  integer solution.
- **Use in this project:** Supports modeling measured material doses as integer
  counts of declared dose increments and recording solver termination data.

- **Entry:** HiGHS option definitions
- **URL:** https://ergo-code.github.io/HiGHS/dev/options/definitions/
- **Type:** Authoritative solver documentation
- **Relevant claims:** Documents numerical thresholds and feasibility options,
  including the MIP feasibility tolerance. Solver feasibility tolerances are
  not a substitute for engine-level reconstruction of the returned plan.
- **Use in this project:** Supports retaining raw solver results for audit while
  independently validating increment counts, bounds, objective nonnegativity,
  and agreement with the ordinary forward calculation.

## 5. Cross-domain profile and consumer-model research queues

Research now has two distinct purposes: (1) admit well-sourced target/reference
data that the generic Engine can already use, and (2) inform consumer/domain
models while identifying any lower-level chemistry that is genuinely reusable
enough to extract into the Engine. Coffee is the strongest early profile-data
candidate; deeper coffee, tea, dough, and brewing-process science remains
consumer/domain work unless a common chemistry primitive emerges. Create
separate research notes as needed:

- `research/coffee.md`
- `research/tea.md`
- `research/dough-and-bread.md`
- `research/alkaline-noodles.md`
- `research/cheesemaking.md`
- `research/lacto-fermentation.md`
- `research/sensory-water.md`

Each note should identify target constituents, measurable outcomes, treatment methods, safety constraints, known standards, validated datasets, and gaps in evidence.

## 6. Reference-data admission rules

A profile or treatment definition may enter bundled `reference-data/` only when:

1. Its provenance is recorded.
2. The meaning of the numbers is clear: source water, treated process water, target range, historical estimate, or measured result.
3. Units and reporting bases are explicit.
4. Redistribution is permitted.
5. Uncertainty, range, date, and regional variation are retained where available.
6. The entry has a stable identifier and version.
7. At least one review or validation test exists.

Historical city profiles must not be labeled as a brewery's actual treated liquor unless the source supports that interpretation.

## 7. Research-record template

```markdown
### Citation key

- **Full citation:**
- **Stable identifier:** DOI / ISBN / method number / report ID
- **Source class:**
- **Domains:**
- **Claims relevant to the engine:**
- **Formulae/tables/data used:**
- **Units and basis:**
- **Assumptions and valid range:**
- **Implementation implications:**
- **Validation tests:**
- **Redistribution status:**
- **Verification status:** verified / provisional / ASBC verification pending
- **Notes:**
```

## 8. Immediate research priorities

1. Continue validating the chemical definitions and ion yields for the version
   1 salts. Anhydrous calcium chloride is now implemented as a distinct identity
   from the dihydrate using the registered PubChem reference and independently
   checked formula-mass and ion-yield cases.
2. Continue validating treatment-material semantics. Exact and ranged active-
   chemical mass fractions now cover solid and aqueous-solution mass dosing;
   ranged specifications stay unresolved. Exact-density manual volume dosing
   now requires a retained reference temperature and matching measurement
   condition. An exact active-mass-per-solution-volume basis can resolve a
   manual volume dose directly under the same temperature-match rule without
   inferring density. Thermal correction, volume-dose optimization, and
   practical-use-limit policy remain to be defined before use.
3. Complete the 0.5 total-alkalinity source semantics by preserving supplied
   analytical context (alkalinity versus ANC, method/endpoint, sample state,
   original analyte wording/unit) and document that the conservative-equivalent
   model is not a laboratory-titration simulator.
4. Identify defensible initial beer, mead, and distilling target profiles with redistribution rights.
5. Identify the first defensible coffee target/reference profiles and classify each as standard, recommendation, practitioner reference, experimental reference, or optimized target as appropriate.
6. Identify tea and dough/bread/pizza reference profiles only where the evidence and redistribution status support admission; do not manufacture optimal profiles from regional analyses.
7. Find primary or authoritative references for charge-balance diagnostics,
   hardness reconciliation, carbonate speciation, and reusable aqueous
   equilibrium calculations.
8. Catalogue unverified water-treatment formulas and claims encountered during research and compare them against stronger sources.
9. Extend the implemented `TargetProfileCatalog` domain boundary into a
   machine-readable bundled-data format that also records citation,
   redistribution/licensing, verification, and review status. Catalog identity
   validation alone is not sufficient for admission.
