"""Public facade of the ``ingestion`` context.

This is the ONLY module other bounded contexts may import (enforced by import-linter).
Expose use cases and DTOs here, never domain entities or infrastructure.
"""

from drtc_chatbot.contexts.ingestion.application.commands.preview_ingestion import PreviewIngestion
from drtc_chatbot.contexts.ingestion.application.commands.run_ingestion import (
    IngestionOutcome,
    RunIngestion,
)

__all__ = ["IngestionOutcome", "PreviewIngestion", "RunIngestion"]
