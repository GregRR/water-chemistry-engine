import pytest
from fermunits import Q_

from water_chemistry_engine.comparison_policy import (
    TargetComparisonPolicy,
    TargetIonClosenessPolicy,
)
from water_chemistry_engine.ions import Ion


def _calcium_policy() -> TargetIonClosenessPolicy:
    return TargetIonClosenessPolicy.mg_per_liter(
        Ion.CALCIUM,
        maximum_below_deviation=5.0,
        maximum_above_deviation=10.0,
    )


def test_closeness_policy_preserves_asymmetric_absolute_thresholds() -> None:
    policy = _calcium_policy()

    assert policy.maximum_below_deviation == Q_(5.0, "milligram / liter")
    assert policy.maximum_above_deviation == Q_(10.0, "milligram / liter")


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("maximum_below_deviation", Q_(-1.0, "mg/L"), "cannot be negative"),
        ("maximum_above_deviation", Q_(float("nan"), "mg/L"), "must be finite"),
        ("maximum_below_deviation", Q_(float("inf"), "mg/L"), "must be finite"),
        (
            "maximum_above_deviation",
            Q_(1.0, "gram"),
            "convertible to mass per volume",
        ),
    ],
)
def test_closeness_policy_rejects_invalid_thresholds(
    field: str,
    value: object,
    message: str,
) -> None:
    values = {
        "maximum_below_deviation": Q_(1.0, "mg/L"),
        "maximum_above_deviation": Q_(1.0, "mg/L"),
    }
    values[field] = value

    with pytest.raises(ValueError, match=message):
        TargetIonClosenessPolicy(ion=Ion.CALCIUM, **values)  # type: ignore[arg-type]


def test_closeness_policy_rejects_raw_ion_string() -> None:
    with pytest.raises(TypeError, match="must use Ion"):
        TargetIonClosenessPolicy.mg_per_liter(
            "calcium",  # type: ignore[arg-type]
            maximum_below_deviation=1.0,
            maximum_above_deviation=1.0,
        )


def test_comparison_policy_returns_ion_policy() -> None:
    calcium = _calcium_policy()
    policy = TargetComparisonPolicy(
        key="example-operational-bands",
        version="1",
        description="Example caller-defined absolute comparison bands.",
        ion_policies=(calcium,),
    )

    assert policy.policy_for(Ion.CALCIUM) is calcium
    assert policy.policy_for(Ion.SULFATE) is None


@pytest.mark.parametrize("field", ["key", "version", "description"])
def test_comparison_policy_rejects_empty_identity_or_description(field: str) -> None:
    values = {
        "key": "example",
        "version": "1",
        "description": "Example policy.",
    }
    values[field] = "   "

    with pytest.raises(ValueError, match=rf"{field} cannot be empty"):
        TargetComparisonPolicy(ion_policies=(_calcium_policy(),), **values)


def test_comparison_policy_requires_an_ion_policy() -> None:
    with pytest.raises(ValueError, match="at least one ion policy"):
        TargetComparisonPolicy(
            key="empty",
            version="1",
            description="Invalid empty policy.",
            ion_policies=(),
        )


def test_comparison_policy_rejects_duplicate_ions() -> None:
    with pytest.raises(ValueError, match="duplicate ion policies"):
        TargetComparisonPolicy(
            key="duplicate",
            version="1",
            description="Invalid duplicate policy.",
            ion_policies=(_calcium_policy(), _calcium_policy()),
        )


def test_comparison_policy_rejects_wrong_policy_type() -> None:
    with pytest.raises(TypeError, match="TargetIonClosenessPolicy"):
        TargetComparisonPolicy(
            key="wrong-type",
            version="1",
            description="Invalid policy member.",
            ion_policies=("calcium",),  # type: ignore[arg-type]
        )
