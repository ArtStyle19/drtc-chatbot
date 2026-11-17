"""Composition root: the only place that instantiates concrete adapters and wires use cases.

Dependencies are wired by hand on purpose (ADR-0002): it keeps the wiring explicit and easy
to read. Revisit a DI library (e.g. dishka) only when this file becomes hard to maintain.
"""

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine

from drtc_chatbot.bootstrap.settings import Settings
from drtc_chatbot.contexts.identity.infrastructure.anonymous_identity_provider import (
    AnonymousIdentityProvider,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.list_legal_instruments import (
    ListLegalInstruments,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_catalog import (
    ManifestInstrumentCatalog,
)
from drtc_chatbot.shared_kernel.application import Clock, IdentityProvider
from drtc_chatbot.shared_kernel.infrastructure.database import create_database_engine
from drtc_chatbot.shared_kernel.infrastructure.system_clock import SystemClock


@dataclass(frozen=True, slots=True)
class LegalCorpusModule:
    """Use cases of the legal_corpus context, as seen by its HTTP router."""

    list_legal_instruments: ListLegalInstruments


@dataclass(frozen=True, slots=True)
class Container:
    settings: Settings
    engine: AsyncEngine
    clock: Clock
    identity_provider: IdentityProvider
    legal_corpus: LegalCorpusModule

    async def aclose(self) -> None:
        await self.engine.dispose()


def build_container(settings: Settings) -> Container:
    engine = create_database_engine(settings.database_url, echo=settings.database_echo)
    catalog = ManifestInstrumentCatalog(settings.corpus_manifest_path)
    return Container(
        settings=settings,
        engine=engine,
        clock=SystemClock(),
        identity_provider=AnonymousIdentityProvider(),
        legal_corpus=LegalCorpusModule(list_legal_instruments=ListLegalInstruments(catalog)),
    )
