"""A deterministic, offline EmbeddingProvider for tests and demos (never for production).

Feature hashing of the words of a text into a vector of 256 numbers: texts that share words are close. To
simulate "meaning" without a network, ``aliases`` maps words to a shared concept
(``{"mototaxi": "menores"}``: a text with "mototaxi" is then as close as possible to one with "menores").
"""

import hashlib
import math
from collections.abc import Mapping, Sequence

from drtc_chatbot.contexts.retrieval.application.ports import EmbeddingBatch
from drtc_chatbot.contexts.retrieval.domain.lexical import strip_accents, words

DIMENSIONS = 256


class FakeEmbeddingProvider:
    external = False

    def __init__(
        self, aliases: Mapping[str, str] | None = None, *, model: str = "fake-hash-256"
    ) -> None:
        self._aliases = dict(aliases or {})
        self._model = model
        self.calls: list[int] = []  # size of every batch asked for (tests assert on cost behaviour)
        self._tokens_used = 0

    @property
    def model(self) -> str:
        return self._model

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    async def embed(
        self, texts: Sequence[str], *, timeout_seconds: float | None = None
    ) -> EmbeddingBatch:
        del timeout_seconds
        self.calls.append(len(texts))
        vectors = tuple(self._vector(text) for text in texts)
        tokens = sum(len(words(t)) for t in texts)
        self._tokens_used += tokens
        return EmbeddingBatch(vectors, tokens=tokens)

    def _vector(self, text: str) -> tuple[float, ...]:
        values = [0.0] * DIMENSIONS
        for word in words(text):
            key = self._aliases.get(strip_accents(word), strip_accents(word))
            digest = hashlib.sha256(key.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big") % DIMENSIONS
            values[slot] += 1.0 if digest[4] % 2 else -1.0
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return tuple(v / norm for v in values)
