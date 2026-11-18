"""Adapter: reads the legal instruments from ``corpus/manifest.yaml``.

Walking-skeleton implementation of the LegalInstrumentCatalog port (spec 001). Spec 002 adds a
PostgreSQL repository; the use cases do not change because they only know the port.
"""

import asyncio
from collections.abc import Sequence
from pathlib import Path

import yaml
from pydantic import ValidationError

from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import (
    InstrumentVersion,
    LegalInstrument,
    SourceDocumentRef,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentId,
    PageRange,
    PageSection,
    Sha256Digest,
    VersionId,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_schema import (
    CorpusManifest,
    InstrumentEntry,
    SourceEntry,
)
from drtc_chatbot.shared_kernel.domain import DomainError


class CorpusManifestError(Exception):
    """The corpus manifest is missing, unreadable or inconsistent."""


class ManifestInstrumentCatalog:
    """Implements LegalInstrumentCatalog by parsing the YAML manifest once and caching it."""

    def __init__(self, manifest_path: Path) -> None:
        self._manifest_path = manifest_path
        self._instruments: tuple[LegalInstrument, ...] | None = None
        self._lock = asyncio.Lock()

    async def list_instruments(self) -> Sequence[LegalInstrument]:
        if self._instruments is None:
            async with self._lock:
                if self._instruments is None:
                    self._instruments = await asyncio.to_thread(self._load)
        return self._instruments

    def _load(self) -> tuple[LegalInstrument, ...]:
        manifest = load_manifest(self._manifest_path)
        sources = {source.id: source for source in manifest.sources}
        try:
            return tuple(_to_domain(entry, sources) for entry in manifest.instruments)
        except DomainError as error:
            raise CorpusManifestError(f"{self._manifest_path}: {error.message}") from error


def load_manifest(manifest_path: Path) -> CorpusManifest:
    """Read and validate the manifest file."""
    try:
        raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise CorpusManifestError(f"Corpus manifest not found: {manifest_path}") from error
    except yaml.YAMLError as error:
        raise CorpusManifestError(f"Corpus manifest is not valid YAML: {error}") from error
    try:
        return CorpusManifest.model_validate(raw)
    except ValidationError as error:
        raise CorpusManifestError(f"Corpus manifest is invalid: {error}") from error


def _to_domain(entry: InstrumentEntry, sources: dict[str, SourceEntry]) -> LegalInstrument:
    versions = []
    for version in entry.versions:
        source = sources[version.source]
        sections = tuple(
            PageSection(role=role, pages=PageRange(first, last))
            for role, ranges in version.page_ranges.items()
            for first, last in ranges
        )
        versions.append(
            InstrumentVersion(
                version_id=VersionId(version.id),
                edition_label=version.edition_label,
                verification_status=version.verification_status,
                source=SourceDocumentRef(
                    source_id=source.id,
                    file_name=Path(source.file).name,
                    sha256=Sha256Digest(source.sha256),
                    page_count=source.page_count,
                ),
                consolidated_as_of=version.consolidated_as_of,
                consolidation_note=version.consolidation_note,
                page_sections=sections,
                alerts=tuple(version.alerts),
            )
        )
    return LegalInstrument(
        InstrumentId(entry.id),
        instrument_type=entry.type,
        number=entry.number,
        title=entry.title,
        short_name=entry.short_name,
        issuing_authority=entry.issuing_authority,
        publication_date=entry.publication_date,
        aliases=entry.aliases,
        versions=versions,
    )
