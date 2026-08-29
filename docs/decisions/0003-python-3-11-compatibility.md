# ADR 0003: Python 3.11 Compatibility Baseline

## Status

Accepted

## Context

The calculation engine is intended to run outside a developer workstation,
including Raspberry Pi systems, brewery controllers, home servers, scripts,
and downstream applications. Requiring Python 3.14 would unnecessarily exclude
many otherwise suitable deployments.

The engine already depends on Python 3.11 standard-library features such as
`enum.StrEnum`, making Python 3.11 a natural minimum without compatibility
shims. FermUnits 0.1.2 also supports Python 3.11 and is published on PyPI.

The pre-0.2 codebase used Python 3.12 `type` alias syntax and also benefited from
Python 3.14's deferred annotation behavior. Both assumptions must be removed to
make the stated compatibility floor real rather than metadata-only.

## Decision

The workspace, `water-treatment-engine`, and `water-treatment-web` support
Python 3.11 and newer. The 0.2 release gate explicitly tests Python 3.11, 3.12,
3.13, and 3.14.

Python 3.11 is the compatibility baseline:

- package metadata uses `requires-python = ">=3.11"`;
- the checked-in `.python-version` selects Python 3.11 by default;
- Ruff targets `py311`;
- mypy checks Python 3.11 language semantics;
- unguarded source code must not require syntax or standard-library APIs newer
  than Python 3.11;
- CI compiles and tests the workspace on every supported Python minor version.

The engine requires `ferm-units>=0.1.2,<0.2.0` so its dependency floor shares
this compatibility contract.

## Consequences

- Raspberry Pi and other Linux deployments are not forced onto Python 3.14.
- Newer Python syntax may be adopted only after the minimum supported runtime is
  deliberately raised in a future release.
- Type aliases use Python-3.11-compatible `typing.TypeAlias` declarations.
- Modules with self-referential annotations explicitly postpone annotation
  evaluation so behavior is consistent across Python 3.11 through 3.14.
- The initial Django web implementation should remain on a release line that
  supports Python 3.11; ADR 0002 selects Django 5.2 LTS for that purpose.
