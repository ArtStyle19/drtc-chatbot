import pytest

from drtc_chatbot.contexts.identity.infrastructure.anonymous_identity_provider import (
    AnonymousIdentityProvider,
)
from drtc_chatbot.shared_kernel.application import ActorKind, Credentials


async def test_every_caller_is_anonymous_in_the_mvp() -> None:
    actor = await AnonymousIdentityProvider().resolve(Credentials(bearer_token="ignored"))

    assert actor.kind is ActorKind.ANONYMOUS
    assert not actor.is_authenticated
    assert actor.actor_id == "anonymous"


async def test_a_valid_browser_session_id_is_kept_normalized() -> None:
    credentials = Credentials(session_id="3F2504E0-4F89-41D3-9A0C-0305E82C3301")

    actor = await AnonymousIdentityProvider().resolve(credentials)

    assert actor.actor_id == "anonymous:3f2504e0-4f89-41d3-9a0c-0305e82c3301"


@pytest.mark.parametrize("session_id", ["", "not-a-uuid", "x" * 200, "../../etc/passwd"])
async def test_invalid_session_ids_are_ignored(session_id: str) -> None:
    actor = await AnonymousIdentityProvider().resolve(Credentials(session_id=session_id))

    assert actor.actor_id == "anonymous"
