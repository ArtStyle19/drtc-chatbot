"""ManifestReader adapter: turns corpus/manifest.yaml into a snapshot for the corpus store."""

from pathlib import Path

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    IngestionTarget,
    ManifestInstrument,
    ManifestSnapshot,
    ManifestSource,
    ManifestVersion,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import PageRole
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_catalog import load_manifest


class YamlManifestReader:
    def __init__(self, manifest_path: Path) -> None:
        self._manifest_path = manifest_path

    def read(self) -> ManifestSnapshot:
        manifest = load_manifest(self._manifest_path)
        root = self._manifest_path.parent
        sources = tuple(
            ManifestSource(
                source_id=source.id,
                file=(root / source.file).resolve(),
                file_name=Path(source.file).name,
                sha256=source.sha256,
                page_count=source.page_count,
            )
            for source in manifest.sources
        )
        instruments, versions = [], []
        for entry in manifest.instruments:
            instruments.append(
                ManifestInstrument(
                    instrument_id=entry.id,
                    instrument_type=entry.type,
                    number=entry.number,
                    title=entry.title,
                    short_name=entry.short_name,
                    issuing_authority=entry.issuing_authority,
                    publication_date=entry.publication_date,
                    aliases=tuple(entry.aliases),
                )
            )
            for ordinal, version in enumerate(entry.versions, start=1):
                versions.append(
                    ManifestVersion(
                        version_id=version.id,
                        instrument_id=entry.id,
                        ordinal=ordinal,
                        source_id=version.source,
                        edition_label=version.edition_label,
                        consolidated_as_of=version.consolidated_as_of,
                        consolidation_note=version.consolidation_note,
                        verification_status=version.verification_status,
                        parser=version.parser,
                        page_sections=tuple(
                            (role.value, first, last)
                            for role, ranges in version.page_ranges.items()
                            for first, last in ranges
                        ),
                        alerts=tuple(version.alerts),
                    )
                )
        return ManifestSnapshot(sources, tuple(instruments), tuple(versions))


def ingestion_targets(snapshot: ManifestSnapshot) -> list[IngestionTarget]:
    """One target per instrument version: file, fingerprint, normative pages and parser profile."""
    sources = {source.source_id: source for source in snapshot.sources}
    targets = []
    for version in snapshot.versions:
        source = sources[version.source_id]
        normative = tuple(
            (first, last)
            for role, first, last in version.page_sections
            if role == PageRole.NORMATIVE.value
        )
        targets.append(
            IngestionTarget(
                version_id=version.version_id,
                instrument_id=version.instrument_id,
                source_file=source.file,
                sha256=source.sha256,
                page_count=source.page_count,
                normative_pages=normative,
                parser=version.parser,
            )
        )
    return targets
