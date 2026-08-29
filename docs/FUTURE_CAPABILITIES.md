# Water Chemistry Engine Future Capabilities

This document preserves useful engine ideas intentionally outside the active
near-term release path in `docs/ROADMAP.md`. Inclusion here is not a promise for
a particular release.

Product-owned ideas such as accounts, browser workflows, AI document review,
mobile UI, persistence, purchasing, and application history belong in consumer
application roadmaps rather than this engine backlog.

## Advanced optimization and planning

- Robust optimization under uncertain/ranged source-water reports.
- Sensitivity analysis and worst-case planning.
- Pareto-front exploration.
- More sophisticated target weighting and policy customization.
- Caller-supplied treatment-cost constraints.
- Caller-supplied treatment availability and quantity constraints.
- Multi-batch treatment planning where a reusable scientific contract emerges.
- Production-scale water allocation constraints where they belong to the
  calculation model rather than an inventory system.

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
- Brewery-scale service/dilution/process-water calculations where appropriate.

## Structured import and validation boundaries

Document parsing, OCR/AI extraction, human review queues, and persistence are
application responsibilities. The engine may later add reusable boundary
helpers when concrete import workflows demonstrate a need, for example:

- validation of normalized candidate measurement structures;
- deterministic mapping helpers for well-defined external laboratory formats;
- explicit ambiguity/error models that are useful across multiple consumers;
- versioned data contracts for accepted source-profile inputs.

These helpers must not make the engine depend on a document parser, AI service,
web framework, or user-review system.

## Interchange and external integrations

- Expanded BeerJSON compatibility as standards evolve.
- Richer FermentationJSON archival/interchange support.
- Stable public API/SDK surfaces for third-party applications.
- Platform-neutral request/result schemas.
- Portable conformance vectors for alternative-language implementations.
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
