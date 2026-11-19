"""The OpenAI adapter against a simulated HTTP transport: no network, no real key."""

import json
import re
from collections.abc import Callable

import httpx
import pytest
from openai import AsyncOpenAI
from pydantic import SecretStr

from drtc_chatbot.contexts.retrieval.domain.errors import EmbeddingUnavailableError
from drtc_chatbot.contexts.retrieval.infrastructure.openai_embeddings import OpenAIEmbeddingProvider

KEY = SecretStr("sk-test-NOT-A-REAL-KEY-abcdef0123456789")  # a fake key, to prove it never leaks
QUESTION = "mi hermano Juan Pérez DNI 12345678 chocó la camioneta placa ABC-123"


def embeddings_response(
    vectors: list[list[float]], tokens: int = 7, *, shuffled: bool = False
) -> dict:
    data = [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vectors)]
    if shuffled:
        data.reverse()
    return {
        "object": "list",
        "data": data,
        "model": "text-embedding-3-small",
        "usage": {"prompt_tokens": tokens, "total_tokens": tokens},
    }


class Recorder:
    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self.requests: list[httpx.Request] = []
        self._handler = handler

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)

    def body(self, n: int = 0) -> dict:
        return json.loads(self.requests[n].content)


def provider(
    handler: Callable[[httpx.Request], httpx.Response],
    *,
    dimensions: int | None = None,
    model: str = "text-embedding-3-small",
) -> tuple[OpenAIEmbeddingProvider, Recorder]:
    recorder = Recorder(handler)
    client = AsyncOpenAI(
        api_key=KEY.get_secret_value(),
        base_url="https://api.test/v1",
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(recorder)),
    )
    return OpenAIEmbeddingProvider(
        KEY, model, dimensions=dimensions, client=client, indexing_retries=0
    ), recorder


def ok(vectors: list[list[float]], **kwargs: object) -> Callable[[httpx.Request], httpx.Response]:
    return lambda request: httpx.Response(200, json=embeddings_response(vectors, **kwargs))  # type: ignore[arg-type]


@pytest.mark.spec("004-FR-007")
async def test_it_sends_the_model_and_the_texts_and_returns_vectors_in_order_with_the_real_usage() -> (
    None
):
    p, recorder = provider(ok([[0.1, 0.2], [0.3, 0.4]], tokens=12, shuffled=True))

    batch = await p.embed(["uno", "dos"])

    assert batch.vectors == (
        (0.1, 0.2),
        (0.3, 0.4),
    )  # re-ordered by index, whatever the order received
    assert batch.tokens == 12  # as REPORTED by the provider
    body = recorder.body()
    assert body["model"] == "text-embedding-3-small"
    assert body["input"] == ["uno", "dos"]
    assert body["encoding_format"] == "float"
    assert "dimensions" not in body
    assert recorder.requests[0].url.path == "/v1/embeddings"
    assert recorder.requests[0].headers["authorization"] == f"Bearer {KEY.get_secret_value()}"


async def test_shortened_vectors_ask_for_dimensions_and_have_their_own_model_key() -> None:
    p, recorder = provider(ok([[0.1]]), dimensions=1024, model="text-embedding-3-large")

    await p.embed(["x"])

    assert recorder.body()["dimensions"] == 1024
    assert (
        p.model == "text-embedding-3-large@1024"
    )  # vectors of another size are never mixed with 3072
    assert provider(ok([[0.1]]))[0].model == "text-embedding-3-small"


async def test_an_empty_batch_does_not_call_the_provider() -> None:
    p, recorder = provider(ok([]))

    batch = await p.embed([])

    assert (batch.vectors, batch.tokens) == ((), 0)
    assert recorder.requests == []


def test_it_is_an_external_provider() -> None:
    assert provider(ok([]))[0].external is True


@pytest.mark.spec("004-FR-013")
@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "rejected the API key"),
        (403, "rejected the API key"),
        (429, "limiting requests"),
        (500, "server error (HTTP 500)"),
        (503, "server error (HTTP 503)"),
        (400, "an error (HTTP 400)"),
    ],
)
async def test_every_http_failure_becomes_a_degradation_with_a_safe_message(
    status: int, message: str
) -> None:
    p, _ = provider(
        lambda request: httpx.Response(
            status, json={"error": {"message": f"echo of your input: {QUESTION}", "type": "x"}}
        )
    )

    with pytest.raises(EmbeddingUnavailableError, match=re.escape(message)) as caught:
        await p.embed([QUESTION])

    # the provider's own message (which may echo the input) and the key never reach ours
    assert QUESTION not in caught.value.message
    assert "Pérez" not in caught.value.message
    assert KEY.get_secret_value() not in caught.value.message


@pytest.mark.spec("004-FR-013")
async def test_a_timeout_and_a_connection_failure_are_degradations_too() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    with pytest.raises(EmbeddingUnavailableError, match="did not answer in time"):
        await provider(timeout)[0].embed(["x"], timeout_seconds=3.0)
    with pytest.raises(EmbeddingUnavailableError, match="Could not reach"):
        await provider(refused)[0].embed(["x"])


@pytest.mark.spec("004-FR-014")
async def test_neither_the_key_nor_the_text_can_be_found_in_the_error_chain() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=f"{QUESTION} {KEY.get_secret_value()}")

    p, _ = provider(boom)
    with pytest.raises(EmbeddingUnavailableError) as caught:
        await p.embed([QUESTION])

    assert QUESTION not in str(caught.value)
    assert KEY.get_secret_value() not in str(caught.value)
    assert KEY.get_secret_value() not in repr(p.__dict__.get("_model_id"))


async def test_the_key_is_not_part_of_the_provider_repr_or_model_key() -> None:
    p, _ = provider(ok([]))

    assert KEY.get_secret_value() not in p.model
    assert KEY.get_secret_value() not in repr(KEY)


@pytest.mark.spec("004-FR-013")
async def test_an_interactive_query_does_not_retry_so_it_can_degrade_within_its_time() -> None:
    calls = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={"error": {"message": "x", "type": "server_error"}})

    p = OpenAIEmbeddingProvider(
        KEY,
        "text-embedding-3-small",
        client=AsyncOpenAI(
            api_key="k",
            base_url="https://api.test/v1",
            max_retries=2,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(flaky)),
        ),
    )
    with pytest.raises(EmbeddingUnavailableError):
        await p.embed(["x"], timeout_seconds=3.0)

    assert calls["n"] == 1


async def test_verify_checks_the_model_exists_without_embedding_anything() -> None:
    present, recorder = provider(
        lambda request: httpx.Response(
            200,
            json={
                "id": "text-embedding-3-small",
                "object": "model",
                "created": 1,
                "owned_by": "openai",
            },
        )
    )
    absent, _ = provider(
        lambda request: httpx.Response(
            404, json={"error": {"message": "no", "type": "invalid_request_error"}}
        ),
        model="text-embedding-9",
    )

    await present.verify()
    with pytest.raises(EmbeddingUnavailableError, match="does not exist for this key"):
        await absent.verify()

    assert recorder.requests[0].url.path == "/v1/models/text-embedding-3-small"
    assert recorder.requests[0].method == "GET"


async def test_indexing_retries_by_default_with_backoff_unlike_a_query() -> None:
    calls = {"n": 0}

    def flaky_then_fine(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(
                429,
                headers={"retry-after-ms": "1"},
                json={"error": {"message": "x", "type": "rate_limit"}},
            )
        return httpx.Response(200, json=embeddings_response([[0.5]]))

    client = AsyncOpenAI(
        api_key="k",
        base_url="https://api.test/v1",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(flaky_then_fine)),
    )
    p = OpenAIEmbeddingProvider(KEY, "text-embedding-3-small", client=client, indexing_retries=2)

    batch = await p.embed(["x"])  # not interactive: it retries and succeeds

    assert batch.vectors == ((0.5,),)
    assert calls["n"] == 2
