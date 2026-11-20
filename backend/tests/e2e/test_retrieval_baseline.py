"""The evaluation gate (spec 004): the deterministic arms must not get worse than the baseline.

Runs the real golden set over the three real norms in PostgreSQL. No network, no API key: only the
methods that need none are evaluated here (exact and words).
"""

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from drtc_chatbot.bootstrap.container import Container
from drtc_chatbot.contexts.retrieval.application.lexical_retriever import LexicalRetriever
from drtc_chatbot.contexts.retrieval.domain.evaluation import MethodReport
from drtc_chatbot.contexts.retrieval.domain.metrics import compare_to_baseline
from drtc_chatbot.contexts.retrieval.infrastructure.sql_passage_index import (
    LexicalTuning,
    SqlPassageIndex,
)
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker

ACTOR = Actor("test", ActorKind.SERVICE)
DETERMINISTIC = ("exact", "lexical")


async def evaluate(
    container: Container, name: str, retriever: object | None = None
) -> MethodReport:
    module = container.retrieval_cli
    questions = list(module.golden_set(module.default_dataset).load())
    return await module.run_evaluation.execute(
        ACTOR, retriever or module.retrievers[name], questions
    )  # type: ignore[arg-type]


@pytest.mark.spec("004-FR-004")
async def test_the_deterministic_methods_do_not_get_worse_than_the_committed_baseline(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        await container.retrieval_cli.build_index.execute(ACTOR)
        reports = [await evaluate(container, name) for name in DETERMINISTIC]
        baseline = container.retrieval_cli.store.read_baseline()

    regressions = compare_to_baseline(reports, baseline["methods"])

    assert [r.describe() for r in regressions] == []


@pytest.mark.spec("004-SC-007")
async def test_the_gate_fails_when_the_words_search_is_deliberately_degraded(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        await container.retrieval_cli.build_index.execute(ACTOR)
        sessions = async_sessionmaker(container.engine, expire_on_commit=False)
        # no length normalisation and equal weights: a plausible "optimisation" that is in fact worse
        worse = LexicalRetriever(
            SqlPassageIndex(sessions, LexicalTuning(weights=(1.0, 1.0, 1.0, 1.0), normalization=0))
        )
        report = await evaluate(container, "lexical", worse)
        baseline = container.retrieval_cli.store.read_baseline()

    regressions = compare_to_baseline([report], baseline["methods"])

    assert regressions, "a clearly worse ranking must not pass the gate"
    assert any(r.metric == "mrr" and r.level == "unit" for r in regressions)


@pytest.mark.spec("004-SC-002")
async def test_the_exact_arm_puts_every_question_with_an_explicit_reference_first(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        report = await evaluate(container, "exact")

    explicit = report.by_tag["explicit_reference"]
    assert explicit.unit.n >= 6
    assert explicit.unit.hit[1] == 1.0
    assert explicit.provision.hit[1] == 1.0


@pytest.mark.spec("004-FR-009")
async def test_the_exact_arm_never_answers_a_question_that_has_no_answer_in_the_corpus(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        report = await evaluate(container, "exact")

    assert report.unanswerable["n"] >= 8
    assert report.unanswerable["with_results"] == 0


@pytest.mark.spec("004-FR-016")
async def test_indexing_the_real_corpus_is_idempotent(full_corpus: str) -> None:
    async with open_stack(full_corpus) as (_, container):
        first = await container.retrieval_cli.build_index.execute(ACTOR)
        second = await container.retrieval_cli.build_index.execute(ACTOR)

    assert first.added > 2500
    assert (first.changed, first.removed) == (0, 0)
    assert (second.added, second.changed, second.removed) == (0, 0, 0)
    assert second.unchanged == first.added
