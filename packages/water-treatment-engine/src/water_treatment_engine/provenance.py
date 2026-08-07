from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class SourceWaterProvenance:
    """Provenance for a reported or measured source-water profile."""

    provider: str
    report_title: str | None = None
    report_date: date | None = None
    source_url: str | None = None
    retrieved_on: date | None = None
    page_reference: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("Source water provenance provider cannot be empty.")

        optional_text_fields = {
            "report_title": self.report_title,
            "source_url": self.source_url,
            "page_reference": self.page_reference,
            "notes": self.notes,
        }

        for field_name, value in optional_text_fields.items():
            if value is not None and not value.strip():
                raise ValueError(
                    f"Source water provenance {field_name} cannot be empty."
                )
