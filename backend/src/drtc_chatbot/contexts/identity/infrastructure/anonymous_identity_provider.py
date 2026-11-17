"""IdentityProvider adapter for the MVP without login (ADR-0007)."""

import re

from drtc_chatbot.shared_kernel.application import Actor, ActorKind, Credentials

_SESSION_ID = re.compile(r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$")


class AnonymousIdentityProvider:
    """Treats every caller as anonymous.

    A browser-generated session id (UUID) is kept, when valid, so a future spec can group an
    anonymous visitor's conversations. Bearer tokens are ignored until an authenticating adapter
    (DRTC JWT or OIDC) replaces this one in the composition root.
    """

    async def resolve(self, credentials: Credentials) -> Actor:
        session_id = (credentials.session_id or "").strip().lower()
        if _SESSION_ID.fullmatch(session_id):
            return Actor(actor_id=f"anonymous:{session_id}", kind=ActorKind.ANONYMOUS)
        return Actor(actor_id="anonymous", kind=ActorKind.ANONYMOUS)
