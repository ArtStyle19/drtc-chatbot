"""The text a person types to search by content: its limits and what is safe to do with it.

The same rules apply wherever a search starts (HTTP, command line, evaluation). The text is NEVER
logged or stored (constitution VI): only its length may be recorded.
"""

from drtc_chatbot.shared_kernel.domain import InvariantViolationError

MIN_QUERY_CHARS = 1
MAX_QUERY_CHARS = 300


def validate_query(text: str) -> str:
    """The text without the spaces at its ends, or an error when it is empty or too long."""
    cleaned = " ".join(text.split())
    if len(cleaned) < MIN_QUERY_CHARS:
        raise InvariantViolationError("The search text is empty")
    if len(cleaned) > MAX_QUERY_CHARS:
        raise InvariantViolationError(
            f"The search text is longer than {MAX_QUERY_CHARS} characters"
        )
    return cleaned
