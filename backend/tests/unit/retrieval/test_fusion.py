"""Reciprocal Rank Fusion: hand-computable and property-style cases."""

import random

import pytest

from drtc_chatbot.contexts.retrieval.domain.fusion import reciprocal_rank_fusion


def keys(result: list) -> list[str]:  # type: ignore[type-arg]
    return [f.key for f in result]


@pytest.mark.spec("004-FR-008")
def test_the_score_is_the_sum_of_one_over_k_plus_rank_for_every_list_that_has_the_item() -> None:
    fused = reciprocal_rank_fusion({"words": ["a", "b"], "meaning": ["b", "c"]}, k=60)

    by_key = {f.key: f for f in fused}
    assert by_key["a"].score == pytest.approx(1 / 61)
    assert by_key["b"].score == pytest.approx(1 / 62 + 1 / 61)
    assert by_key["c"].score == pytest.approx(1 / 62)


@pytest.mark.spec("004-FR-008")
def test_what_both_methods_found_rises_above_what_only_one_found() -> None:
    # "b" is 2nd in both lists; "a" and "x" are 1st in only one list each
    fused = reciprocal_rank_fusion({"words": ["a", "b"], "meaning": ["x", "b"]}, k=60)

    assert keys(fused) == ["b", "a", "x"]
    assert fused[0].ranks == {"words": 2, "meaning": 2}


@pytest.mark.spec("004-FR-008")
def test_nothing_is_duplicated_and_nothing_is_lost() -> None:
    fused = reciprocal_rank_fusion({"w": ["a", "b", "c"], "m": ["c", "d", "a"]})

    assert sorted(keys(fused)) == ["a", "b", "c", "d"]


def test_a_list_alone_keeps_its_order() -> None:
    assert keys(reciprocal_rank_fusion({"words": ["c", "a", "b"]})) == ["c", "a", "b"]


def test_an_empty_list_or_no_lists_give_nothing() -> None:
    assert reciprocal_rank_fusion({}) == []
    assert keys(reciprocal_rank_fusion({"w": [], "m": ["a"]})) == ["a"]


def test_an_item_repeated_inside_one_list_counts_once_at_its_best_position() -> None:
    fused = reciprocal_rank_fusion({"w": ["a", "b", "a"]}, k=60)

    by_key = {f.key: f for f in fused}
    assert by_key["a"].ranks == {"w": 1}
    assert by_key["a"].score == pytest.approx(1 / 61)
    assert by_key["b"].ranks == {"w": 2}  # the repeat did not push "b" down


def test_ties_are_broken_by_the_best_individual_position_then_by_arrival_order() -> None:
    # a: 1st in words only; b: 1st in meaning only -> same score, same best rank: arrival order decides
    assert keys(reciprocal_rank_fusion({"words": ["a"], "meaning": ["b"]})) == ["a", "b"]
    # a symmetric case: same score and same best position, so the order of arrival decides
    tie = reciprocal_rank_fusion({"w": ["p", "q"], "m": ["q", "p"]})
    assert keys(tie) == ["p", "q"]  # same score 1/61 + 1/62; both best rank 1; "p" arrived first


def test_arm_weights_can_favour_one_method() -> None:
    plain = reciprocal_rank_fusion({"words": ["a"], "meaning": ["b"]})
    weighted = reciprocal_rank_fusion({"words": ["a"], "meaning": ["b"]}, weights={"meaning": 2.0})

    assert keys(plain) == ["a", "b"]
    assert keys(weighted) == ["b", "a"]


def test_a_smaller_k_makes_the_top_positions_count_more() -> None:
    lists = {"w": ["a", "x", "y"], "m": ["z", "w", "a"]}

    low = {f.key: f.score for f in reciprocal_rank_fusion(lists, k=1)}
    high = {f.key: f.score for f in reciprocal_rank_fusion(lists, k=100)}

    assert (
        low["a"] / low["z"] < high["a"] / high["z"]
    )  # with a high k the gap between ranks shrinks... so a catches up


def test_k_must_be_positive() -> None:
    with pytest.raises(ValueError, match="at least 1"):
        reciprocal_rank_fusion({"w": ["a"]}, k=0)


@pytest.mark.spec("004-SC-004")
def test_the_result_is_deterministic_and_independent_of_the_order_of_equal_inputs() -> None:
    rng = random.Random(7)
    items = [f"i{n}" for n in range(30)]
    for _ in range(20):
        a, b = items[:], items[:]
        rng.shuffle(a)
        rng.shuffle(b)
        first = reciprocal_rank_fusion({"w": a, "m": b})
        again = reciprocal_rank_fusion({"w": a, "m": b})
        assert keys(first) == keys(again)
        assert len(set(keys(first))) == 30
        assert [f.score for f in first] == sorted((f.score for f in first), reverse=True)


@pytest.mark.spec("004-SC-004")
def test_an_item_ranked_first_by_both_arms_is_always_first() -> None:
    rng = random.Random(11)
    for _ in range(30):
        rest = [f"r{n}" for n in range(15)]
        a = ["top", *rng.sample(rest, 15)]
        b = ["top", *rng.sample(rest, 15)]

        assert keys(reciprocal_rank_fusion({"w": a, "m": b}))[0] == "top"
