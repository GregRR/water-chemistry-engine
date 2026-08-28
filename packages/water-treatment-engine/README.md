# Water Treatment Engine

Reusable Python engineering engine for water-profile analysis, deterministic
blending, mineral treatment, and target/reference comparison.

## Current status

Version 0.2 provides the deterministic forward-calculation boundary used by the
next web-application milestone. Public APIs are still pre-1.0 and may change as
the application, optimization, and interchange layers are added.

Implemented capabilities include:

- source-water and target/reference models;
- source-report semantics for exact values, ranges, bounds, `ND`, statistics,
  provenance/context, and disinfectants;
- explicit policy-controlled source resolution;
- fixed multi-source blending;
- supported mineral-addition stoichiometry and treatment application;
- exact derived aqueous ion states with conservative unknown propagation;
- source/blend/final target comparison;
- source/treatment contribution matrices;
- structured preparation instructions;
- structured forward-result notices and audit detail.

Not implemented in 0.2:

- automatic treatment optimization or ranked plans;
- BeerJSON/FermentationJSON adapters;
- recipe-aware mash-pH prediction;
- generalized aqueous-equilibrium, solubility, or precipitation modeling;
- calculated working-water pH.

## Intended consumers

The package is intended for:

- the standalone Water Treatment Calculator web application;
- brewing, mead-making, and distilling workflows;
- Mechani-Brew;
- future mobile/desktop applications;
- scripts, APIs, tests, and third-party Python software.

## Architecture

This package contains only scientific and engineering logic. It must not depend
on:

- web frameworks;
- databases;
- HTML templates;
- application-specific storage;
- user-interface code;
- Mechani-Brew internals.

Applications pass structured inputs to the engine and render the structured
outputs using their own interfaces.

## Units

All dimensional inputs and outputs use FermUnits/Pint quantities.

Saved and exchanged data should use explicit, unambiguous unit identifiers.
Applications may localize displayed units without changing stored meaning.

## License

Mozilla Public License 2.0.
