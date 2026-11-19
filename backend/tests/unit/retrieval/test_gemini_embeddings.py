"""The Gemini adapter against a simulated HTTP transport: no network, no real key."""

import json
import re
from collections.abc import Callable

import httpx
import pytest
from openai import AsyncOpenAI
from pydantic import SecretStr

from drtc_chatbot.contexts.retrieval.application.ports import EmbeddingPurpose
from drtc_chatbot.contexts.retrieval.domain.errors import (
    EmbeddingRateLimitedError,
    EmbeddingUnavailableError,
)
from drtc_chatbot.contexts.retrieval.infrastructure.gemini_embeddings import (
    BATCH_ITEMS,
    DOCUMENT_PREFIX,
    GEMINI_BASE_URL,
    QUERY_PREFIX,
    GeminiEmbeddingProvider,
    PerMinuteLimit,
)

KEY = SecretStr("AIza-test-NOT-A-REAL-KEY-abcdef0123456789")  # fake: to prove it never leaks
QUESTION = "mi hermano Juan Pérez DNI 12345678 chocó la camioneta placa ABC-123"


def response_for(request: httpx.Request, *, usage: bool = True) -> httpx.Response:
    texts = json.loads(request.content)["input"]
    body: dict = {
        "object": "list",
        "model": "gemini-embedding-2",
        "data": [
            {"object": "embedding", "index": i, "embedding": [float(i), 1.0, 2.0]}
            for i in range(len(texts))
        ],
    }
    if usage:
        body["usage"] = {"prompt_tokens": 5 * len(texts), "total_tokens": 5 * len(texts)}
    return httpx.Response(200, json=body)


class Recorder:
    def __init__(self, handler: Callable[[httpx.Request], httpx.Response] = response_for) -> None:
        self.requests: list[httpx.Request] = []
        self._handler = handler

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)

    def inputs(self, n: int = 0) -> list[str]:
        return json.loads(self.requests[n].content)["input"]


class Clock:
    """A clock the test moves by hand; sleeping advances it (nothing really waits)."""

    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def __call__(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def make(
    handler: Callable[[httpx.Request], httpx.Response] = response_for,
    *,
    model: str = "gemini-embedding-2",
    max_tokens_per_minute: int = 25_000,
    max_requests_per_minute: int = 1_000,
    clock: Clock | None = None,
) -> tuple[GeminiEmbeddingProvider, Recorder, Clock]:
    recorder = Recorder(handler)
    clock = clock or Clock()
    client = AsyncOpenAI(
        api_key=KEY.get_secret_value(),
        base_url=GEMINI_BASE_URL,
        max_retries=0,
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(recorder)),
    )
    provider = GeminiEmbeddingProvider(
        KEY,
        model,
        max_tokens_per_minute=max_tokens_per_minute,
        max_requests_per_minute=max_requests_per_minute,
        client=client,
        indexing_retries=0,
        clock=clock,
        sleep=clock.sleep,
    )
    return provider, recorder, clock


# ------------------------------------------------------------------ what it sends
@pytest.mark.spec("004-FR-007")
async def test_a_document_gets_the_document_prefix_google_documents() -> None:
    p, recorder, _ = make()

    await p.embed(["Artículo 5. Competencias"], purpose=EmbeddingPurpose.DOCUMENT)

    assert recorder.inputs() == ["title: none | text: Artículo 5. Competencias"]
    assert DOCUMENT_PREFIX == "title: none | text: "


@pytest.mark.spec("004-FR-007")
async def test_what_a_person_typed_gets_the_query_prefix_google_documents() -> None:
    p, recorder, _ = make()

    await p.embed(["plazo para apelar"], purpose=EmbeddingPurpose.QUERY, timeout_seconds=3.0)

    assert recorder.inputs() == ["task: search result | query: plazo para apelar"]
    assert QUERY_PREFIX == "task: search result | query: "


async def test_the_default_purpose_is_document() -> None:
    p, recorder, _ = make()

    await p.embed(["x"])

    assert recorder.inputs() == ["title: none | text: x"]


async def test_the_older_model_gets_the_plain_text_because_it_takes_no_prefix() -> None:
    p, recorder, _ = make(model="gemini-embedding-001")

    await p.embed(["plazo"], purpose=EmbeddingPurpose.QUERY, timeout_seconds=3.0)
    await p.embed(["texto"], purpose=EmbeddingPurpose.DOCUMENT)

    assert [recorder.inputs(0), recorder.inputs(1)] == [["plazo"], ["texto"]]
    assert p.model == "gemini-embedding-001"


async def test_it_talks_to_the_gemini_address_with_the_model_and_asks_for_floats() -> None:
    p, recorder, _ = make()

    await p.embed(["x"])

    request = recorder.requests[0]
    assert str(request.url) == f"{GEMINI_BASE_URL}embeddings"
    assert request.headers["authorization"] == f"Bearer {KEY.get_secret_value()}"
    body = json.loads(request.content)
    assert body["model"] == "gemini-embedding-2"
    assert body["encoding_format"] == "float"
    assert "dimensions" not in body  # the default 3072: nothing to normalise


async def test_the_model_key_is_the_model_name_and_it_is_an_external_provider() -> None:
    p, _, _ = make()

    assert p.model == "gemini-embedding-2"
    assert p.external is True
    assert p.data_notice is not None
    assert "plan gratuito" in p.data_notice


# ------------------------------------------------------------------ results
async def test_vectors_come_back_in_order_with_the_tokens_the_provider_reported() -> None:
    p, _, _ = make()

    batch = await p.embed(["uno", "dos", "tres"])

    assert [v[0] for v in batch.vectors] == [0.0, 1.0, 2.0]
    assert batch.tokens == 15
    assert p.tokens_used == 15


async def test_when_the_provider_reports_no_usage_the_tokens_are_estimated_not_a_crash() -> None:
    p, _, _ = make(lambda request: response_for(request, usage=False))

    batch = await p.embed(["x" * 300])

    assert len(batch.vectors) == 1
    assert batch.tokens > 0  # an upper-bound estimate (characters / 3, plus the prefix)
    assert p.tokens_used == batch.tokens


async def test_a_missing_index_on_the_first_item_means_zero_as_the_real_endpoint_does() -> None:
    """Found with the real API: the first item comes without `index` (proto3 omits a default 0)."""

    def first_item_has_no_index(request: httpx.Request) -> httpx.Response:
        body = response_for(request).json()
        del body["data"][0]["index"]
        return httpx.Response(200, json=body)

    p, _, _ = make(first_item_has_no_index)

    batch = await p.embed(["uno", "dos", "tres"])

    assert [v[0] for v in batch.vectors] == [0.0, 1.0, 2.0]


async def test_an_answer_with_no_indexes_at_all_keeps_the_order_it_came_in() -> None:
    def no_indexes(request: httpx.Request) -> httpx.Response:
        body = response_for(request).json()
        for item in body["data"]:
            del item["index"]
        return httpx.Response(200, json=body)

    p, _, _ = make(no_indexes)

    batch = await p.embed(["uno", "dos", "tres"])

    assert [v[0] for v in batch.vectors] == [0.0, 1.0, 2.0]


async def test_an_empty_list_sends_nothing() -> None:
    p, recorder, _ = make()

    batch = await p.embed([])

    assert (batch.vectors, batch.tokens) == ((), 0)
    assert recorder.requests == []


# ------------------------------------------------------------------ batching and the limiter
async def test_indexing_sends_small_batches_and_keeps_every_vector_in_order() -> None:
    p, recorder, _ = make()
    texts = [f"texto {i}" for i in range(BATCH_ITEMS * 2 + 3)]

    batch = await p.embed(texts)

    assert [len(r) for r in (recorder.inputs(n) for n in range(len(recorder.requests)))] == [
        BATCH_ITEMS,
        BATCH_ITEMS,
        3,
    ]
    assert len(batch.vectors) == len(texts)
    assert p.tokens_used == batch.tokens == 5 * len(texts)


async def test_a_batch_never_exceeds_half_of_the_tokens_per_minute_ceiling() -> None:
    p, recorder, _ = make(max_tokens_per_minute=2_000)  # half = 1,000 tokens ≈ 3,000 characters
    texts = ["a" * 1_500] * 6  # each ≈ 500 tokens (+ prefix)

    await p.embed(texts)

    assert max(len(recorder.inputs(n)) for n in range(len(recorder.requests))) <= 2


async def test_the_limiter_makes_indexing_wait_instead_of_failing_with_429() -> None:
    clock = Clock()
    p, recorder, clock = make(max_tokens_per_minute=3_000, clock=clock)
    texts = ["a" * 2_700] * 4  # ≈ 900 tokens each, batches of one: 3,000 per minute holds three

    await p.embed(texts)

    assert len(recorder.requests) == 4  # nothing was dropped
    assert clock.slept, "it had to wait for the minute to pass"
    assert clock.now >= 60.0 - 0.5  # the fourth request went out only after the window moved


async def test_every_text_counts_as_one_request_against_the_per_minute_ceiling() -> None:
    """Found with the real API: Google's free tier allows 100 embed requests a minute, per TEXT."""
    clock = Clock()
    p, recorder, clock = make(max_requests_per_minute=30, clock=clock)
    texts = [f"texto {i}" for i in range(70)]  # 16 per batch: 16+16+16+16+6

    await p.embed(texts)

    assert len(recorder.requests) == 5
    assert sum(len(recorder.inputs(n)) for n in range(5)) == 70  # nothing was dropped
    # 30 a minute: the first 16 go at once, every later batch has to wait for room in the minute
    assert clock.slept, "70 texts cannot go out inside one minute at 30 per minute"
    assert (
        clock.now >= 120.0 - 0.5
    )  # 70 texts need three minutes of 30: the last batch goes out in the third


async def test_a_429_while_indexing_waits_a_whole_minute_and_sends_the_same_batch_again() -> None:
    clock = Clock()
    answers = iter([429, 200])

    def limited_once(request: httpx.Request) -> httpx.Response:
        if next(answers) == 429:
            return httpx.Response(429, json={"error": {"message": "slow down"}})
        return response_for(request)

    p, recorder, clock = make(limited_once, clock=clock)

    batch = await p.embed(["uno", "dos"])

    assert len(recorder.requests) == 2  # the same batch twice
    assert recorder.inputs(0) == recorder.inputs(1)
    assert 65.0 in clock.slept  # a whole window, not a quick retry
    assert len(batch.vectors) == 2


async def test_a_429_that_never_clears_is_given_up_with_a_rate_limit_error() -> None:
    clock = Clock()
    p, recorder, clock = make(
        lambda request: httpx.Response(429, json={"error": {"message": "x"}}), clock=clock
    )

    with pytest.raises(EmbeddingRateLimitedError, match="limiting requests"):
        await p.embed(["uno"])

    assert len(recorder.requests) == 5  # the first try and four more after a pause each
    assert clock.slept.count(65.0) == 4


async def test_an_interactive_query_does_not_wait_out_a_429_it_degrades() -> None:
    clock = Clock()
    p, recorder, clock = make(
        lambda request: httpx.Response(429, json={"error": {"message": "x"}}), clock=clock
    )

    with pytest.raises(EmbeddingUnavailableError, match="limiting requests"):
        await p.embed(["plazo"], purpose=EmbeddingPurpose.QUERY, timeout_seconds=3.0)

    assert len(recorder.requests) == 1
    assert clock.slept == []


async def test_an_interactive_query_never_waits_for_the_limiter() -> None:
    clock = Clock()
    p, recorder, clock = make(max_tokens_per_minute=1_000, clock=clock)
    await p.embed(["a" * 2_900])  # uses up the minute

    await p.embed(["plazo"], purpose=EmbeddingPurpose.QUERY, timeout_seconds=3.0)

    assert len(recorder.requests) == 2
    assert clock.now == 0.0  # a person is waiting: it answers or degrades, it does not queue


async def test_the_limiter_alone_lets_a_request_through_when_there_is_room() -> None:
    clock = Clock()
    limiter = PerMinuteLimit(1_000, clock=clock, sleep=clock.sleep)

    await limiter.acquire(400)
    await limiter.acquire(400)

    assert clock.slept == []


async def test_the_limiter_clamps_a_request_bigger_than_the_ceiling_instead_of_waiting_forever() -> (
    None
):
    clock = Clock()
    limiter = PerMinuteLimit(1_000, clock=clock, sleep=clock.sleep)

    await limiter.acquire(50_000)

    assert clock.slept == []


# ------------------------------------------------------------------ failures
@pytest.mark.spec("004-FR-013")
@pytest.mark.parametrize(
    ("status", "message"),
    [
        (400, "an error (HTTP 400)"),
        (401, "API key is not valid"),
        (403, "has no permission for this call"),
        (404, "does not know that model or address (HTTP 404)"),
        (429, "limiting requests"),
        (503, "server error (HTTP 503)"),
    ],
)
async def test_every_http_failure_becomes_a_degradation_with_a_safe_message(
    status: int, message: str
) -> None:
    p, _, _ = make(
        lambda request: httpx.Response(
            status, json={"error": {"message": f"echo of your input: {QUESTION}", "status": "X"}}
        )
    )

    with pytest.raises(EmbeddingUnavailableError, match=re.escape(message)) as raised:
        await p.embed([QUESTION], purpose=EmbeddingPurpose.QUERY, timeout_seconds=3.0)

    text = str(raised.value)
    assert QUESTION not in text
    assert "12345678" not in text
    assert KEY.get_secret_value() not in text


@pytest.mark.spec("004-FR-014")
async def test_the_key_is_not_in_the_repr_of_the_provider_nor_in_a_failure_while_indexing() -> None:
    p, _, _ = make(lambda request: httpx.Response(401, json={"error": {"message": "bad"}}))

    with pytest.raises(EmbeddingUnavailableError) as raised:
        await p.embed([QUESTION])

    assert KEY.get_secret_value() not in repr(p)
    assert KEY.get_secret_value() not in str(raised.value)
    assert QUESTION not in str(raised.value)


async def test_an_unreachable_provider_is_a_degradation() -> None:
    def boom(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route")

    p, _, _ = make(boom)

    with pytest.raises(EmbeddingUnavailableError, match="Could not reach"):
        await p.embed(["x"], purpose=EmbeddingPurpose.QUERY, timeout_seconds=3.0)


# ------------------------------------------------------------------ verify
async def test_verify_is_one_tiny_real_embedding_that_proves_key_model_and_address() -> None:
    p, recorder, _ = make()

    await p.verify()

    assert len(recorder.requests) == 1
    assert recorder.inputs() == ["task: search result | query: prueba"]


async def test_verify_says_the_key_is_not_valid_when_google_refuses_it() -> None:
    p, _, _ = make(lambda request: httpx.Response(401, json={"error": {"message": "no"}}))

    with pytest.raises(EmbeddingUnavailableError, match="API key is not valid"):
        await p.verify()


async def test_verify_says_the_model_is_unknown_on_a_404() -> None:
    p, _, _ = make(lambda request: httpx.Response(404, json={"error": {"message": "no"}}))

    with pytest.raises(EmbeddingUnavailableError, match="does not know that model"):
        await p.verify()
