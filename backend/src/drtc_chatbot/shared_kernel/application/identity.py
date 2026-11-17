"""Who is executing a use case.

Every use case receives an :class:`Actor`. In the MVP there is no login (ADR-0007), so the
actor is anonymous; adding authentication later means adding an :class:`IdentityProvider`
adapter in ``contexts.identity`` without touching the use cases.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol


class ActorKind(StrEnum):
    ANONYMOUS = "anonymous"
    STAFF = "staff"
    CITIZEN = "citizen"
    SERVICE = "service"


@dataclass(frozen=True, slots=True)
class Actor:
    """The person or system executing a use case."""

    actor_id: str
    kind: ActorKind
    roles: frozenset[str] = field(default_factory=frozenset)
    display_name: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.kind is not ActorKind.ANONYMOUS

    def has_role(self, role: str) -> bool:
        return role in self.roles


@dataclass(frozen=True, slots=True)
class Credentials:
    """Raw credentials extracted by a delivery mechanism (HTTP headers, CLI flags...)."""

    bearer_token: str | None = None
    session_id: str | None = None


class IdentityProvider(Protocol):
    """Port: resolves raw credentials into an :class:`Actor`."""

    async def resolve(self, credentials: Credentials) -> Actor: ...
