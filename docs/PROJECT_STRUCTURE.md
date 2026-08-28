# Project Structure

## Repository layout

    water-treatment-calculator/
    ├── .github/
    │   └── workflows/
    │       └── ci.yml
    ├── apps/
    │   └── water-treatment-web/
    │       ├── pyproject.toml
    │       ├── README.md
    │       ├── src/
    │       │   └── water_treatment_web/
    │       │       ├── __init__.py
    │       │       ├── app.py
    │       │       ├── py.typed
    │       │       ├── static/
    │       │       └── templates/
    │       └── tests/
    │           └── test_web_package.py
    ├── packages/
    │   └── water-treatment-engine/
    │       ├── pyproject.toml
    │       ├── README.md
    │       ├── src/
    │       │   └── water_treatment_engine/
    │       │       ├── ... scientific/calculation modules
    │       │       └── py.typed
    │       └── tests/
    │           └── ... engine tests
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
    └── README.md

## Workspace organization

The repository is a uv workspace containing two separately installable
Python distributions:

- `water-treatment-engine`
- `water-treatment-web`

The repository root coordinates development dependencies, testing, linting,
formatting, type checking, and continuous integration. It is not itself an
installable application package.

## `water-treatment-engine`

Location:

    packages/water-treatment-engine/

Import package:

    water_treatment_engine

In 0.2 this package owns the implemented reusable scientific and engineering
behavior, including:

- water-profile domain models
- source-water resolution
- fixed water blending
- mineral stoichiometry and forward treatment application
- target/reference comparison
- contribution reporting
- preparation instructions
- structured notices and validation
- calculation audit/provenance data

As later milestones add optimization, treatment-plan ranking, richer
constraints, and serialization/interchange adapters, those responsibilities
also belong in the engine rather than in application code.

The engine must remain independent of:

- Django
- databases
- HTML
- HTMX
- web frameworks
- operating-system interfaces
- application-specific storage
- Mechani-Brew internals

The same engine should be usable by Mechani-Brew, the standalone web
application, scripts, APIs, tests, and third-party applications.

## `water-treatment-web`

Location:

    apps/water-treatment-web/

Import package:

    water_treatment_web

In 0.2 this package is a scaffold. Beginning with milestone 0.3 it will provide
the standalone graphical web application.

The web layer owns or will own:

- web routes
- forms
- HTML templates
- static assets
- localized presentation
- application navigation
- validation display
- result tables and charts
- standalone application state

It depends on `water-treatment-engine` for all scientific calculations.

No chemistry equation, optimization rule, or treatment model should be
implemented only in the web application.

## Mechani-Brew integration

Mechani-Brew will depend directly on `water-treatment-engine`.

Mechani-Brew will provide its own:

- Django models
- database records
- user accounts
- saved profiles
- recipes and batches
- inventory integration
- forms
- templates
- navigation
- styling

This allows the calculator to appear as a seamless native Mechani-Brew feature
without coupling the engine to Mechani-Brew’s interface or database.

## FermUnits

FermUnits is an external required dependency of the engineering package.

FermUnits is responsible for:

- quantities
- dimensional validation
- unit conversion
- explicit brewing and fermentation units

The water-treatment engine is responsible for the chemical meaning of those
quantities.

Reporting bases and chemical semantics such as alkalinity “as CaCO3,”
hardness, hydration state, and mass-versus-volume concentration must remain
explicit domain data rather than being hidden in ordinary unit conversion.

## FermentationJSON

FermentationJSON provides portable interchange structures for water profiles,
water blends, treatment plans, and related fermentation data.

The engine should use adapters rather than making its internal domain models
identical to the JSON schema.

Applications may convert among:

1. application or database records;
2. engine-domain objects;
3. FermentationJSON documents.

## Supporting directories

### `docs/decisions/`

Architecture Decision Records documenting important technical decisions and
their reasoning.

### `docs/research/`

Working scientific notes, formula investigations, validation records, and
unresolved research questions.

### `reference-data/water/`

Curated water profiles, ingredient definitions, and related reference data
approved for inclusion in the project.

Every included dataset must retain provenance, licensing information, and
appropriate scientific references.

### `schemas/water/`

Machine-readable schemas for project-specific water data and adapters under
development.

Normative FermentationJSON schemas should remain in the FermentationJSON
project.

### `test-vectors/water/`

Portable inputs and expected outputs used to validate:

- the Python engine;
- future alternative-language implementations;
- Mechani-Brew integration;
- mobile implementations;
- regression behavior across releases.

### `scripts/`

Research, validation, data-import, schema-generation, and maintenance
utilities.

One-off scripts should not become hidden sources of production chemistry
logic.

## Dependency direction

    FermUnits
        ↓
    water-treatment-engine
        ↓
    water-treatment-web

    Other applications ──> water-treatment-engine

The engine must never depend on the standalone web application or Mechani-Brew.

## Packaging names

Hyphenated names identify Python distributions and repository directories:

- `water-treatment-engine`
- `water-treatment-web`

Underscored names identify importable Python packages:

- `water_treatment_engine`
- `water_treatment_web`

This is standard Python packaging practice and is intentional.