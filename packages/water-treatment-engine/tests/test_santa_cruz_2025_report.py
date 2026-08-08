from datetime import date

from fermunits import Q_
from water_treatment_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentrationRange,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.profiles import SourceWaterProfile
from water_treatment_engine.reported_properties import (
    Alkalinity,
    Conductivity,
    ReportedPH,
    TotalDissolvedSolids,
    TotalHardness,
)
from water_treatment_engine.reporting_context import (
    ObservationPeriod,
    ReportedResultContext,
    ResultCoverage,
    WaterStage,
)
from water_treatment_engine.source_document import SourceDocumentMetadata
from water_treatment_engine.water_identity import (
    PhysicalSourceType,
    PhysicalWaterSource,
    WaterIdentity,
    WaterType,
)

REPORT_PERIOD = ObservationPeriod(
    start=date(2025, 1, 1),
    end=date(2025, 12, 31),
)

SOURCE_DOCUMENT = SourceDocumentMetadata(
    publisher="City of Santa Cruz Water Department",
    analysis_provider="City of Santa Cruz Water Department Water Quality Laboratory",
    title="2025 Annual Water Quality Report",
    source_url=(
        "https://www.santacruzca.gov/files/assets/city/v/1/wt/documents/"
        "water-quality-reports/scwd-wqr-2025.pdf"
    ),
    retrieved_on=date(2026, 8, 8),
    page_reference="Pages 15-16",
    notes=(
        "Treatment-plant averages and ranges reported for calendar year 2025. "
        "Regulatory limits are not modeled as source-water chemistry."
    ),
)


def _context(sample_location: str) -> ReportedResultContext:
    return ReportedResultContext(
        observation_period=REPORT_PERIOD,
        coverage=ResultCoverage.OBSERVATION_PERIOD_SUMMARY,
        water_stage=WaterStage.TREATMENT_PLANT_OUTPUT,
        sample_location=sample_location,
    )


def _ion_range(
    ion: Ion,
    *,
    average: float,
    minimum: float,
    maximum: float,
    context: ReportedResultContext,
) -> IonConcentrationRange:
    return IonConcentrationRange(
        ion=ion,
        minimum=ExactConcentrationEndpoint.mg_per_liter(minimum),
        maximum=ExactConcentrationEndpoint.mg_per_liter(maximum),
        reported_average=Q_(average, "milligram / liter"),
        result_context=context,
    )


def _property_range(
    cls: type[Alkalinity | TotalHardness | TotalDissolvedSolids | Conductivity],
    *,
    average: float,
    minimum: float,
    maximum: float,
    unit: str,
    context: ReportedResultContext,
) -> Alkalinity | TotalHardness | TotalDissolvedSolids | Conductivity:
    return cls(
        minimum=Q_(minimum, unit),
        maximum=Q_(maximum, unit),
        reported_average=Q_(average, unit),
        result_context=context,
    )


def _profile(
    *,
    name: str,
    identity: WaterIdentity,
    calcium: tuple[float, float, float],
    magnesium: tuple[float, float, float],
    sodium: tuple[float, float, float],
    potassium: tuple[float, float, float],
    chloride: tuple[float, float, float],
    sulfate: tuple[float, float, float],
    alkalinity: tuple[float, float, float],
    hardness: tuple[float, float, float],
    tds: tuple[float, float, float],
    conductivity: tuple[float, float, float],
    ph: tuple[float, float, float],
) -> SourceWaterProfile:
    context = _context(name)

    concentrations = tuple(
        _ion_range(
            ion,
            average=values[0],
            minimum=values[1],
            maximum=values[2],
            context=context,
        )
        for ion, values in (
            (Ion.CALCIUM, calcium),
            (Ion.MAGNESIUM, magnesium),
            (Ion.SODIUM, sodium),
            (Ion.POTASSIUM, potassium),
            (Ion.CHLORIDE, chloride),
            (Ion.SULFATE, sulfate),
        )
    )

    return SourceWaterProfile(
        name=f"Santa Cruz 2025 - {name}",
        concentrations=concentrations,
        ph=ReportedPH(
            minimum=ph[1],
            maximum=ph[2],
            reported_average=ph[0],
            result_context=context,
        ),
        observation_period=REPORT_PERIOD,
        source_document=SOURCE_DOCUMENT,
        identity=identity,
        alkalinity=_property_range(
            Alkalinity,
            average=alkalinity[0],
            minimum=alkalinity[1],
            maximum=alkalinity[2],
            unit="milligram / liter",
            context=context,
        ),
        total_hardness=_property_range(
            TotalHardness,
            average=hardness[0],
            minimum=hardness[1],
            maximum=hardness[2],
            unit="milligram / liter",
            context=context,
        ),
        total_dissolved_solids=_property_range(
            TotalDissolvedSolids,
            average=tds[0],
            minimum=tds[1],
            maximum=tds[2],
            unit="milligram / liter",
            context=context,
        ),
        conductivity=_property_range(
            Conductivity,
            average=conductivity[0],
            minimum=conductivity[1],
            maximum=conductivity[2],
            unit="microsiemens / centimeter",
            context=context,
        ),
    )


GRAHAM_HILL = _profile(
    name="Graham Hill Water Treatment Plant",
    identity=WaterIdentity(
        provider="City of Santa Cruz Water Department",
        water_type=WaterType.MUNICIPAL_WATER,
        physical_sources=(
            PhysicalWaterSource(
                source_type=PhysicalSourceType.RIVER,
                name="San Lorenzo River",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.WELL,
                name="Tait Wells",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.RESERVOIR,
                name="Loch Lomond Reservoir",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.SPRING,
                name="Liddell Spring",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.SURFACE_WATER,
                name="Laguna Creek",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.SURFACE_WATER,
                name="Majors Creek",
            ),
        ),
    ),
    calcium=(51.0, 50.0, 53.0),
    magnesium=(9.3, 9.1, 9.7),
    sodium=(22.0, 20.0, 23.0),
    potassium=(2.2, 1.9, 2.4),
    chloride=(22.0, 19.0, 25.0),
    sulfate=(72.0, 63.0, 75.0),
    alkalinity=(108.0, 86.0, 118.0),
    hardness=(160.0, 136.0, 192.0),
    tds=(262.0, 260.0, 270.0),
    conductivity=(436.0, 375.0, 455.0),
    ph=(7.2, 7.0, 7.4),
)

BELTZ = _profile(
    name="Beltz Water Treatment Plant",
    identity=WaterIdentity(
        provider="City of Santa Cruz Water Department",
        water_type=WaterType.MUNICIPAL_WATER,
        physical_sources=(
            PhysicalWaterSource(
                source_type=PhysicalSourceType.WELL,
                name="Beltz Well 8",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.WELL,
                name="Beltz Well 9",
            ),
            PhysicalWaterSource(
                source_type=PhysicalSourceType.WELL,
                name="Beltz Well 10",
            ),
        ),
    ),
    calcium=(77.0, 73.0, 80.0),
    magnesium=(19.0, 18.0, 20.0),
    sodium=(50.0, 47.0, 52.0),
    potassium=(7.0, 6.3, 7.5),
    chloride=(57.0, 51.0, 65.0),
    sulfate=(152.0, 140.0, 160.0),
    alkalinity=(149.0, 106.0, 160.0),
    hardness=(258.0, 200.0, 272.0),
    tds=(508.0, 490.0, 530.0),
    conductivity=(744.0, 605.0, 785.0),
    ph=(8.0, 7.9, 8.4),
)

BELTZ_12 = _profile(
    name="Beltz 12 Water Treatment Plant",
    identity=WaterIdentity(
        provider="City of Santa Cruz Water Department",
        water_type=WaterType.MUNICIPAL_WATER,
        physical_sources=(
            PhysicalWaterSource(
                source_type=PhysicalSourceType.WELL,
                name="Beltz Well 12",
            ),
        ),
    ),
    calcium=(68.0, 66.0, 70.0),
    magnesium=(25.0, 20.0, 28.0),
    sodium=(32.0, 30.0, 35.0),
    potassium=(4.1, 3.7, 4.3),
    chloride=(40.0, 38.0, 43.0),
    sulfate=(91.0, 89.0, 93.0),
    alkalinity=(182.0, 164.0, 202.0),
    hardness=(265.0, 236.0, 288.0),
    tds=(435.0, 400.0, 460.0),
    conductivity=(660.0, 615.0, 690.0),
    ph=(7.4, 7.2, 7.5),
)


def test_santa_cruz_profiles_preserve_reported_average_and_range() -> None:
    calcium = GRAHAM_HILL.concentration_for(Ion.CALCIUM)

    assert isinstance(calcium, IonConcentrationRange)
    assert calcium.reported_average is not None
    assert calcium.reported_average.to("milligram / liter").magnitude == 51.0
    assert calcium.minimum.value.to("milligram / liter").magnitude == 50.0
    assert calcium.maximum.value.to("milligram / liter").magnitude == 53.0


def test_santa_cruz_profiles_do_not_invent_bicarbonate() -> None:
    for profile in (GRAHAM_HILL, BELTZ, BELTZ_12):
        assert profile.concentration_for(Ion.BICARBONATE) is None
        assert profile.alkalinity is not None


def test_santa_cruz_ph_uses_reported_average_not_range_midpoint() -> None:
    assert BELTZ.ph is not None

    assert BELTZ.ph.reported_average == 8.0
    assert BELTZ.ph.minimum == 7.9
    assert BELTZ.ph.maximum == 8.4
    assert BELTZ.ph.calculation_value == 8.0


def test_santa_cruz_conductivity_does_not_invent_reference_temperature() -> None:
    for profile in (GRAHAM_HILL, BELTZ, BELTZ_12):
        assert profile.conductivity is not None
        assert profile.conductivity.reference_temperature_celsius is None


def test_santa_cruz_results_preserve_treatment_plant_context() -> None:
    sodium = BELTZ_12.concentration_for(Ion.SODIUM)

    assert isinstance(sodium, IonConcentrationRange)
    assert sodium.result_context is not None
    assert sodium.result_context.water_stage is WaterStage.TREATMENT_PLANT_OUTPUT
    assert sodium.result_context.sample_location == "Beltz 12 Water Treatment Plant"
    assert sodium.result_context.observation_period == REPORT_PERIOD


def test_santa_cruz_document_metadata_separates_publisher_and_analysis_provider() -> (
    None
):
    assert SOURCE_DOCUMENT.publisher == "City of Santa Cruz Water Department"
    assert (
        SOURCE_DOCUMENT.analysis_provider
        == "City of Santa Cruz Water Department Water Quality Laboratory"
    )


def test_santa_cruz_beltz_sources_preserve_well_identity() -> None:
    assert BELTZ.identity is not None
    assert tuple(source.name for source in BELTZ.identity.physical_sources) == (
        "Beltz Well 8",
        "Beltz Well 9",
        "Beltz Well 10",
    )

    assert BELTZ_12.identity is not None
    assert tuple(source.name for source in BELTZ_12.identity.physical_sources) == (
        "Beltz Well 12",
    )
