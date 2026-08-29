# ADR 0005: Water Chemistry Naming

## Status

Accepted

## Context

The reusable engine began under the `water-treatment-engine` name. By the
0.2 release boundary, its responsibility had become broader than treatment
operations alone: it characterizes reported source-water chemistry, preserves
measurement semantics and provenance, resolves and blends sources, compares
water with targets/references, applies treatments, and is intended to support
additional validated water-domain models.

The separate end-user product is also intended to expose multiple purpose-specific
workflows, such as brewing, coffee, and dough-water design. Using "water
chemistry" as the shared project family better describes that broader domain
without implying that every capability is an industrial water-treatment
operation.

## Decision

Before the 0.2.0 release, rename the reusable project consistently to:

- project: **Water Chemistry Engine**;
- repository: `water-chemistry-engine`;
- Python distribution: `water-chemistry-engine`;
- Python import package: `water_chemistry_engine`;
- source package: `src/water_chemistry_engine/`.

The separate end-user application project uses the **Water Chemistry
Calculator** / `water-chemistry-calculator` name. Product modes may use more
specific user-facing names without changing this engine boundary.

No compatibility alias for `water_treatment_engine` is added because the rename
occurs before the 0.2.0 release and before the supported consumer-facing API is
stabilized. Historical review records and superseded decisions retain the names
and paths that were accurate when they were written.

## Consequences

- Package metadata, imports, tests, documentation, CI/build output, lock data,
  and live repository links use the new name.
- Existing pre-0.2 development imports must change from
  `water_treatment_engine` to `water_chemistry_engine`.
- The engine identity covers characterization, comparison, treatment,
  optimization, and other validated water-chemistry capabilities.
- Treatment remains a central capability, but it no longer defines the name of
  the entire reusable scientific domain.
