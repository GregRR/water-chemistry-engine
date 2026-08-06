# Water Treatment Engine

Reusable Python engineering engine for water-profile analysis, blending, and treatment optimization.

The package is intended for:

- brewing;
- mead making;
- distilling;
- standalone calculators;
- Mecha-Brew;
- mobile and web applications;
- third-party Python software.

## Scope

The engine will provide:

- source-water and target-water models;
- dated water profiles and provenance;
- blending of multiple water sources;
- mineral contribution calculations;
- target-profile comparison;
- treatment-plan optimization;
- ranked solutions;
- machine-readable warnings;
- human-readable explanations.

## Architecture

This package contains only scientific and engineering logic.

It must not depend on:

- web frameworks;
- databases;
- HTML templates;
- application-specific storage;
- user-interface code;
- Mecha-Brew internals.

Applications should pass structured inputs to the engine and render the resulting structured outputs using their own interfaces.

## Units

All dimensional inputs and outputs will use FermUnits.

Saved and exchanged data should use explicit, unambiguous unit identifiers. Applications may localize displayed units without changing the stored meaning.

## Status

Early repository setup. Public APIs and calculation models are not yet stable.

## License

Mozilla Public License 2.0.