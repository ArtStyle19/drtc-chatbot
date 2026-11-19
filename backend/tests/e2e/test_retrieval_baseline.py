"""The evaluation gate (spec 004): the deterministic arms must not get worse than the baseline.

Runs the real golden set over the three real norms in PostgreSQL. No network, no API key: only the
methods that need none are evaluated here (exact now; words from the lexical phase on).
"""

import pytest

from drtc_chatbot.contexts.retrieval.domain.metrics import compare_to_baseline
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker

ACTOR = Actor("test", ActorKind.SERVICE)
DETERMINISTIC = ("exact",)


@pytest.mark.spec("004-FR-004")
async def test_the_deterministic_methods_do_not_get_worse_than_the_committed_baseline(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        module = container.retrieval_cli
        questions = list(module.golden_set(module.default_dataset).load())
        reports = [
            await module.run_evaluation.execute(ACTOR, module.retrievers[name], questions)
            for name in DETERMINISTIC
        ]
        baseline = module.store.read_baseline()

    regressions = compare_to_baseline(reports, baseline["methods"])

    assert [r.describe() for r in regressions] == []


@pytest.mark.spec("004-SC-002")
async def test_the_exact_arm_puts_every_question_with_an_explicit_reference_first(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        module = container.retrieval_cli
        questions = list(module.golden_set(module.default_dataset).load())
        report = await module.run_evaluation.execute(ACTOR, module.retrievers["exact"], questions)

    explicit = report.by_tag["explicit_reference"]
    assert explicit.unit.n >= 6
    assert explicit.unit.hit[1] == 1.0
    assert explicit.provision.hit[1] == 1.0


@pytest.mark.spec("004-FR-009")
async def test_the_exact_arm_never_answers_a_question_that_has_no_answer_in_the_corpus(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        module = container.retrieval_cli
        questions = list(module.golden_set(module.default_dataset).load())
        report = await module.run_evaluation.execute(ACTOR, module.retrievers["exact"], questions)

    assert report.unanswerable["n"] >= 8
    assert report.unanswerable["with_results"] == 0
