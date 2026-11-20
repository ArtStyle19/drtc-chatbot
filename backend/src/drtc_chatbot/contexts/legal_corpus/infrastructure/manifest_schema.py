"""Pydantic schema of corpus/manifest.yaml (a persistence format, hence infrastructure)."""

from datetime import date
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, model_validator

from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    PageRole,
    VerificationStatus,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SourceEntry(_Strict):
    id: str
    file: str
    original_filename: str
    sha256: str
    media_type: Literal["application/pdf"]
    page_count: PositiveInt
    has_text_layer: bool
    printed_page_labels: Literal["none", "same_as_physical", "offset", "custom"]
    provenance: str


class VersionEntry(_Strict):
    id: str
    source: str
    edition_label: str
    consolidated_as_of: date | None = None
    consolidation_note: str | None = None
    verification_status: VerificationStatus
    parser: str | None = None
    page_ranges: dict[PageRole, list[tuple[PositiveInt, PositiveInt]]] = Field(default_factory=dict)
    alerts: list[str] = Field(default_factory=list)


class InstrumentEntry(_Strict):
    id: str
    type: InstrumentType
    number: str
    title: str
    short_name: str
    issuing_authority: str
    publication_date: date | None = None
    versions: list[VersionEntry] = Field(min_length=1)


class CorpusManifest(_Strict):
    schema_version: Literal[1]
    updated_on: date
    sources: list[SourceEntry]
    instruments: list[InstrumentEntry]

    @model_validator(mode="after")
    def _references_are_consistent(self) -> Self:
        source_ids = [source.id for source in self.sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("Duplicated source ids in the manifest")
        instrument_ids = [instrument.id for instrument in self.instruments]
        if len(set(instrument_ids)) != len(instrument_ids):
            raise ValueError("Duplicated instrument ids in the manifest")
        known_sources = set(source_ids)
        for instrument in self.instruments:
            for version in instrument.versions:
                if version.source not in known_sources:
                    raise ValueError(
                        f"Version {version.id} references unknown source {version.source}"
                    )
        return self
