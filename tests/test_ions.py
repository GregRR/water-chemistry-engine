from water_chemistry_engine.ions import Ion


def test_ion_values_are_stable() -> None:
    assert Ion.CALCIUM == "calcium"
    assert Ion.SULFATE == "sulfate"
    assert Ion.BICARBONATE == "bicarbonate"


def test_ion_members_are_strings() -> None:
    assert isinstance(Ion.CALCIUM, str)
