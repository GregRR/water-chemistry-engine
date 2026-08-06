# Water Treatment Calculator

A reusable water-treatment engineering system for brewing, mead making, and distilling.

The project will provide:

- water-profile storage and comparison;
- blending of multiple water sources;
- mineral-addition calculations;
- automatic treatment-plan optimization;
- ranked solutions with explanations;
- FermentationJSON import and export;
- a standalone web interface;
- reusable calculation engines for Mecha-Brew and other applications.

## Project status

Early design and repository setup.

The first release will focus on:

- dated source-water profiles;
- target-water profiles;
- beer, mead, and distilling profiles;
- water blending;
- common brewing mineral additions;
- ranked treatment plans;
- unit-safe calculations through FermUnits;
- a responsive server-rendered web interface.

Acid treatment, mash-pH prediction, advanced carbonate chemistry, and broader food-science applications are planned for later releases.

## Repository structure

    water-treatment-calculator/
    ├── apps/
    │   └── water-treatment-web/
    ├── packages/
    │   └── water-treatment-engine/
    ├── docs/
    ├── reference-data/
    ├── schemas/
    ├── scripts/
    └── test-vectors/

### `water-treatment-engine`

The reusable Python engineering package.

It will contain:

- domain models;
- water blending;
- mineral contribution calculations;
- profile comparison;
- optimization;
- validation;
- warnings and explanations.

It must remain independent of databases, web frameworks, and user interfaces.

### `water-treatment-web`

The standalone web application.

It will provide the graphical interface while using the engine package for all scientific calculations.

Mecha-Brew will integrate the engine directly and provide its own interface.

## Dependencies

The project will use:

- Python 3.14
- uv
- FermUnits
- pytest
- Hypothesis
- Ruff
- mypy

The standalone web application is planned to use server-rendered HTML with HTMX.

## Documentation

Primary project documents are stored under `docs/`:

- `WATER_CHEM_DESIGN.md`
- `WATER_CHEM_REFERENCES.md`
- `ROADMAP.md`
- `PROJECT_STRUCTURE.md`

## License

This project is licensed under the Mozilla Public License 2.0.