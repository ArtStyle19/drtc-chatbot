"""Public facade of the ``legal_corpus`` context.

This is the ONLY module other bounded contexts may import (enforced by import-linter).
Expose use cases and DTOs here, never domain entities or infrastructure.
"""

from drtc_chatbot.contexts.legal_corpus.application.commands.approve_version import (
    ApproveInstrumentVersion,
)
from drtc_chatbot.contexts.legal_corpus.application.commands.publish_provisions import (
    PublishProvisions,
)
from drtc_chatbot.contexts.legal_corpus.application.commands.sync_corpus_manifest import (
    SyncCorpusManifest,
)
from drtc_chatbot.contexts.legal_corpus.application.dto import (
    ApprovalResult,
    EditionSummary,
    EventRequest,
    IngestionTarget,
    LegalInstrumentSummary,
    ManifestSnapshot,
    NoteDraft,
    ProvisionDetail,
    ProvisionPage,
    PublishOutcome,
    PublishRequest,
    RevisionRequest,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.get_provision import GetProvision
from drtc_chatbot.contexts.legal_corpus.application.queries.list_legal_instruments import (
    ListLegalInstruments,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.list_provisions import ListProvisions
from drtc_chatbot.contexts.legal_corpus.domain.approval import ApprovalPolicy, ApprovalPolicyName
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_reader import ingestion_targets

__all__ = [
    "ApprovalPolicy",
    "ApprovalPolicyName",
    "ApprovalResult",
    "ApproveInstrumentVersion",
    "EditionSummary",
    "EventRequest",
    "GetProvision",
    "IngestionTarget",
    "LegalInstrumentSummary",
    "ListLegalInstruments",
    "ListProvisions",
    "ManifestSnapshot",
    "NoteDraft",
    "ProvisionDetail",
    "ProvisionPage",
    "PublishOutcome",
    "PublishProvisions",
    "PublishRequest",
    "RevisionRequest",
    "SyncCorpusManifest",
    "ingestion_targets",
]
