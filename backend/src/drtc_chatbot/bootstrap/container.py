"""Composition root: the only place that instantiates concrete adapters and wires use cases.

Dependencies are wired by hand on purpose (ADR-0002): it keeps the wiring explicit and easy
to read. Revisit a DI library (e.g. dishka) only when this file becomes hard to maintain.
"""

from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from drtc_chatbot.bootstrap.settings import Settings
from drtc_chatbot.contexts.identity.infrastructure.anonymous_identity_provider import (
    AnonymousIdentityProvider,
)
from drtc_chatbot.contexts.ingestion.api import PreviewIngestion, RunIngestion
from drtc_chatbot.contexts.ingestion.infrastructure.corpus_gateway import LegalCorpusGateway
from drtc_chatbot.contexts.ingestion.infrastructure.pdfium_extractor import PdfiumTextExtractor
from drtc_chatbot.contexts.ingestion.infrastructure.sql_jobs import SqlIngestionJobRepository
from drtc_chatbot.contexts.legal_corpus.api import (
    ApprovalPolicy,
    ApprovalPolicyName,
    ApproveInstrumentVersion,
    GetOutline,
    GetProvision,
    GetReadingUnit,
    GetSourceDocument,
    ListLegalInstruments,
    ListProvisionIndex,
    ListProvisions,
    PublishProvisions,
    SyncCorpusManifest,
)
from drtc_chatbot.contexts.legal_corpus.application.ports import LegalInstrumentCatalog
from drtc_chatbot.contexts.legal_corpus.infrastructure.local_document_storage import (
    LocalDocumentStorage,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_catalog import (
    ManifestInstrumentCatalog,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_reader import YamlManifestReader
from drtc_chatbot.contexts.legal_corpus.infrastructure.sql_reading import SqlReadingStore
from drtc_chatbot.contexts.legal_corpus.infrastructure.sql_store import SqlLegalCorpusStore
from drtc_chatbot.contexts.retrieval.api import LookupReference
from drtc_chatbot.contexts.retrieval.application.exact_retriever import ExactRetriever
from drtc_chatbot.contexts.retrieval.application.ports import EvaluationStore, GoldenSet, Retriever
from drtc_chatbot.contexts.retrieval.application.run_evaluation import RunEvaluation
from drtc_chatbot.contexts.retrieval.infrastructure.evaluation_files import FileEvaluationStore
from drtc_chatbot.contexts.retrieval.infrastructure.jsonl_golden_set import JsonlGoldenSet
from drtc_chatbot.contexts.retrieval.infrastructure.legal_corpus_directory import (
    LegalCorpusDirectory,
)
from drtc_chatbot.shared_kernel.application import Clock, IdentityProvider
from drtc_chatbot.shared_kernel.infrastructure.database import create_database_engine
from drtc_chatbot.shared_kernel.infrastructure.system_clock import SystemClock


@dataclass(frozen=True, slots=True)
class LegalCorpusModule:
    """Use cases of the legal_corpus context, as seen by its HTTP router."""

    list_legal_instruments: ListLegalInstruments
    list_provisions: ListProvisions
    get_provision: GetProvision
    get_outline: GetOutline
    get_reading_unit: GetReadingUnit
    get_source_document: GetSourceDocument
    list_provision_index: ListProvisionIndex


@dataclass(frozen=True, slots=True)
class RetrievalModule:
    """Use cases of the retrieval context, as seen by its HTTP router."""

    lookup_reference: LookupReference


@dataclass(frozen=True, slots=True)
class RetrievalCliModule:
    """What the ``drtc-retrieval`` command line needs from the retrieval context."""

    run_evaluation: RunEvaluation
    retrievers: Mapping[str, Retriever]
    default_dataset: Path
    store: EvaluationStore
    clock: Clock

    def golden_set(self, path: Path) -> GoldenSet:
        return JsonlGoldenSet(path)


@dataclass(frozen=True, slots=True)
class IngestionModule:
    """Use cases of the ingestion context, as seen by its CLI."""

    run_ingestion: RunIngestion
    preview: PreviewIngestion
    gateway: LegalCorpusGateway
    jobs: SqlIngestionJobRepository


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    engine: AsyncEngine
    clock: Clock
    identity_provider: IdentityProvider
    legal_corpus: LegalCorpusModule
    ingestion: IngestionModule
    retrieval: RetrievalModule
    retrieval_cli: RetrievalCliModule

    async def aclose(self) -> None:
        await self.engine.dispose()


def build_container(settings: Settings) -> Container:
    engine = create_database_engine(settings.database_url, echo=settings.database_echo)
    clock = SystemClock()
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    store = SqlLegalCorpusStore(sessions)
    reading = SqlReadingStore(sessions)
    documents = LocalDocumentStorage(settings.corpus_manifest_path.parent / "sources")
    catalog: LegalInstrumentCatalog = (
        store
        if settings.catalog_backend == "database"
        else ManifestInstrumentCatalog(settings.corpus_manifest_path)
    )
    policy = ApprovalPolicy(
        ApprovalPolicyName(settings.ingestion_approval_policy or "manual"),
        settings.environment.value,
    )
    approve = ApproveInstrumentVersion(store, clock, policy)
    gateway = LegalCorpusGateway(
        SyncCorpusManifest(YamlManifestReader(settings.corpus_manifest_path), store),
        PublishProvisions(store, clock),
        approve,
    )
    extractor = PdfiumTextExtractor()
    jobs = SqlIngestionJobRepository(sessions)
    list_instruments = ListLegalInstruments(catalog)
    list_index = ListProvisionIndex(reading)
    directory = LegalCorpusDirectory(list_instruments, list_index)
    lookup = LookupReference(directory)
    return Container(
        settings=settings,
        engine=engine,
        clock=clock,
        identity_provider=AnonymousIdentityProvider(),
        legal_corpus=LegalCorpusModule(
            list_legal_instruments=list_instruments,
            list_provisions=ListProvisions(store),
            get_provision=GetProvision(store),
            get_outline=GetOutline(reading),
            get_reading_unit=GetReadingUnit(reading),
            get_source_document=GetSourceDocument(reading, documents),
            list_provision_index=list_index,
        ),
        ingestion=IngestionModule(
            run_ingestion=RunIngestion(gateway, extractor, jobs, clock),
            preview=PreviewIngestion(gateway, extractor),
            gateway=gateway,
            jobs=jobs,
        ),
        retrieval=RetrievalModule(lookup_reference=lookup),
        retrieval_cli=RetrievalCliModule(
            run_evaluation=RunEvaluation(directory),
            retrievers={"exact": ExactRetriever(lookup)},
            default_dataset=settings.evaluation_dir / "datasets" / "golden-v1.jsonl",
            store=FileEvaluationStore(settings.evaluation_dir),
            clock=clock,
        ),
    )


@asynccontextmanager
async def ingestion_module(settings: Settings | None = None) -> AsyncIterator[IngestionModule]:
    """Use-case bundle for the command line; closes the database pool when done."""
    container = build_container(settings or Settings())
    try:
        yield container.ingestion
    finally:
        await container.aclose()


@asynccontextmanager
async def retrieval_module(settings: Settings | None = None) -> AsyncIterator[RetrievalCliModule]:
    """Use-case bundle for ``drtc-retrieval``; closes the database pool when done."""
    container = build_container(settings or Settings())
    try:
        yield container.retrieval_cli
    finally:
        await container.aclose()
