# Water Chemistry Engine

A reusable, scientifically grounded Python engine for characterizing, blending,
treating, comparing, and eventually optimizing water for brewing, fermentation,
and other validated uses.

The engine is intentionally independent of web frameworks, databases, graphical
interfaces, and product-specific persistence. End-user applications consume this
package from separate projects.

## Project status

The **0.3 supported-consumer-API milestone is complete**. The engine can
resolve reported source-water chemistry, blend multiple characterized sources,
apply supported mineral additions, calculate the resulting water, compare it
with target/reference criteria, and return auditable contribution, instruction,
and notice data.

Python 3.11 is the project compatibility baseline, with CI coverage through
Python 3.14. Public APIs remain pre-1.0 and may evolve as real consumer
applications exercise the engine.

Version 0.3 establishes a supported package-root consumer facade covering both
the deterministic forward-result graph and the complete source-reporting and
provenance input graph. Its compatibility expectations are documented in
the [consumer API guide](https://github.com/GregRR/water-chemistry-engine/blob/v0.3.0/docs/CONSUMER_API.md).
Reported and target pH use FermUnits' semantic `PHValue`; calculated
working-water pH remains explicitly deferred until a validated reusable model
is ready.

### Forward-calculator capabilities established in 0.2

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

### Planned after 0.3

- **0.4:** curated target/reference profiles and practical treatment materials;
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
uv add water-chemistry-engine==0.3.0
```

or:

```bash
python -m pip install water-chemistry-engine==0.3.0
```

Version 0.3 exposes a supported package-root facade. APIs remain pre-1.0 and may
evolve under the [consumer API compatibility policy](https://github.com/GregRR/water-chemistry-engine/blob/v0.3.0/docs/CONSUMER_API.md).

## Quickstart

This example resolves and blends equal volumes of two reported source waters.
Calcium therefore blends from 40 mg/L and 80 mg/L to 60 mg/L:

```python
from fermunits import Q_

from water_chemistry_engine import (
    ForwardWaterSource,
    Ion,
    IonConcentration,
    SourceResolutionPolicy,
    SourceWaterProfile,
    calculate_forward_water,
)

source_a = SourceWaterProfile(
    name="Source A",
    concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 40.0),),
)
source_b = SourceWaterProfile(
    name="Source B",
    concentrations=(IonConcentration.mg_per_liter(Ion.CALCIUM, 80.0),),
)

result = calculate_forward_water(
    (
        ForwardWaterSource(source_a, Q_(1.0, "liter")),
        ForwardWaterSource(source_b, Q_(1.0, "liter")),
    ),
    source_resolution_policy=SourceResolutionPolicy(allow_exact_range_midpoints=False),
)

calcium = result.final_state.concentration_for(Ion.CALCIUM)
assert calcium is not None
print(calcium)
```

Expected output:

```text
60.0 milligram / liter
```

The explicit source-resolution policy prevents the example from silently
choosing representative values for ranges. See the
[consumer API guide](https://github.com/GregRR/water-chemistry-engine/blob/v0.3.0/docs/CONSUMER_API.md)
for the complete supported workflow, including treatments, targets, notices,
and audit results.

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
- `CONSUMER_API.md` — supported 0.3 package-root facade and integration guide;
- `reviews/` — point-in-time external review records.

Release history is summarized in `CHANGELOG.md`.

## License

This project is licensed under the Mozilla Public License 2.0.
