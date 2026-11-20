"""Running an evaluation: expectations resolved against the corpus index, outcomes per question."""

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from drtc_chatbot.contexts.retrieval.application.exact_retriever import ExactRetriever
from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference
from drtc_chatbot.contexts.retrieval.application.ports import Retrieval
from drtc_chatbot.contexts.retrieval.application.run_evaluation import (
    EvaluationDataError,
    RunEvaluation,
)
from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    GoldenCitation,
    GoldenQuestion,
    RankedResult,
)
from drtc_chatbot.contexts.retrieval.infrastructure.jsonl_golden_set import JsonlGoldenSet
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError
from tests.conftest import REPO_ROOT
from tests.unit.retrieval.test_lookup_reference import ANONYMOUS, FakeDirectory

LEY_V = "ley@1"


def question(
    qid: str = "q-001",
    text: str = "pregunta",
    *,
    path: str | None = "articulo:2",
    answerable: bool = True,
    tags: tuple[str, ...] = (),
    version: str = LEY_V,
) -> GoldenQuestion:
    citations = (GoldenCitation(version, path, "Ley 27181, art. 2"),) if answerable else ()
    return GoldenQuestion(qid, text, "concept", answerable, "draft", tags, citations)


class ScriptedRetriever:
    """Returns what it was told for each text; records latency-free calls."""

    name = "scripted"

    def __init__(self, answers: dict[str, Sequence[RankedResult]]) -> None:
        self.answers = answers
        self.limits: list[int] = []

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval:
        self.limits.append(limit)
        return Retrieval(tuple(self.answers.get(text, ())), degraded=())


def hit(path: str, unit: str | None = None, version: str = LEY_V) -> RankedResult:
    return RankedResult(version, path, unit or path.split("/", maxsplit=1)[0])


@pytest.mark.spec("004-FR-003")
async def test_a_method_is_scored_at_provision_and_unit_level() -> None:
    retriever = ScriptedRetriever(
        {
            "primera": [hit("articulo:5"), hit("articulo:2")],  # found 2nd
            "segunda": [hit("articulo:2/literal:e")],  # a literal of the expected article's unit
            "tercera": [hit("articulo:11")],  # missed
        }
    )
    questions = [
        question("q-001", "primera"),
        question("q-002", "segunda"),
        question("q-003", "tercera"),
    ]

    report = await RunEvaluation(FakeDirectory()).execute(
        ANONYMOUS, retriever, questions, ks=(1, 3)
    )  # type: ignore[arg-type]

    assert (report.method, report.questions, report.answerable) == ("scripted", 3, 3)
    assert report.overall.unit.hit == {1: pytest.approx(1 / 3), 3: pytest.approx(2 / 3)}
    # provision level: the literal is BELOW the expected article, so it counts there too
    assert report.overall.provision.hit[3] == pytest.approx(2 / 3)
    assert report.overall.unit.mrr == pytest.approx((1 / 2 + 1 + 0) / 3)
    assert [w["id"] for w in report.worst] == ["q-003", "q-001"]
    assert retriever.limits == [3, 3, 3]  # asks for as many results as the largest K


@pytest.mark.spec("004-FR-003")
async def test_a_deeper_expected_provision_needs_the_exact_path_or_something_below_it() -> None:
    retriever = ScriptedRetriever({"q": [hit("articulo:2"), hit("articulo:2/literal:e")]})

    report = await RunEvaluation(FakeDirectory()).execute(  # type: ignore[arg-type]
        ANONYMOUS, retriever, [question("q-001", "q", path="articulo:2/literal:e")], ks=(1, 3)
    )

    assert report.overall.unit.hit[1] == 1.0  # same unit: the article is already the right place
    assert report.overall.provision.hit[1] == 0.0  # but the article is ABOVE the expected literal
    assert report.overall.provision.hit[3] == 1.0


async def test_unanswerable_questions_are_reported_apart_and_never_scored() -> None:
    retriever = ScriptedRetriever(
        {"fuera": [RankedResult(LEY_V, "articulo:5", "articulo:5", score=0.42)]}
    )
    questions = [question("q-001", "x"), question("q-010", "fuera", answerable=False)]

    report = await RunEvaluation(FakeDirectory()).execute(ANONYMOUS, retriever, questions, ks=(1,))  # type: ignore[arg-type]

    assert report.answerable == 1
    assert report.overall.unit.n == 1
    assert report.unanswerable["with_results"] == 1
    assert report.unanswerable["top_score"] == {"min": 0.42, "median": 0.42, "max": 0.42}


async def test_a_citation_without_a_path_is_not_scored_but_the_question_still_runs() -> None:
    retriever = ScriptedRetriever({})

    report = await RunEvaluation(FakeDirectory()).execute(  # type: ignore[arg-type]
        ANONYMOUS, retriever, [question("q-008", "x", path=None)], ks=(1,)
    )

    assert report.questions == 1
    assert report.overall.unit.n == 0


async def test_a_golden_path_that_the_corpus_does_not_have_fails_loudly() -> None:
    with pytest.raises(
        EvaluationDataError, match="q-001: articulo:999 is not in the approved edition"
    ):
        await RunEvaluation(FakeDirectory()).execute(  # type: ignore[arg-type]
            ANONYMOUS, ScriptedRetriever({}), [question("q-001", path="articulo:999")], ks=(1,)
        )


async def test_an_edition_the_corpus_does_not_have_fails_loudly_too() -> None:
    with pytest.raises(EvaluationDataError):
        await RunEvaluation(FakeDirectory()).execute(  # type: ignore[arg-type]
            ANONYMOUS, ScriptedRetriever({}), [question("q-001", version="otra@v9")], ks=(1,)
        )


async def test_latency_is_measured_per_question_with_the_injected_clock() -> None:
    ticks = iter([0.0, 0.010, 1.0, 1.030])  # 10 ms then 30 ms
    use_case = RunEvaluation(FakeDirectory(), timer=lambda: next(ticks))  # type: ignore[arg-type]

    report = await use_case.execute(
        ANONYMOUS, ScriptedRetriever({}), [question("q-001", "a"), question("q-002", "b")], ks=(1,)
    )

    assert report.latency_ms == {"p50": 10.0, "p95": 30.0}


# ------------------------------------------------------------------------------ exact arm
@pytest.mark.spec("004-FR-009")
async def test_the_exact_arm_finds_a_provision_named_inside_a_natural_question() -> None:
    exact = ExactRetriever(LookupReference(FakeDirectory()))  # type: ignore[arg-type]

    found = await exact.retrieve(
        ANONYMOUS, "Según el artículo 2 de la Ley 27181, ¿qué es un servicio?", 10
    )

    assert [(r.version_id, r.path, r.unit_path) for r in found.results] == [
        (LEY_V, "articulo:2", "articulo:2")
    ]


async def test_the_exact_arm_lists_every_candidate_of_an_ambiguous_reference_and_never_chooses() -> (
    None
):
    exact = ExactRetriever(LookupReference(FakeDirectory()))  # type: ignore[arg-type]

    found = await exact.retrieve(ANONYMOUS, "art. 11", 10)

    assert [r.version_id for r in found.results] == ["ley@1", "renat@1", "tuo@1"]


@pytest.mark.parametrize("text", ["¿cómo se clasifican las infracciones?", "", "x" * 500])
async def test_the_exact_arm_returns_nothing_when_the_text_is_not_a_reference(text: str) -> None:
    exact = ExactRetriever(LookupReference(FakeDirectory()))  # type: ignore[arg-type]

    assert (await exact.retrieve(ANONYMOUS, text, 10)).results == ()


async def test_the_exact_arm_honours_the_limit_and_skips_whole_norm_hits() -> None:
    exact = ExactRetriever(LookupReference(FakeDirectory()))  # type: ignore[arg-type]

    assert len((await exact.retrieve(ANONYMOUS, "art. 11", 2)).results) == 2
    assert (
        await exact.retrieve(ANONYMOUS, "LPAG", 10)
    ).results == ()  # a whole norm is not a provision


# ------------------------------------------------------------------------------ loader
def _write(tmp_path: Path, *rows: dict) -> Path:
    path = tmp_path / "golden.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def _row(qid: str = "q-001", **overrides: object) -> dict:
    row = {
        "id": qid, "question": "¿Cuál es el plazo?", "intent": "exact_provision", "audience": "staff",
        "answerable": True, "tags": ["explicit_reference"], "review_status": "draft",
        "expected": {"answer_summary": "x", "citations": [
            {"version_id": "v1", "provision": "Ley 1, art. 2", "path": "articulo:2", "pdf_pages": [1],
             "supporting_text": "texto de respaldo", "page_role": "normative"}]},
    }  # fmt: skip
    row.update(overrides)
    return row


def test_the_loader_reads_questions_with_their_tags_and_citations(tmp_path: Path) -> None:
    [loaded] = JsonlGoldenSet(_write(tmp_path, _row())).load()

    assert (loaded.id, loaded.text, loaded.tags) == (
        "q-001",
        "¿Cuál es el plazo?",
        ("explicit_reference",),
    )
    assert loaded.citations == (GoldenCitation("v1", "articulo:2", "Ley 1, art. 2"),)


def test_the_loader_rejects_duplicated_ids_missing_fields_and_missing_files(tmp_path: Path) -> None:
    with pytest.raises(InvariantViolationError, match="Duplicated"):
        JsonlGoldenSet(_write(tmp_path, _row("q-001"), _row("q-001"))).load()
    broken = _row()
    del broken["intent"]
    with pytest.raises(InvariantViolationError, match="Line 1: missing field 'intent'"):
        JsonlGoldenSet(_write(tmp_path, broken)).load()
    with pytest.raises(InvariantViolationError, match="not found"):
        JsonlGoldenSet(tmp_path / "nope.jsonl").load()


def test_the_real_golden_set_loads() -> None:
    questions = JsonlGoldenSet(REPO_ROOT / "evaluation" / "datasets" / "golden-v1.jsonl").load()

    assert len(questions) >= 50
    assert all(q.text for q in questions)
