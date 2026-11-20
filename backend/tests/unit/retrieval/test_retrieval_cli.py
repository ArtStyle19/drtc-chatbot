"""``drtc-retrieval eval``: options, exit codes and the baseline workflow (no database)."""

import json
from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from drtc_chatbot.contexts.retrieval.application.ports import GoldenSet, Retrieval, Retriever
from drtc_chatbot.contexts.retrieval.application.run_evaluation import RunEvaluation
from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    GoldenCitation,
    GoldenQuestion,
    MethodReport,
    RankedResult,
)
from drtc_chatbot.contexts.retrieval.domain.metrics import baseline_of
from drtc_chatbot.contexts.retrieval.presentation.cli.app import build_app
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError
from tests.unit.retrieval.test_lookup_reference import FakeDirectory

V = "ley@1"
QUESTIONS = (
    GoldenQuestion(
        id="q-001", text="uno", intent="concept", answerable=True, review_status="draft",
        tags=("explicit_reference",), citations=(GoldenCitation(V, "articulo:2", "x"),),
    ),
    GoldenQuestion(
        id="q-002", text="dos", intent="concept", answerable=True, review_status="draft",
        tags=("colloquial",), citations=(GoldenCitation(V, "articulo:5", "x"),),
    ),
)  # fmt: skip


class Scripted:
    def __init__(self, name: str, answers: dict[str, list[RankedResult]]) -> None:
        self.name, self.answers = name, answers

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval:
        return Retrieval(tuple(self.answers.get(text, ())))


class MemoryStore:
    def __init__(self, baseline: Mapping[str, Any] | None = None) -> None:
        self.baseline = baseline
        self.changelog: list[tuple[date, str, Mapping[str, str]]] = []
        self.reports: list[tuple[Path, str]] = []

    def read_baseline(self) -> Mapping[str, Any]:
        if self.baseline is None:
            raise InvariantViolationError("No hay línea base")
        return self.baseline

    def write_baseline(
        self, reports: Iterable[MethodReport], *, dataset: str, recorded_on: date, questions: int
    ) -> Mapping[str, Any]:
        self.baseline = {"dataset": dataset, "methods": baseline_of(reports)}
        return self.baseline

    def append_changelog(
        self, *, recorded_on: date, reason: str, summary: Mapping[str, str]
    ) -> None:
        self.changelog.append((recorded_on, reason, summary))

    def write_report(
        self,
        directory: Path,
        label: str,
        *,
        recorded_on: date,
        payload: Mapping[str, Any],
        markdown: str,
    ) -> tuple[Path, Path]:
        self.reports.append((directory, label))
        assert json.dumps(payload)
        assert "# " in markdown
        return directory / f"{label}.json", directory / f"{label}.md"


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 11, 19, 10, 0, tzinfo=UTC)


class Golden:
    def load(self) -> Sequence[GoldenQuestion]:
        return QUESTIONS


class Module:
    def __init__(self, store: MemoryStore, retrievers: dict[str, Retriever]) -> None:
        self.run_evaluation = RunEvaluation(FakeDirectory())  # type: ignore[arg-type]
        self.retrievers, self.store = retrievers, store
        self.default_dataset, self.clock = Path("golden.jsonl"), FakeClock()
        self.embedding = None  # no meaning provider: these tests are about the deterministic arms
        self.embed_passages = None
        self.search_passages = None
        self.passage_index = None
        self.build_index = None

    def golden_set(self, path: Path) -> GoldenSet:
        return Golden()


def invoke(store: MemoryStore, retrievers: dict[str, Retriever], *args: str):
    module = Module(store, retrievers)

    @asynccontextmanager
    async def factory() -> AsyncIterator[Module]:
        yield module

    return CliRunner().invoke(build_app(factory), ["eval", *args])  # type: ignore[arg-type]


def good() -> dict[str, Retriever]:
    return {
        "exact": Scripted(
            "exact", {"uno": [RankedResult(V, "articulo:2", "articulo:2")], "dos": []}
        )
    }


def worse() -> dict[str, Retriever]:
    return {"exact": Scripted("exact", {"uno": [], "dos": []})}


@pytest.mark.spec("004-FR-003")
def test_eval_prints_a_summary_per_method_and_tag() -> None:
    result = invoke(MemoryStore(), good())

    assert result.exit_code == 0, result.output
    assert "exact: 2 preguntas (2 con respuesta)" in result.output
    assert "etiqueta explicit_reference: acierto@1 (unidad) 100% de 1" in result.output


@pytest.mark.spec("004-FR-003")
def test_eval_writes_the_report_files_when_asked() -> None:
    store = MemoryStore()

    result = invoke(store, good(), "--out", "informes")

    assert result.exit_code == 0, result.output
    assert store.reports == [(Path("informes"), "exact")]
    assert "Informe:" in result.output


def test_an_unknown_method_is_refused_listing_the_available_ones() -> None:
    result = invoke(MemoryStore(), good(), "--modes", "magic")

    assert result.exit_code != 0
    assert "Método desconocido: magic" in result.output
    assert "Disponibles: exact" in result.output


@pytest.mark.parametrize("bad", ["a,b", "0,3", ""])
def test_k_must_be_a_list_of_positive_integers(bad: str) -> None:
    assert invoke(MemoryStore(), good(), "--k", bad).exit_code != 0


@pytest.mark.spec("004-FR-004")
def test_writing_the_baseline_requires_a_reason_and_leaves_a_changelog_entry() -> None:
    store = MemoryStore()

    refused = invoke(store, good(), "--write-baseline")
    accepted = invoke(store, good(), "--write-baseline", "--reason", "Primera medición")

    assert refused.exit_code != 0
    assert "--reason" in refused.output
    assert accepted.exit_code == 0, accepted.output
    assert store.baseline is not None
    assert store.changelog == [
        (date(2026, 11, 19), "Primera medición", {"exact": "unidad acierto@10 50 %, MRR 0.500"})
    ]


@pytest.mark.spec("004-FR-004")
def test_the_gate_passes_with_the_same_numbers_and_fails_with_a_list_when_something_got_worse() -> (
    None
):
    store = MemoryStore()
    invoke(store, good(), "--write-baseline", "--reason", "base")

    same = invoke(store, good(), "--check-baseline")
    regressed = invoke(store, worse(), "--check-baseline")

    assert same.exit_code == 0
    assert "Sin empeoramientos" in same.output
    assert regressed.exit_code == 1
    assert "EMPEORÓ" in regressed.output
    assert "exact · overall · unit · hit@1: 0.5 → 0" in regressed.output


def test_the_gate_needs_a_baseline() -> None:
    result = invoke(MemoryStore(), good(), "--check-baseline")

    assert result.exit_code == 1
    assert "No hay línea base" in result.output


def test_the_baseline_cannot_be_compared_with_other_ks() -> None:
    result = invoke(MemoryStore(), good(), "--check-baseline", "--k", "1,5")

    assert result.exit_code != 0
    assert "K=1,3,5,10" in result.output
