# Water Treatment Calculator Future Capabilities

This document preserves useful ideas that are intentionally outside the active
near-term release path in `docs/ROADMAP.md`. Inclusion here is not a promise for
a particular release; it means the idea should not be lost while the project
prioritizes a usable application and a stable Version 1.0.

## Advanced optimization and planning

- Robust optimization under uncertain/ranged source-water reports.
- Sensitivity analysis and worst-case planning.
- Pareto-front exploration.
- More sophisticated target weighting and policy customization.
- Treatment-cost optimization.
- Inventory-aware treatment planning.
- Package-size and purchasing considerations.
- Multi-batch production planning.
- Production-scale water allocation and availability constraints.

## Additional treatment methods

Potential future non-additive or reactive treatment workflows include:

- activated-carbon filtration/dechlorination;
- reverse-osmosis treatment and rejection models;
- ion exchange;
- lime softening;
- other softening/dealkalization methods;
- deaeration;
- chlorine/chloramine removal processes;
- membrane filtration where relevant;
- other validated treatment chains.

Do not force these into one universal `TreatmentOperation` abstraction until
multiple implemented workflows demonstrate the common contract.

## Advanced brewing and fermentation chemistry

- Recipe-aware mash-pH prediction.
- Grain buffering models.
- Acid and alkali additions.
- Separate mash and sparge optimization.
- Deeper carbonate/bicarbonate equilibrium behavior.
- Precipitation/solubility modeling where useful.
- Purpose-aware brewery process-water workflows beyond the first validated uses.
- Spirit-proofing-specific guidance where scientifically supported.
- Brewery-scale service/dilution/process-water workflows where appropriate.

## Report ingestion and source-water history

Beyond the initial AI-assisted report workflow:

- broader document formats;
- improved table extraction and document-layout handling;
- longitudinal comparison of dated reports;
- multiple-source and multiple-treatment-stage reports;
- laboratory-result imports;
- review queues and extraction-confidence workflows;
- change detection across source-water reports;
- additional regulatory/reference-value preservation where useful.

## Interchange and external integrations

- Expanded BeerJSON compatibility as standards evolve.
- Richer FermentationJSON archival/interchange support.
- Stable public API/SDK surfaces for third-party applications.
- Future native mobile and desktop applications.
- Additional import/export formats only when concrete demand exists.

## Reference and historical datasets

- Additional current municipal source-water datasets.
- Historical regional/city water analyses kept as separate sourced records.
- Published brewery or practitioner point-of-use profiles.
- Measured bakery/pizzeria point-of-use profiles.
- Historical/reference coffee and tea waters.
- Experimental water datasets from peer-reviewed food/beverage studies.
- Versioned profile history rather than silent replacement or averaging.

## Domain-specific food and beverage science

Early profile/reference data may appear before these models. The following are
reserved for deeper domain-specific calculation, prediction, or guidance:

- coffee extraction and sensory models;
- coffee equipment scaling/corrosion constraints where useful;
- tea infusion/extraction models;
- bread and pizza dough behavior;
- sourdough starter establishment and maintenance;
- fermentation/yeast effects of chlorine/chloramine and mineral composition;
- alkaline noodles and kansui;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages;
- sensory-water research that cannot be represented as a simple target profile.

## Selected industrial water applications

Potential long-term areas include:

- laboratory preparation water;
- cleaning and rinsing water;
- boiler/steam feedwater;
- cooling water;
- selected manufacturing/process-water applications.

Industrial support requires dedicated safety, regulatory,
materials-compatibility, treatment, and validation work. It must not be created
by relabeling food-oriented calculations.

## Research/data principles that remain in force

- Preserve provenance and the evidentiary class of every profile.
- Do not manufacture canonical profiles by averaging conflicting sources.
- Do not relabel regional/reference water as an experimentally optimized target.
- Keep reported, derived, predicted, and measured data distinct.
- Keep source-water identity separate from intended use.
- Preserve unknowns, censoring, and reporting bases.
- Keep pH logarithmic and model-derived pH explicitly versioned.
