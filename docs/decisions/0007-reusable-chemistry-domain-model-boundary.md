# ADR 0007: Reusable Chemistry and Domain-Model Boundary

## Status

Accepted

## Context

ADR 0004 separated the reusable engine repository from end-user products and
assigned scientific/domain logic broadly to the Engine. Subsequent work on
brewing, coffee, tea, and dough requirements showed that this wording was too
broad. A scientific model can still be purpose-specific: mash-pH prediction
requires malt/grain and recipe inputs, coffee extraction depends on coffee-
specific variables, and dough behavior depends on a food-process model.

Putting every scientific model in the Engine would make the shared water core
depend on individual product domains and would blur the boundary between water
chemistry and purpose-specific interpretation.

## Decision

Water Chemistry Engine owns reusable, purpose-neutral capabilities, including:

- water/source measurement and reporting semantics;
- general aqueous chemistry and validated state calculations;
- blending and treatment mechanics;
- treatment-material and dose semantics;
- generic target/reference comparison, validation, and optimization; and
- model limitations, provenance, notices, and auditable scientific results.

Consumer applications or separate domain libraries own purpose-specific
interpretation, prediction, and recommendation, including recipe-aware mash-pH,
malt/grain buffering, brewing residual-alkalinity interpretation, beer-style
guidance, coffee extraction, tea infusion, and dough behavior.

A domain model may compose lower-level Engine results. When multiple domains
need the same defensible lower-level chemistry, that reusable primitive should
be extracted into the Engine rather than duplicated. The Engine must not import
or depend on a consumer or domain library.

Source-water identity remains independent of intended use. Well-sourced target
or reference data may be represented by the generic Engine without turning the
associated purpose-specific interpretation into Engine behavior.

## Consequences

- Scientific rigor remains required in both the Engine and domain libraries;
  repository ownership is determined by reusability, not by whether work is
  scientific.
- Generic working-water pH, charge balance, carbonate speciation, and aqueous
  equilibrium may belong in the Engine when their contracts are validated.
- Mash-pH, grain buffering, sensory prediction, and similar domain models do not
  become Engine features merely because they use water-chemistry inputs.
- Consumer integration may reveal missing Engine primitives, but it does not
  automatically move the complete consumer model into this repository.
- ADR 0004 continues to govern repository separation; this ADR refines its
  earlier ownership-boundary wording.
