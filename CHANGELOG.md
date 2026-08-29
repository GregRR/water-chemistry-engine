# Changelog

This project follows semantic versioning for repository milestones and versions
individual distributable packages independently where appropriate.

## 0.2.0 - 2026-08-28

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
- The standalone web application remains a scaffold until milestone 0.3.
