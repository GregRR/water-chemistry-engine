from datetime import date

import pytest

from water_chemistry_engine.source_document import SourceDocumentMetadata


def test_source_document_preserves_document_metadata() -> None:
    metadata = SourceDocumentMetadata(
        publisher="City of Example Water Department",
        analysis_provider="Example Environmental Laboratory",
        title="2025 Drinking Water Quality Report",
        publication_date=date(2026, 6, 1),
        source_url="https://example.org/water-report.pdf",
        retrieved_on=date(2026, 8, 7),
        page_reference="Pages 12-14",
        notes="Annual water-quality report.",
    )

    assert metadata.publisher == "City of Example Water Department"
    assert metadata.analysis_provider == "Example Environmental Laboratory"
    assert metadata.title == "2025 Drinking Water Quality Report"
    assert metadata.publication_date == date(2026, 6, 1)
    assert metadata.source_url == "https://example.org/water-report.pdf"
    assert metadata.retrieved_on == date(2026, 8, 7)
    assert metadata.page_reference == "Pages 12-14"
    assert metadata.notes == "Annual water-quality report."


def test_analysis_provider_is_optional() -> None:
    metadata = SourceDocumentMetadata(
        publisher="Example Water Utility",
    )

    assert metadata.analysis_provider is None


def test_source_document_requires_publisher() -> None:
    with pytest.raises(
        ValueError,
        match="publisher cannot be empty",
    ):
        SourceDocumentMetadata(publisher="   ")


@pytest.mark.parametrize(
    ("field", "kwargs"),
    [
        (
            "analysis_provider",
            {"analysis_provider": "   "},
        ),
        (
            "title",
            {"title": "   "},
        ),
        (
            "source_url",
            {"source_url": "   "},
        ),
        (
            "page_reference",
            {"page_reference": "   "},
        ),
        (
            "notes",
            {"notes": "   "},
        ),
    ],
)
def test_source_document_rejects_empty_optional_text(
    field: str,
    kwargs: dict[str, str],
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"{field} cannot be empty",
    ):
        SourceDocumentMetadata(
            publisher="Example Water Utility",
            **kwargs,
        )
