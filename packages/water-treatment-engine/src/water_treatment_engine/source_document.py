from dataclasses import dataclass
from datetime import date


def _validate_optional_text(value: str | None, field_name: str) -> None:
    if value is not None and not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")


@dataclass(frozen=True, slots=True)
class SourceDocumentMetadata:
    """Metadata identifying the document that reported water-quality data."""

    publisher: str
    analysis_provider: str | None = None
    title: str | None = None
    publication_date: date | None = None
    source_url: str | None = None
    retrieved_on: date | None = None
    page_reference: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.publisher.strip():
            raise ValueError("publisher cannot be empty.")

        _validate_optional_text(
            self.analysis_provider,
            "analysis_provider",
        )
        _validate_optional_text(self.title, "title")
        _validate_optional_text(self.source_url, "source_url")
        _validate_optional_text(
            self.page_reference,
            "page_reference",
        )
        _validate_optional_text(self.notes, "notes")
