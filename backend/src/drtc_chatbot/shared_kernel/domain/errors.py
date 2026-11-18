"""Domain error hierarchy.

``code`` is a stable, machine-readable identifier exposed by the API (RFC 9457 problem
details), so clients never have to parse messages.
"""

from typing import ClassVar


class DomainError(Exception):
    """Base class for business-rule violations."""

    code: ClassVar[str] = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvariantViolationError(DomainError):
    """A domain object would end up in an invalid state."""

    code = "invariant_violation"


class IntegrityViolationError(DomainError):
    """Stored data no longer matches its recorded fingerprint (e.g. an altered original PDF).

    A server-side failure, not a client error: it is logged and reported without internal details.
    """

    code = "integrity_violation"


class NotFoundError(DomainError):
    """A requested domain object does not exist."""

    code = "not_found"
