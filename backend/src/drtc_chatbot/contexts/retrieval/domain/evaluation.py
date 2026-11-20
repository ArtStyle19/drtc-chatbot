"""Entities of the retrieval evaluation (spec 004): golden questions, what a method returned and the
outcome of one question. Pure Python; the metrics live in ``metrics.py``.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

Level = Literal["provision", "unit"]
LEVELS: tuple[Level, ...] = ("provision", "unit")


@dataclass(frozen=True, slots=True)
class GoldenCitation:
    """What the golden set says a good answer cites (``path`` is None for non-provisions)."""

    version_id: str
    path: str | None
    provision: str


@dataclass(frozen=True, slots=True)
class GoldenQuestion:
    id: str
    text: str
    intent: str
    answerable: bool
    review_status: str
    tags: tuple[str, ...]
    citations: tuple[GoldenCitation, ...]


@dataclass(frozen=True, slots=True)
class Expectation:
    """A provision a good retrieval must surface, with the reading unit that contains it."""

    version_id: str
    path: str
    unit_path: str


@dataclass(frozen=True, slots=True)
class RankedResult:
    """One result of a retrieval method, best first. ``score`` is method-specific (may be None)."""

    version_id: str
    path: str
    unit_path: str
    score: float | None = None


@dataclass(frozen=True, slots=True)
class QuestionOutcome:
    """How one method did on one question."""

    question_id: str
    text: str
    intent: str
    review_status: str
    tags: tuple[str, ...]
    answerable: bool
    expected: tuple[str, ...]  # expected provision paths (for the "worst" list)
    # 1-based position of each expectation among the DISTINCT results at that level (None = missed).
    ranks: Mapping[Level, tuple[int | None, ...]]
    top: tuple[str, ...]  # the first provision paths returned
    returned: int
    latency_ms: float
    degraded: tuple[str, ...] = ()
    top_score: float | None = None


@dataclass(frozen=True, slots=True)
class Metrics:
    """Aggregate of a set of answerable questions at one level."""

    n: int
    hit: Mapping[int, float]  # share of questions with ANY expected item in the top K
    recall: Mapping[int, float]  # mean share of the expected items found in the top K
    mrr: float  # mean reciprocal rank of the first expected item found

    def as_dict(self) -> dict[str, float | int]:
        values: dict[str, float | int] = {"n": self.n}
        values.update({f"hit@{k}": round(v, 4) for k, v in sorted(self.hit.items())})
        values.update({f"recall@{k}": round(v, 4) for k, v in sorted(self.recall.items())})
        values["mrr"] = round(self.mrr, 4)
        return values


@dataclass(frozen=True, slots=True)
class SliceMetrics:
    provision: Metrics
    unit: Metrics

    def as_dict(self) -> dict[str, dict[str, float | int]]:
        return {"provision": self.provision.as_dict(), "unit": self.unit.as_dict()}


@dataclass(frozen=True, slots=True)
class MethodReport:
    method: str
    questions: int
    answerable: int
    overall: SliceMetrics
    by_tag: Mapping[str, SliceMetrics]
    by_intent: Mapping[str, SliceMetrics]
    by_review_status: Mapping[str, SliceMetrics]
    latency_ms: Mapping[str, float]
    worst: tuple[Mapping[str, object], ...]
    unanswerable: Mapping[str, object]
    degraded_questions: int = 0
    extra: Mapping[str, object] = field(default_factory=dict)

    def slices(self) -> dict[str, SliceMetrics]:
        """The slices a baseline pins: everything, and each tag."""
        result = {"overall": self.overall}
        result.update({f"tag:{tag}": metrics for tag, metrics in sorted(self.by_tag.items())})
        return result

    def as_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "questions": self.questions,
            "answerable": self.answerable,
            "degraded_questions": self.degraded_questions,
            "overall": self.overall.as_dict(),
            "by_tag": {k: v.as_dict() for k, v in sorted(self.by_tag.items())},
            "by_intent": {k: v.as_dict() for k, v in sorted(self.by_intent.items())},
            "by_review_status": {k: v.as_dict() for k, v in sorted(self.by_review_status.items())},
            "latency_ms": dict(self.latency_ms),
            "unanswerable": dict(self.unanswerable),
            "worst": [dict(item) for item in self.worst],
            **({"extra": dict(self.extra)} if self.extra else {}),
        }
