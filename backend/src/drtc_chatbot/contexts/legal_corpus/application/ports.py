"""Ports (interfaces) the legal-corpus use cases depend on. Adapters live in infrastructure."""

from collections.abc import Sequence
from typing import Protocol

from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import LegalInstrument


class LegalInstrumentCatalog(Protocol):
    """Read port: every legal instrument known to the corpus, in a stable order."""

    async def list_instruments(self) -> Sequence[LegalInstrument]: ...
