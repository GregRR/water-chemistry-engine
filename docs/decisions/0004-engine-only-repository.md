# ADR 0004: Engine-Only Repository

## Status

Accepted

## Context

The repository began as a combined workspace for the reusable scientific engine
and a planned standalone web application. By the end of the 0.2 engine work,
the web package was still only a scaffold while the engine had become a useful
independent Python distribution with multiple potential consumers.

Keeping product code in the same public repository would couple independent
release lifecycles and prematurely make product implementation choices part of
the engine project.

## Decision

This repository contains the open-source `water-chemistry-engine` and its
scientific documentation, reference data, schemas, validation tooling, and
conformance material.

End-user products are separate projects. The first known product is a separate web application, and future native
applications are also separate.

The ownership boundary is:

- chemistry, water-domain interpretation, validation, optimization,
  calculation semantics, scientific notices, and structured scientific results
  belong in the engine;
- presentation, persistence, authentication, navigation, workflow state,
  document extraction/review, and product-specific interaction belong in
  consumer applications.

Real application use is expected to reveal missing engine capabilities. Those
capabilities must be added to the engine when they are scientific/domain logic
rather than implemented only in a consumer.

The 0.2 web scaffold is removed before the 0.2.0 release so the repository
structure matches this decision.

With only one installable distribution remaining, the former monorepo-style
`packages/` wrapper and non-installable root workspace are also removed. The
repository root becomes the Python project root and the engine uses
`src/water_chemistry_engine/`.

## Consequences

- Engine and application versions/releases are independent.
- The engine can remain openly auditable while product repositories make their
  own licensing and deployment decisions.
- Consumer applications may begin against pinned pre-1.0 engine versions and
  feed API findings back into engine development.
- Cross-repository integration requires deliberate dependency/version
  management instead of atomic monorepo changes.
- The engine repository uses a conventional single-project `src/` layout.
