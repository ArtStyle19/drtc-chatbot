"""Review flags: which provisions the reviewer (and the reader's user) must look at."""

from drtc_chatbot.contexts.ingestion.domain.parsing.model import ParseResult, RevisionStatus

# Anomaly codes that point at a concrete provision and affect how far its text can be trusted.
FLAGGED_CODES = frozenset(
    {
        "paragraph_replacement_unapplied",
        "continuation_after_quote",
        "duplicate_unquoted_unit",
    }
)


def flags_by_path(result: ParseResult) -> dict[str, tuple[str, ...]]:
    """Flags per provision path, to be stored on the CURRENT revision of that path."""
    current = {p.path for p in result.provisions if p.status is RevisionStatus.CURRENT}
    found: dict[str, set[str]] = {}
    for anomaly in result.anomalies:
        if anomaly.code in FLAGGED_CODES and anomaly.path in current:
            found.setdefault(anomaly.path, set()).add(anomaly.code)
    return {path: tuple(sorted(codes)) for path, codes in found.items()}
