# Water Chemistry Engine Future Capabilities

This document preserves useful engine ideas intentionally outside the active
near-term release path in `docs/ROADMAP.md` and records related domain
capabilities that are deliberately owned by consumers. Inclusion here is not a
promise for a particular release.

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

## Advanced generic aqueous chemistry and reactive treatment

Potential reusable chemistry primitives include:

- carbonate speciation from a sufficiently complete chemical state;
- state-based aqueous equilibrium calculations;
- acid/base dose to a target **water** pH;
- a general buffer-system/equilibrium solver if a defensible domain-neutral
  contract can be established;
- charge-balance and report-consistency diagnostics;
- comparison of reported hardness with hardness reconstructed from known ions;
- deeper carbonate/bicarbonate and CO2 equilibrium behavior;
- equilibrium, precipitation, saturation, solubility, and dissolution behavior
  where validated and practically useful, including carbonate/chalk systems;
- ordered process-state and order-of-addition chemistry; and
- reaction kinetics where time materially changes a validated result.

These capabilities must remain expressed in terms of water/solution chemistry.
They should not require malt, grain bills, beer styles, coffee extraction,
dough behavior, or other domain-specific inputs.

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

## Consumer-owned reference and historical datasets

The following are useful Water Chemistry Designer or other consumer-library
content, not Engine-bundled data or Engine persistence work:

- Additional current municipal source-water datasets.
- Historical regional/city water analyses kept as separate sourced records.
- Published brewery or practitioner point-of-use profiles.
- Measured bakery/pizzeria point-of-use profiles.
- Historical/reference coffee and tea waters.
- Experimental water datasets from peer-reviewed food/beverage studies.
- Versioned profile history rather than silent replacement or averaging.

Consumers should preserve these records in their databases and map selected
records to Engine domain objects. The Engine may retain narrowly scoped sourced
fixtures or conformance vectors when they are needed to verify profile
semantics or calculations; such fixtures are not a product-facing library.

## Domain-specific consumer science enabled by the engine

The following are useful product/domain capabilities, but they are not Engine
backlog items. They belong in Water Chemistry Designer or another domain
consumer and may compose generic Engine calculations:

- recipe-aware mash-pH prediction;
- malt/grain buffering and titration models;
- Kolbach residual-alkalinity interpretation and Z-alkalinity mash models;
- mash-versus-sparge recommendations and beer-style guidance;
- coffee extraction and sensory models;
- coffee equipment scaling/corrosion policy where it is purpose-specific;
- tea infusion/extraction models;
- bread and pizza dough behavior;
- sourdough starter establishment and maintenance;
- fermentation/yeast interpretation of chlorine/chloramine and mineral
  composition;
- alkaline noodles and kansui;
- cheesemaking;
- lacto-fermented vegetables;
- other fermented foods and beverages; and
- sensory-water research that cannot be represented as generic water chemistry
  or a simple target/reference profile.

If several domains need the same lower-level chemistry, extract that common
piece into the Engine rather than duplicating it in each consumer.

## Selected industrial consumers

Potential long-term consumers include laboratory preparation water, cleaning
and rinsing water, boiler/steam feedwater, cooling water, and selected
manufacturing/process-water applications.

The Engine may add generic chemistry or treatment primitives these consumers
need when they are reusable. Industrial safety, regulatory,
materials-compatibility, operating-policy, and process-specific guidance remain
outside the Engine and require dedicated domain validation.

## Research/data principles that remain in force

- Preserve provenance and the evidentiary class of every profile.
- Do not manufacture canonical profiles by averaging conflicting sources.
- Do not relabel regional/reference water as an experimentally optimized target.
- Keep reported, derived, predicted, and measured data distinct.
- Keep source-water identity separate from intended use.
- Keep reusable water chemistry in the Engine and domain-specific interpretation
  in consumers or separate domain libraries.
- Preserve unknowns, censoring, and reporting bases.
- Keep pH logarithmic and model-derived pH explicitly versioned.
