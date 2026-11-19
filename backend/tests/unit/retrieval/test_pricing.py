"""Cost estimate shown before any run that sends text to a provider."""

import pytest

from drtc_chatbot.contexts.retrieval.domain.pricing import (
    PRICE_PER_MILLION_TOKENS,
    estimate_cost_usd,
    estimate_tokens,
)


@pytest.mark.spec("004-FR-005")
@pytest.mark.parametrize(
    ("chars", "tokens"), [(0, 0), (-5, 0), (1, 1), (3, 1), (4, 2), (692_000, 230_667)]
)
def test_tokens_are_estimated_as_an_upper_bound_of_three_characters_each(
    chars: int, tokens: int
) -> None:
    assert estimate_tokens(chars) == tokens


@pytest.mark.spec("004-FR-005")
def test_the_whole_corpus_costs_cents_with_either_candidate_model() -> None:
    tokens = estimate_tokens(692_000)  # about what the three norms hold

    small = estimate_cost_usd(tokens, "text-embedding-3-small")
    large = estimate_cost_usd(tokens, "text-embedding-3-large")

    assert small == pytest.approx(0.0046, abs=0.0001)
    assert large == pytest.approx(0.030, abs=0.001)
    assert (small or 0) + (large or 0) < 0.50  # SC-010: both models, well under half a dollar


def test_an_unknown_model_has_no_price_instead_of_a_wrong_one() -> None:
    assert estimate_cost_usd(1_000_000, "otro-modelo") is None


def test_prices_can_be_overridden() -> None:
    assert estimate_cost_usd(1_000_000, "x", {"x": 0.5}) == 0.5


def test_both_candidate_models_have_a_price() -> None:
    assert set(PRICE_PER_MILLION_TOKENS) >= {"text-embedding-3-small", "text-embedding-3-large"}
