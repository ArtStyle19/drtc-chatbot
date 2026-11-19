"""``drtc-retrieval embed``, ``search`` and ``eval`` with the meaning arm: nothing is sent without a yes."""

from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from drtc_chatbot.contexts.retrieval.application.embed_passages import EmbedPassages
from drtc_chatbot.contexts.retrieval.application.hybrid_retriever import HybridRetriever
from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference
from drtc_chatbot.contexts.retrieval.application.ports import (
    GoldenSet,
    Retriever,
    StoredEmbedding,
    WindowToEmbed,
)
from drtc_chatbot.contexts.retrieval.application.run_evaluation import RunEvaluation
from drtc_chatbot.contexts.retrieval.application.search_passages import SearchPassages
from drtc_chatbot.contexts.retrieval.application.vector_retriever import VectorRetriever
from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    GoldenCitation,
    GoldenQuestion,
    MethodReport,
)
from drtc_chatbot.contexts.retrieval.domain.metrics import baseline_of
from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import FakeEmbeddingProvider
from drtc_chatbot.contexts.retrieval.presentation.cli.app import build_app
from drtc_chatbot.shared_kernel.application import Actor
from tests.unit.retrieval.test_lookup_reference import FakeDirectory
from tests.unit.retrieval.test_search_passages import LEY, Editions, ScriptedIndex, hit

QUESTIONS = (
    GoldenQuestion(id="q-001", text="¿mototaxis?", intent="concept", answerable=True, review_status="draft", tags=("colloquial",), citations=(GoldenCitation(LEY, "articulo:2", "x"),)),
    GoldenQuestion(id="q-002", text="¿impuesto?", intent="out_of_scope", answerable=False, review_status="draft", tags=(), citations=()),
)  # fmt: skip


class Paid(FakeEmbeddingProvider):
    external = True

    def __init__(self) -> None:
        super().__init__(model="text-embedding-3-small")


class Index(ScriptedIndex):
    """The scripted arms plus pending windows and storage, as the CLI needs for `embed`."""

    def __init__(self, *args: Any, windows: int = 3, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.pending = [WindowToEmbed(f"p{i}", 0, f"texto {i}", f"h{i}") for i in range(windows)]
        self.stored: list[StoredEmbedding] = []

    async def missing_windows(self, model: str) -> Sequence[WindowToEmbed]:
        done = {s.passage_id for s in self.stored}
        return [w for w in self.pending if w.passage_id not in done]

    async def store_embeddings(self, model: str, items: Sequence[StoredEmbedding]) -> None:
        self.stored.extend(items)


class MemoryStore:
    def __init__(self) -> None:
        self.reports: list[Mapping[str, Any]] = []

    def read_baseline(self) -> Mapping[str, Any]:
        return {"methods": baseline_of([])}

    def write_baseline(
        self, reports: Iterable[MethodReport], *, dataset: str, recorded_on: date, questions: int
    ) -> Mapping[str, Any]:
        return {}

    def append_changelog(self, **kwargs: Any) -> None: ...

    def write_report(
        self,
        directory: Path,
        label: str,
        *,
        recorded_on: date,
        payload: Mapping[str, Any],
        markdown: str,
    ) -> tuple[Path, Path]:
        self.reports.append(payload)
        return directory / "a.json", directory / "a.md"


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 11, 19, tzinfo=UTC)


class Golden:
    def load(self) -> Sequence[GoldenQuestion]:
        return QUESTIONS


class Module:
    def __init__(self, index: Index, provider: FakeEmbeddingProvider | None) -> None:
        directory = FakeDirectory()
        lookup = LookupReference(directory)  # type: ignore[arg-type]
        self.search_passages = SearchPassages(lookup, index, Editions(), provider)  # type: ignore[arg-type]
        self.passage_index = index
        self.embedding = provider
        self.embed_passages = EmbedPassages(index, provider) if provider else None  # type: ignore[arg-type]
        self.run_evaluation = RunEvaluation(directory)  # type: ignore[arg-type]
        self.retrievers: dict[str, Retriever] = {
            "vector": VectorRetriever(index, provider),
            "hybrid": HybridRetriever(self.search_passages),
        }  # type: ignore[arg-type]
        self.store = MemoryStore()
        self.default_dataset, self.clock = Path("g.jsonl"), Clock()
        self.build_index = None

    def golden_set(self, path: Path) -> GoldenSet:
        return Golden()


def invoke(index: Index, provider: FakeEmbeddingProvider | None, *args: str) -> tuple[Any, Module]:
    module = Module(index, provider)

    @asynccontextmanager
    async def factory() -> AsyncIterator[Module]:
        yield module

    return CliRunner().invoke(build_app(factory), list(args)), module  # type: ignore[arg-type]


# ---------------------------------------------------------------------------------- embed
@pytest.mark.spec("004-FR-005")
def test_embed_without_a_provider_explains_where_the_key_goes_and_sends_nothing() -> None:
    result, _ = invoke(Index(), None, "embed")

    assert result.exit_code == 1
    assert "DRTC_OPENAI_API_KEY" in result.output
    assert ".env" in result.output


@pytest.mark.spec("004-FR-005")
def test_a_dry_run_estimates_and_never_sends() -> None:
    provider = Paid()

    result, _ = invoke(Index(), provider, "embed", "--dry-run")

    assert result.exit_code == 0, result.output
    assert "Modelo: text-embedding-3-small" in result.output
    assert "Pendientes: 3 fragmentos" in result.output
    assert "se enviarían a un servicio externo" in result.output
    assert "USD" in result.output
    assert provider.calls == []


@pytest.mark.spec("004-FR-005")
def test_an_external_provider_without_a_yes_sends_nothing_and_says_how_to_confirm() -> None:
    provider, index = Paid(), Index()

    result, _ = invoke(index, provider, "embed")  # CliRunner has no terminal: it cannot ask

    assert result.exit_code == 2
    assert "--yes" in result.output
    assert provider.calls == []
    assert index.stored == []


@pytest.mark.spec("004-FR-005")
def test_with_a_yes_it_sends_stores_and_reports_the_real_usage_against_the_estimate() -> None:
    provider, index = Paid(), Index(windows=3)

    result, _ = invoke(index, provider, "embed", "--yes")

    assert result.exit_code == 0, result.output
    assert len(index.stored) == 3
    assert "Listo: 3 fragmentos" in result.output
    assert "tokens reales" in result.output
    assert "(estimado" in result.output
    assert provider.calls == [3]


def test_an_offline_provider_needs_no_confirmation() -> None:
    provider, index = FakeEmbeddingProvider(), Index()

    result, _ = invoke(index, provider, "embed")

    assert result.exit_code == 0, result.output
    assert "se calcularían en este servidor" in result.output
    assert len(index.stored) == 3


def test_when_nothing_is_pending_nothing_is_sent() -> None:
    provider = Paid()

    result, _ = invoke(Index(windows=0), provider, "embed", "--yes")

    assert "No hay nada pendiente" in result.output
    assert provider.calls == []


def test_a_limit_sends_only_the_first_fragments() -> None:
    provider, index = Paid(), Index(windows=5)

    invoke(index, provider, "embed", "--yes", "--limit", "2")

    assert len(index.stored) == 2


# ---------------------------------------------------------------------------------- search
def test_search_shows_marks_edition_status_and_a_notice_when_it_degrades() -> None:
    index = Index(lexical=[hit(LEY, "articulo:5", words="plazo")])

    result, _ = invoke(index, None, "search", "art. 5 Ley 27181 plazo", "--mode", "lexical")

    assert result.exit_code == 0, result.output
    assert "Entendí la referencia: art. 5" in result.output
    assert "[reference+lexical]" in result.output
    assert "unverified" in result.output
    assert "**plazo**" in result.output
    assert "1 resultados" in result.output


def test_search_without_a_provider_says_it_is_showing_words_only() -> None:
    index = Index(lexical=[hit(LEY, "articulo:5")])

    result, _ = invoke(index, None, "search", "algo")

    assert "Aviso: la búsqueda por significado no está disponible" in result.output


def test_search_can_show_which_method_found_each_result() -> None:
    index = Index(lexical=[hit(LEY, "articulo:5")])

    result, _ = invoke(index, None, "search", "algo", "--debug")

    assert "debug:" in result.output
    assert "lexical_rank" in result.output


# ---------------------------------------------------------------------------------- eval with meaning
@pytest.mark.spec("004-FR-005")
@pytest.mark.parametrize("mode", ["vector", "hybrid"])
def test_evaluating_meaning_without_a_provider_is_refused_instead_of_scoring_zeros(
    mode: str,
) -> None:
    result, _ = invoke(Index(), None, "eval", "--modes", mode)

    assert result.exit_code == 1
    assert "DRTC_OPENAI_API_KEY" in result.output


def test_evaluating_meaning_without_vectors_tells_to_run_embed_first() -> None:
    result, _ = invoke(Index(embedded=0), Paid(), "eval", "--modes", "vector", "--yes")

    assert result.exit_code == 1
    assert "ejecute `drtc-retrieval embed`" in result.output


@pytest.mark.spec("004-FR-005")
def test_evaluating_meaning_with_an_external_provider_shows_the_estimate_and_needs_a_yes() -> None:
    provider = Paid()

    result, _ = invoke(Index(embedded=9), provider, "eval", "--modes", "vector")

    assert result.exit_code == 2
    assert "Se enviarán 2 preguntas a text-embedding-3-small" in result.output
    assert provider.calls == []


@pytest.mark.spec("004-FR-005")
def test_the_report_records_provider_model_tokens_and_cost() -> None:
    index = Index(vector=[hit(LEY, "articulo:2")], embedded=9)

    result, module = invoke(
        index, Paid(), "eval", "--modes", "vector", "--yes", "--out", "informes"
    )

    assert result.exit_code == 0, result.output
    assert "Uso real del proveedor" in result.output
    [payload] = module.store.reports
    provider_info = payload["methods"]["vector"]["extra"]["provider"]
    assert provider_info["model"] == "text-embedding-3-small"
    assert provider_info["tokens"] > 0
    assert provider_info["estimated_cost_usd"] is not None


def test_an_offline_provider_is_evaluated_without_asking_for_anything() -> None:
    index = Index(vector=[hit(LEY, "articulo:2")], embedded=9)

    result, _ = invoke(index, FakeEmbeddingProvider(), "eval", "--modes", "vector")

    assert result.exit_code == 0, result.output
    assert "Se enviarán" not in result.output


# ---------------------------------------------------------------------------------- the retrievers
async def test_the_hybrid_retriever_flattens_each_unit_into_its_matching_passages_and_reports_degradation() -> (
    None
):
    index = Index(
        lexical=[
            hit(LEY, "articulo:2/literal:e", unit="articulo:2"),
            hit(LEY, "articulo:2/literal:a", unit="articulo:2"),
        ]
    )
    module = Module(index, None)

    retrieval = await module.retrievers["hybrid"].retrieve(
        Actor(
            "t",
            __import__(
                "drtc_chatbot.shared_kernel.application", fromlist=["ActorKind"]
            ).ActorKind.SERVICE,
        ),
        "algo",
        5,
    )

    assert [r.path for r in retrieval.results] == ["articulo:2/literal:e", "articulo:2/literal:a"]
    assert {r.unit_path for r in retrieval.results} == {"articulo:2"}
    assert retrieval.degraded == ("vector_unavailable",)
