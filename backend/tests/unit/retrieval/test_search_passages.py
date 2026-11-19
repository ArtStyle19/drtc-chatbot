"""The content search with simulated arms: precedence, fusion, grouping, degradation, filters."""

import asyncio
from collections.abc import Mapping, Sequence

import pytest

from drtc_chatbot.contexts.retrieval.application.dto import SearchMode, SearchResponse
from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference
from drtc_chatbot.contexts.retrieval.application.ports import (
    EditionInfo,
    EmbeddingBatch,
    EmbeddingPurpose,
    PassageHit,
    Segment,
)
from drtc_chatbot.contexts.retrieval.application.search_passages import MAX_MATCHED, SearchPassages
from drtc_chatbot.contexts.retrieval.domain.chunking import PassageText
from drtc_chatbot.contexts.retrieval.domain.errors import EmbeddingUnavailableError
from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import FakeEmbeddingProvider
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError
from tests.unit.retrieval.test_lookup_reference import ANONYMOUS, FakeDirectory

LEY, RENAT, TUO = "ley@1", "renat@1", "tuo@1"
INSTRUMENT = {LEY: "ley-27181", RENAT: "ds-017-2009-mtc", TUO: "tuo-ley-27444"}


def hit(
    version: str, path: str, score: float = 1.0, *, unit: str | None = None, words: str = "texto"
) -> PassageHit:
    passage = PassageText(
        instrument_id=INSTRUMENT.get(version, "otra"), version_id=version, path=path, unit_path=unit or path.split("/", maxsplit=1)[0],
        kind="numeral", label=path.rsplit(":", maxsplit=1)[-1], title=None, breadcrumb=f"b {path}", lead=None, body=words,
        page_start=5, page_end=5, citation=f"cita {path}",
    )  # fmt: skip
    return PassageHit(passage, score, (Segment("otro "), Segment(words, match=True)))


class ScriptedIndex:
    """Returns what it is told, per (instrument filter), and records how it was asked."""

    def __init__(
        self,
        lexical: Sequence[PassageHit] = (),
        vector: Sequence[PassageHit] = (),
        embedded: int = 10,
    ) -> None:
        self.lexical, self.vector, self.embedded = list(lexical), list(vector), embedded
        self.lexical_calls: list[tuple[str, str | None, int]] = []
        self.vector_calls: list[tuple[str, str | None, int]] = []

    @staticmethod
    def _filter(hits: Sequence[PassageHit], instrument_id: str | None) -> list[PassageHit]:
        return [
            h for h in hits if instrument_id is None or h.passage.instrument_id == instrument_id
        ]

    async def lexical_search(
        self, text: str, *, instrument_id: str | None, limit: int
    ) -> Sequence[PassageHit]:
        self.lexical_calls.append((text, instrument_id, limit))
        return self._filter(self.lexical, instrument_id)[:limit]

    async def vector_search(
        self, model: str, vector: Sequence[float], *, instrument_id: str | None, limit: int
    ) -> Sequence[PassageHit]:
        self.vector_calls.append((model, instrument_id, limit))
        return self._filter(self.vector, instrument_id)[:limit]

    async def embedded_passages(self, model: str) -> int:
        return self.embedded


class Editions:
    def __init__(self, status: str = "unverified") -> None:
        self.status = status

    async def editions(self, actor: Actor) -> Mapping[str, EditionInfo]:
        return {
            v: EditionInfo(i, f"Norma {i}", f"Título {i}", v, f"Edición {v}", self.status)
            for v, i in INSTRUMENT.items()
        }


def search_with(
    index: ScriptedIndex,
    provider: object | None = None,
    *,
    status: str = "unverified",
    **kwargs: object,
) -> SearchPassages:
    return SearchPassages(
        LookupReference(FakeDirectory()),
        index,
        Editions(status),
        provider or FakeEmbeddingProvider(),
        **kwargs,
    )  # type: ignore[arg-type]


async def run(search: SearchPassages, text: str, **kwargs: object) -> SearchResponse:
    return await search.execute(ANONYMOUS, text, **kwargs)  # type: ignore[arg-type]


def units(response: SearchResponse) -> list[tuple[str, str]]:
    return [(r.version_id, r.unit_path) for r in response.results]


# ------------------------------------------------------------------------------- precedence
@pytest.mark.spec("004-FR-009")
async def test_a_provision_identified_by_reference_comes_first_and_is_marked_as_such() -> None:
    index = ScriptedIndex(
        lexical=[
            hit(TUO, "articulo:218/numeral:218.2", unit="articulo:218"),
            hit(LEY, "articulo:5"),
        ]
    )

    response = await run(
        search_with(index), "art. 5 Ley 27181 plazo para apelar", mode=SearchMode.LEXICAL
    )

    first = response.results[0]
    assert (first.version_id, first.unit_path, first.via) == (
        LEY,
        "articulo:5",
        ("reference", "lexical"),
    )  # one result, two marks
    assert response.reference == "art. 5"
    assert units(response).count((LEY, "articulo:5")) == 1  # never duplicated
    assert [r.unit_path for r in response.results] == ["articulo:5", "articulo:218"]


@pytest.mark.spec("004-FR-009")
async def test_only_the_words_that_are_not_part_of_the_reference_are_searched_by_content() -> None:
    index = ScriptedIndex()

    await run(search_with(index), "art. 5 Ley 27181 plazo para apelar", mode=SearchMode.LEXICAL)

    assert index.lexical_calls[0][0] == "plazo apelar"


@pytest.mark.spec("004-FR-009")
async def test_a_text_that_is_only_a_reference_searches_no_content_at_all() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:9")])
    provider = FakeEmbeddingProvider()

    response = await run(search_with(index, provider), "art. 5 Ley 27181")

    assert [r.via for r in response.results] == [("reference",)]
    assert index.lexical_calls == []
    assert index.vector_calls == []
    assert provider.calls == []  # nothing was sent to the provider either


@pytest.mark.spec("004-FR-009")
async def test_an_ambiguous_reference_lists_every_candidate_and_chooses_none() -> None:
    response = await run(search_with(ScriptedIndex()), "art. 11")

    assert [r.version_id for r in response.results] == [LEY, RENAT, TUO]
    assert {r.via for r in response.results} == {("reference",)}


async def test_a_reference_to_something_that_does_not_exist_is_not_content() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:5")])

    response = await run(search_with(index), "art. 999 ley 27181", mode=SearchMode.LEXICAL)

    assert (
        response.results == ()
    )  # understood, not found: the rest of the text is empty, nothing to search
    assert response.reference == "art. 999"


async def test_a_text_that_is_not_a_reference_is_searched_whole() -> None:
    index = ScriptedIndex()

    response = await run(
        search_with(index), "¿se puede cobrar por el servicio de mototaxi?", mode=SearchMode.LEXICAL
    )

    assert index.lexical_calls[0][0] == "¿se puede cobrar por el servicio de mototaxi?"
    assert response.reference is None


# ------------------------------------------------------------------------------- fusion
@pytest.mark.spec("004-FR-008")
async def test_what_both_arms_found_ranks_above_what_only_one_found_and_says_so() -> None:
    both = hit(TUO, "articulo:218/numeral:218.2", unit="articulo:218")
    index = ScriptedIndex(
        lexical=[hit(LEY, "articulo:1"), both],
        vector=[hit(RENAT, "articulo:9"), both],
    )

    response = await run(search_with(index), "como apelar")

    assert response.results[0].unit_path == "articulo:218"
    assert response.results[0].via == ("lexical", "vector")
    assert sorted(units(response)) == sorted(
        {(LEY, "articulo:1"), (RENAT, "articulo:9"), (TUO, "articulo:218")}
    )


@pytest.mark.spec("004-FR-010")
async def test_passages_of_one_article_are_grouped_under_it_with_the_best_one_first() -> None:
    index = ScriptedIndex(
        lexical=[
            hit(TUO, "articulo:218/numeral:218.2", unit="articulo:218"),
            hit(LEY, "articulo:3"),
            hit(TUO, "articulo:218/numeral:218.1", unit="articulo:218"),
            hit(TUO, "articulo:218", unit="articulo:218"),
        ]
    )

    response = await run(search_with(index), "recursos", mode=SearchMode.LEXICAL)

    article = next(r for r in response.results if r.unit_path == "articulo:218")
    assert article.path == "articulo:218/numeral:218.2"  # the best passage represents the unit
    assert [m.path for m in article.matched] == [
        "articulo:218/numeral:218.2",
        "articulo:218/numeral:218.1",
        "articulo:218",
    ]
    assert len([r for r in response.results if r.unit_path == "articulo:218"]) == 1


async def test_at_most_five_matching_passages_are_listed_per_unit() -> None:
    index = ScriptedIndex(
        lexical=[hit(TUO, f"articulo:7/numeral:7.{n}", unit="articulo:7") for n in range(1, 10)]
    )

    response = await run(search_with(index), "algo", mode=SearchMode.LEXICAL)

    assert len(response.results[0].matched) == MAX_MATCHED


async def test_each_result_carries_citation_pages_snippet_and_its_edition() -> None:
    index = ScriptedIndex(
        lexical=[hit(TUO, "articulo:218/numeral:218.2", unit="articulo:218", words="quince días")]
    )

    [result] = (await run(search_with(index), "plazo", mode=SearchMode.LEXICAL)).results

    assert result.citation == "cita articulo:218/numeral:218.2"
    assert (result.page_start, result.page_end) == (5, 5)
    assert [s.text for s in result.snippet if s.match] == ["quince días"]
    assert (result.instrument_short_name, result.edition_label) == (
        "Norma tuo-ley-27444",
        f"Edición {TUO}",
    )


# ------------------------------------------------------------------------------- modes
@pytest.mark.spec("004-FR-013")
async def test_the_lexical_mode_never_touches_the_provider() -> None:
    provider = FakeEmbeddingProvider()
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")])

    response = await run(search_with(index, provider), "algo", mode=SearchMode.LEXICAL)

    assert provider.calls == []
    assert index.vector_calls == []
    assert response.degraded == ()  # asking for words only is not a degradation


async def test_the_vector_mode_uses_only_meaning() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")], vector=[hit(RENAT, "articulo:9")])

    response = await run(search_with(index), "algo", mode=SearchMode.VECTOR)

    assert units(response) == [(RENAT, "articulo:9")]
    assert index.lexical_calls == []


# ------------------------------------------------------------------------------- degradation
@pytest.mark.spec("004-SC-006")
async def test_without_a_provider_the_search_answers_with_words_and_says_so() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")], vector=[hit(RENAT, "articulo:9")])
    search = SearchPassages(LookupReference(FakeDirectory()), index, Editions(), None)  # type: ignore[arg-type]

    response = await run(search, "algo")

    assert units(response) == [(LEY, "articulo:1")]
    assert response.degraded == ("vector_unavailable",)


@pytest.mark.spec("004-SC-006")
async def test_a_provider_error_is_a_degradation_not_a_failure() -> None:
    class Down(FakeEmbeddingProvider):
        async def embed(
            self,
            texts: Sequence[str],
            *,
            purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
            timeout_seconds: float | None = None,
        ) -> EmbeddingBatch:
            raise EmbeddingUnavailableError("503")

    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")])

    response = await run(search_with(index, Down()), "algo")

    assert units(response) == [(LEY, "articulo:1")]
    assert response.degraded == ("vector_unavailable",)


@pytest.mark.spec("004-SC-006")
async def test_a_provider_that_is_too_slow_is_a_degradation_within_the_time_limit() -> None:
    class Slow(FakeEmbeddingProvider):
        async def embed(
            self,
            texts: Sequence[str],
            *,
            purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
            timeout_seconds: float | None = None,
        ) -> EmbeddingBatch:
            await asyncio.sleep(5)
            return await super().embed(texts, purpose=purpose)

    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")])
    search = search_with(index, Slow(), vector_timeout_seconds=0.05)

    started = asyncio.get_running_loop().time()
    response = await run(search, "algo")

    assert asyncio.get_running_loop().time() - started < 1.0  # it did not wait for the provider
    assert response.degraded == ("vector_unavailable",)
    assert units(response) == [(LEY, "articulo:1")]


async def test_a_provider_that_works_but_has_no_vectors_yet_is_reported_as_not_indexed() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")], vector=[], embedded=0)

    response = await run(search_with(index), "algo")

    assert response.degraded == ("vector_not_indexed",)
    assert units(response) == [(LEY, "articulo:1")]


async def test_a_vector_arm_that_simply_found_nothing_is_not_a_degradation() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")], vector=[], embedded=500)

    assert (await run(search_with(index), "algo")).degraded == ()


@pytest.mark.spec("004-FR-004")
async def test_the_search_embeds_what_was_typed_as_a_query_not_as_a_document() -> None:
    seen: list[EmbeddingPurpose] = []

    class Spy(FakeEmbeddingProvider):
        async def embed(
            self,
            texts: Sequence[str],
            *,
            purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
            timeout_seconds: float | None = None,
        ) -> EmbeddingBatch:
            seen.append(purpose)
            return await super().embed(texts, purpose=purpose)

    await run(search_with(ScriptedIndex(), Spy()), "algo")

    assert seen == [EmbeddingPurpose.QUERY]


async def test_the_provider_is_asked_with_the_configured_timeout() -> None:
    seen: list[float | None] = []

    class Spy(FakeEmbeddingProvider):
        async def embed(
            self,
            texts: Sequence[str],
            *,
            purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
            timeout_seconds: float | None = None,
        ) -> EmbeddingBatch:
            seen.append(timeout_seconds)
            return await super().embed(texts, purpose=purpose)

    await run(search_with(ScriptedIndex(), Spy(), vector_timeout_seconds=2.5), "algo")

    assert seen == [2.5]


# ------------------------------------------------------------------------------- filter, facets, limit
@pytest.mark.spec("004-FR-019")
async def test_the_norm_filter_applies_before_the_limit_and_the_facets_still_show_every_norm() -> (
    None
):
    index = ScriptedIndex(
        lexical=[hit(RENAT, f"articulo:{n}") for n in range(30)] + [hit(TUO, "articulo:218")]
    )

    response = await run(
        search_with(index), "plazo", mode=SearchMode.LEXICAL, instrument_id="tuo-ley-27444", limit=3
    )

    assert units(response) == [
        (TUO, "articulo:218")
    ]  # found although 30 RENAT passages ranked above it
    assert {c[1] for c in index.lexical_calls} == {
        None,
        "tuo-ley-27444",
    }  # asked with and without the filter
    assert {f.instrument_id: f.count for f in response.facets} == {
        "ds-017-2009-mtc": 30,
        "tuo-ley-27444": 1,
    }


async def test_facets_are_ordered_by_count_and_name_the_norm() -> None:
    index = ScriptedIndex(
        lexical=[hit(LEY, "articulo:1"), hit(RENAT, "articulo:2"), hit(RENAT, "articulo:3")]
    )

    response = await run(search_with(index), "algo", mode=SearchMode.LEXICAL)

    assert [(f.instrument_id, f.count, f.instrument_short_name) for f in response.facets] == [
        ("ds-017-2009-mtc", 2, "Norma ds-017-2009-mtc"),
        ("ley-27181", 1, "Norma ley-27181"),
    ]


async def test_the_limit_cuts_the_list_but_the_total_counts_everything() -> None:
    index = ScriptedIndex(lexical=[hit(LEY, f"articulo:{n}") for n in range(25)])

    response = await run(search_with(index), "algo", mode=SearchMode.LEXICAL, limit=7)

    assert (len(response.results), response.total) == (7, 25)


async def test_each_arm_is_asked_for_the_configured_number_of_candidates() -> None:
    index = ScriptedIndex()

    await run(search_with(index, arm_top_n=33), "algo")

    assert index.lexical_calls[0][2] == 33
    assert index.vector_calls[0][2] == 33


# ------------------------------------------------------------------------------- validity, diagnostics
@pytest.mark.spec("004-SC-009")
@pytest.mark.parametrize("status", ["unverified", "pending_review", "unknown", "superseded"])
async def test_the_verification_status_travels_with_every_result_and_is_never_upgraded(
    status: str,
) -> None:
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1")])

    [result] = (
        await run(search_with(index, status=status), "algo", mode=SearchMode.LEXICAL)
    ).results

    assert result.verification_status == status


async def test_a_result_whose_edition_is_not_known_is_reported_as_unknown_not_as_valid() -> None:
    index = ScriptedIndex(
        lexical=[hit("otra@v9", "articulo:1")]
    )  # an edition the catalog does not list

    [result] = (await run(search_with(index), "algo", mode=SearchMode.LEXICAL)).results

    assert result.verification_status == "unknown"
    assert result.edition_label == ""


@pytest.mark.spec("004-FR-017")
async def test_the_debug_view_says_which_arm_found_each_result_and_where() -> None:
    both = hit(TUO, "articulo:218/numeral:218.2", unit="articulo:218")
    index = ScriptedIndex(lexical=[hit(LEY, "articulo:1"), both], vector=[both])

    response = await run(search_with(index), "algo", debug=True)

    top = response.results[0]
    assert top.debug is not None
    assert (top.debug["lexical_rank"], top.debug["vector_rank"]) == (2, 1)
    assert top.debug["reference_rank"] is None
    plain = await run(search_with(index), "algo", debug=False)
    assert all(r.debug is None for r in plain.results)


async def test_a_reference_result_shows_its_position_in_the_debug_view() -> None:
    response = await run(search_with(ScriptedIndex()), "art. 11", debug=True)

    assert [r.debug for r in response.results] == [
        {"reference_rank": 1},
        {"reference_rank": 2},
        {"reference_rank": 3},
    ]


# ------------------------------------------------------------------------------- input and timing
@pytest.mark.spec("004-FR-014")
@pytest.mark.parametrize("text", ["", "   ", "x" * 301])
async def test_an_empty_or_too_long_text_is_refused_before_anything_is_searched(text: str) -> None:
    index = ScriptedIndex()
    provider = FakeEmbeddingProvider()

    with pytest.raises(InvariantViolationError):
        await run(search_with(index, provider), text)

    assert index.lexical_calls == []
    assert provider.calls == []  # nothing left the server


async def test_the_text_is_normalised_and_the_latency_is_measured() -> None:
    ticks = iter([10.0, 10.25])
    search = search_with(ScriptedIndex(), timer=lambda: next(ticks))

    response = await run(search, "  plazo   para   apelar \n", mode=SearchMode.LEXICAL)

    assert response.query == "plazo para apelar"
    assert response.latency_ms == 250.0
