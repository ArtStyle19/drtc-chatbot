"""Aggregate root: the entry point of a consistency boundary."""

from drtc_chatbot.shared_kernel.domain.domain_event import DomainEvent
from drtc_chatbot.shared_kernel.domain.entity import Entity


class AggregateRoot[IdT](Entity[IdT]):
    """Entity that guards the invariants of its aggregate and records domain events.

    Events are collected while the aggregate changes and are pulled by the application
    layer after a successful commit, so they are never published for a rolled-back change.
    """

    __slots__ = ("_pending_events",)

    def __init__(self, entity_id: IdT) -> None:
        super().__init__(entity_id)
        self._pending_events: list[DomainEvent] = []

    def _record_event(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return the recorded events and clear them."""
        events = self._pending_events
        self._pending_events = []
        return events
