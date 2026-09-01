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
  - Non-additive treatment processes exist, but a generalized treatment-operation abstraction is not required for Version 1.
- **Caution:** The paper's numerical water-requirement tables are the authors' recommendations in an industrial-brewery context; they are not assumed to be universal standards for every brewery or product.

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
- **Roadmap:** Supports early generic target/reference data where defensible; domain-specific sensory/process modeling remains later work.

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
- **Occidental Chemical Corporation (OxyChem), _Calcium Chloride: A Guide to Physical Properties_**
  - URL: https://www.oxy.com/siteassets/documents/chemicals/products/other-essentials/173-01791.pdf
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

- US EPA drinking-water terminology and reporting guidance.
- USGS water-chemistry terminology and conversion guidance.
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

## 5. Cross-domain profile and domain-model research queues

Research now has two distinct purposes: (1) admit well-sourced target/reference data that the generic engine can already use, and (2) prepare later domain-specific predictive/guidance models. Coffee is the strongest early profile-data candidate; deeper coffee, tea, and dough science remains separate later work. Create separate research notes as needed:

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

1. Validate the chemical definitions and ion yields for the version 1 salts,
   including anhydrous calcium chloride as a distinct identity.
2. Define and validate treatment-material semantics for solid assay/purity,
   liquid concentration basis, mass dosing, density-supported volume dosing,
   and ranged material specifications before optimizer work relies on them.
3. Establish authoritative semantics for alkalinity, hardness, bicarbonate, carbonate, and `as CaCO3` reporting.
4. Identify defensible initial beer, mead, and distilling target profiles with redistribution rights.
5. Identify the first defensible coffee target/reference profiles and classify each as standard, recommendation, practitioner reference, experimental reference, or optimized target as appropriate.
6. Identify tea and dough/bread/pizza reference profiles only where the evidence and redistribution status support admission; do not manufacture optimal profiles from regional analyses.
7. Find primary or authoritative water-blending and charge-balance references.
8. Catalogue unverified water-treatment formulas and claims encountered during research and compare them against stronger sources.
9. Define a citation, evidentiary-classification, and versioning format for bundled reference data.
