import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from fermunits import Q_
from water_treatment_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
)
from water_treatment_engine.ions import Ion
from water_treatment_engine.profiles import SourceWaterProfile
from water_treatment_engine.reported_properties import (
    Alkalinity,
    Conductivity,
    ReportedPH,
    ReportingBasis,
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

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORT_FIXTURE_ROOT = REPO_ROOT / "test-vectors" / "water" / "reports"
FIXTURE_PATHS = tuple(sorted(REPORT_FIXTURE_ROOT.rglob("*.json")))

type JsonObject = dict[str, Any]


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


def _load_observation_period(
    data: Mapping[str, Any] | None,
) -> ObservationPeriod | None:
    if data is None:
        return None
    return ObservationPeriod(
        start=date.fromisoformat(data["start"]),
        end=date.fromisoformat(data["end"]),
    )


def _load_result_context(
    data: Mapping[str, Any] | None,
    *,
    observation_period: ObservationPeriod | None,
) -> ReportedResultContext | None:
    if data is None:
        return None
    return ReportedResultContext(
        observed_on=_parse_date(data.get("observed_on")),
        observation_period=(
            _load_observation_period(data.get("observation_period"))
            if data.get("observation_period") is not None
            else observation_period
        ),
        coverage=(
            ResultCoverage(data["coverage"])
            if data.get("coverage") is not None
            else None
        ),
        water_stage=(
            WaterStage(data["water_stage"])
            if data.get("water_stage") is not None
            else None
        ),
        sample_location=data.get("sample_location"),
    )


def _load_source_document(data: Mapping[str, Any]) -> SourceDocumentMetadata:
    return SourceDocumentMetadata(
        publisher=data["publisher"],
        analysis_provider=data.get("analysis_provider"),
        title=data.get("title"),
        publication_date=_parse_date(data.get("publication_date")),
        source_url=data.get("source_url"),
        retrieved_on=_parse_date(data.get("retrieved_on")),
        page_reference=data.get("page_reference"),
        notes=data.get("notes"),
    )


def _load_identity(data: Mapping[str, Any] | None) -> WaterIdentity | None:
    if data is None:
        return None

    physical_sources = tuple(
        PhysicalWaterSource(
            source_type=PhysicalSourceType(item["source_type"]),
            name=item.get("name"),
            location=item.get("location"),
        )
        for item in data.get("physical_sources", ())
    )

    return WaterIdentity(
        provider=data["provider"],
        brand=data.get("brand"),
        product_name=data.get("product_name"),
        water_type=(
            WaterType(data["water_type"])
            if data.get("water_type") is not None
            else None
        ),
        physical_sources=physical_sources,
    )


def _load_concentration(
    ion_name: str,
    data: Mapping[str, Any],
    *,
    result_context: ReportedResultContext | None,
) -> (
    IonConcentration
    | IonConcentrationRange
    | IonConcentrationUpperBound
    | IonConcentrationLowerBound
    | IonConcentrationNotDetected
):
    ion = Ion(ion_name)
    unit = data.get("unit", "milligram / liter")
    form = data["form"]

    if form == "exact":
        return IonConcentration(
            ion=ion,
            value=Q_(data["value"], unit),
            result_context=result_context,
        )

    if form == "range":
        return IonConcentrationRange(
            ion=ion,
            minimum=ExactConcentrationEndpoint(Q_(data["minimum"], unit)),
            maximum=ExactConcentrationEndpoint(Q_(data["maximum"], unit)),
            reported_average=(
                Q_(data["reported_average"], unit)
                if data.get("reported_average") is not None
                else None
            ),
            result_context=result_context,
        )

    if form == "upper_bound":
        return IonConcentrationUpperBound(
            ion=ion,
            maximum=Q_(data["maximum"], unit),
            result_context=result_context,
        )

    if form == "lower_bound":
        return IonConcentrationLowerBound(
            ion=ion,
            minimum=Q_(data["minimum"], unit),
            result_context=result_context,
        )

    if form == "not_detected":
        return IonConcentrationNotDetected(
            ion=ion,
            detection_limit=(
                Q_(data["detection_limit"], unit)
                if data.get("detection_limit") is not None
                else None
            ),
            result_context=result_context,
        )

    raise ValueError(f"Unsupported concentration result form: {form}")


def _load_ph(
    data: Mapping[str, Any] | None,
    *,
    result_context: ReportedResultContext | None,
) -> ReportedPH | None:
    if data is None:
        return None

    form = data["form"]
    if form == "exact":
        return ReportedPH(
            value=data["value"],
            result_context=result_context,
        )
    if form == "range":
        return ReportedPH(
            minimum=data["minimum"],
            maximum=data["maximum"],
            reported_average=data.get("reported_average"),
            result_context=result_context,
        )
    if form == "average":
        return ReportedPH(
            reported_average=data["reported_average"],
            result_context=result_context,
        )

    raise ValueError(f"Unsupported pH result form: {form}")


def _quantity_or_none(
    data: Mapping[str, Any],
    key: str,
    unit: str,
):
    value = data.get(key)
    if value is None:
        return None
    return Q_(value, unit)


def _load_property(
    name: str,
    data: Mapping[str, Any],
    *,
    result_context: ReportedResultContext | None,
) -> Alkalinity | TotalHardness | TotalDissolvedSolids | Conductivity:
    unit = data["unit"]
    kwargs = {
        "value": _quantity_or_none(data, "value", unit),
        "minimum": _quantity_or_none(data, "minimum", unit),
        "maximum": _quantity_or_none(data, "maximum", unit),
        "reported_average": _quantity_or_none(
            data,
            "reported_average",
            unit,
        ),
        "result_context": result_context,
    }

    if name == "alkalinity":
        return Alkalinity(**kwargs, basis=ReportingBasis(data["reporting_basis"]))
    if name == "total_hardness":
        return TotalHardness(**kwargs, basis=ReportingBasis(data["reporting_basis"]))
    if name == "total_dissolved_solids":
        return TotalDissolvedSolids(**kwargs)
    if name == "conductivity":
        return Conductivity(
            **kwargs,
            reference_temperature_celsius=data.get("reference_temperature_celsius"),
        )

    raise ValueError(f"Unsupported reported property: {name}")


def _load_profile(
    data: Mapping[str, Any],
    *,
    source_document: SourceDocumentMetadata,
) -> SourceWaterProfile:
    observation_period = _load_observation_period(data.get("observation_period"))
    result_context = _load_result_context(
        data.get("result_context"),
        observation_period=observation_period,
    )

    concentrations = tuple(
        _load_concentration(
            ion_name,
            concentration,
            result_context=result_context,
        )
        for ion_name, concentration in data.get("concentrations", {}).items()
    )

    properties = data.get("properties", {})

    return SourceWaterProfile(
        name=data["name"],
        concentrations=concentrations,
        ph=_load_ph(data.get("ph"), result_context=result_context),
        observed_on=_parse_date(data.get("observed_on")),
        observation_period=observation_period,
        source_document=source_document,
        identity=_load_identity(data.get("identity")),
        alkalinity=(
            _load_property(
                "alkalinity",
                properties["alkalinity"],
                result_context=result_context,
            )
            if "alkalinity" in properties
            else None
        ),
        total_hardness=(
            _load_property(
                "total_hardness",
                properties["total_hardness"],
                result_context=result_context,
            )
            if "total_hardness" in properties
            else None
        ),
        total_dissolved_solids=(
            _load_property(
                "total_dissolved_solids",
                properties["total_dissolved_solids"],
                result_context=result_context,
            )
            if "total_dissolved_solids" in properties
            else None
        ),
        conductivity=(
            _load_property(
                "conductivity",
                properties["conductivity"],
                result_context=result_context,
            )
            if "conductivity" in properties
            else None
        ),
    )


def _load_fixture(path: Path) -> tuple[JsonObject, tuple[SourceWaterProfile, ...]]:
    data: JsonObject = json.loads(path.read_text())
    if data.get("fixture_format") != "water-treatment-real-report-v1":
        raise ValueError(f"Unsupported real-report fixture format in {path}")

    source_document = _load_source_document(data["source_document"])
    profiles = tuple(
        _load_profile(profile, source_document=source_document)
        for profile in data["profiles"]
    )
    return data, profiles


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_real_report_fixture_loads_into_source_water_profiles(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    assert profiles
    assert len(profiles) == len(data["profiles"])
    assert all(isinstance(profile, SourceWaterProfile) for profile in profiles)


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_real_report_fixture_preserves_reported_values(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        assert profile.name == raw_profile["name"]

        for ion_name, raw_result in raw_profile.get("concentrations", {}).items():
            result = profile.concentration_for(Ion(ion_name))
            assert result is not None

            if raw_result["form"] == "range":
                assert isinstance(result, IonConcentrationRange)
                unit = raw_result["unit"]
                assert result.minimum.value.to(unit).magnitude == pytest.approx(
                    raw_result["minimum"]
                )
                assert result.maximum.value.to(unit).magnitude == pytest.approx(
                    raw_result["maximum"]
                )
                if raw_result.get("reported_average") is not None:
                    assert result.reported_average is not None
                    assert result.reported_average.to(unit).magnitude == pytest.approx(
                        raw_result["reported_average"]
                    )

        raw_ph = raw_profile.get("ph")
        if raw_ph is not None:
            assert profile.ph is not None
            if raw_ph.get("reported_average") is not None:
                assert profile.ph.reported_average == pytest.approx(
                    raw_ph["reported_average"]
                )
                assert profile.ph.calculation_value == pytest.approx(
                    raw_ph["reported_average"]
                )


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_real_report_fixture_preserves_identity_document_and_context(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        assert profile.source_document is not None
        assert profile.source_document.publisher == data["source_document"]["publisher"]

        raw_identity = raw_profile.get("identity")
        if raw_identity is not None:
            assert profile.identity is not None
            assert profile.identity.provider == raw_identity["provider"]
            assert tuple(
                source.name for source in profile.identity.physical_sources
            ) == tuple(
                source.get("name")
                for source in raw_identity.get("physical_sources", ())
            )

        raw_context = raw_profile.get("result_context")
        if raw_context is not None and profile.concentrations:
            result_context = profile.concentrations[0].result_context
            assert result_context is not None
            assert result_context.coverage is ResultCoverage(raw_context["coverage"])
            assert result_context.water_stage is WaterStage(raw_context["water_stage"])
            assert result_context.sample_location == raw_context.get("sample_location")


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_alkalinity_does_not_create_unreported_bicarbonate(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        if "alkalinity" in raw_profile.get(
            "properties", {}
        ) and "bicarbonate" not in raw_profile.get("concentrations", {}):
            assert profile.alkalinity is not None
            assert profile.concentration_for(Ion.BICARBONATE) is None


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_conductivity_reference_temperature_is_not_invented(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        raw_conductivity = raw_profile.get("properties", {}).get("conductivity")
        if raw_conductivity is None:
            continue

        assert profile.conductivity is not None
        assert (
            profile.conductivity.reference_temperature_celsius
            == raw_conductivity.get("reference_temperature_celsius")
        )
