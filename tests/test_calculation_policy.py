from water_chemistry_engine.calculation_policy import (
    ION_CALCULATION_CAPABILITIES,
    capabilities_for,
)
from water_chemistry_engine.ions import Ion


def test_every_ion_has_an_explicit_calculation_policy() -> None:
    assert set(ION_CALCULATION_CAPABILITIES) == set(Ion)


def test_carbonate_species_are_preserved_but_not_optimizer_supported() -> None:
    for ion in (Ion.BICARBONATE, Ion.CARBONATE):
        capabilities = capabilities_for(ion)

        assert capabilities.reported_source
        assert capabilities.linear_blend
        assert capabilities.manual_treatment_contribution
        assert not capabilities.ordinary_target_comparison
        assert not capabilities.optimizer_target
        assert not capabilities.optimizer_material_contribution
        assert not capabilities.equilibrium_speciation


def test_supported_conservative_ion_capabilities_remain_unchanged() -> None:
    capabilities = capabilities_for(Ion.CHLORIDE)

    assert capabilities.reported_source
    assert capabilities.linear_blend
    assert capabilities.manual_treatment_contribution
    assert capabilities.ordinary_target_comparison
    assert capabilities.optimizer_target
    assert capabilities.optimizer_material_contribution
