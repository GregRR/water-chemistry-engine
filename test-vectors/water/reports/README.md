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

A single numeric result may carry `reported_statistic` metadata when the source
identifies the number as an average, percentile, running annual average, or other
reported statistic. This prevents an aggregate number from being mistaken for a
single exact observation.

When a source reports a calculator-relevant value that the engine cannot yet
represent without changing its meaning, a fixture may retain it under
`unmodeled_source_results`. This is preferable to coercing it into a nearby but
semantically different engine field.

A range endpoint may be a plain number for an exact endpoint or an object when
that endpoint is qualified. For example, `{"form": "not_detected"}` preserves
`ND` without turning it into zero, while upper/lower-bound endpoint objects
preserve `<X` and `>X` without treating the limit itself as the measurement.

A result may also supply its own `result_context`. Result-level timing overrides
profile-level timing for that result while omitted sampling-context fields may
inherit from the profile. In particular, an explicit single `observed_on` date
must not be combined with an inherited observation period.
