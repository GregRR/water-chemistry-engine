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

Development toward 0.3 is establishing a supported package-root consumer API.
That unreleased surface and its compatibility expectations are documented in
[`docs/CONSUMER_API.md`](docs/CONSUMER_API.md); published 0.2.0 consumers should
continue using tested module-level imports until 0.3.0 is released.

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

## Installation

Water Chemistry Engine requires Python 3.11 or newer. Install the published
package with uv or pip:

```bash
uv add water-chemistry-engine
```

or:

```bash
python -m pip install water-chemistry-engine
```

Version 0.2 exposes useful module-level APIs for calculations and domain models.
These APIs remain pre-1.0 and may evolve as the supported consumer-facing API is
formalized in milestone 0.3.

## Quickstart

This example blends equal volumes of two already-resolved water states. Calcium
therefore blends from 40 mg/L and 80 mg/L to 60 mg/L:

```python
from fermunits import Q_

from water_chemistry_engine.blending import BlendSource, blend_waters
from water_chemistry_engine.chemical_state import (
    AqueousChemicalState,
    DerivedIonConcentration,
)
from water_chemistry_engine.ions import Ion

source_a = AqueousChemicalState(
    concentrations=(DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),)
)
source_b = AqueousChemicalState(
    concentrations=(DerivedIonConcentration.mg_per_liter(Ion.CALCIUM, 80.0),)
)

blend = blend_waters(
    (
        BlendSource("Source A", source_a, Q_(1.0, "liter")),
        BlendSource("Source B", source_b, Q_(1.0, "liter")),
    )
)

calcium = blend.state.concentration_for(Ion.CALCIUM)
assert calcium is not None
print(calcium)
```

Expected output:

```text
60.0 milligram / liter
```

Reported source-water values should normally be passed through the engine's
explicit source-resolution workflow before blending. The example starts from
resolved states to keep the first installed-package example focused.

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
- `CONSUMER_API.md` — unreleased 0.3 package-root facade and integration guide;
- `reviews/` — point-in-time external review records.

Release history is summarized in `CHANGELOG.md`.

## License

This project is licensed under the Mozilla Public License 2.0.
