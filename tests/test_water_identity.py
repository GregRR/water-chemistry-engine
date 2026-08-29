import pytest

from water_chemistry_engine.water_identity import (
    PhysicalSourceType,
    PhysicalWaterSource,
    WaterIdentity,
    WaterType,
)


def test_municipal_water_identity() -> None:
    identity = WaterIdentity(
        provider="City of Example Water Department",
        water_type=WaterType.MUNICIPAL_WATER,
    )

    assert identity.provider == "City of Example Water Department"
    assert identity.water_type is WaterType.MUNICIPAL_WATER
    assert identity.brand is None
    assert identity.product_name is None
    assert identity.physical_sources == ()


def test_bottled_water_identity_preserves_brand_and_product() -> None:
    identity = WaterIdentity(
        provider="Example Bottling Company",
        brand="Example Springs",
        product_name="Natural Spring Water",
        water_type=WaterType.SPRING_WATER,
    )

    assert identity.provider == "Example Bottling Company"
    assert identity.brand == "Example Springs"
    assert identity.product_name == "Natural Spring Water"
    assert identity.water_type is WaterType.SPRING_WATER


def test_identity_supports_multiple_physical_sources() -> None:
    reservoir = PhysicalWaterSource(
        source_type=PhysicalSourceType.RESERVOIR,
        name="Example Reservoir",
        location="Example County, California",
    )
    well = PhysicalWaterSource(
        source_type=PhysicalSourceType.WELL,
        name="Well 12",
        location="Example City, California",
    )

    identity = WaterIdentity(
        provider="Example Water Utility",
        water_type=WaterType.MUNICIPAL_WATER,
        physical_sources=(reservoir, well),
    )

    assert identity.physical_sources == (reservoir, well)


def test_physical_source_does_not_require_invented_name() -> None:
    source = PhysicalWaterSource(
        source_type=PhysicalSourceType.MUNICIPAL_SYSTEM,
    )

    assert source.name is None
    assert source.location is None


def test_identity_requires_provider() -> None:
    with pytest.raises(
        ValueError,
        match="provider cannot be empty",
    ):
        WaterIdentity(provider="   ")


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("brand", {"brand": "   "}),
        ("product_name", {"product_name": "   "}),
    ],
)
def test_identity_rejects_empty_optional_text(
    field: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field} cannot be empty",
    ):
        WaterIdentity(
            provider="Example Water Company",
            **kwargs,
        )


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        ("name", {"name": "   "}),
        ("location", {"location": "   "}),
    ],
)
def test_physical_source_rejects_empty_optional_text(
    field: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field} cannot be empty",
    ):
        PhysicalWaterSource(
            source_type=PhysicalSourceType.SPRING,
            **kwargs,
        )
