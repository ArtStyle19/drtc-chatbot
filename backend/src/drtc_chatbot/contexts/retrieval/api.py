"""Public facade of the ``retrieval`` context.

This is the ONLY module other bounded contexts may import (enforced by import-linter).
Expose use cases and DTOs here, never domain entities or infrastructure.
"""

from drtc_chatbot.contexts.retrieval.application.dto import LookupHit, LookupResult, LookupStatus
from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference

__all__ = ["LookupHit", "LookupReference", "LookupResult", "LookupStatus"]
