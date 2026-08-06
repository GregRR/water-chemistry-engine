# Project Structure

The public water-treatment repository is separate from the private draft-system repository, while both follow the same calculator-family conventions.

```text
water-treatment-calculator/
├── .github/
│   └── workflows/
│       └── ci.yml
├── apps/
│   └── water-treatment-web/
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/water_treatment_web/
│       │   ├── __init__.py
│       │   └── app.py
│       ├── templates/
│       ├── static/
│       └── tests/
├── docs/
│   ├── WATER_CHEM_DESIGN.md
│   ├── WATER_CHEM_REFERENCES.md
│   ├── PROJECT_STRUCTURE.md
│   ├── ROADMAP.md
│   ├── decisions/
│   │   └── 0001-tooling-and-repository-boundary.md
│   └── research/
│       ├── brewing.md
│       ├── mead.md
│       ├── distilling.md
│       └── sensory-water.md
├── packages/
│   └── water-treatment-engine/
│       ├── pyproject.toml
│       ├── README.md
│       ├── src/water_treatment/
│       │   ├── __init__.py
│       │   └── py.typed
│       └── tests/
├── reference-data/
│   └── water/
│       ├── ingredients/
│       ├── profiles/
│       │   ├── beer/
│       │   ├── mead/
│       │   └── distilling/
│       └── README.md
├── schemas/
│   └── water/
│       └── README.md
├── scripts/
│   └── README.md
├── test-vectors/
│   └── water/
│       └── README.md
├── .gitignore
├── .python-version
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock                 # generated after `uv sync`
```

## Dependency direction

```text
FermUnits
    ↓
water-treatment-engine
    ↓
water-treatment-web

Mecha-Brew ───────────────→ water-treatment-engine
FermentationJSON adapters ↔ water-treatment-engine boundary models
```

The engine must not import the web application, Mecha-Brew, a database, or a platform-specific user-interface framework.
