"""Retrieval metrics (spec 004): hand-computable cases."""

import pytest

from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    Expectation,
    Level,
    QuestionOutcome,
    RankedResult,
)
from drtc_chatbot.contexts.retrieval.domain.metrics import (
    aggregate,
    baseline_of,
    build_method_report,
    compare_to_baseline,
    distinct,
    hit_ranks,
    is_match,
    percentile,
)

V = "tuo-ley-27444@x"


def result(
    path: str, unit: str | None = None, version: str = V, score: float | None = None
) -> RankedResult:
    return RankedResult(version, path, unit or path.split("/", maxsplit=1)[0], score)


def expected(path: str, unit: str | None = None, version: str = V) -> Expectation:
    return Expectation(version, path, unit or path.split("/", maxsplit=1)[0])


def outcome(
    qid: str = "q-001",
    *,
    ranks_unit: tuple[int | None, ...] = (1,),
    ranks_provision: tuple[int | None, ...] | None = None,
    answerable: bool = True,
    tags: tuple[str, ...] = (),
    intent: str = "concept",
    status: str = "draft",
    returned: int = 3,
    latency: float = 10.0,
    top_score: float | None = None,
) -> QuestionOutcome:
    ranks: dict[Level, tuple[int | None, ...]] = {
        "unit": ranks_unit,
        "provision": ranks_unit if ranks_provision is None else ranks_provision,
    }
    return QuestionOutcome(
        question_id=qid, text=f"pregunta {qid}", intent=intent, review_status=status, tags=tags,
        answerable=answerable, expected=("articulo:1",) if answerable else (), ranks=ranks,
        top=("articulo:1",), returned=returned, latency_ms=latency, top_score=top_score,
    )  # fmt: skip


# ------------------------------------------------------------------------------ matching
@pytest.mark.parametrize(
    ("expectation", "returned", "level", "ok"),
    [
        (("articulo:218/numeral:218.2",), "articulo:218/numeral:218.2", "provision", True),
        (("articulo:218",), "articulo:218/numeral:218.2", "provision", True),  # below the expected
        (("articulo:218/numeral:218.2",), "articulo:218", "provision", False),  # above: not enough
        (
            ("articulo:21",),
            "articulo:218",
            "provision",
            False,
        ),  # a prefix of the text is not a path
        (("articulo:218/numeral:218.2",), "articulo:218/numeral:218.1", "provision", False),
        (("articulo:218/numeral:218.2",), "articulo:218/numeral:218.1", "unit", True),  # same unit
        (("articulo:218/numeral:218.2",), "articulo:219", "unit", False),
    ],
)
def test_a_result_matches_at_provision_or_unit_level(
    expectation: tuple[str], returned: str, level: Level, ok: bool
) -> None:
    assert is_match(expected(*expectation), result(returned), level) is ok


def test_the_same_path_in_another_edition_is_not_a_match() -> None:
    assert not is_match(expected("articulo:5"), result("articulo:5", version="otra@v2"), "unit")


# ------------------------------------------------------------------------------ ranks
def test_ranks_count_distinct_items_at_the_level() -> None:
    results = [
        result("articulo:218/numeral:218.1"),
        result("articulo:218/numeral:218.2"),
        result("articulo:219"),
        result("articulo:220"),
    ]

    # unit level: the two numerals of article 218 take ONE place, so article 220 is 3rd (not 4th)
    assert [i.unit_path for i in distinct(results, "unit")] == [
        "articulo:218",
        "articulo:219",
        "articulo:220",
    ]
    assert hit_ranks([expected("articulo:220")], results, "unit") == (3,)
    assert hit_ranks([expected("articulo:220")], results, "provision") == (4,)


def test_each_expectation_gets_its_own_rank_and_misses_are_none() -> None:
    results = [result("articulo:2"), result("articulo:9"), result("articulo:5")]

    ranks = hit_ranks(
        [expected("articulo:5"), expected("articulo:2"), expected("articulo:77")],
        results,
        "provision",
    )

    assert ranks == (3, 1, None)


def test_no_results_means_every_expectation_missed() -> None:
    assert hit_ranks([expected("articulo:1")], [], "unit") == (None,)


# ------------------------------------------------------------------------------ aggregate
def test_hit_rate_recall_and_mrr_by_hand() -> None:
    outcomes = [
        outcome("q-001", ranks_unit=(1,)),          # found 1st
        outcome("q-002", ranks_unit=(3,)),          # found 3rd
        outcome("q-003", ranks_unit=(None,)),       # missed
        outcome("q-004", ranks_unit=(2, None)),     # two expected, one found 2nd
    ]  # fmt: skip

    metrics = aggregate(outcomes, "unit", ks=(1, 3, 10))

    assert metrics.n == 4
    assert metrics.hit == {1: 0.25, 3: 0.75, 10: 0.75}  # q-001 | + q-002, q-004 | same
    # recall: q-004 finds 1 of 2 → 0.5 where the others find 1/1 or 0
    assert metrics.recall[3] == pytest.approx((1 + 1 + 0 + 0.5) / 4)
    assert metrics.mrr == pytest.approx((1 + 1 / 3 + 0 + 1 / 2) / 4)


def test_unanswerable_questions_and_questions_without_expectations_are_not_scored() -> None:
    outcomes = [
        outcome("q-001", ranks_unit=(1,)),
        outcome("q-010", ranks_unit=(), answerable=False),
        outcome("q-011", ranks_unit=()),  # answerable but its only citation had no path
    ]

    assert aggregate(outcomes, "unit").n == 1


def test_an_empty_set_gives_zeros_instead_of_dividing_by_zero() -> None:
    metrics = aggregate([], "unit")

    assert (metrics.n, metrics.mrr) == (0, 0.0)
    assert set(metrics.hit.values()) == {0.0}


def test_metrics_are_reported_with_stable_names() -> None:
    values = aggregate([outcome(ranks_unit=(2,))], "unit", ks=(1, 3)).as_dict()

    assert values == {
        "n": 1,
        "hit@1": 0.0,
        "hit@3": 1.0,
        "recall@1": 0.0,
        "recall@3": 1.0,
        "mrr": 0.5,
    }


# ------------------------------------------------------------------------------ percentiles
@pytest.mark.parametrize(
    ("values", "q", "expected_value"),
    [([], 50, 0.0), ([5.0], 95, 5.0), ([1.0, 2.0, 3.0, 4.0], 50, 2.0), ([1.0, 2.0, 3.0, 4.0], 95, 4.0),
     ([10.0, 1.0, 5.0], 100, 10.0)],
)  # fmt: skip
def test_nearest_rank_percentile(values: list[float], q: float, expected_value: float) -> None:
    assert percentile(values, q) == expected_value


# ------------------------------------------------------------------------------ report
def test_the_method_report_slices_by_tag_intent_and_review_status() -> None:
    outcomes = [
        outcome("q-001", ranks_unit=(1,), tags=("explicit_reference",), intent="exact_provision"),
        outcome("q-002", ranks_unit=(None,), tags=("colloquial",), status="approved"),
        outcome("q-003", ranks_unit=(4,), tags=("colloquial", "cross_norm")),
        outcome("q-010", ranks_unit=(), answerable=False, returned=2, top_score=0.4),
    ]

    report = build_method_report("lexical", outcomes, ks=(1, 3, 10))

    assert (report.questions, report.answerable) == (4, 3)
    assert report.overall.unit.hit[10] == pytest.approx(2 / 3)
    assert report.by_tag["explicit_reference"].unit.hit[1] == 1.0
    assert report.by_tag["colloquial"].unit.n == 2
    assert report.by_intent["exact_provision"].unit.n == 1
    assert report.by_review_status["approved"].unit.hit[10] == 0.0
    assert report.unanswerable == {
        "n": 1,
        "with_results": 1,
        "top_score": {"min": 0.4, "median": 0.4, "max": 0.4},
    }


def test_the_worst_list_puts_misses_first_then_the_deepest_hits_and_skips_first_places() -> None:
    outcomes = [
        outcome("q-001", ranks_unit=(1,)),
        outcome("q-002", ranks_unit=(7,)),
        outcome("q-003", ranks_unit=(None,)),
        outcome("q-004", ranks_unit=(3,)),
    ]

    worst = build_method_report("exact", outcomes).worst

    assert [w["id"] for w in worst] == ["q-003", "q-002", "q-004"]


def test_latency_percentiles_and_degraded_questions_are_reported() -> None:
    outcomes = [outcome(f"q-{i:03}", latency=float(i)) for i in range(1, 21)]

    report = build_method_report("hybrid", outcomes)

    assert report.latency_ms == {"p50": 10.0, "p95": 19.0}
    assert report.degraded_questions == 0


# ------------------------------------------------------------------------------ baseline
def _report(
    unit_ranks: tuple[int | None, ...] = (1,), tags: tuple[str, ...] = ("explicit_reference",)
):
    return build_method_report(
        "exact", [outcome("q-001", ranks_unit=unit_ranks, tags=tags)], ks=(1, 10)
    )


def test_a_baseline_pins_overall_and_each_tag_at_both_levels() -> None:
    pinned = baseline_of([_report()])

    assert set(pinned["exact"]) == {"overall", "tag:explicit_reference"}
    assert set(pinned["exact"]["overall"]) == {"provision", "unit"}
    assert pinned["exact"]["overall"]["unit"]["hit@1"] == 1.0


def test_the_same_numbers_are_not_a_regression() -> None:
    assert compare_to_baseline([_report()], baseline_of([_report()])) == []


def test_a_drop_larger_than_the_tolerance_is_reported_with_where_and_how_much() -> None:
    pinned = baseline_of([_report((1,))])

    regressions = compare_to_baseline([_report((None,))], pinned, tolerance=0.02)

    assert {(r.slice, r.level, r.metric) for r in regressions} >= {
        ("overall", "unit", "hit@1"),
        ("tag:explicit_reference", "provision", "mrr"),
    }
    assert regressions[0].baseline == 1.0
    assert regressions[0].current == 0.0
    assert "exact · " in regressions[0].describe()


def test_a_small_drop_within_the_tolerance_is_accepted() -> None:
    better = [outcome(f"q-{i:03}", ranks_unit=(1,)) for i in range(50)]
    worse = [
        outcome(f"q-{i:03}", ranks_unit=((None,) if i == 0 else (1,))) for i in range(50)
    ]  # 98 %
    pinned = baseline_of([build_method_report("exact", better, ks=(1,))])

    assert (
        compare_to_baseline([build_method_report("exact", worse, ks=(1,))], pinned, tolerance=0.02)
        == []
    )
    assert (
        compare_to_baseline([build_method_report("exact", worse, ks=(1,))], pinned, tolerance=0.01)
        != []
    )


def test_improvements_never_fail_the_gate() -> None:
    pinned = baseline_of([_report((None,))])

    assert compare_to_baseline([_report((1,))], pinned) == []


def test_a_different_number_of_scored_questions_asks_for_a_deliberate_new_baseline() -> None:
    pinned = baseline_of([_report()])
    bigger = build_method_report(
        "exact",
        [
            outcome("q-001", tags=("explicit_reference",)),
            outcome("q-002", tags=("explicit_reference",)),
        ],
        ks=(1, 10),
    )

    regressions = compare_to_baseline([bigger], pinned)

    assert {r.metric for r in regressions} == {"n"}


def test_methods_and_slices_missing_from_the_baseline_are_ignored() -> None:
    pinned = baseline_of([_report()])
    other = build_method_report("lexical", [outcome()], ks=(1, 10))

    assert compare_to_baseline([other], pinned) == []
