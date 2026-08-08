from dataclasses import dataclass
from enum import StrEnum


def _validate_optional_text(value: str | None, field_name: str) -> None:
    if value is not None and not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")


class WaterType(StrEnum):
    """High-level classification explicitly associated with a water."""

    MUNICIPAL_WATER = "municipal_water"
    SPRING_WATER = "spring_water"
    PURIFIED_WATER = "purified_water"
    DISTILLED_WATER = "distilled_water"
    ARTESIAN_WATER = "artesian_water"
    WELL_WATER = "well_water"
    ALKALINE_WATER = "alkaline_water"
    MINERAL_WATER = "mineral_water"
    REVERSE_OSMOSIS_WATER = "reverse_osmosis_water"
    OTHER = "other"


class PhysicalSourceType(StrEnum):
    """Physical origin from which water is drawn."""

    SPRING = "spring"
    WELL = "well"
    ARTESIAN_WELL = "artesian_well"
    RESERVOIR = "reservoir"
    RIVER = "river"
    LAKE = "lake"
    GROUNDWATER = "groundwater"
    SURFACE_WATER = "surface_water"
    MUNICIPAL_SYSTEM = "municipal_system"
    MIXED_SOURCES = "mixed_sources"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class PhysicalWaterSource:
    """A physical source contributing water to a reported profile."""

    source_type: PhysicalSourceType
    name: str | None = None
    location: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_text(self.name, "name")
        _validate_optional_text(self.location, "location")


@dataclass(frozen=True, slots=True)
class WaterIdentity:
    """Identity of the supplied or produced water represented by a profile."""

    provider: str
    brand: str | None = None
    product_name: str | None = None
    water_type: WaterType | None = None
    physical_sources: tuple[PhysicalWaterSource, ...] = ()

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider cannot be empty.")

        _validate_optional_text(self.brand, "brand")
        _validate_optional_text(
            self.product_name,
            "product_name",
        )
