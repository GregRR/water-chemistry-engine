import json
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from typing import Any, TypeAlias

import pytest
from fermunits import Q_

from water_chemistry_engine.concentrations import (
    ExactConcentrationEndpoint,
    IonConcentration,
    IonConcentrationLowerBound,
    IonConcentrationNotDetected,
    IonConcentrationRange,
    IonConcentrationUpperBound,
    LowerBoundConcentrationEndpoint,
    NotDetectedConcentrationEndpoint,
    UpperBoundConcentrationEndpoint,
)
from water_chemistry_engine.ions import Ion
from water_chemistry_engine.profiles import SourceWaterProfile
from water_chemistry_engine.reported_disinfectants import (
    DisinfectantKind,
    ReportedDisinfectant,
)
from water_chemistry_engine.reported_properties import (
    Alkalinity,
    Conductivity,
    ReportedPH,
    ReportingBasis,
    TotalDissolvedSolids,
    TotalHardness,
)
from water_chemistry_engine.reported_statistics import (
    ReportedStatistic,
    ReportedStatisticKind,
)
from water_chemistry_engine.reporting_context import (
    ObservationPeriod,
    ReportedResultContext,
    ResultCoverage,
    WaterStage,
)
from water_chemistry_engine.source_document import SourceDocumentMetadata
from water_chemistry_engine.water_identity import (
    PhysicalSourceType,
    PhysicalWaterSource,
    WaterIdentity,
    WaterType,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_FIXTURE_ROOT = REPO_ROOT / "test-vectors" / "water" / "reports"
FIXTURE_PATHS = tuple(sorted(REPORT_FIXTURE_ROOT.rglob("*.json")))

JsonObject: TypeAlias = dict[str, Any]


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
    observation_period: ObservationPeriod | None = None,
    fallback: ReportedResultContext | None = None,
) -> ReportedResultContext | None:
    if data is None:
        return fallback

    observed_on = _parse_date(data.get("observed_on"))
    explicit_period = _load_observation_period(data.get("observation_period"))

    # A result-specific date is more precise than the profile's broad reporting
    # period.  Do not accidentally inherit both: ReportedResultContext correctly
    # treats a single observation date and an observation period as mutually
    # exclusive.  Other sampling context can still inherit from the profile.
    if "observation_period" in data:
        effective_period = explicit_period
    elif observed_on is not None:
        effective_period = None
    elif fallback is not None:
        effective_period = fallback.observation_period
    else:
        effective_period = observation_period

    return ReportedResultContext(
        observed_on=observed_on,
        observation_period=effective_period,
        coverage=(
            ResultCoverage(data["coverage"])
            if data.get("coverage") is not None
            else fallback.coverage
            if fallback is not None
            else None
        ),
        water_stage=(
            WaterStage(data["water_stage"])
            if data.get("water_stage") is not None
            else fallback.water_stage
            if fallback is not None
            else None
        ),
        sample_location=(
            data.get("sample_location")
            if "sample_location" in data
            else fallback.sample_location
            if fallback is not None
            else None
        ),
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


def _load_reported_statistic(
    data: Mapping[str, Any] | None,
) -> ReportedStatistic | None:
    if data is None:
        return None

    return ReportedStatistic(
        kind=ReportedStatisticKind(data["kind"]),
        percentile=data.get("percentile"),
        label=data.get("label"),
    )


def _load_range_endpoint(
    data: Any,
    *,
    unit: str,
) -> (
    ExactConcentrationEndpoint
    | UpperBoundConcentrationEndpoint
    | LowerBoundConcentrationEndpoint
    | NotDetectedConcentrationEndpoint
):
    if isinstance(data, (int, float)):
        return ExactConcentrationEndpoint(Q_(data, unit))
    if not isinstance(data, Mapping):
        raise TypeError(f"Unsupported concentration range endpoint: {data!r}")

    # Keep censoring exactly as the source reported it.  In particular, ND is
    # not zero, and a '<X' or '>X' endpoint is not silently converted to X.
    # Any future numeric substitution belongs in an explicit calculation policy,
    # not in fixture ingestion.
    form = data["form"]
    if form == "exact":
        return ExactConcentrationEndpoint(Q_(data["value"], unit))
    if form == "upper_bound":
        return UpperBoundConcentrationEndpoint(Q_(data["limit"], unit))
    if form == "lower_bound":
        return LowerBoundConcentrationEndpoint(Q_(data["limit"], unit))
    if form == "not_detected":
        return NotDetectedConcentrationEndpoint(
            detection_limit=(
                Q_(data["detection_limit"], unit)
                if data.get("detection_limit") is not None
                else None
            )
        )

    raise ValueError(f"Unsupported concentration range endpoint form: {form}")


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
    reported_statistic = _load_reported_statistic(data.get("reported_statistic"))
    effective_result_context = _load_result_context(
        data.get("result_context"),
        fallback=result_context,
    )

    if form in {"exact", "value"}:
        return IonConcentration(
            ion=ion,
            value=Q_(data["value"], unit),
            reported_statistic=reported_statistic,
            result_context=effective_result_context,
        )

    if form == "range":
        return IonConcentrationRange(
            ion=ion,
            minimum=_load_range_endpoint(data["minimum"], unit=unit),
            maximum=_load_range_endpoint(data["maximum"], unit=unit),
            reported_average=(
                Q_(data["reported_average"], unit)
                if data.get("reported_average") is not None
                else None
            ),
            reported_statistic=reported_statistic,
            result_context=effective_result_context,
        )

    if form == "upper_bound":
        return IonConcentrationUpperBound(
            ion=ion,
            maximum=Q_(data["maximum"], unit),
            reported_statistic=reported_statistic,
            result_context=effective_result_context,
        )

    if form == "lower_bound":
        return IonConcentrationLowerBound(
            ion=ion,
            minimum=Q_(data["minimum"], unit),
            reported_statistic=reported_statistic,
            result_context=effective_result_context,
        )

    if form == "not_detected":
        return IonConcentrationNotDetected(
            ion=ion,
            detection_limit=(
                Q_(data["detection_limit"], unit)
                if data.get("detection_limit") is not None
                else None
            ),
            reported_statistic=reported_statistic,
            result_context=effective_result_context,
        )

    raise ValueError(f"Unsupported concentration result form: {form}")


def _load_disinfectant(
    data: Mapping[str, Any],
    *,
    result_context: ReportedResultContext | None,
) -> ReportedDisinfectant:
    unit = data.get("unit", "milligram / liter")
    effective_result_context = _load_result_context(
        data.get("result_context"),
        fallback=result_context,
    )
    form = data["form"]

    kwargs = {
        "kind": DisinfectantKind(data["kind"]),
        "species_name": data.get("species_name"),
        "reported_label": data.get("reported_label"),
        "reporting_basis": data.get("reporting_basis"),
        "reported_statistic": _load_reported_statistic(data.get("reported_statistic")),
        "result_context": effective_result_context,
    }

    if form in {"exact", "value"}:
        return ReportedDisinfectant(
            **kwargs,
            value=Q_(data["value"], unit),
        )
    if form == "range":
        return ReportedDisinfectant(
            **kwargs,
            minimum=Q_(data["minimum"], unit),
            maximum=Q_(data["maximum"], unit),
            reported_average=(
                Q_(data["reported_average"], unit)
                if data.get("reported_average") is not None
                else None
            ),
        )
    if form == "average":
        return ReportedDisinfectant(
            **kwargs,
            reported_average=Q_(data["reported_average"], unit),
        )

    raise ValueError(f"Unsupported disinfectant result form: {form}")


def _load_ph(
    data: Mapping[str, Any] | None,
    *,
    result_context: ReportedResultContext | None,
) -> ReportedPH | None:
    if data is None:
        return None

    effective_result_context = _load_result_context(
        data.get("result_context"),
        fallback=result_context,
    )
    form = data["form"]
    if form == "exact":
        return ReportedPH(
            value=data["value"],
            result_context=effective_result_context,
        )
    if form == "range":
        return ReportedPH(
            minimum=data["minimum"],
            maximum=data["maximum"],
            reported_average=data.get("reported_average"),
            result_context=effective_result_context,
        )
    if form == "average":
        return ReportedPH(
            reported_average=data["reported_average"],
            result_context=effective_result_context,
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
    effective_result_context = _load_result_context(
        data.get("result_context"),
        fallback=result_context,
    )
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
        "result_context": effective_result_context,
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
    disinfectants = tuple(
        _load_disinfectant(
            disinfectant,
            result_context=result_context,
        )
        for disinfectant in data.get("disinfectants", ())
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
        disinfectants=disinfectants,
    )


def _load_fixture(path: Path) -> tuple[JsonObject, tuple[SourceWaterProfile, ...]]:
    data: JsonObject = json.loads(path.read_text())
    if data.get("fixture_format") != "water-chemistry-real-report-v1":
        raise ValueError(f"Unsupported real-report fixture format in {path}")

    source_document = _load_source_document(data["source_document"])
    profiles = tuple(
        _load_profile(profile, source_document=source_document)
        for profile in data["profiles"]
    )
    return data, profiles


def _assert_range_endpoint_matches(
    endpoint: Any,
    raw_endpoint: Any,
    *,
    unit: str,
) -> None:
    if isinstance(raw_endpoint, (int, float)):
        assert isinstance(endpoint, ExactConcentrationEndpoint)
        assert endpoint.value.to(unit).magnitude == pytest.approx(raw_endpoint)
        return

    assert isinstance(raw_endpoint, Mapping)
    form = raw_endpoint["form"]
    if form == "not_detected":
        assert isinstance(endpoint, NotDetectedConcentrationEndpoint)
        raw_limit = raw_endpoint.get("detection_limit")
        if raw_limit is None:
            assert endpoint.detection_limit is None
        else:
            assert endpoint.detection_limit is not None
            assert endpoint.detection_limit.to(unit).magnitude == pytest.approx(
                raw_limit
            )
        return
    if form == "upper_bound":
        assert isinstance(endpoint, UpperBoundConcentrationEndpoint)
        assert endpoint.limit.to(unit).magnitude == pytest.approx(raw_endpoint["limit"])
        return
    if form == "lower_bound":
        assert isinstance(endpoint, LowerBoundConcentrationEndpoint)
        assert endpoint.limit.to(unit).magnitude == pytest.approx(raw_endpoint["limit"])
        return
    if form == "exact":
        assert isinstance(endpoint, ExactConcentrationEndpoint)
        assert endpoint.value.to(unit).magnitude == pytest.approx(raw_endpoint["value"])
        return

    raise AssertionError(f"Unhandled fixture range endpoint form: {form}")


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

            if raw_result["form"] in {"exact", "value"}:
                assert isinstance(result, IonConcentration)
                unit = raw_result["unit"]
                assert result.value.to(unit).magnitude == pytest.approx(
                    raw_result["value"]
                )

            if raw_result["form"] == "range":
                assert isinstance(result, IonConcentrationRange)
                unit = raw_result["unit"]
                _assert_range_endpoint_matches(
                    result.minimum,
                    raw_result["minimum"],
                    unit=unit,
                )
                _assert_range_endpoint_matches(
                    result.maximum,
                    raw_result["maximum"],
                    unit=unit,
                )
                if raw_result.get("reported_average") is not None:
                    assert result.reported_average is not None
                    assert result.reported_average.to(unit).magnitude == pytest.approx(
                        raw_result["reported_average"]
                    )

        raw_ph = raw_profile.get("ph")
        if raw_ph is not None:
            assert profile.ph is not None
            if raw_ph["form"] == "range":
                assert profile.ph.minimum == pytest.approx(raw_ph["minimum"])
                assert profile.ph.maximum == pytest.approx(raw_ph["maximum"])
            if raw_ph.get("reported_average") is not None:
                assert profile.ph.reported_average == pytest.approx(
                    raw_ph["reported_average"]
                )
                assert profile.ph.calculation_value == pytest.approx(
                    raw_ph["reported_average"]
                )

        for property_name, raw_result in raw_profile.get("properties", {}).items():
            result = getattr(profile, property_name)
            assert result is not None
            unit = raw_result["unit"]

            for field in ("value", "minimum", "maximum", "reported_average"):
                raw_value = raw_result.get(field)
                if raw_value is None:
                    continue

                result_value = getattr(result, field)
                assert result_value is not None
                assert result_value.to(unit).magnitude == pytest.approx(raw_value)

            if raw_result.get("reporting_basis") is not None:
                assert result.basis is ReportingBasis(raw_result["reporting_basis"])

        for raw_result in raw_profile.get("disinfectants", ()):
            kind = DisinfectantKind(raw_result["kind"])
            result = profile.disinfectant_for(
                kind,
                species_name=raw_result.get("species_name"),
            )
            assert result is not None
            assert result.reported_label == raw_result.get("reported_label")
            assert result.reporting_basis == raw_result.get("reporting_basis")

            unit = raw_result["unit"]
            for field in ("value", "minimum", "maximum", "reported_average"):
                raw_value = raw_result.get(field)
                if raw_value is None:
                    continue

                result_value = getattr(result, field)
                assert result_value is not None
                assert result_value.to(unit).magnitude == pytest.approx(raw_value)


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_real_report_fixture_preserves_reported_statistics(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        for ion_name, raw_result in raw_profile.get("concentrations", {}).items():
            raw_statistic = raw_result.get("reported_statistic")
            if raw_statistic is None:
                continue

            result = profile.concentration_for(Ion(ion_name))
            assert result is not None
            assert result.reported_statistic is not None
            assert result.reported_statistic.kind is ReportedStatisticKind(
                raw_statistic["kind"]
            )
            assert result.reported_statistic.percentile == raw_statistic.get(
                "percentile"
            )
            assert result.reported_statistic.label == raw_statistic.get("label")

        for raw_result in raw_profile.get("disinfectants", ()):
            raw_statistic = raw_result.get("reported_statistic")
            if raw_statistic is None:
                continue

            result = profile.disinfectant_for(
                DisinfectantKind(raw_result["kind"]),
                species_name=raw_result.get("species_name"),
            )
            assert result is not None
            assert result.reported_statistic is not None
            assert result.reported_statistic.kind is ReportedStatisticKind(
                raw_statistic["kind"]
            )
            assert result.reported_statistic.percentile == raw_statistic.get(
                "percentile"
            )
            assert result.reported_statistic.label == raw_statistic.get("label")


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_qualified_ranges_do_not_invent_numeric_endpoints_or_midpoints(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        for ion_name, raw_result in raw_profile.get("concentrations", {}).items():
            if raw_result["form"] != "range":
                continue
            if not any(
                isinstance(raw_result[key], Mapping) for key in ("minimum", "maximum")
            ):
                continue

            result = profile.concentration_for(Ion(ion_name))
            assert isinstance(result, IonConcentrationRange)
            if raw_result.get("reported_average") is None:
                with pytest.raises(ValueError):
                    _ = result.calculation_value
            else:
                unit = raw_result["unit"]
                assert result.calculation_value.to(unit).magnitude == pytest.approx(
                    raw_result["reported_average"]
                )


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_range_only_ph_does_not_invent_a_representative_value(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        raw_ph = raw_profile.get("ph")
        if (
            raw_ph is None
            or raw_ph["form"] != "range"
            or raw_ph.get("reported_average") is not None
        ):
            continue

        assert profile.ph is not None
        with pytest.raises(ValueError):
            _ = profile.ph.calculation_value


@pytest.mark.parametrize(
    "fixture_path",
    FIXTURE_PATHS,
    ids=lambda path: str(path.relative_to(REPORT_FIXTURE_ROOT)),
)
def test_result_specific_context_overrides_profile_timing(
    fixture_path: Path,
) -> None:
    data, profiles = _load_fixture(fixture_path)

    for raw_profile, profile in zip(data["profiles"], profiles, strict=True):
        profile_context = raw_profile.get("result_context", {})
        for ion_name, raw_result in raw_profile.get("concentrations", {}).items():
            raw_context = raw_result.get("result_context")
            if raw_context is None:
                continue

            result = profile.concentration_for(Ion(ion_name))
            assert result is not None
            assert result.result_context is not None

            if raw_context.get("observed_on") is not None:
                assert result.result_context.observed_on == date.fromisoformat(
                    raw_context["observed_on"]
                )
                assert result.result_context.observation_period is None
            if raw_context.get("observation_period") is not None:
                expected_period = raw_context["observation_period"]
                assert result.result_context.observation_period == ObservationPeriod(
                    start=date.fromisoformat(expected_period["start"]),
                    end=date.fromisoformat(expected_period["end"]),
                )

            if (
                raw_context.get("coverage") is None
                and profile_context.get("coverage") is not None
            ):
                assert result.result_context.coverage is ResultCoverage(
                    profile_context["coverage"]
                )
            if (
                raw_context.get("water_stage") is None
                and profile_context.get("water_stage") is not None
            ):
                assert result.result_context.water_stage is WaterStage(
                    profile_context["water_stage"]
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
            if raw_context.get("coverage") is not None:
                assert result_context.coverage is ResultCoverage(
                    raw_context["coverage"]
                )
            if raw_context.get("water_stage") is not None:
                assert result_context.water_stage is WaterStage(
                    raw_context["water_stage"]
                )
            assert result_context.sample_location == raw_context.get("sample_location")


def test_santa_cruz_fixture_preserves_distribution_system_chlorine() -> None:
    fixture_path = REPORT_FIXTURE_ROOT / "santa-cruz" / "2025.json"
    _, profiles = _load_fixture(fixture_path)
    distribution_profile = next(
        profile
        for profile in profiles
        if profile.name == "Santa Cruz 2025 - Distribution System"
    )

    chlorine = distribution_profile.disinfectant_for(DisinfectantKind.CHLORINE)
    assert chlorine is not None
    assert chlorine.reported_label == "Chlorine"
    assert chlorine.reporting_basis is None
    assert chlorine.reported_average is not None
    assert chlorine.minimum is not None
    assert chlorine.maximum is not None
    assert chlorine.reported_average.to("milligram / liter").magnitude == pytest.approx(
        0.86
    )
    assert chlorine.minimum.to("milligram / liter").magnitude == pytest.approx(0.11)
    assert chlorine.maximum.to("milligram / liter").magnitude == pytest.approx(1.52)
    assert chlorine.result_context is not None
    assert chlorine.result_context.water_stage is WaterStage.DISTRIBUTION_SYSTEM

    # The report calls this result only "Chlorine".  Do not reinterpret it as
    # free chlorine, and do not confuse it with the chloride ion.
    assert distribution_profile.disinfectant_for(DisinfectantKind.FREE_CHLORINE) is None
    assert distribution_profile.concentration_for(Ion.CHLORIDE) is None


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
