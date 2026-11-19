"""Use case: measure a retrieval method with the golden set (spec 004, FR-003).

For each answerable question the expected provisions are resolved to their reading unit through the
SAME corpus index the search uses, so a golden path that does not exist fails loudly instead of
silently counting as a miss.
"""

import time
from collections.abc import Callable, Sequence

from drtc_chatbot.contexts.retrieval.application.ports import ProvisionDirectory, Retriever
from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    Expectation,
    GoldenQuestion,
    MethodReport,
    QuestionOutcome,
)
from drtc_chatbot.contexts.retrieval.domain.metrics import (
    DEFAULT_KS,
    TOP_SHOWN,
    build_method_report,
    distinct,
    hit_ranks,
)
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class EvaluationDataError(InvariantViolationError):
    """The golden set points at something the loaded corpus does not have."""


class RunEvaluation:
    def __init__(
        self, directory: ProvisionDirectory, *, timer: Callable[[], float] = time.perf_counter
    ) -> None:
        self._directory = directory
        self._timer = timer

    async def execute(
        self,
        actor: Actor,
        retriever: Retriever,
        questions: Sequence[GoldenQuestion],
        *,
        ks: Sequence[int] = DEFAULT_KS,
    ) -> MethodReport:
        units = await self._unit_index(actor)
        limit = max(ks)
        outcomes = [await self._run(actor, retriever, q, units, limit) for q in questions]
        return build_method_report(retriever.name, outcomes, ks)

    async def _unit_index(self, actor: Actor) -> dict[tuple[str, str], str]:
        """(edition, provision path) → reading unit, for the approved edition of every norm."""
        index: dict[tuple[str, str], str] = {}
        for norm in await self._directory.norms(actor):
            edition = await self._directory.edition(actor, norm.instrument_id)
            if edition is None:
                continue
            for entry in edition.entries:
                index[(edition.version_id, entry.path)] = entry.unit_path
        return index

    @staticmethod
    def _expectations(
        question: GoldenQuestion, units: dict[tuple[str, str], str]
    ) -> tuple[Expectation, ...]:
        expectations = []
        for citation in question.citations:
            if citation.path is None:
                continue  # not a provision of the corpus (e.g. a preamble): not scored
            unit = units.get((citation.version_id, citation.path))
            if unit is None:
                raise EvaluationDataError(
                    f"{question.id}: {citation.path} is not in the approved edition "
                    f"{citation.version_id}"
                )
            expectations.append(Expectation(citation.version_id, citation.path, unit))
        return tuple(expectations)

    async def _run(
        self,
        actor: Actor,
        retriever: Retriever,
        question: GoldenQuestion,
        units: dict[tuple[str, str], str],
        limit: int,
    ) -> QuestionOutcome:
        expectations = self._expectations(question, units) if question.answerable else ()
        started = self._timer()
        retrieval = await retriever.retrieve(actor, question.text, limit)
        latency_ms = (self._timer() - started) * 1000
        results = retrieval.results
        return QuestionOutcome(
            question_id=question.id,
            text=question.text,
            intent=question.intent,
            review_status=question.review_status,
            tags=question.tags,
            answerable=question.answerable,
            expected=tuple(e.path for e in expectations),
            ranks={
                "provision": hit_ranks(expectations, results, "provision"),
                "unit": hit_ranks(expectations, results, "unit"),
            },
            top=tuple(r.path for r in distinct(results, "provision")[:TOP_SHOWN]),
            returned=len(results),
            latency_ms=latency_ms,
            degraded=retrieval.degraded,
            top_score=results[0].score if results else None,
        )
