# Water Treatment Web

Standalone web interface for the Water Treatment Engine.

The application will provide a graphical interface for:

- entering source-water chemistry;
- selecting or creating target profiles;
- blending multiple water sources;
- choosing permitted mineral additions;
- generating ranked treatment plans;
- comparing predicted and target profiles;
- viewing per-source and per-treatment ion contributions;
- importing and exporting FermentationJSON data.

## Architecture

This application depends on `water-treatment-engine` for all scientific and engineering calculations.

The web layer is responsible for:

- forms;
- page navigation;
- HTML rendering;
- unit-display preferences;
- validation presentation;
- saved application state;
- charts and tables.

Scientific formulas and optimization logic must remain in the engine package.

## Planned interface stack

The interface is planned to use:

- server-rendered HTML;
- HTMX;
- a lightweight Python ASGI framework;
- progressively enhanced forms;
- responsive layouts for desktop, tablet, and mobile use.

The exact ASGI framework has not yet been selected.

## Mecha-Brew integration

Mecha-Brew will use `water-treatment-engine` directly and provide its own native interface.

This standalone web application is a separate consumer of the same engine and is not intended to be embedded inside Mecha-Brew.

## Status

Early repository setup. No web interface has been implemented yet.

## License

Mozilla Public License 2.0.