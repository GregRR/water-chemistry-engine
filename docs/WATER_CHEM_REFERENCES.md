# Water Treatment Engineering References

**Status:** Initial curated bibliography and research register  
**Project:** Water Treatment Calculator  
**Purpose:** Track scientific, technical, historical, and implementation sources used to design, validate, or contextualize the engine.

## 1. Source policy

Sources are not all treated as equally authoritative. Each entry should be classified as one or more of:

- **Primary scientific source:** peer-reviewed paper, standard, official analytical method, or original dataset.
- **Authoritative technical source:** recognized professional organization, government agency, standards body, or established technical manual.
- **Specialist secondary source:** technically informed book, article, calculator documentation, or practitioner reference.
- **Historical/software reference:** useful for feature inspiration or comparison, but not accepted as chemical authority without independent verification.
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

### ProMash Water Profiler tour

- **Title:** Water Profiler — ProMash Software Tour
- **Publisher:** Sausalito Brewing Company / ProMash
- **URL:** https://web.archive.org/web/20040806024646/http://www.promash.com/Software/Tour/StandAlone/Tour_Calculators5.html
- **Type:** Historical/software reference
- **Relevance:** Principal user-interface inspiration. Demonstrates stored water profiles, mineral-addition entry, and per-mineral ion-contribution tables.
- **Use in this project:** Preserve the transparent contribution table while replacing manual trial-and-error with automatic blend-and-treatment optimization.
- **Caution:** ProMash behavior and formulas must not be treated as authoritative without independent verification.

### Legacy BrewSession calculator source

- **Artifact:** `BrewSessionCalculators(2).zip`
- **Type:** Historical/software reference and regression candidate
- **Relevance:** User's earlier calculator implementations may reveal intended workflows and calculations.
- **Use in this project:** Catalogue features, extract test candidates, and identify legacy assumptions.
- **Caution:** Every formula must be checked against stronger sources before adoption.

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

### Bru'n Water knowledge resources

- **Title:** Water Knowledge
- **Author/site:** Martin Brungard / Bru'n Water
- **URL:** https://www.brunwater.com/water-knowledge
- **Type:** Specialist secondary source
- **Relevant topics:** Brewing ions, alkalinity, hardness, mash effects, and practical adjustment.
- **Use in this project:** Comparison, terminology, and test-case discovery. Formulas should be traced to primary or authoritative sources where possible.

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
- **Roadmap:** Primarily version 3 and later, with provenance and extensibility designed into version 1.

### Food Science Toolbox overview

- **Author:** Courtney Simons
- **Title:** Why Water Plays a Central Role in Food
- **Date:** 2026-03-16
- **URL:** https://foodsciencetoolbox.com/why-water-plays-a-central-role-in-food/
- **Type:** Introductory food-science source
- **Relevant topics:** Water polarity, solvent behavior, hydration, food reactions, texture, gluten formation, gelatinization, and stability.
- **Use in this project:** Roadmap context and educational framing for later food modules; not a quantitative treatment-model source.

## 4. Authoritative and primary sources to acquire or verify

The following categories are required before the corresponding calculations are considered validated.

### Brewing chemistry and analytical methods

- ASBC Methods of Analysis: water, alkalinity, hardness, minerals, pH, and related brewing-liquor methods. **ASBC verification pending.**
- European Brewery Convention methods relevant to brewing water. **Verification pending.**
- Current editions of recognized brewing-science texts, including water chemistry, mash chemistry, and mineral-treatment references.
- Government or accredited-laboratory methods for interpreting municipal and bottled-water analyses.

### Chemical composition and stoichiometry

For every included salt, acid, or alkali:

- authoritative molecular formula and molar mass;
- hydration state;
- purity/concentration conventions;
- ion yield per unit mass or volume;
- solubility and practical-use limits;
- safety documentation where relevant.

Preferred sources include NIST, PubChem, recognized chemical suppliers' technical specifications, pharmacopeial/food-grade standards, and peer-reviewed chemistry references.

### Water quality and reporting semantics

- US EPA drinking-water terminology and reporting guidance.
- USGS water-chemistry terminology and conversion guidance.
- WHO drinking-water guidance where relevant.
- Bottled-water regulatory and quality-report requirements.
- Definitions and conversions for alkalinity, hardness, `as CaCO3`, equivalents, detection limits, and uncertainty.

### Mead and distilling

Version 1 requires a focused research set for:

- mead fermentation-water guidance;
- distilling mash and fermentation water;
- distillery process water;
- spirit proofing water;
- sensory and stability implications of proofing-water composition.

These use cases must remain distinct. A profile suitable for fermentation is not automatically suitable for proofing finished spirits.

## 5. Version 3 research queues

Create separate research notes before implementing each domain:

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

1. Validate the chemical definitions and ion yields for the version 1 salts.
2. Establish authoritative semantics for alkalinity, hardness, bicarbonate, carbonate, and `as CaCO3` reporting.
3. Identify defensible initial beer, mead, and distilling target profiles with redistribution rights.
4. Find primary or authoritative water-blending and charge-balance references.
5. Catalogue the legacy BrewSession water-calculator formulas and compare them against stronger sources.
6. Define a citation and versioning format for bundled reference data.
