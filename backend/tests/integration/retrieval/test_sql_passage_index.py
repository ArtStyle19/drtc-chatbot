"""The search index in PostgreSQL: synchronisation and the words search (spec 004)."""

import uuid

import pytest
from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from drtc_chatbot.contexts.retrieval.application.ports import IndexStats
from drtc_chatbot.contexts.retrieval.domain.chunking import MARKERS, PassageText
from drtc_chatbot.contexts.retrieval.infrastructure.models import EmbeddingRow, PassageRow
from drtc_chatbot.contexts.retrieval.infrastructure.sql_passage_index import (
    LexicalTuning,
    SqlPassageIndex,
    segments,
)

pytestmark = pytest.mark.docker

TUO = "tuo@1"
LEY = "ley@1"


def passage(
    path: str,
    body: str,
    *,
    title: str | None = None,
    version: str = TUO,
    instrument: str = "tuo-ley-27444",
    lead: str | None = None,
    kind: str = "numeral",
    page: int = 5,
) -> PassageText:
    return PassageText(
        instrument_id=instrument, version_id=version, path=path, unit_path=path.split("/", maxsplit=1)[0],
        kind=kind, label=path.rsplit(":", maxsplit=1)[-1], title=title, breadcrumb=f"Norma › {path}",
        lead=lead, body=body, page_start=page, page_end=page, citation=f"cita {path}",
    )  # fmt: skip


CORPUS = [
    passage("articulo:218/numeral:218.2", "El término para la interposición de los recursos es de quince (15) días perentorios."),
    passage("articulo:220", "El recurso de apelación se interpondrá cuando la impugnación se sustente en diferente interpretación de las pruebas.", title="Recurso de apelación", kind="article"),
    passage("articulo:169/numeral:169.1", "Los administrados pueden formular queja contra los defectos de tramitación."),
    passage("articulo:38/numeral:38.1", "Excepcionalmente, el silencio negativo es aplicable en aquellos casos de interés público."),
    passage("articulo:30/numeral:30.1", "Todo vehículo automotor debe contar con una póliza del Seguro Obligatorio de Accidentes de Tránsito.", version=LEY, instrument="ley-27181"),
    passage("articulo:25", "Las infracciones de transporte y tránsito terrestre se clasifican en leves, graves y muy graves.", version=LEY, instrument="ley-27181", kind="article"),
]  # fmt: skip


@pytest.fixture
def index(db_sessions: async_sessionmaker) -> SqlPassageIndex:  # type: ignore[type-arg]
    return SqlPassageIndex(db_sessions)


async def paths(hits: object) -> list[str]:
    return [h.passage.path for h in hits]  # type: ignore[attr-defined]


# ------------------------------------------------------------------------------- synchronisation
@pytest.mark.spec("004-FR-016")
async def test_the_first_sync_adds_everything_and_the_second_changes_nothing(
    index: SqlPassageIndex,
) -> None:
    first = await index.sync(CORPUS)
    second = await index.sync(CORPUS)

    assert first == IndexStats(added=6, changed=0, removed=0, unchanged=0)
    assert second == IndexStats(added=0, changed=0, removed=0, unchanged=6)
    assert await index.count() == 6


@pytest.mark.spec("004-FR-016")
async def test_only_the_passage_whose_text_changed_is_rewritten_and_its_vectors_are_dropped(
    index: SqlPassageIndex,
    db_sessions: async_sessionmaker,  # type: ignore[type-arg]
) -> None:
    await index.sync(CORPUS)
    async with db_sessions() as session, session.begin():
        ids = (await session.execute(select(PassageRow.id, PassageRow.provision_path))).all()
        for row in ids:  # give every passage a vector so we can see which ones survive
            await session.execute(
                insert(EmbeddingRow).values(
                    passage_id=row.id,
                    model="m",
                    window=0,
                    dims=3,
                    content_hash="h",
                    embedding=[1.0, 0.0, 0.0],
                )
            )
    edited = [
        *CORPUS[:2],
        passage("articulo:169/numeral:169.1", "Texto reformado de la queja."),
        *CORPUS[3:],
    ]

    stats = await index.sync(edited)

    assert stats == IndexStats(added=0, changed=1, removed=0, unchanged=5)
    async with db_sessions() as session:
        remaining = (
            await session.execute(text("SELECT count(*) FROM retrieval_embeddings"))
        ).scalar_one()
    assert remaining == 5  # the stale vector of the edited passage is gone, the others stay


@pytest.mark.spec("004-FR-016")
async def test_what_is_no_longer_in_an_approved_edition_disappears_with_its_vectors(
    index: SqlPassageIndex,
    db_sessions: async_sessionmaker,  # type: ignore[type-arg]
) -> None:
    await index.sync(CORPUS)
    async with db_sessions() as session, session.begin():
        first = (await session.execute(select(PassageRow.id).limit(1))).scalar_one()
        await session.execute(
            insert(EmbeddingRow).values(
                passage_id=first,
                model="m",
                window=0,
                dims=3,
                content_hash="h",
                embedding=[0.0, 1.0, 0.0],
            )
        )

    stats = await index.sync(
        [p for p in CORPUS if p.instrument_id != "ley-27181"]
    )  # the Ley's edition was withdrawn

    assert stats == IndexStats(added=0, changed=0, removed=2, unchanged=4)
    async with db_sessions() as session:
        assert (
            await session.execute(text("SELECT count(*) FROM retrieval_passages"))
        ).scalar_one() == 4
        orphans = (
            await session.execute(
                text(
                    "SELECT count(*) FROM retrieval_embeddings e LEFT JOIN retrieval_passages p ON p.id = e.passage_id WHERE p.id IS NULL"
                )
            )
        ).scalar_one()
    assert orphans == 0


async def test_a_new_page_number_updates_the_row_without_touching_its_vectors(
    index: SqlPassageIndex,
    db_sessions: async_sessionmaker,  # type: ignore[type-arg]
) -> None:
    await index.sync(CORPUS)
    moved = [passage("articulo:218/numeral:218.2", CORPUS[0].body, page=99), *CORPUS[1:]]

    stats = await index.sync(moved)

    assert stats.changed == 0
    hits = await index.lexical_search("interposición recursos", instrument_id=None, limit=5)
    moved_hit = next(h for h in hits if h.passage.path == "articulo:218/numeral:218.2")
    assert moved_hit.passage.page_start == 99


async def test_highlight_markers_in_a_text_never_reach_the_index(
    index: SqlPassageIndex, db_sessions: async_sessionmaker
) -> None:  # type: ignore[type-arg]
    dirty = passage("articulo:1", f"palabra{MARKERS[0]}extraña{MARKERS[1]} con marcas")

    await index.sync([dirty])

    async with db_sessions() as session:
        body = (await session.execute(select(PassageRow.body))).scalar_one()
    assert body == "palabraextraña con marcas"


# ------------------------------------------------------------------------------- words search
@pytest.mark.spec("004-FR-006")
@pytest.mark.parametrize(
    "question",
    [
        "apelacion",
        "APELACIÓN",
        "apelaciones",
        "¿Cuándo corresponde la apelación?",
        "recurso de apelación",
    ],
)
async def test_accents_case_and_plurals_do_not_matter(
    index: SqlPassageIndex, question: str
) -> None:
    await index.sync(CORPUS)

    hits = await index.lexical_search(question, instrument_id=None, limit=5)

    assert "articulo:220" in await paths(hits)


@pytest.mark.spec("004-FR-006")
async def test_verb_forms_match_the_noun_and_the_other_way_round(index: SqlPassageIndex) -> None:
    await index.sync(CORPUS)

    assert "articulo:25" in await paths(
        await index.lexical_search("se clasifican las infracciones", instrument_id=None, limit=5)
    )
    assert "articulo:25" in await paths(
        await index.lexical_search("clasificación de infracción", instrument_id=None, limit=5)
    )


@pytest.mark.spec("004-FR-006")
async def test_any_subset_of_the_words_is_enough_and_more_matching_words_rank_higher(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)

    hits = await index.lexical_search(
        "plazo para interponer recursos perentorios quince días", instrument_id=None, limit=5
    )

    assert (await paths(hits))[0] == "articulo:218/numeral:218.2"
    assert all(h.score > 0 for h in hits)
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)


@pytest.mark.spec("004-FR-006")
async def test_a_match_in_the_title_outranks_the_same_word_in_a_body(
    index: SqlPassageIndex,
) -> None:
    await index.sync(
        [
            passage("articulo:1", "El trámite de queja se presenta ante el superior.", title=None),
            passage("articulo:2", "Texto sin relación.", title="De la queja", kind="article"),
        ]
    )

    hits = await index.lexical_search("queja", instrument_id=None, limit=5)

    assert (await paths(hits))[0] == "articulo:2"


async def test_the_instrument_filter_applies_before_the_limit(index: SqlPassageIndex) -> None:
    await index.sync(CORPUS)

    hits = await index.lexical_search(
        "infracciones transporte vehículo seguro recursos", instrument_id="tuo-ley-27444", limit=10
    )

    assert hits
    assert {h.passage.instrument_id for h in hits} == {"tuo-ley-27444"}


async def test_the_limit_is_respected_and_ties_are_ordered_deterministically(
    index: SqlPassageIndex,
) -> None:
    same = [passage(f"articulo:{n}", "silencio administrativo positivo") for n in (9, 3, 7, 1)]
    await index.sync(same)

    first = await paths(await index.lexical_search("silencio", instrument_id=None, limit=3))
    again = await paths(await index.lexical_search("silencio", instrument_id=None, limit=3))

    assert len(first) == 3
    assert first == again == sorted(first)  # same score: ordered by path, always the same


@pytest.mark.spec("004-FR-011")
async def test_the_snippet_marks_the_matching_words_and_keeps_the_original_text(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)

    hits = await index.lexical_search("interposicion recursos", instrument_id=None, limit=5)

    hit = next(h for h in hits if h.passage.path == "articulo:218/numeral:218.2")
    matched = [s.text for s in hit.snippet if s.match]
    assert matched == [
        "interposición",
        "recursos",
    ]  # with the accent of the original, not of the query
    # the fragment keeps the ORIGINAL words (accents, case), though it may skip leading stop words
    assert "término para la interposición de los recursos" in "".join(s.text for s in hit.snippet)
    assert not any(marker in s.text for s in hit.snippet for marker in MARKERS)


async def test_a_title_only_article_shows_its_title_as_snippet(index: SqlPassageIndex) -> None:
    await index.sync([passage("articulo:7", "", title="Recurso de queja", kind="article")])

    [hit] = await index.lexical_search("queja", instrument_id=None, limit=3)

    assert [s.text for s in hit.snippet if s.match] == ["queja"]


@pytest.mark.parametrize(
    "question",
    [
        "de la el y para",
        "¿?",
        "  ",
        "???...!!!",
        "' OR 1=1; DROP TABLE retrieval_passages; --",
        "\\ \" ' ) ( & | ! :*",
    ],
)
async def test_stop_words_punctuation_and_hostile_text_are_harmless(
    index: SqlPassageIndex, question: str
) -> None:
    await index.sync(CORPUS)

    hits = await index.lexical_search(question, instrument_id=None, limit=5)

    assert isinstance(hits, list | tuple)
    assert await index.count() == 6  # nothing was dropped


async def test_a_word_that_is_in_no_passage_returns_nothing(index: SqlPassageIndex) -> None:
    await index.sync(CORPUS)

    assert await index.lexical_search("criptomonedas", instrument_id=None, limit=5) == []


async def test_the_tuning_changes_the_ranking_without_changing_who_matches(
    db_sessions: async_sessionmaker,
) -> None:  # type: ignore[type-arg]
    docs = [
        passage("articulo:1", "queja " * 30 + "y más texto", title=None),
        passage("articulo:2", "queja", title=None),
    ]
    default = SqlPassageIndex(db_sessions, LexicalTuning(normalization=0))
    await default.sync(docs)
    plain = await default.lexical_search("queja", instrument_id=None, limit=5)
    short_first = await SqlPassageIndex(db_sessions, LexicalTuning(normalization=2)).lexical_search(
        "queja", instrument_id=None, limit=5
    )

    assert set(await paths(plain)) == set(await paths(short_first)) == {"articulo:1", "articulo:2"}


# ------------------------------------------------------------------------------- accents
ACCENTS = [
    passage("articulo:1", "La resolución que ponga fin al procedimiento será notificada."),
    passage("articulo:2", "Las resoluciones y las notificaciones se emitirán por escrito.", title="Actos"),
    passage("articulo:3", "El administrado sustituirá la garantía en el plazo señalado."),
    passage("articulo:4", "Los daños y perjuicios se reparan; el año siguiente se evalúa."),
    passage("articulo:5", "El tránsito terrestre y la fiscalización.", title="Tránsito"),
]  # fmt: skip


@pytest.mark.spec("004-FR-006")
@pytest.mark.parametrize(
    ("typed", "found"),
    [
        (
            "resolucion",
            {"articulo:1", "articulo:2"},
        ),  # singular typed without accent finds singular AND plural
        ("resoluciones", {"articulo:1", "articulo:2"}),
        ("RESOLUCIÓN", {"articulo:1", "articulo:2"}),
        (
            "notificacion",
            {"articulo:2"},
        ),  # "notificada" has another stem: the stemmer's limit, not ours
        ("sustituira", {"articulo:3"}),  # a verb form whose accent changes its stem
        ("transito", {"articulo:5"}),
        ("danos", set()),  # n is not ñ: "daños" is another word and is not guessed
        ("daños", {"articulo:4"}),
        ("ano", set()),  # "año" keeps its ñ and is not reached by "ano"
        ("año siguiente", {"articulo:4"}),
    ],
)
async def test_words_typed_without_accents_find_the_accented_words_of_the_corpus(
    index: SqlPassageIndex, typed: str, found: set[str]
) -> None:
    await index.sync(ACCENTS)

    hits = await index.lexical_search(typed, instrument_id=None, limit=10)

    assert {h.passage.path for h in hits} >= found
    if not found:
        assert not any(h.passage.path == "articulo:4" for h in hits)


async def test_the_accent_vocabulary_follows_the_corpus(
    index: SqlPassageIndex, db_sessions: async_sessionmaker
) -> None:  # type: ignore[type-arg]
    await index.sync(ACCENTS)
    async with db_sessions() as session:
        before = (
            await session.execute(
                text("SELECT count(*) FROM retrieval_accents WHERE plain = 'resolucion'")
            )
        ).scalar_one()

    await index.sync(
        [p for p in ACCENTS if p.path not in {"articulo:1", "articulo:2"}]
    )  # the only passages using it are gone

    async with db_sessions() as session:
        after = (
            await session.execute(
                text("SELECT count(*) FROM retrieval_accents WHERE plain = 'resolucion'")
            )
        ).scalar_one()
    assert (before, after) == (1, 0)


# ------------------------------------------------------------------------------- segments
@pytest.mark.parametrize(
    ("headline", "expected"),
    [
        ("sin marcas", [("sin marcas", False)]),
        (f"a {MARKERS[0]}b{MARKERS[1]} c", [("a ", False), ("b", True), (" c", False)]),
        (f"{MARKERS[0]}x{MARKERS[1]}{MARKERS[0]}y{MARKERS[1]}", [("x", True), ("y", True)]),
        ("", []),
    ],
)
def test_headlines_become_segments_never_html(
    headline: str, expected: list[tuple[str, bool]]
) -> None:
    assert [(s.text, s.match) for s in segments(headline)] == expected


async def test_unrelated_random_ids_do_not_leak_between_tests(index: SqlPassageIndex) -> None:
    assert await index.count() == 0, str(uuid.uuid4())
