# Palmer and Kaminski Chapter 7 Validation Candidates

## Status and boundary

This note records possible Engine test and conformance cases from John Palmer
and Colin Kaminski, *Water: A Comprehensive Guide for Brewers* (Brewers
Publications, 2013), Chapter 7, "Adjusting Water for Style."

These cases are not an Engine-owned profile library. Suggested style profiles
belong in a consumer database if Water Chemistry Designer chooses to offer
them. The Engine should use only narrowly scoped cases that verify generic
range, blending, treatment, comparison, or provenance behavior.

OCR was used to locate the material. The table headings, reporting bases, and
numbers below were checked against the scanned pages. Before an executable
fixture is admitted, its arithmetic should also be recomputed independently
using the Engine's reviewed chemical identities and current constants.

## Candidate 1: suggested-profile range semantics

Tables 18 and 19 on book pages 156-159 give suggested lager and ale water
profiles. The tables use:

- exact values, ranges, and values described in the surrounding text as
  minimums;
- calcium, sulfate, and chloride in mg/L;
- total alkalinity and Kolbach residual alkalinity in mg/L as CaCO3; and
- categorical brewing guidance that is not generic water chemistry.

The authors explicitly describe the profiles as experience-based suggestions,
opinions, and starting points for experimentation rather than universal
standards. If a consumer stores them, their evidentiary classification should
therefore remain a published recommendation or practitioner reference, not an
experimentally validated optimum.

These tables can test that the Engine preserves exact/range/bound target
semantics and reporting bases. They should not make residual alkalinity,
acidification advice, beer-style interpretation, or the table itself an
Engine-owned catalog.

## Candidate 2: fixed dilution followed by gypsum

The American pale ale example on book pages 161-165 starts with:

- calcium: 70 mg/L;
- magnesium: 15 mg/L;
- total alkalinity: 125 mg/L as CaCO3;
- sodium: 35 mg/L;
- chloride: 55 mg/L; and
- sulfate: 110 mg/L.

For a 1:1 blend with RO water, the book displays 35 mg/L calcium, 8 mg/L
magnesium, 63 mg/L total alkalinity as CaCO3, 18 mg/L sodium, 28 mg/L
chloride, and 55 mg/L sulfate. These are whole-number presentation values:
the exact linear results include 7.5 mg/L magnesium, 62.5 mg/L alkalinity,
17.5 mg/L sodium, and 27.5 mg/L chloride. An Engine test must retain the exact
calculation and treat the book's integers as rounded display values, not as a
different chemistry rule.

The example then adds 1 gram of gypsum per US gallon. The book quotes
61.5 mg/L calcium and 147.4 mg/L sulfate from that dose and displays a final
profile of 97 mg/L calcium, 8 mg/L magnesium, 63 mg/L total alkalinity as
CaCO3, 18 mg/L sodium, 28 mg/L chloride, and 202 mg/L sulfate.

This is a strong candidate for an end-to-end fixed-blend plus manual-treatment
test, subject to these conditions:

1. the RO source is represented explicitly rather than assumed from a special
   dilution shortcut;
2. volume additivity and the source's known-zero values are explicit;
3. the Engine recomputes gypsum yield from its supported chemical identity and
   current molar masses; and
4. comparison with the publication allows for its stated whole-number
   presentation rather than pinning Engine constants to rounded book values.

## Candidate 3: calcium-chloride water build

The Pilsner example on book pages 166-167 starts from low-mineral water and
uses a target of 30 mg/L calcium in 10 US gallons. It quotes a calcium-chloride
yield of 72.0 mg/L calcium and 127.4 mg/L chloride per gram per US gallon,
then calculates 4.17 grams, rounded to 4.2 grams, and 53.5 mg/L chloride from
the rounded dose.

Those yields correspond to the book's calcium-chloride preparation and must
not be applied to an unspecified or anhydrous product. An executable case must
identify calcium chloride dihydrate explicitly, recompute its yields from the
Engine identity, and distinguish the exact 4.17-gram calculation from the
book's practical 4.2-gram dose. This case can test hydration-state identity,
manual dosing, practical rounding, and post-dose forward recalculation.

## Cases to defer

Other Chapter 7 examples depend on capabilities intentionally outside the
current generic Engine contract:

- acidification to a target water pH;
- mash-pH prediction and malt buffering;
- Kolbach residual-alkalinity recommendations;
- the book's proposed Z-alkalinity mash model; and
- calcium-hydroxide or sodium-hydroxide alkalinity treatments that have not
  been separately implemented and validated.

They may inform later research, but they must not be converted into current
tests by silently implementing brewing-specific assumptions or unsupported
chemistry.

## Admission checklist

Before adding any executable vector derived from this chapter:

1. verify every used value against the scan;
2. record the book page, table/example, source classification, and reporting
   basis;
3. independently recompute expected chemistry from reviewed Engine constants;
4. record publication rounding separately from exact expected results;
5. include unknown/unsupported behavior where the example crosses the current
   model boundary; and
6. confirm that the copied facts are suitable for inclusion as a small
   validation fixture rather than a redistributed profile collection.
