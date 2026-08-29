# ADR 0002: Django and HTMX Web Stack

## Status

Accepted

## Context

The standalone calculator needs server-rendered forms, validation, persistence
for saved profiles/results, and a straightforward path to later authenticated
features without moving scientific logic out of `water-treatment-engine`.

## Decision

`water-treatment-web` will use Django for the application framework and
server-rendered templates, with HTMX for progressive enhancement where it
improves the workflow. Minimal vanilla JavaScript may be used for browser-only
behavior that HTMX does not cover cleanly.

Django and its ORM belong only to the web application. The reusable engine
remains framework- and database-independent. Django will be introduced during
the 0.3 web-application milestone rather than as an unused 0.2 dependency.

The initial web implementation will use the Django 5.2 LTS release line. Django
5.2 supports Python 3.11 while Django 6.0 requires Python 3.12 or newer, so the
5.2 LTS line preserves the repository's Python 3.11 compatibility floor.

## Consequences

- The first usable UI does not require a client-side SPA or Node build system.
- Saved-profile/result persistence can use normal Django models while keeping
  engine-domain objects separate from database records.
- Future API endpoints remain adapters around the same engine rather than a
  second implementation of calculation logic.
- Raising the Django major version beyond a Python-3.11-compatible release line
  requires an explicit decision to raise the web package's Python floor.
- Mechani-Brew and other consumers can continue to use the engine directly.
