# Project Structure

## Repository layout

    water-chemistry-engine/
    ├── .github/
    │   └── workflows/
    │       └── ci.yml
    ├── src/
    │   └── water_chemistry_engine/
    │       ├── ... scientific/calculation modules
    │       └── py.typed
    ├── tests/
    │   └── ... engine tests
    ├── docs/
    │   ├── decisions/
    │   ├── research/
    │   ├── PROJECT_STRUCTURE.md
    │   ├── ROADMAP.md
    │   ├── WATER_CHEM_DESIGN.md
    │   └── WATER_CHEM_REFERENCES.md
    ├── reference-data/
    │   └── water/
    ├── schemas/
    │   └── water/
    ├── scripts/
    ├── test-vectors/
    │   └── water/
    ├── .gitignore
    ├── .python-version
    ├── CHANGELOG.md
    ├── LICENSE
    ├── pyproject.toml
    ├── README.md
    └── uv.lock

## Single-package repository

The repository contains one installable Python distribution:

- distribution: `water-chemistry-engine`
- import package: `water_chemistry_engine`

Because the web application and future end-user products now live in separate
repositories, a monorepo-style `packages/` wrapper and non-installable root
workspace no longer provide useful separation. The repository root is the
Python project root, and the engine uses the standard `src/` layout.

This keeps packaging metadata, development tooling, documentation, tests, and
the installable distribution under one project boundary while retaining the
important protection of a `src/` layout: repository-root imports do not
accidentally bypass the installed package.

## `src/water_chemistry_engine/`

This is the importable engine package.

In 0.2 it owns the implemented reusable scientific and engineering behavior,
including:

- water-profile domain models;
- source-water resolution;
- fixed water blending;
- mineral stoichiometry and forward treatment application;
- target/reference comparison;
- contribution reporting;
- preparation instructions;
- structured notices and validation;
- calculation audit/provenance data.

Development for 0.3 adds an explicit supported facade at the package root.
Ordinary consumers should prefer the names in
`water_chemistry_engine.__all__`; `docs/CONSUMER_API.md` defines that boundary,
integration expectations, and the pre-1.0 compatibility policy. The facade
re-exports the proven domain and orchestration objects rather than introducing
a second chemistry implementation.

As later milestones add optimization, treatment-plan ranking, richer
constraints, calculated working-water pH, and serialization/interchange
adapters, those responsibilities also belong in the engine.

The engine must remain independent of:

- web frameworks;
- databases;
- HTML/template systems;
- operating-system interfaces;
- application-specific storage or authentication;
- product-specific UI state;
- Mechani-Brew internals.

## `tests/`

Repository-level engine tests live here and import the installed
`water_chemistry_engine` package from `src/` through the project environment.

Tests include unit, regression, integration, property-based, and real-report
fixture coverage. Portable cross-implementation conformance fixtures belong in
`test-vectors/` rather than being hidden only inside Python tests.

## Consumer applications

End-user products live in separate projects and depend on the engine. They may
include a web application, Mechani-Brew, automation services, scripts, or
future native clients.

Applications own presentation, persistence, accounts, navigation, workflow
state, document-upload/review workflows, and product-specific interaction.

No chemistry equation, source-report interpretation, optimization rule,
scientific validation rule, or treatment model should exist only in a consumer
application. When real application use exposes a missing scientific/domain
capability, that capability should be implemented in the engine.

## FermUnits

FermUnits is an external required dependency of the engine.

FermUnits is responsible for:

- quantities;
- dimensional validation;
- unit conversion;
- explicit brewing and fermentation units;
- once its M4 pH API is released and adopted here, a semantic `PHValue` and
  the exact definitional transform between pH and dimensionless hydrogen-ion
  activity.

FermUnits does not define chemical pH as a Pint unit. In particular,
`Q_(7.0, "pH")` must not be used for chemical pH because Pint can interpret
`pH` as picohenry. The M4 pH API is planned rather than part of the currently
consumed FermUnits 0.1.x contract.

The Water Chemistry Engine is responsible for the chemical meaning of
quantities and for pH behavior that requires a chemistry model or application
policy. This includes activity coefficients, concentration/activity modeling,
equilibria, buffering, treatment and blending effects, prediction, targets,
and reported/measurement provenance. FermUnits' pH/activity transform does not
equate hydrogen-ion activity with concentration.

Reporting bases and chemical semantics such as alkalinity “as CaCO3,” hardness,
hydration state, and mass-versus-volume concentration remain explicit domain
data rather than being hidden in ordinary unit conversion.

## FermentationJSON

FermentationJSON provides portable interchange structures for water profiles,
water blends, treatment plans, and related fermentation data.

The engine should use adapters rather than making its internal domain models
identical to the JSON schema.

External applications may convert among:

1. application/database records;
2. engine-domain objects;
3. FermentationJSON documents.

## Supporting directories

### `docs/decisions/`

Architecture Decision Records documenting important engine/repository decisions
and their reasoning.

### `docs/research/`

Working scientific notes, formula investigations, validation records, and
unresolved research questions.

### `reference-data/water/`

Curated water profiles, ingredient definitions, and related reference data
approved for inclusion in the engine project.

Every included dataset must retain provenance, licensing information, and
appropriate scientific references.

### `schemas/water/`

Machine-readable schemas for project-specific water data and adapters under
development.

Normative FermentationJSON schemas remain in the FermentationJSON project.

### `test-vectors/water/`

Portable inputs and expected outputs used to validate:

- the Python reference engine;
- future alternative-language implementations;
- downstream integrations;
- regression behavior across releases.

### `scripts/`

Research, validation, data-import, schema-generation, and maintenance
utilities.

One-off scripts must not become hidden sources of production chemistry logic.

## Dependency direction

    FermUnits
        ↓
    water-chemistry-engine
        ↓
    external consumer applications

The engine never depends on a consumer application.

## Packaging names

The Python distribution is `water-chemistry-engine` and the importable package
is `water_chemistry_engine`. The package source lives at
`src/water_chemistry_engine/`, following standard Python `src/` layout
practice.
