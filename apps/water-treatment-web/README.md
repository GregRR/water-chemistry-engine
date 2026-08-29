# Water Treatment Web

Standalone web interface for the Water Treatment Engine.

## Status

The package is currently a scaffold. The **0.3 milestone** will implement the
first usable web calculator on top of the completed deterministic 0.2 engine.

The selected interface stack is:

- Django;
- server-rendered HTML templates;
- HTMX for progressive enhancement;
- minimal vanilla JavaScript where browser-only behavior requires it.

Django is intentionally not a 0.2 dependency; it will be added when 0.3 web
implementation begins.

## Python compatibility

The web package requires Python 3.11 or newer. CI currently tests Python 3.11,
3.12, 3.13, and 3.14, with Python 3.11 treated as the compatibility baseline.
The 0.3 implementation will use the Django 5.2 LTS line so the application can
preserve that minimum runtime.

## 0.3 interface scope

The first usable application will support:

- manual source-water entry;
- built-in and user-entered target/reference profiles;
- fixed blending of multiple characterized sources;
- supported mineral-addition rows;
- source, blend, final, and target comparison displays;
- source/treatment contribution detail;
- preparation instructions;
- clear unknown, unavailable, assumption, and not-calculated states;
- responsive layouts with no account required for basic calculations.

Automatic optimization, ranked plans, and BeerJSON/FermentationJSON adapters
are later milestones and do not block the first UI.

## Architecture

This application depends on `water-treatment-engine` for all scientific and
engineering calculations.

The web layer owns forms, navigation, templates, localized presentation,
validation display, saved application state, charts/tables, and eventual Django
ORM persistence. Scientific formulas, treatment models, and optimization logic
remain in the engine.

Mechani-Brew consumes `water-treatment-engine` directly and provides its own
interface rather than embedding this standalone application.

## License

Mozilla Public License 2.0.
