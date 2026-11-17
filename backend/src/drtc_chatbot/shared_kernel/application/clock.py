"""Clock port, so use cases and tests never call ``datetime.now()`` directly."""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Return the current time as a timezone-aware datetime."""
        ...
