"""Conversions for explicitly reported alkalinity species and reporting bases.

These helpers are intentionally narrow. They convert the *reporting basis* of a
result that the source has already identified as a particular carbonate species.
They do not estimate carbonate speciation from total alkalinity, pH, or other
water properties.

That distinction matters for source fidelity: a reported bicarbonate result may
be normalized to the engine's bicarbonate concentration field, but a total
alkalinity result must remain total alkalinity unless a separate, documented
chemical model is deliberately used to derive species concentrations.
"""

from pint import Quantity

# USGS PHREEQC documentation uses approximately 50.04 g/eq for alkalinity
# reported "as CaCO3". Its PHREEQC FAQ gives 61.0173 g/eq for alkalinity
# reported "as HCO3". Bicarbonate carries one equivalent per mole, so the
# ratio of these equivalent masses converts the same number of equivalents
# between the two mass-reporting bases.
#
# Sources:
# - USGS PHREEQC SOLUTION documentation: CaCO3 equivalent mass ~50.04 g/eq
# - USGS PHREEQC FAQ, question 184: HCO3 equivalent mass 61.0173 g/eq
_CACO3_EQUIVALENT_MASS_G_PER_EQ = 50.04
_BICARBONATE_EQUIVALENT_MASS_G_PER_EQ = 61.0173


def bicarbonate_from_bicarbonate_alkalinity_as_caco3(
    value: Quantity,
) -> Quantity:
    """Convert bicarbonate alkalinity from a CaCO3 basis to mg/L HCO3.

    Use this only when the source explicitly identifies the reported result as
    *bicarbonate alkalinity* (or otherwise explicitly identifies bicarbonate)
    but expresses that result in mass-per-volume "as CaCO3".

    Do not pass total alkalinity to this function merely because bicarbonate is
    often the dominant contributor to alkalinity. Total alkalinity can contain
    contributions from carbonate, hydroxide, and other acid-neutralizing
    species, so converting total alkalinity directly to bicarbonate would be a
    chemical inference rather than a reporting-basis normalization.

    The conversion preserves equivalents:

        mg/L HCO3 =
            mg/L as CaCO3 * (61.0173 g/eq HCO3 / 50.04 g/eq CaCO3)

    The returned quantity is normalized to milligrams per liter.
    """
    try:
        concentration = value.to("milligram / liter")
    except Exception as exc:
        raise ValueError(
            "Bicarbonate alkalinity must be convertible to mass per volume."
        ) from exc

    if concentration.magnitude < 0:
        raise ValueError("Bicarbonate alkalinity cannot be negative.")

    conversion_factor = (
        _BICARBONATE_EQUIVALENT_MASS_G_PER_EQ / _CACO3_EQUIVALENT_MASS_G_PER_EQ
    )
    return concentration * conversion_factor
