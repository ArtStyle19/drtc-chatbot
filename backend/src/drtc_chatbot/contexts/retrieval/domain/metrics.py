"""Retrieval metrics (spec 004). Pure and deterministic: the same results always give the same numbers.

Two levels, because "found" depends on what the person needs:

* ``provision``: the result IS the expected provision or is BELOW it (the expected article is
  satisfied by one of its numerals); a parent of the expected provision does not count;
* ``unit``: the result lives in the same reading unit (article, disposition, annex) as the expected
  provision, which is what the reader opens.

Ranks count DISTINCT items at the level, so five numerals of one article take one place at unit level.
"""

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from statistics import median

from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    LEVELS,
    Expectation,
    Level,
    MethodReport,
    Metrics,
    QuestionOutcome,
    RankedResult,
    SliceMetrics,
)

DEFAULT_KS: tuple[int, ...] = (1, 3, 5, 10)
BASELINE_TOLERANCE = 0.02
WORST_LIMIT = 10
TOP_SHOWN = 3


def is_match(expectation: Expectation, result: RankedResult, level: Level) -> bool:
    if result.version_id != expectation.version_id:
        return False
    if level == "unit":
        return result.unit_path == expectation.unit_path
    return result.path == expectation.path or result.path.startswith(expectation.path + "/")


def distinct(results: Iterable[RankedResult], level: Level) -> list[RankedResult]:
    seen: set[tuple[str, str]] = set()
    unique: list[RankedResult] = []
    for result in results:
        key = (result.version_id, result.unit_path if level == "unit" else result.path)
        if key not in seen:
            seen.add(key)
            unique.append(result)
    return unique


def hit_ranks(
    expectations: Sequence[Expectation], results: Sequence[RankedResult], level: Level
) -> tuple[int | None, ...]:
    """1-based position of the first match of each expectation (None when it was missed)."""
    items = distinct(results, level)
    ranks: list[int | None] = []
    for expectation in expectations:
        rank = next(
            (i for i, item in enumerate(items, start=1) if is_match(expectation, item, level)),
            None,
        )
        ranks.append(rank)
    return tuple(ranks)


def aggregate(
    outcomes: Sequence[QuestionOutcome], level: Level, ks: Sequence[int] = DEFAULT_KS
) -> Metrics:
    """Metrics over the ANSWERABLE questions that have something to find."""
    scored = [o for o in outcomes if o.answerable and o.ranks.get(level)]
    if not scored:
        return Metrics(0, dict.fromkeys(ks, 0.0), dict.fromkeys(ks, 0.0), 0.0)
    hit = dict.fromkeys(ks, 0.0)
    recall = dict.fromkeys(ks, 0.0)
    reciprocal = 0.0
    for outcome in scored:
        ranks = outcome.ranks[level]
        found = [r for r in ranks if r is not None]
        reciprocal += 1 / min(found) if found else 0.0
        for k in ks:
            within = [r for r in found if r <= k]
            hit[k] += 1.0 if within else 0.0
            recall[k] += len(within) / len(ranks)
    n = len(scored)
    return Metrics(
        n, {k: v / n for k, v in hit.items()}, {k: v / n for k, v in recall.items()}, reciprocal / n
    )


def _slice(outcomes: Sequence[QuestionOutcome], ks: Sequence[int]) -> SliceMetrics:
    return SliceMetrics(
        provision=aggregate(outcomes, "provision", ks), unit=aggregate(outcomes, "unit", ks)
    )


def _group(
    outcomes: Sequence[QuestionOutcome],
    keys: Callable[[QuestionOutcome], Iterable[str]],
    ks: Sequence[int],
) -> dict[str, SliceMetrics]:
    groups: dict[str, list[QuestionOutcome]] = {}
    for outcome in outcomes:
        for key in keys(outcome):
            groups.setdefault(key, []).append(outcome)
    return {key: _slice(group, ks) for key, group in sorted(groups.items())}


def percentile(values: Sequence[float], q: float) -> float:
    """Nearest-rank percentile (q in 0..100); 0.0 for no values."""
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q / 100 * len(ordered)) - 1)]


def _best_unit_rank(outcome: QuestionOutcome) -> int | None:
    found = [rank for rank in outcome.ranks.get("unit", ()) if rank is not None]
    return min(found) if found else None


def _worst(outcomes: Sequence[QuestionOutcome]) -> tuple[Mapping[str, object], ...]:
    """Answerable questions NOT solved at the first place: missed ones first, then the deepest."""
    problems = [
        o
        for o in outcomes
        if o.answerable
        and o.ranks.get("unit")
        and (_best_unit_rank(o) is None or (_best_unit_rank(o) or 0) > 1)
    ]
    problems.sort(
        key=lambda o: (_best_unit_rank(o) is not None, -(_best_unit_rank(o) or 0), o.question_id)
    )
    return tuple(
        {
            "id": o.question_id,
            "question": o.text,
            "expected": list(o.expected),
            "unit_ranks": list(o.ranks["unit"]),
            "top": list(o.top),
        }
        for o in problems[:WORST_LIMIT]
    )


def build_method_report(
    method: str,
    outcomes: Sequence[QuestionOutcome],
    ks: Sequence[int] = DEFAULT_KS,
) -> MethodReport:
    unanswerable = [o for o in outcomes if not o.answerable]
    scores = [o.top_score for o in unanswerable if o.top_score is not None]
    unanswerable_summary: dict[str, object] = {
        "n": len(unanswerable),
        "with_results": sum(1 for o in unanswerable if o.returned > 0),
    }
    if scores:
        unanswerable_summary["top_score"] = {
            "min": round(min(scores), 4),
            "median": round(median(scores), 4),
            "max": round(max(scores), 4),
        }
    latencies = [o.latency_ms for o in outcomes]
    return MethodReport(
        method=method,
        questions=len(outcomes),
        answerable=sum(1 for o in outcomes if o.answerable),
        overall=_slice(outcomes, ks),
        by_tag=_group(outcomes, lambda o: o.tags, ks),
        by_intent=_group(outcomes, lambda o: (o.intent,), ks),
        by_review_status=_group(outcomes, lambda o: (o.review_status,), ks),
        latency_ms={
            "p50": round(percentile(latencies, 50), 1),
            "p95": round(percentile(latencies, 95), 1),
        },
        worst=_worst(outcomes),
        unanswerable=unanswerable_summary,
        degraded_questions=sum(1 for o in outcomes if o.degraded),
    )


@dataclass(frozen=True, slots=True)
class Regression:
    method: str
    slice: str
    level: str
    metric: str
    baseline: float
    current: float

    def describe(self) -> str:
        return (
            f"{self.method} · {self.slice} · {self.level} · {self.metric}: "
            f"{self.baseline:g} → {self.current:g}"
        )


def baseline_of(
    reports: Iterable[MethodReport],
) -> dict[str, dict[str, dict[str, dict[str, float | int]]]]:
    """The numbers a baseline pins: per method, ``overall`` and each tag, at both levels."""
    return {r.method: {name: s.as_dict() for name, s in r.slices().items()} for r in reports}


def compare_to_baseline(
    reports: Iterable[MethodReport],
    baseline: Mapping[str, Mapping[str, Mapping[str, Mapping[str, float]]]],
    tolerance: float = BASELINE_TOLERANCE,
) -> list[Regression]:
    """Everything that got WORSE than the baseline by more than ``tolerance``.

    A different number of scored questions (``n``) is reported too: it means the dataset or the
    corpus changed, so the baseline has to be regenerated on purpose (with a changelog entry).
    """
    regressions: list[Regression] = []
    for report in reports:
        pinned = baseline.get(report.method)
        if pinned is None:
            continue
        for name, current in report.slices().items():
            if name not in pinned:
                continue
            for level in LEVELS:
                now = (
                    current.provision.as_dict() if level == "provision" else current.unit.as_dict()
                )
                before = pinned[name][level]
                for metric, base_value in before.items():
                    value = float(now[metric])
                    if metric == "n":
                        if value != base_value:
                            regressions.append(
                                Regression(report.method, name, level, "n", base_value, value)
                            )
                    elif value < base_value - tolerance:
                        regressions.append(
                            Regression(report.method, name, level, metric, base_value, value)
                        )
    return regressions
