# Changelog

This project follows semantic versioning for the Water Chemistry Engine
distribution and its repository milestones.

## 0.5.0 - Unreleased

Development of the total-alkalinity, treatment-material, profile, and
comparison-expansion milestone is in progress.

### Compatibility warning

- Refined the CaCO3 equivalent-mass constant from 50.04 to 50.04345 g/eq and
  made it the single calculation constant used by both the new alkalinity model
  and `bicarbonate_from_bicarbonate_alkalinity_as_caco3`. For an input of
  100 mg/L, that existing conversion now returns approximately 121.92864 rather
  than 121.93705 mg/L HCO3. Consumers comparing exact derived values should
  expect this small precision change.

### Added

- Added optional target-profile provenance with explicit evidentiary
  classification, source-document attribution, and paired stable key/version;
  unclassified profiles remain unclassified, while classifications that make
  published or scientific claims require document attribution.
- Added versioned, described per-ion closeness policies using asymmetric
  absolute mg/L deviations from accepted target boundaries. Comparisons now
  report within-target, close, far, or not-evaluated interpretation separately
  from below/within/above status without inventing universal percentages.
- Added the first end-to-end conservative-equivalent total-alkalinity workflow:
  policy-controlled source resolution, unknown-preserving blend calculation,
  reviewed sodium-bicarbonate treatment contributions, modeled final
  alkalinity, target comparison, and a structured contribution-matrix row.
- Added one-sided lower/upper total-alkalinity values. They remain unresolved
  when used as source reports and act as supported numeric bounds when used as
  target criteria.
- Added total-alkalinity optimization across fixed blends, proportional
  dilution, and bounded source-volume selection. The optimizer admits reviewed
  sodium bicarbonate only when starting alkalinity is resolved and an
  alkalinity criterion is present, includes its sodium effect normally, and
  replays selected practical doses through the forward calculation.
- Added pure anhydrous calcium chloride (`CaCl2`) as a distinct supported
  chemical identity with its own formula mass and per-gram ion yield; it is not
  treated as interchangeable with calcium chloride dihydrate or commercial
  calcium-chloride products.
- Added mass-dosed solid and aqueous-solution material types with explicit
  exact or ranged active-chemical mass fractions. Exact fractions resolve to
  ordinary treatment additions without density; ranged fractions preserve
  active-mass bounds and never select an implicit midpoint. Optional source-
  document metadata retains composition/specification provenance.
- Extended optimizer admission to exact mass-fraction materials. Operational
  increments, limits, and mass ranking use measured material mass while
  chemistry and forward replay use resolved active chemical mass; ranged
  compositions remain rejected. Plan additions provide measured-material
  preparation text so consumers do not mistake replay-active mass for the
  operator dose.

### Documentation

- Defined the planned 0.5 conservative-equivalent total-alkalinity balance,
  including source resolution, blending, reviewed treatment contributions,
  target comparison, contribution reporting, optimizer admission,
  post-rounding replay, public-consumer responsibilities, scientific sources,
  and explicit exclusions for carbonate speciation and calculated pH.
- Documented that mixed ion/alkalinity optimization uses an unweighted ranking
  across different reporting bases as a project policy, not as a claim of
  scientific interchangeability.
- Clarified directly on the generic forward preparation-instruction types that
  their treatment mass is resolved active chemical mass and may differ from an
  optimizer plan's operator-facing measured material dose.

## 0.4.1 - 2026-09-14

### Compatibility warning

Consumers upgrading from 0.4.0 should expect optimizer requests using
`Ion.BICARBONATE`, `Ion.CARBONATE`, total alkalinity, or any automatically
selectable material contributing those species (including sodium bicarbonate)
to be rejected with `OptimizerInputSupportStatus.UNSUPPORTED`. See the
consumer API guide for the stable diagnostic codes and the supported manual
forward-calculation path.

### Fixed

- Separated carbonate-system chemical identity from calculation eligibility so
  adding an `Ion` no longer silently grants ordinary target-comparison or
  optimizer support.
- Marked forward bicarbonate and carbonate values as formal linear inventory,
  not equilibrium species concentrations, in comparison results, contribution
  rows, and stable structured notices.
- Rejected bicarbonate and carbonate optimizer targets and automatically
  selectable carbonate-system materials, including sodium bicarbonate, until a
  validated carbonate-system policy exists. Manual sodium-bicarbonate forward
  calculations remain available with explicit model limitations.
- Added a distinct total-alkalinity target property whose comparison remains
  explicitly `NOT_CALCULATED`; total alkalinity is never converted silently to
  bicarbonate.

## 0.4.0 - 2026-09-13

### Added

- The internal exact-composition, mass-dosed treatment-material boundary
  and solver-free optimizer request contract with explicit blend authority,
  source availability, bounded material inputs, diluent input, and separate
  support, feasibility, target-fit, and operational-practicality status
  vocabularies.
- The first fixed-blend optimizer strategy: minimize unweighted
  absolute target deviation in mg/L over bounded whole dose increments, use
  total measured material mass as a tie-breaker, and verify the selected plan
  through the ordinary forward-calculation path.
- Proportional-dilution optimization with an explicitly characterized
  diluent, preserved source proportions, source/diluent availability limits,
  and an optional deduplicated no-dilution best-effort plan.
- Bounded source-volume optimization across caller-permitted waters,
  including exact total-volume enforcement, independent chemistry resolution,
  positional source identity, and structured insufficient-availability results.
- Deterministic candidate generation for an equally close
  fewest-treatment-products strategy, with binary product-use decisions,
  lower-mass tertiary ranking, operational deduplication, and explicit tradeoff
  explanations. No-dilution plans now identify unavoidable starting-water
  overshoots and their signed deviations.
- The complete optimizer request/result graph and narrow exact-composition,
  mass-dosed material boundary in the supported package-root consumer facade,
  backed by an end-to-end package-root integration test.

### Changed

- Selected SciPy's HiGHS mixed-integer interface for practical dose-increment
  decisions, constrained to the Python 3.11-compatible 1.17 release line.
- Hardened the solver boundary after independent review: reject unsupported
  integer-count ranges, reject impossible negative objectives, recompute the
  selected objective from returned increment counts, preserve the raw solver
  objective separately, and compare the reconstructed objective with the
  ordinary forward result.
- Aligned integer-result validation with the backend's documented MIP
  feasibility tolerance, require the solver's complete decision-vector shape,
  and document the engine-reconstructed objective as the authoritative score.
- Kept numerical solver feasibility tolerances separate from caller-declared
  physical source availability, so a near-boundary solve cannot create volume
  beyond a source or diluent maximum.
- Aligned candidate-ranking comparisons with HiGHS's MIP feasibility tolerance,
  preserved an already-validated primary plan when an optional candidate solve
  fails, and hardened non-finite solver-output handling.
- Accounted for feasibility noise accumulated across multiple target-deviation
  variables when validating secondary and tertiary ranking solutions.

### Documentation

- Added a complete optimizer consumer example, documented blend-policy and
  candidate-ordering semantics, and aligned the active design and project
  boundary documents with the implemented SciPy-backed optimizer.

## 0.3.1 - 2026-09-06

### Changed

- Expanded the supported FermUnits dependency range from
  `>=0.1.3,<0.2.0` to `>=0.1.3,<2.0.0`. This retains the previously supported
  floor while allowing the stable FermUnits 1.x contract; the locked development
  and release environment uses FermUnits 1.0.0.
- Updated the release workflow to the Node 24-based `actions/upload-artifact`
  v7.0.1 release, pinned to its immutable commit.
- Added a dedicated Python 3.11 CI job for the retained FermUnits 0.1.3
  compatibility floor while the ordinary locked matrix tests FermUnits 1.0.0
  across Python 3.11 through 3.14.
- Bumped the Water Chemistry Engine package version to 0.3.1 without changing
  the supported package-root consumer facade or scientific calculations.

### Documentation

- Recorded the FermUnits 1.0 compatibility policy and clarified that consumers
  do not need a direct Pint dependency for functionality exposed by FermUnits.
- Reprioritized the first practical optimizer and ranked candidate-plan slice
  to 0.4 based on concrete consumer integration needs.

## 0.3.0 - 2026-09-04

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
- Exported `ScalarQuantity` so typed consumers can name the scalar FermUnits
  quantity policy used by supported fields and return values.

### Changed

- Raised the minimum FermUnits version to 0.1.3 and imported quantity typing
  through its public API, keeping FermUnits as the sole unit dependency boundary
  while retaining real Pint quantities in the supported result contract.
- **Breaking from 0.2.0:** migrated `ReportedPH` fields and
  `calculation_value` from floats to FermUnits `PHValue`. The `.exact()`,
  `.range()`, and `.average()` constructors still accept numeric arguments,
  while direct field construction now requires `PHValue`.
- **Breaking from 0.2.0:** changed `TargetWaterProfile.ph` from a float to
  `PHValue`; callers must replace values such as `ph=7.0` with
  `ph=PHValue(7.0)`.
- Removed the unsupported assumption that every valid pH must fall between 0
  and 14 while preserving finite-value validation and the range-only
  no-midpoint rule.

### Migration from 0.2.0

- Import `PHValue` from `fermunits` for direct reported-pH fields and target pH.
- Existing calls such as `ReportedPH.exact(7.2)` remain valid, but stored pH
  fields and `calculation_value` now return `PHValue`; use the semantic object's
  `.value` attribute when a numeric display/interchange adapter requires it.
- Change `TargetWaterProfile(..., ph=7.0)` to
  `TargetWaterProfile(..., ph=PHValue(7.0))`.

### Documentation

- Documented the FermUnits 0.1.3 boundary for semantic pH values and the exact
  pH/hydrogen-ion-activity transform while retaining activity models,
  concentration conversion, calculated pH, and reporting policy in the engine.
- Documented why chemical pH must not be represented as a Pint `pH` unit and
  why the former 0-through-14 validation was reviewed rather than treated as a
  universal pH invariant.
- Added IUPAC pH definition and measurement sources supporting the semantic
  activity-based pH boundary.
- Documented the planned separation between ideal treatment chemical
  identities and real treatment materials, including commercial assay/purity,
  liquid concentration basis, density/reference-temperature requirements, and
  explicit ranged-specification handling before optimization.
- Added authoritative/reference-source entries for calcium chloride identities,
  commercial flakes/solutions, and carbonate/chalk equilibrium; clarified that
  non-authoritative practitioner claims remain discovery inputs until
  independently verified.
- Updated the OxyChem calcium-chloride handbook citation to its current verified
  PDF location after external review.
- Clarified that RO/distilled "ion-free dilution" is already ordinary
  multi-source blending and does not require a separate engine chemistry
  primitive.

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
