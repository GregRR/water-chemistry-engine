# Real water-report test vectors

This directory contains data-only fixtures derived from real water-quality reports.

These files are **test vectors**, not a public interchange format and not a
FermentationJSON schema. Their purpose is to pressure-test the water-treatment
engine against the reporting patterns found in real source documents while
FermentationJSON continues to define the long-term interchange representation.

## Layout

Each source/report gets a data file beneath a provider-specific directory, for
example:

```text
reports/
  santa-cruz/
    2025.json
  niagara/
    2024.json
```

The Python test suite loads these files generically. Adding another report should
normally require only another data file unless that report exposes a reporting
semantic the engine or fixture loader cannot yet represent.

## Fixture format

The current internal fixture format is identified by:

```json
"fixture_format": "water-treatment-real-report-v1"
```

The format deliberately mirrors concepts already present in the engine:
source-document metadata, water identity, profile-level observation timing,
result context, reported ion concentrations, pH, and other reported water
properties.

Do not treat this internal test-vector format as a compatibility promise.
