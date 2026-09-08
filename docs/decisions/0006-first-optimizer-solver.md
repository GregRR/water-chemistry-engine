# ADR 0006: First Optimizer Solver

## Status

Accepted

## Context

The 0.4 optimizer needs continuous, nonnegative decision variables for source
volumes; discrete measured-material decisions that honor declared dose
increments; equality constraints for total volume; upper bounds for source
availability and material limits; and linear target-deviation objectives and
constraints. Implementing and maintaining a numerical linear or mixed-integer
solver inside the engine would add substantial correctness and numerical risk
unrelated to water chemistry.

SciPy's `optimize.milp` solves a linear objective with continuous and integer
variables subject to linear constraints and bounds through HiGHS. This permits
each measured material mass to be represented as an integer count of its
declared dose increment. SciPy's own example demonstrates why rounding a
continuous optimum does not in general produce the correct integer solution.

SciPy 1.17 supports Python 3.11 through 3.14. SciPy 1.18 requires Python 3.12 or
newer, so it is incompatible with the engine's Python 3.11 baseline.

Authoritative references:

- <https://docs.scipy.org/doc/scipy-1.17.0/reference/generated/scipy.optimize.milp.html>
- <https://docs.scipy.org/doc/scipy/release/1.17.0-notes.html>
- <https://pypi.org/project/scipy/1.17.0/>

## Decision

The first optimizer uses `scipy.optimize.milp`, backed by HiGHS, and declares
`scipy>=1.17,<1.18`. Material variables are integer counts of their positive
dose increments. Proportional dilution combines those integer material
variables with one continuous diluent-volume variable while preserving the
ordinary sources' declared proportions. Source-volume optimization adds one
bounded continuous variable per permitted source and constrains their sum to
the requested total volume.

The engine owns construction of the optimization problem, policy semantics,
post-solver validation, practical dose construction, full forward recalculation,
diagnostics, notices, and deterministic candidate ordering. A successful
solver status is never accepted as proof of chemically or operationally valid
output without those engine checks.

Integrality is used only where the existing material contract requires a whole
number of dose increments. Fewest-product and other binary-selection policies
remain separate design decisions; they must not be smuggled into this
operational constraint.

## Consequences

- NumPy is installed transitively by SciPy, but the engine does not declare or
  use NumPy directly unless later source code actually requires its API.
- Python 3.11 compatibility constrains SciPy to the 1.17 release line while the
  current runtime baseline remains in force.
- Solver method, status, tolerances relevant to interpretation, and the engine's
  optimization-policy version must be visible in plan results.
- The SciPy/HiGHS integration accepts at most 1,000,000 dose increments per
  material. This conservative, project-tested numerical ceiling is an
  implementation limit rather than a scientific or operational limit. Larger
  ranges are explicitly unsupported and are not silently coarsened.
- Model coefficients at or beyond HiGHS's documented small/large matrix-value
  thresholds, and constraint bounds at or beyond its documented infinite-bound
  threshold, are rejected as unsupported before solving.
- The raw solver objective is audit data, not the postvalidation reference. The
  engine requires the complete solver decision vector, validates returned
  integer counts within HiGHS's documented MIP feasibility tolerance and the
  declared bounds, rejects a negative raw deviation objective, reconstructs the
  primary objective from the counts, and compares that value with the ordinary
  forward-calculation result. The reconstructed value is authoritative; the raw
  value is retained for audit and may differ within backend tolerances.
- Independent analytical cases and post-solver forward recalculation remain
  required; tests must not merely reproduce SciPy's returned arrays.
