# Water Treatment Calculator Roadmap

This roadmap describes the intended development sequence. Release contents may
change as research, validation, and implementation reveal new requirements.

## Version 1.0 — Brewing and Fermentation Water Treatment

Version 1.0 will establish the reusable engineering engine and its first
standalone graphical interface.

### Supported domains

- Beer brewing
- Mead making
- Distilling
  - mashing and fermentation water
  - general process water
  - spirit-proofing water profiles where scientifically appropriate

### Water profiles

- Dated source-water profiles
- Municipal, well, bottled, reverse-osmosis, and distilled water
- Exact target profiles
- Target ranges
- Historical city profiles
- Published brewery profiles
- Beer-style profiles
- Mead and distilling profiles
- User-created profiles
- Previously achieved brewing-liquor profiles
- Profile provenance and citations

### Water blending

- Blend two or more source waters
- Calculate a fixed blend selected by the user
- Optimize source-water proportions automatically
- Enforce source availability and volume limits
- Report each source water’s contribution to the final blend

### Mineral treatment

- Common brewing and fermentation salts
- Explicit chemical and hydration forms
- Ingredient purity
- Mineral contribution calculations
- Practical weighing increments
- Recalculation after dose rounding
- Restrictions to user-selected available treatments

### Optimization and results

- Closest practical target match
- Fewest different treatment products
- Lowest total mineral addition
- Least dilution-water use
- Water-only blend where feasible
- No-dilution treatment plan
- Multiple distinct ranked plans
- Explanation of compromises and infeasible targets
- Per-water and per-treatment ion contribution tables
- Predicted final profile and target deviations
- Machine-readable warnings and explanation codes

### Units and interchange

- FermUnits for dimensional quantities and conversions
- Canonical calculation units
- Explicit US customary, Imperial, and metric units
- Localized input and display preferences
- FermentationJSON import and export adapters
- Versioned calculation inputs and results

### Applications

- Independently installable Python engine
- Responsive standalone web interface
- Server-rendered HTML with HTMX
- Direct integration into Mecha-Brew
- Stable interfaces suitable for future mobile applications

## Version 2.0 — Advanced Brewing-Water Chemistry

- Acid additions
- Alkali additions
- Alkalinity neutralization
- Separate mash- and sparge-water treatment
- Recipe-aware mash-pH prediction
- Deeper carbonate and bicarbonate chemistry
- Precipitation and solubility considerations where practical
- Uncertainty propagation
- Optimization using uncertain or ranged source-water reports
- Pareto-front exploration
- Optional treatment-cost inputs
- Optional Mecha-Brew inventory integration
- Expanded brewery-scale workflows

## Version 3.0 — Broader Food and Beverage Applications

The shared water engine may be extended through independently validated
domain modules for:

- Coffee
- Tea
- Bread
- Sourdough
- Pizza dough
- Alkaline noodles
- Ramen and kansui
- Cheesemaking
- Lacto-fermented vegetables
- Other fermented foods and beverages

These modules should share water-composition, blending, provenance, and
optimization infrastructure while retaining their own scientific models,
target profiles, warnings, references, and validation suites.

## Version 4.0 — Selected Industrial Applications

Possible future modules may address selected non-food process-water uses.

Industrial support must not be introduced until the relevant safety,
regulatory, materials-compatibility, treatment, and validation requirements
have been researched and documented.

## Development principle

Later features should be anticipated in the architecture without delaying a
scientifically sound and useful Version 1.0. Features must not be advertised
until their calculations, operating ranges, references, and validation tests
are implemented and documented.
