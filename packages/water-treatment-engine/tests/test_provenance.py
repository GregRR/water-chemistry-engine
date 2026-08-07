from datetime import date

import pytest
from water_treatment_engine.provenance import SourceWaterProvenance


def test_provenance_stores_report_metadata() -> None:
    provenance = SourceWaterProvenance(
        provider="Example Water Company",
        report_title="2026 Water Quality Report",
        report_date=date(2026, 6, 1),
        source_url="https://example.com/water-report.pdf",
        retrieved_on=date(2026, 8, 7),
        page_reference="pp. 8-10",
        notes="Chemistry values transcribed from the published report.",
    )

    assert provenance.provider == "Example Water Company"
    assert provenance.report_title == "2026 Water Quality Report"
    assert provenance.report_date == date(2026, 6, 1)
    assert provenance.source_url == "https://example.com/water-report.pdf"
    assert provenance.retrieved_on == date(2026, 8, 7)
    assert provenance.page_reference == "pp. 8-10"


def test_empty_provider_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="provider cannot be empty",
    ):
        SourceWaterProvenance(provider="   ")


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        ("report_title", {"report_title": "   "}),
        ("source_url", {"source_url": "   "}),
        ("page_reference", {"page_reference": "   "}),
        ("notes", {"notes": "   "}),
    ],
)
def test_empty_optional_text_is_rejected(
    field_name: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field_name} cannot be empty",
    ):
        SourceWaterProvenance(
            provider="Example Water Company",
            **kwargs,
        )
