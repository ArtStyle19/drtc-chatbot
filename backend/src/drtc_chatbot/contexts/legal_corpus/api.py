"""Public facade of the ``legal_corpus`` context.

This is the ONLY module other bounded contexts may import (enforced by import-linter).
Expose use cases and DTOs here, never domain entities or infrastructure.
"""

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionSummary,
    LegalInstrumentSummary,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.list_legal_instruments import (
    ListLegalInstruments,
)

__all__ = ["EditionSummary", "LegalInstrumentSummary", "ListLegalInstruments"]
