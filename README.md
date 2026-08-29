# Water Chemistry Engine

A reusable, scientifically grounded Python engine for characterizing, blending,
treating, comparing, and eventually optimizing water for brewing, fermentation,
and other validated uses.

The engine is intentionally independent of web frameworks, databases, graphical
interfaces, and product-specific persistence. End-user applications consume this
package from separate projects.

## Project status

The **0.2 deterministic forward-calculator milestone is complete**. The engine
can resolve reported source-water chemistry, blend multiple characterized
sources, apply supported mineral additions, calculate the resulting water,
compare it with target/reference criteria, and return auditable contribution,
instruction, and notice data.

Version 0.2 also establishes Python 3.11 as the compatibility baseline, with CI
coverage on Python 3.11 through 3.14. Public APIs remain pre-1.0 and may evolve
as real consumer applications exercise the engine.

### Implemented in 0.2

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

- **0.3:** supported consumer-facing Python API and integration examples;
- **0.4:** curated target/reference profiles;
- **0.5–0.6:** automatic and ranked treatment optimization;
- **0.7:** reusable working-water pH if a defensible model is ready;
- **0.8:** BeerJSON/FermentationJSON interchange, conformance work, and 1.0
  hardening.

AI-assisted document ingestion, accounts, persistence, browser UI, and native
application code belong to separate consumer applications rather than this
repository.

## Repository structure

    water-chemistry-engine/
    ├── src/
    │   └── water_chemistry_engine/
    ├── tests/
    ├── docs/
    ├── reference-data/
    ├── schemas/
    ├── scripts/
    └── test-vectors/

### `src/water_chemistry_engine`

The importable Python engine package, using the standard `src/` layout. It owns
scientific calculations, domain models, validation, warnings/notices,
optimization as it is added, and structured calculation results.

External applications such as web, automation, Mechani-Brew, and future native
clients can consume the engine while providing their own interfaces and
persistence.

## Development stack

- Python 3.11+ (CI tests 3.11–3.14; 3.11 is the compatibility baseline)
- uv
- FermUnits
- pytest and Hypothesis
- Ruff
- mypy
- GitHub Actions

## Development

Install uv, then run from the repository root. The checked-in
`.python-version` selects the Python 3.11 compatibility baseline:

```bash
uv sync --dev
uv run pytest
```

The full CI gate tests Python 3.11, 3.12, 3.13, and 3.14. It also checks the
lockfile, formatting, linting, strict typing against Python 3.11 semantics, and
builds the engine distribution.

## Documentation

Primary project documents are stored under `docs/`:

- `WATER_CHEM_DESIGN.md` — scientific and architectural design;
- `WATER_CHEM_REFERENCES.md` — source and reference register;
- `ROADMAP.md` — active engine release path;
- `PROJECT_STRUCTURE.md` — repository/package boundaries;
- `reviews/` — point-in-time external review records.

Release history is summarized in `CHANGELOG.md`.

## License

This project is licensed under the Mozilla Public License 2.0.
