"""HTTP dependencies shared by the routers of every bounded context."""

from typing import Annotated, cast

from fastapi import Depends, Request

from drtc_chatbot.shared_kernel.application.identity import Actor, Credentials, IdentityProvider

_BEARER_PREFIX = "bearer "


def _bearer_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith(_BEARER_PREFIX):
        return authorization[len(_BEARER_PREFIX) :].strip() or None
    return None


async def current_actor(request: Request) -> Actor:
    """Resolve the caller with the IdentityProvider wired by the composition root."""
    provider = cast(IdentityProvider, request.app.state.identity_provider)
    credentials = Credentials(
        bearer_token=_bearer_token(request.headers.get("authorization")),
        session_id=request.headers.get("x-session-id"),
    )
    return await provider.resolve(credentials)


CurrentActor = Annotated[Actor, Depends(current_actor)]
