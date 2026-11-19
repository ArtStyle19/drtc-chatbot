"""The lookup use case with an in-memory directory: statuses, messages and safety rules."""

from collections.abc import Sequence

import pytest

from drtc_chatbot.contexts.retrieval.application.dto import LookupResult, LookupStatus
from drtc_chatbot.contexts.retrieval.application.lookup_reference import (
    MAX_HITS,
    MAX_QUERY_LENGTH,
    LookupReference,
)
from drtc_chatbot.contexts.retrieval.application.ports import IndexedEdition, IndexedProvision
from drtc_chatbot.contexts.retrieval.domain.norms import NormInfo
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from drtc_chatbot.shared_kernel.domain import InvariantViolationError
from tests.unit.retrieval.test_reference_domain import LEY, RENAT, TUO

ANONYMOUS = Actor("anonymous", ActorKind.ANONYMOUS)


def entry(
    path: str, label: str, *, kind: str = "article", page: int = 2, parent: str | None = None
) -> IndexedProvision:
    return IndexedProvision(
        path,
        path.split("/", maxsplit=1)[0],
        kind,
        label,
        None,
        f"Texto de {path}",
        page,
        f"cita {path}",
        parent,
    )


def edition(version: str, *paths: tuple[str, str]) -> IndexedEdition:
    return IndexedEdition(
        version, f"Edición {version}", "unverified", tuple(entry(p, label) for p, label in paths)
    )


EDITIONS = {
    "ley-27181": edition(
        "ley@1", ("articulo:2", "2"), ("articulo:2/literal:e", "e"), ("articulo:5", "5"), ("articulo:11", "11"),
        ("articulo:4-A/numeral:4-A.1/literal:a", "a"), ("articulo:4-A/numeral:4-A.2/literal:a", "a"),
        ("disposiciones:finales/tercera", "tercera"),
    ),
    "ds-017-2009-mtc": edition(
        "renat@1", ("articulo:5", "5"), ("articulo:11", "11"), ("anexo:2", "2"),
        ("seccion:sexta/disposiciones:complementarias-finales/primera", "primera"),
    ),
    "tuo-ley-27444": edition("tuo@1", ("articulo:5", "5"), ("articulo:11", "11"), ("articulo:218/numeral:218.2", "218.2"), ("titulo:IV", "IV")),
}  # fmt: skip


class FakeDirectory:
    def __init__(self, editions: dict[str, IndexedEdition] | None = None) -> None:
        self.editions = EDITIONS if editions is None else editions
        self.edition_calls: list[str] = []

    async def norms(self, actor: Actor) -> Sequence[NormInfo]:
        return [LEY, RENAT, TUO]

    async def edition(self, actor: Actor, instrument_id: str) -> IndexedEdition | None:
        self.edition_calls.append(instrument_id)
        return self.editions.get(instrument_id)


async def look(query: str, directory: FakeDirectory | None = None) -> LookupResult:
    return await LookupReference(directory or FakeDirectory()).execute(ANONYMOUS, query)  # type: ignore[arg-type]


@pytest.mark.spec("003-FR-007")
@pytest.mark.parametrize(
    "query",
    [
        "art. 5 Ley 27181",
        "artículo 5 de la LGTTT",
        "Ley 27181 art 5",
        "ARTICULO 5° DE LA LEY N° 27181",
        "el art. 5 de la ley general de transporte",
    ],
)
async def test_equivalent_references_resolve_to_the_same_provision(query: str) -> None:
    result = await look(query)

    assert result.status is LookupStatus.RESOLVED
    [hit] = result.hits
    assert (hit.instrument_id, hit.path, hit.version_id) == ("ley-27181", "articulo:5", "ley@1")
    assert hit.citation == "cita articulo:5"
    assert result.reference == "art. 5"
    assert result.norms == ("Ley 27181 (LGTTT)",)
    assert result.message == ""


async def test_a_literal_is_resolved_with_its_unit_to_open() -> None:
    [hit] = (await look("lit. e del art. 2 de la ley 27181")).hits

    assert (hit.path, hit.unit_path, hit.kind, hit.label) == (
        "articulo:2/literal:e",
        "articulo:2",
        "article",
        "e",
    )


@pytest.mark.spec("003-FR-007")
async def test_a_reference_without_a_norm_lists_every_norm_that_has_it_and_never_chooses() -> None:
    result = await look("art 11")

    assert result.status is LookupStatus.AMBIGUOUS
    assert [h.instrument_id for h in result.hits] == [
        "ley-27181",
        "ds-017-2009-mtc",
        "tuo-ley-27444",
    ]
    assert result.total == 3
    assert "3 disposiciones coinciden" in result.message
    assert result.norms == ()


async def test_a_reference_that_matches_several_places_of_one_norm_lists_them_all() -> None:
    result = await look("art 4-A lit a ley 27181")

    assert result.status is LookupStatus.AMBIGUOUS
    assert [h.path for h in result.hits] == [
        "articulo:4-A/numeral:4-A.1/literal:a",
        "articulo:4-A/numeral:4-A.2/literal:a",
    ]


@pytest.mark.spec("003-FR-007")
async def test_a_well_formed_reference_to_something_that_does_not_exist_says_what_was_understood() -> (
    None
):
    result = await look("art. 999 ley 27181")

    assert result.status is LookupStatus.NOT_FOUND
    assert result.reference == "art. 999"
    assert (
        "Ley 27181 (LGTTT) no tiene «art. 999» en la edición cargada (Edición ley@1)"
        in result.message
    )
    assert result.hits == ()


@pytest.mark.spec("003-FR-007")
async def test_a_norm_that_is_not_in_the_corpus_is_reported_and_other_norms_are_not_searched() -> (
    None
):
    directory = FakeDirectory()

    result = await look("art 5 ley 99999", directory)

    assert result.status is LookupStatus.NOT_FOUND
    assert "No reconozco la norma «ley 99999»" in result.message
    assert "RENAT" in result.message  # the available norms are listed
    assert directory.edition_calls == []  # it did not fall back to searching every norm


@pytest.mark.spec("003-FR-007")
@pytest.mark.parametrize(
    "query", ["transporte de mercancías", "hola", "5", "qué es el silencio administrativo"]
)
async def test_text_that_is_not_a_reference_is_explained_with_examples(query: str) -> None:
    result = await look(query)

    assert result.status is LookupStatus.UNRECOGNIZED
    assert "puede buscarlo por su contenido" in result.message
    assert "art. 5 Ley 27181" in result.message


async def test_a_norm_name_alone_opens_the_norm() -> None:
    result = await look("ley 27181")

    assert result.status is LookupStatus.RESOLVED
    [hit] = result.hits
    assert (hit.instrument_id, hit.path, hit.unit_path) == ("ley-27181", None, None)
    assert (await look("renat")).hits[0].instrument_id == "ds-017-2009-mtc"


async def test_a_norm_name_followed_by_free_text_is_not_a_reference() -> None:
    assert (await look("ley 27181 transporte de mercancías")).status is LookupStatus.UNRECOGNIZED


async def test_two_norms_without_a_reference_are_ambiguous() -> None:
    result = await look("ley 27181 y renat")

    assert result.status is LookupStatus.AMBIGUOUS
    assert [h.instrument_id for h in result.hits] == ["ley-27181", "ds-017-2009-mtc"]


async def test_extra_words_around_a_reference_are_reported_not_silently_used() -> None:
    result = await look("qué dice el art. 5 de la ley 27181 sobre mototaxis")

    assert result.status is LookupStatus.RESOLVED
    assert result.ignored_text == "sobre mototaxis"


@pytest.mark.parametrize(
    ("query", "path"),
    [
        ("anexo 2 RENAT", "anexo:2"),
        (
            "primera disposición complementaria final RENAT",
            "seccion:sexta/disposiciones:complementarias-finales/primera",
        ),
        ("tercera disposición final LGTTT", "disposiciones:finales/tercera"),
        ("título IV TUO", "titulo:IV"),
        ("218.2 TUO", "articulo:218/numeral:218.2"),
        ("art 218.2 ley 27444", "articulo:218/numeral:218.2"),
    ],
)
async def test_annexes_dispositions_titles_and_numerals_are_resolved(query: str, path: str) -> None:
    result = await look(query)

    assert result.status is LookupStatus.RESOLVED, result.message
    assert result.hits[0].path == path


async def test_a_norm_without_an_approved_edition_is_explained() -> None:
    result = await look("art 5 ley 27181", FakeDirectory({}))

    assert result.status is LookupStatus.NOT_FOUND
    assert "ninguna" in result.message.lower() or "edición aprobada" in result.message


async def test_a_named_norm_without_an_edition_is_mentioned_next_to_the_ones_that_have_one() -> (
    None
):
    result = await look(
        "art 999 ley 27181 y renat", FakeDirectory({"ds-017-2009-mtc": EDITIONS["ds-017-2009-mtc"]})
    )

    assert "Ley 27181 (LGTTT) no tiene una edición aprobada todavía" in result.message
    assert "RENAT" in result.message


async def test_the_number_of_results_is_capped_but_the_total_is_honest() -> None:
    many = edition(
        "ley@1", *[(f"articulo:1/numeral:1.{i}/literal:a", "a") for i in range(1, MAX_HITS + 6)]
    )

    result = await look("art 1 lit a ley 27181", FakeDirectory({"ley-27181": many}))

    assert (result.total, len(result.hits)) == (MAX_HITS + 5, MAX_HITS)
    assert f"Se muestran las primeras {MAX_HITS}" in result.message


@pytest.mark.parametrize("query", ["", "   ", "x" * (MAX_QUERY_LENGTH + 1)])
async def test_empty_or_oversized_queries_are_rejected(query: str) -> None:
    with pytest.raises(InvariantViolationError):
        await look(query)


PRELIMINARY = IndexedEdition(
    "tuo@1", "Edición tuo", "unverified",
    (
        entry("titulo:PRELIMINAR", "PRELIMINAR", kind="title"),
        entry("articulo:IV", "IV", parent="titulo:PRELIMINAR"),
        entry("titulo:I", "I", kind="title"),
        entry("articulo:5", "5", parent="titulo:I"),
        entry("titulo:IV", "IV", kind="title"),
        entry("titulo:IV/capitulo:I", "I", kind="chapter", parent="titulo:IV"),
        entry("articulo:229", "229", parent="titulo:IV/capitulo:I"),
        entry("articulo:229/numeral:229.1", "229.1", parent="articulo:229"),
    ),
)  # fmt: skip


@pytest.mark.parametrize(
    ("query", "path"),
    [
        ("art. IV del título preliminar TUO", "articulo:IV"),
        ("artículo IV, Título Preliminar, TUO", "articulo:IV"),
        ("art 5 título I TUO", "articulo:5"),
        ("art 229 capítulo I título IV TUO", "articulo:229"),
        ("art 229 capítulo I TUO", "articulo:229"),
        ("num 229.1 título IV TUO", "articulo:229/numeral:229.1"),
    ],
)
async def test_an_article_can_be_cited_through_its_title_and_chapter(query: str, path: str) -> None:
    result = await look(query, FakeDirectory({"tuo-ley-27444": PRELIMINARY}))

    assert result.status is LookupStatus.RESOLVED, result.message
    assert result.hits[0].path == path


async def test_the_wrong_title_does_not_match() -> None:
    result = await look("art 5 título II TUO", FakeDirectory({"tuo-ley-27444": PRELIMINARY}))

    assert result.status is LookupStatus.NOT_FOUND


def test_the_container_of_the_top_level_unit_goes_in_front_of_it_and_of_everything_below() -> None:
    paths = {e.path: match for e, match in PRELIMINARY.match_paths()}

    assert paths["articulo:5"] == "titulo:I/articulo:5"
    assert paths["articulo:229/numeral:229.1"] == "titulo:IV/capitulo:I/articulo:229/numeral:229.1"
    assert paths["titulo:IV/capitulo:I"] == "titulo:IV/capitulo:I"  # already contains its container
    assert paths["titulo:IV"] == "titulo:IV"
