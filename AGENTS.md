# AGENTS.md — Water Chemistry Engine Contributor Instructions

This file contains repository-wide instructions for coding agents and human
contributors. It is intentionally concise enough to remain useful as working
context while pointing to the repository's authoritative design and scientific
documentation.

## 1. Project identity and boundary

Water Chemistry Engine is a reusable, scientifically grounded Python engine for
characterizing, blending, treating, comparing, and eventually optimizing water
chemistry.

Current identities:

- Repository/project/distribution: `water-chemistry-engine`
- Python import package: `water_chemistry_engine`
- License: MPL-2.0
- Python compatibility baseline: Python 3.11
- CI-supported Python versions: 3.11, 3.12, 3.13, and 3.14
- Dependency/tooling manager: `uv`

This repository is **engine-only**. Scientific/domain behavior belongs here.
Web/Django applications, native applications, persistence, accounts, UI, and
other product-layer code belong in separate consumer projects. The engine must
not import a consumer application, ORM, web framework, or product-specific
persistence layer.

Do not restore the old `water-treatment-engine`, `water_treatment_engine`, or
combined web/workspace architecture except when editing historical records that
must preserve those names accurately.

## 2. Read the repository before changing it

Before making a nontrivial change, inspect the code, tests, and task-relevant
project documentation. Do not infer architecture or scientific policy from file
names alone.

Authoritative starting points:

- `README.md` — current project scope and implemented capabilities
- `docs/WATER_CHEM_DESIGN.md` — scientific and architectural design
- `docs/WATER_CHEM_REFERENCES.md` — scientific/technical source register
- `docs/ROADMAP.md` — active release path and scientific invariants
- `docs/PROJECT_STRUCTURE.md` — repository and package boundaries
- `docs/FUTURE_CAPABILITIES.md` — intentionally deferred capabilities
- `docs/decisions/` — architecture decision records
- `docs/reviews/` — historical external review checkpoints; useful context,
  but not normative specifications
- `CHANGELOG.md` — implemented release history

When code, tests, and active design documentation appear to disagree, stop and
investigate. Do not silently choose whichever interpretation is easiest.
Historical review documents and superseded ADRs must not override current code,
tests, and active design decisions.

## 3. Scientific rigor is the highest-priority project rule

Scientific correctness, source fidelity, and explicit uncertainty take priority
over convenience, feature velocity, or matching a familiar calculator.

**Do not guess scientific behavior. Do not invent constants, targets, formulas,
chemical assumptions, or treatment rules because they seem plausible.**

When a scientific or technical point is uncertain:

1. Search the existing design, references, tests, and research notes first.
2. Research the question rather than making an assumption.
3. Prefer primary scientific literature, recognized standards, official
   analytical methods, original datasets, and authoritative technical sources.
4. Use specialist secondary/practitioner sources for discovery and context, not
   as unquestioned authority for quantitative rules.
5. Trace important quantitative claims back to the best available primary or
   authoritative source whenever practical.
6. Record the source and its limitations in `docs/WATER_CHEM_REFERENCES.md` or
   an appropriate research document when the evidence affects implementation.
7. Cite DOI, publication, standard/method, official URL, version/date, or other
   durable provenance as appropriate.
8. Distinguish what a source actually establishes from project inference.
9. If evidence is inadequate, model the result as unknown/unsupported, emit an
   explicit limitation/notice where appropriate, or defer the feature.
10. Never turn a regional, historical, practitioner, or experimental reference
    profile into a claim of universal scientific optimality without evidence.

A weak approximation presented confidently is worse than an explicit unknown.
If a defensible model is not ready, preserve the gap rather than hiding it.

### Scientific implementation expectations

For new formulas, conversions, stoichiometry, target rules, or predictive
models:

- document the governing equation and assumptions;
- use dimensional quantities and FermUnits rather than ad hoc unit arithmetic;
- state reporting bases and chemical species explicitly;
- document applicable temperature/reference conditions when material;
- preserve provenance and model/version information when outputs depend on a
  specific model;
- add tests derived from authoritative examples, reference calculations, or
  independently checkable invariants;
- include edge cases and failure/unsupported cases, not only happy paths;
- use property-based tests with Hypothesis where invariants are more important
  than a short list of examples;
- do not overstate precision beyond what the inputs and model justify.

## 4. Core scientific/data invariants

These rules are deliberate and must not be weakened accidentally.

### Reported data versus derived data

- Preserve reported, measured, inferred, estimated, and calculated data as
  distinct concepts.
- Preserve exact values, ranges, qualified bounds, `ND`/not-detected states,
  named reported statistics, original units/reporting bases, and source
  metadata when available.
- A source-reported average is reported data. A midpoint calculated by the
  engine is derived data.
- Range midpoints for linear quantities require explicit policy permission.
- Unknown measurements remain unknown. Do not silently substitute zero.
- `ND` is not zero.
- Known treatment contributions may remain auditable even when an unknown
  starting concentration means the final total is still unknown.

### pH

- pH is logarithmic.
- Never compute an arithmetic midpoint or arithmetic mean of pH values.
- Preserve reported pH values and ranges exactly as reported.
- Use a reported average pH only when the source actually reports that average.
- If averaging actual pH observations is ever required, operate through
  hydrogen-ion activity/concentration as scientifically appropriate rather than
  arithmetic pH averaging.
- Calculated working-water pH remains unsupported until a validated reusable
  aqueous model, input contract, reference cases, and limitations are ready.
- Do not smuggle recipe-aware mash-pH assumptions into generic working-water pH.

### Chlorine, chloramine, chloride, and source reports

- Preserve chlorine/chloramine information whenever a source report provides
  it. It is first-class source-water/report data.
- Chlorine/chloramine are not chloride and must remain distinct.
- Preserve distinctions such as total chlorine, free chlorine, chloramine, and
  named chloramine species when reported.

### Source identity and provenance

- Use `SourceDocumentMetadata` for document/report metadata.
- Prefer `SourceWaterProfile.source_document` for the associated source report.
- Keep document metadata separate from the physical identity of the water
  source and from result-specific sampling context.
- Distinguish document `publisher` from optional `analysis_provider` when both
  are known.
- Preserve title, publication/report date, source URL, retrieval date,
  page/section reference, and notes when applicable.

### Water states, targets, and references

- Source water, target/reference water, derived calculation state, and measured
  treated-water results are distinct concepts.
- Preserve multiple source waters as independent inputs; blending is a core
  engine capability.
- Unknown source chemistry must propagate conservatively through blending.
- Target/reference comparison must not manufacture scientific certainty from
  missing data.
- A reference profile may be something worth reproducing without being an
  experimentally validated optimum.
- Regulatory/advisory limits are not the same thing as measured chemistry or a
  sensory/process target.

## 5. Python and software-engineering standards

Use modern Python best practices while preserving Python 3.11 compatibility.
Code must parse and behave correctly under Python 3.11 semantics even when the
working interpreter is newer.

General expectations:

- Prefer clear, explicit, typed code over clever abstractions.
- Keep scientific logic pure and deterministic where practical.
- Prefer small cohesive modules and domain types over loosely structured
  dictionaries.
- Use immutable/frozen dataclasses or similarly simple immutable objects for
  internal scientific models when appropriate.
- Keep public and internal APIs deliberate. Public APIs are still pre-1.0; do
  not expand them casually.
- Validate at boundaries and fail with actionable errors.
- Preserve unknown/unsupported states explicitly instead of using sentinel
  values that can be mistaken for real chemistry.
- Avoid global mutable state and hidden side effects.
- Avoid premature optimization. Measure before making performance-driven
  complexity changes.
- Avoid broad refactors mixed into scientific feature work unless necessary for
  correctness.
- Follow existing naming and module conventions.
- Add docstrings/comments where they explain scientific intent, non-obvious
  invariants, provenance, or why an apparently simpler implementation is wrong.
  Do not add comments that merely restate the code.

### Units and dependencies

- FermUnits is the project unit boundary; use it instead of duplicating unit
  semantics in this engine.
- Do not manually manipulate unit strings or rely on untyped numeric values
  where dimensional quantities matter.
- Keep dependency constraints appropriately bounded for a reusable library.
- Do not add NumPy, SciPy, Pydantic, or another substantial dependency merely
  because the roadmap anticipates it. Add a dependency when implemented work
  actually requires it and document why.
- Preserve the checked-in `uv.lock` and use locked environments for validation.

## 6. Testing expectations

Every behavioral change should have tests that would fail without the change.
Scientific changes require tests for the scientific contract, not merely code
coverage.

When applicable, cover:

- normal/reference cases;
- units and reporting bases;
- exact boundaries and floating-point noise near boundaries;
- zero/negative/invalid inputs as appropriate;
- unknown and partially known chemistry;
- `ND`, ranges, bounds, and reported averages;
- multiple-source blending;
- provenance and source/result linkage;
- deterministic ordering/serialization where part of the contract;
- regression cases from internal or external review findings.

Prefer testing public behavior. Tests may exercise internals where the internal
scientific invariant itself requires direct validation.

## 7. Standard quality gates

Use `uv`. Do not replace the project's normal tooling with Conda, Poetry, pipenv,
or another environment manager.

For ordinary development, run the task-relevant tests while iterating. Before a
commit boundary, run the complete applicable gate unless the change is clearly
documentation-only.

Baseline checks:

```bash
uv lock --check
uv sync --dev --locked
uv run pytest
uv run ruff format --check .
uv run ruff check .
uv run mypy --strict src
git diff --check
```

For compatibility-sensitive changes and release candidates, mirror CI across
Python 3.11 through 3.14. Python 3.11 is the minimum-runtime proof and therefore
deserves special attention.

CI currently performs, for each supported runtime:

```bash
uv sync --dev --python <VERSION> --locked
uv run --python <VERSION> python -m compileall -q src
uv run --python <VERSION> pytest
```

The distribution/quality job also performs formatting, Ruff, strict mypy, and:

```bash
uv build --python 3.14
```

Do not declare a gate successful if a failure is unexplained. Diagnose it and
fix it or explicitly adjudicate it with the user.

## 8. Documentation is part of the implementation

Update documentation in the same development slice when behavior, architecture,
public APIs, package names, assumptions, limitations, supported versions, or
scientific evidence changes.

In particular:

- keep `README.md`, `docs/WATER_CHEM_DESIGN.md`, `docs/ROADMAP.md`,
  `docs/PROJECT_STRUCTURE.md`, and `CHANGELOG.md` mutually consistent;
- update `docs/WATER_CHEM_REFERENCES.md` when new evidence materially informs
  behavior;
- preserve historical names in historical ADR/review records when accuracy
  requires them;
- do not mechanically replace historical text merely to eliminate an old name;
- keep implemented features described as implemented and future work described
  as planned;
- keep examples executable and current;
- do not claim a scientific capability the engine does not actually provide.

## 9. Change and commit discipline

Work in small, coherent slices that are easy to review and revert.

- Inspect existing implementation and tests before editing.
- Avoid unrelated cleanup in the same change.
- Keep the working tree understandable at stopping points.
- Review the complete diff before committing.
- Run `git diff --check` before commit.
- Use Conventional Commit prefixes.
- Prefer a concrete imperative subject of 50 characters or fewer.
- When a body is useful, separate it with a blank line and wrap lines near
  72 characters.
- Describe what the code actually does and why it matters; avoid vague phrases.
- Do not rewrite shared history, force-push, tag, publish, or create a release
  unless the user explicitly requests it.

When handing multi-file changes to a human outside an agent-managed working
copy, a Git `.patch` is preferred over an ad hoc shell script. Never put
non-runnable explanatory comments into a command block presented as terminal
commands.

## 10. Internal review cadence

Do not wait until the end of a milestone to review your own work.

At good stopping points—typically after a few substantive commits or after one
coherent implementation slice—stop and perform an internal code/science review
of the accumulated work before building more on top of it.

The internal review should actively look for:

- scientific assumptions that lack evidence;
- incorrect chemistry, stoichiometry, units, reporting bases, or sign
  conventions;
- pH/logarithmic mistakes;
- accidental conversion of unknown/`ND` data to zero;
- provenance loss;
- floating-point/boundary issues;
- API leakage or unnecessary coupling;
- Python 3.11 compatibility regressions;
- insufficient tests or tests that only mirror the implementation;
- documentation drift;
- unnecessary dependencies or over-engineering;
- error paths that could produce misleading scientific results.

Treat internal review as an attempt to disprove the implementation, not merely
confirm it. Fix confirmed issues before continuing dependent work.

## 11. External review checkpoints

At meaningful project boundaries, stop and request an independent external code
and scientific review rather than continuing indefinitely.

Good external-review checkpoints include:

- completion of a substantial scientific model or calculation family;
- establishment/change of a public consumer API contract;
- a change to core data/provenance semantics;
- completion of a milestone before dependent work starts;
- after significant internal-review remediation;
- a release candidate before tagging/publishing.

External reviewers should be asked to focus on correctness and scientific risk,
not cosmetic preferences. Useful review topics include chemistry assumptions,
interval/range semantics, units, numerical edge cases, unknown/NaN behavior,
provenance, API contracts, test independence, and documentation claims.

Record important external reviews under `docs/reviews/`. Review findings are
point-in-time audit artifacts; adjudicate each finding and add regression tests
for confirmed bugs. Do not treat an old review as a permanent specification.

## 12. Release discipline

A release is not ready merely because source tests pass. For release work,
verify the exact release commit, documentation, package metadata, artifacts,
clean-install behavior, and publishing path.

Before tagging a release, at minimum:

- run the full source/CI-equivalent validation;
- perform a documentation and stale-name drift sweep;
- build both wheel and sdist;
- inspect artifact contents and metadata;
- verify the artifacts contain `water_chemistry_engine` and no obsolete
  `water_treatment_engine`, old web app, caches, or local artifacts;
- install the built wheel into a clean Python 3.11 environment outside the
  source checkout and run a representative calculation;
- build/install from the sdist where practical and compare package identity and
  essential metadata with the normal wheel;
- follow README installation/quickstart instructions as written;
- confirm CI is green on the exact pushed release commit;
- review the publishing configuration and package name;
- stop for the planned release-candidate review;
- do not tag or publish without explicit user approval.

After publication, verify the public package/release itself from a fresh
environment. A green publishing workflow is not proof that the public artifact
is correct.

## 13. Final operating principle

When choosing between a fast assumption and a slower verifiable answer, choose
the verifiable answer. This project is intended to be scientifically reusable;
its calculations and claims must be explainable, testable, provenance-aware,
and appropriately cautious about what the evidence does and does not support.
