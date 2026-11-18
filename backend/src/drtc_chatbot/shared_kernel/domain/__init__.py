"""Shared domain building blocks. Pure Python only (enforced by import-linter)."""

from drtc_chatbot.shared_kernel.domain.aggregate_root import AggregateRoot
from drtc_chatbot.shared_kernel.domain.domain_event import DomainEvent
from drtc_chatbot.shared_kernel.domain.entity import Entity
from drtc_chatbot.shared_kernel.domain.errors import (
    DomainError,
    IntegrityViolationError,
    InvariantViolationError,
    NotFoundError,
)

__all__ = [
    "AggregateRoot",
    "DomainError",
    "DomainEvent",
    "Entity",
    "IntegrityViolationError",
    "InvariantViolationError",
    "NotFoundError",
]
