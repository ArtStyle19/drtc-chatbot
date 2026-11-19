"""Cost estimate of an embedding run (spec 004, FR-005): nothing is sent before this is shown.

Prices are per million tokens, in US dollars, as published by the provider on the date noted; they are
an ESTIMATE for confirming a run (the real usage reported by each response is what gets recorded) and
can be overridden by configuration when the provider changes them.
"""

import math
from collections.abc import Mapping

# Source: https://developers.openai.com/api/docs/models/text-embedding-3-small (and -large), 2026-11-18.
PRICE_PER_MILLION_TOKENS: Mapping[str, float] = {
    "text-embedding-3-small": 0.02,
    "text-embedding-3-large": 0.13,
    # Google, paid tier (the free tier charges nothing): an upper bound for a run on the free tier.
    # Source: https://ai.google.dev/gemini-api/docs/pricing, 2026-11-19.
    "gemini-embedding-2": 0.20,
    "gemini-embedding-001": 0.15,
}
# Upper bound for Spanish with the tokenizer of these models (about 3.5-4 characters per token), so
# the estimate shown before a run is never lower than what will really be billed.
CHARS_PER_TOKEN_UPPER_BOUND = 3


def estimate_tokens(characters: int) -> int:
    return math.ceil(max(characters, 0) / CHARS_PER_TOKEN_UPPER_BOUND)


def estimate_cost_usd(
    tokens: int, model: str, prices: Mapping[str, float] = PRICE_PER_MILLION_TOKENS
) -> float | None:
    """Dollars for ``tokens`` with ``model``; None when the model has no known price."""
    price = prices.get(model)
    return None if price is None else tokens / 1_000_000 * price
