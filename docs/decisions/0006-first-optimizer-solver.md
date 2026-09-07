# ADR 0006: First Optimizer Solver

## Status

Accepted

## Context

The 0.4 optimizer needs continuous, nonnegative decision variables for source
volumes and measured material masses; equality constraints for total volume;
upper bounds for source availability and material limits; and linear target
deviation objectives and constraints. Implementing and maintaining a numerical
linear-programming solver inside the engine would add substantial correctness
and numerical risk unrelated to water chemistry.

SciPy's `optimize.linprog(method="highs")` solves a linear objective subject to
linear equality/inequality constraints and bounded variables through the HiGHS
solvers. This matches the initial continuous problem without requiring the
mixed-integer policies deliberately deferred from 0.4.

SciPy 1.17 supports Python 3.11 through 3.14. SciPy 1.18 requires Python 3.12 or
newer, so it is incompatible with the engine's Python 3.11 baseline.

Authoritative references:

- <https://docs.scipy.org/doc/scipy-1.17.0/reference/optimize.linprog-highs.html>
- <https://docs.scipy.org/doc/scipy/release/1.17.0-notes.html>
- <https://pypi.org/project/scipy/1.17.0/>

## Decision

The first optimizer uses `scipy.optimize.linprog` with the explicit `highs`
method and declares `scipy>=1.17,<1.18`.

The engine owns construction of the optimization problem, policy semantics,
post-solver validation, practical dose rounding, full forward recalculation,
diagnostics, notices, and deterministic candidate ordering. A successful
solver status is never accepted as proof of chemically or operationally valid
output without those engine checks.

The 0.4 implementation remains continuous. It does not use SciPy's integrality
support to approximate fewest-product or other discrete policies. Those
policies require a separate deliberate design and validation step.

## Consequences

- NumPy is installed transitively by SciPy, but the engine does not declare or
  use NumPy directly unless later source code actually requires its API.
- Python 3.11 compatibility constrains SciPy to the 1.17 release line while the
  current runtime baseline remains in force.
- Solver method, status, tolerances relevant to interpretation, and the engine's
  optimization-policy version must be visible in plan results.
- Independent analytical cases and post-rounding forward recalculation remain
  required; tests must not merely reproduce SciPy's returned arrays.
