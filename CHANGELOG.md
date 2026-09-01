# Changelog

This project follows semantic versioning for the Water Chemistry Engine
distribution and its repository milestones.

## Unreleased

### Added

- Established the first supported package-root consumer facade for the proven
  deterministic forward workflow, including explicit input models, result and
  status types, structured notice codes, supported treatment ingredients, and
  an exact `__all__` contract.
- Added API-level integration tests and consumer documentation covering a
  complete source/blend/treatment/target calculation, validation failures,
  unknown propagation, notice handling, and pre-1.0 compatibility policy.
- Exposed the forward result's source-resolution, blend, treatment,
  contribution-matrix, and preparation-instruction audit types through the
  supported facade so consumers can interpret the complete result graph
  without importing its defining modules.
- Exposed the complete `SourceWaterProfile` reporting and provenance
  construction graph, including reported properties, disinfectants, result
  context/statistics, water identity, physical sources, and source documents.

### Changed

- Raised the minimum FermUnits version to 0.1.3 and imported quantity typing
  through its public API, keeping FermUnits as the sole unit dependency boundary
  while retaining real Pint quantities in the supported result contract.
- Migrated reported and target pH storage to FermUnits `PHValue`, preserving the
  range-only no-midpoint rule while removing the unsupported assumption that
  every valid pH must fall between 0 and 14.

### Documentation

- Documented the FermUnits 0.1.3 boundary for semantic pH values and the exact
  pH/hydrogen-ion-activity transform while retaining activity models,
  concentration conversion, calculated pH, and reporting policy in the engine.
- Documented why chemical pH must not be represented as a Pint `pH` unit and
  why the former 0-through-14 validation was reviewed rather than treated as a
  universal pH invariant.
- Added IUPAC pH definition and measurement sources supporting the semantic
  activity-based pH boundary.

## 0.2.0 - 2026-08-29

### Added

- Explicit policy-controlled resolution of reported source-water chemistry.
- Fixed blending of one or more characterized water sources with preserved
  source fractions, volumes, and per-ion contributions.
- Deterministic application of supported mineral additions with structured
  per-ion treatment audit data.
- Target/reference comparison for exact values, exact-ended ranges, and
  one-sided numeric bounds.
- End-to-end forward-calculation orchestration from reported source profiles to
  final treated-water results.
- Combined source/treatment contribution matrices.
- Structured human-readable blending and treatment instructions.
- Machine-readable notices for calculation assumptions, unresolved inputs,
  target limitations, and deferred working-water pH.
- Property-based coverage for blend/contribution and target-comparison
  invariants.

### Changed

- Renamed the reusable project, distribution, repository, and import package
  to Water Chemistry Engine / `water-chemistry-engine` /
  `water_chemistry_engine` before the 0.2.0 release to reflect the broader
  chemistry characterization, comparison, and treatment scope.
- Made the repository explicitly engine-only and removed the unused standalone
  web-application scaffold so product implementations can evolve in separate
  projects against the reusable engine.
- Flattened the former monorepo package wrapper into a conventional
  single-project `src/` layout now that the engine is the repository's only
  distribution.
- Reframed the post-0.2 roadmap around a supported consumer API, curated
  reference data, optimization, pH, interchange, and conformance rather than a
  bundled user interface.

### Hardened

- Expanded the supported runtime floor to Python 3.11, with CI coverage on
  Python 3.11, 3.12, 3.13, and 3.14 and Python 3.11 as the compatibility
  baseline.
- Updated the engine dependency floor to FermUnits 0.1.2, the first published
  release in the 0.1 line with Python 3.11 support.
- Preserved unknown source chemistry as unknown instead of silently treating it
  as zero.
- Added numerical-noise tolerance at target boundaries so floating-point
  representation artifacts cannot flip target status.
- Normalized treatment contribution units and centralized workflow-linkage
  validation.
- Rejected negative and non-finite chemistry, target, treatment, and supporting
  numeric inputs before they can enter deterministic calculations.
- Pinned the release build backend for materially reproducible wheel rebuilds
  from the source distribution.
- Added external-review regression coverage for the completed 0.2 engine
  boundary.

### Known limitations

- Automatic treatment optimization and ranked strategies are not implemented.
- Calculated working-water pH is intentionally deferred pending a validated
  reusable aqueous model.
- Bicarbonate/carbonate blending remains a documented first-order additive
  approximation rather than an equilibrium/speciation calculation.
- Mineral treatment currently assumes complete dissolution and does not model
  solubility limits or precipitation.
- The 0.2 package exposes useful module-level APIs, but the supported top-level
  consumer facade is intentionally deferred to milestone 0.3.
