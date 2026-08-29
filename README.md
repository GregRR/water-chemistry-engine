# Water Treatment Calculator

A reusable water-treatment engineering system for brewing, mead making, and
distilling, with a standalone web application built on the same engine.

## Project status

The **0.2 deterministic forward-calculator milestone is complete**. The engine
can now resolve reported source-water chemistry, blend multiple characterized
sources, apply supported mineral additions, calculate the resulting water,
compare it with target/reference criteria, and return auditable contribution,
instruction, and notice data.

The next milestone, **0.3**, is the first usable Django/HTMX web application.
The web package is still a scaffold; no user-facing calculator has been
implemented yet.

### Implemented in the 0.2 engine

- source-water and target/reference profile models;
- preservation of exact values, ranges, bounds, `ND`, reported statistics,
  reporting context, source-document metadata, and chlorine/chloramine data;
- explicit source-resolution policy, including opt-in exact-range midpoints;
- fixed multi-source blending with conservative unknown propagation;
- supported mineral-addition stoichiometry and deterministic treatment;
- source, blend, and final target/reference comparison;
- combined source/treatment ion-contribution reporting;
- structured preparation instructions;
- structured notices for assumptions, unresolved inputs, model limitations,
  and deferred target-pH calculation.

### Planned after 0.2

- **0.3:** usable Django/HTMX web calculator;
- **0.4:** curated target/reference profiles;
- **0.5–0.6:** automatic and ranked treatment optimization;
- **0.7:** reusable working-water pH if a defensible model is ready;
- **0.8:** BeerJSON/FermentationJSON interchange and 1.0 hardening.

AI-assisted report ingestion and deeper domain-specific food/beverage models
are intentionally outside the immediate release path.

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

The reusable Python engineering package. It owns scientific calculations,
domain models, validation, warnings/notices, and structured calculation
results. It must remain independent of databases, web frameworks, and user
interfaces.

### `water-treatment-web`

The standalone web application. Beginning with 0.3, it will provide a
server-rendered Django/HTMX interface while using the engine for all scientific
calculations.

Mechani-Brew and other applications can consume the engine directly and provide
their own interfaces.

## Development stack

- Python 3.11+ (CI currently tests 3.11–3.14; 3.11 is the compatibility baseline)
- uv
- FermUnits
- pytest and Hypothesis
- Ruff
- mypy
- GitHub Actions

## Development

Version 0.2 does not yet provide a user-facing web calculator. To work with or
validate the source checkout, install uv, then run from the repository root.
The checked-in `.python-version` selects the Python 3.11 compatibility baseline:

```bash
uv sync --all-packages --dev
uv run pytest
```

The full CI gate tests Python 3.11, 3.12, 3.13, and 3.14. It also checks the
lockfile, formatting, linting, strict typing against Python 3.11 semantics, and
builds both Python distributions.

## Documentation

Primary project documents are stored under `docs/`:

- `WATER_CHEM_DESIGN.md` — scientific and architectural design;
- `WATER_CHEM_REFERENCES.md` — source and reference register;
- `ROADMAP.md` — active release path;
- `PROJECT_STRUCTURE.md` — repository/package boundaries;
- `reviews/` — point-in-time external review records.

Release history is summarized in `CHANGELOG.md`.

## License

This project is licensed under the Mozilla Public License 2.0.
