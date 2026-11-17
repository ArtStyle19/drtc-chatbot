"""Domain event base class."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Something relevant that happened in the domain.

    Name subclasses in the past tense (e.g. ``InstrumentVersionVerified``); they are immutable.
    """

    occurred_at: datetime
