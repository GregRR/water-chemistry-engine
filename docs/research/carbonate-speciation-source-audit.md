# Carbonate-Speciation Source Audit

**Status:** Research record; not an implemented calculation contract

**Reviewed source:** Palmer and Kaminski (2013), *Water: A Comprehensive Guide
for Brewers*, Appendix D, pages 275 and 277

**Authoritative cross-checks:** USGS Office of Water Quality Technical
Memorandum 2012.05; USGS National Field Manual, Chapter A6.6; USGS Alkalinity
Calculator methods

## 1. Trigger and scan verification

Appendix D page 275 states that at pH 7 bicarbonate represents roughly 80
percent of total alkalinity and carbonate represents the other 20 percent. It
then divides a reported 2.95 mEq/L bicarbonate value by 80 percent to estimate
3.69 mEq/L total alkalinity.

The scanned source does say this; it is not an OCR transcription error. However,
the statement conflicts with Table 28 on scanned page 277. The pH 7 row in that
table reports approximately:

- carbonate: 0 percent after table rounding;
- bicarbonate: 80.63 percent; and
- carbonic acid: 19.34 percent.

The table is a distribution of dissolved inorganic carbon species, not a
partition of total alkalinity. The page 275 prose misidentifies the carbonic-
acid share as carbonate and then treats a species fraction as an alkalinity
fraction.

## 2. Correct chemical distinction

For the simplified carbonate system, dissolved inorganic carbon is distributed
among carbonic acid/aqueous carbon dioxide (`H2CO3*`), bicarbonate (`HCO3-`),
and carbonate (`CO3^2-`). With hydrogen-ion activity represented here by `H`,
the idealized species fractions are:

```text
D = H^2 + K1*H + K1*K2

alpha_H2CO3* = H^2 / D
alpha_HCO3-  = K1*H / D
alpha_CO3--  = K1*K2 / D
```

USGS Technical Memorandum 2012.05 gives nominal dilute-freshwater constants at
25 degrees C of `K1 = 10^-6.35`, `K2 = 10^-10.33`, and `Kw = 10^-14.0` when
activity corrections can be neglected. At pH 7, those nominal values give an
independent audit result of approximately:

- `H2CO3*`: 18.285 percent;
- `HCO3-`: 81.677 percent; and
- `CO3^2-`: 0.038 percent.

The numerical percentages differ somewhat from Table 28 because species
fractions depend on the selected equilibrium constants and conditions. Both
calculations nevertheless show the same important identity: the non-
bicarbonate share near pH 7 is overwhelmingly carbonic acid/aqueous carbon
dioxide, not carbonate.

Species fractions are not alkalinity fractions. In the same simplified system,
carbonate alkalinity is:

```text
TA = [HCO3-] + 2*[CO3^2-] + [OH-] - [H+]
```

Other proton-accepting species must be included when materially present.
`H2CO3*` is part of dissolved inorganic carbon but contributes no positive term
to this alkalinity expression.

Under the deliberately narrow assumptions of dilute freshwater at 25 degrees C,
unit activity coefficients, pH 7, and no material noncarbonate contributors, a
reported bicarbonate concentration of 2.95 mEq/L corresponds to approximately
2.953 mEq/L total alkalinity, not 3.69 mEq/L. This is a source-audit calculation,
not a general conversion rule or an implemented Engine capability.

## 3. Authoritative-method constraints

USGS National Field Manual Chapter A6.6 calculates bicarbonate and carbonate
from measured alkalinity or ANC plus pH only under explicit assumptions. It
warns that other titratable constituents can invalidate the simplified result
and recommends a full geochemical model such as PHREEQC when they matter.

USGS Technical Memorandum 2012.05 further documents temperature-dependent
dissociation constants, activity corrections, hydroxide, and noncarbonate
alkalinity limitations. The USGS Alkalinity Calculator uses sample temperature
and ionic-strength information in its equilibrium treatment.

Authoritative references:

- USGS Office of Water Quality Technical Memorandum 2012.05, “Replacement of
  the Simple Speciation Method for Computation of Carbonate and Bicarbonate
  Concentrations from Alkalinity Titrations”:
  https://water.usgs.gov/water-resources/memos/memo.php?id=2098
- Rounds and Wilde, USGS National Field Manual, Chapter A6.6, “Alkalinity and
  Acid Neutralizing Capacity,” DOI `10.3133/twri09A6.6`:
  https://pubs.usgs.gov/publication/twri09A6.6
- USGS Alkalinity Calculator methods:
  https://or.water.usgs.gov/alk/methods.html

## 4. Project implications

1. Do not use the Appendix D page 275 calculation to derive total alkalinity
   from reported bicarbonate.
2. Do not treat a dissolved-inorganic-carbon species fraction as an alkalinity
   fraction.
3. Do not silently convert total alkalinity, bicarbonate, or carbonate into one
   another.
4. Any future carbonate-speciation result must be derived, model-versioned, and
   separate from reported measurements.
5. A future model must define its required chemical state, temperature,
   activity/ionic-strength treatment, equilibrium constants, included
   alkalinity contributors, assumptions, and valid range.
6. Charge balance remains a diagnostic and must not repair a source profile by
   inventing or altering reported values.

These rules reinforce the current 0.5 conservative-equivalent alkalinity model:
it carries total alkalinity on an equivalent basis but does not calculate
carbonate speciation or working-water pH.
