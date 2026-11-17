"""System clock adapter."""

from datetime import UTC, datetime


class SystemClock:
    """Implements the Clock port with the real UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)
