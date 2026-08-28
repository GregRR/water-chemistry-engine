# ADR 0001: Project and Package Boundaries

## Status

Accepted

## Decision

The project will use one public repository containing two independently installable Python distributions:

- `water-treatment-engine`
- `water-treatment-web`

The engine will contain all scientific calculations, validation, optimization, warnings, and structured result models.

The web application will provide the standalone graphical interface and will depend on the engine.

Mechani-Brew will consume the engine directly rather than embedding the standalone web application.

FermUnits will be an external required dependency.

FermentationJSON support will be implemented through adapters at data boundaries.

No shared calculator-core package will be introduced until concrete duplication demonstrates a need for one.

The repository will use uv. The standalone interface will use server-rendered HTML with HTMX.
