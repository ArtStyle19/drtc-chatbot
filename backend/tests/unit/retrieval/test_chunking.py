"""What is embedded for a passage, how long texts are cut, and what decides a re-embed."""

from itertools import pairwise

import pytest

from drtc_chatbot.contexts.retrieval.domain.chunking import (
    MARKERS,
    MAX_WINDOW_CHARS,
    PassageText,
    clean,
    content_hash,
    embedding_windows,
    split_body,
    window_hash,
)


def passage(**overrides: object) -> PassageText:
    values: dict[str, object] = {
        "instrument_id": "ley-27181", "version_id": "ley@1", "path": "articulo:2/literal:e",
        "unit_path": "articulo:2", "kind": "literal", "label": "e", "title": None,
        "breadcrumb": "Ley 27181 › Art. 2 › lit. e)", "lead": "Para efectos de la presente Ley, entiéndase por:",
        "body": "Servicio de Transporte de Personas.", "page_start": 3, "page_end": 3, "citation": "Ley N.° 27181, art. 2, lit. e)",
    }  # fmt: skip
    values.update(overrides)
    return PassageText(**values)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- what is embedded
@pytest.mark.spec("004-FR-006")
def test_a_short_passage_is_one_window_with_its_context_first() -> None:
    [window] = embedding_windows(passage())

    assert window == (
        "Ley 27181 › Art. 2 › lit. e)\nPara efectos de la presente Ley, entiéndase por:\n"
        "Servicio de Transporte de Personas."
    )


def test_missing_lead_and_title_are_simply_left_out() -> None:
    [window] = embedding_windows(passage(lead=None, title=None))

    assert window == "Ley 27181 › Art. 2 › lit. e)\nServicio de Transporte de Personas."


def test_the_title_of_an_article_is_part_of_what_is_embedded() -> None:
    [window] = embedding_windows(passage(kind="article", lead=None, title="De las definiciones"))

    assert "De las definiciones" in window


def test_an_article_without_body_is_embedded_by_its_header_alone() -> None:
    assert embedding_windows(passage(body="", lead=None, title="Recurso de apelación")) == [
        "Ley 27181 › Art. 2 › lit. e)\nRecurso de apelación"
    ]


def test_whitespace_in_the_body_is_collapsed_before_embedding() -> None:
    [window] = embedding_windows(passage(body="Servicio\n\n  de   transporte"))

    assert window.endswith("Servicio de transporte")


def test_highlight_markers_can_never_come_from_a_text() -> None:
    dirty = f"palabra{MARKERS[0]}resaltada{MARKERS[1]} normal"

    assert clean(dirty) == "palabraresaltada normal"
    [window] = embedding_windows(passage(body=dirty))
    assert not any(marker in window for marker in MARKERS)


# --------------------------------------------------------------------------- long texts
SENTENCE = "El transportista debe cumplir con las condiciones técnicas exigidas por el Reglamento. "


def long_body(sentences: int) -> str:
    return "".join(f"{i}. {SENTENCE}" for i in range(sentences)).strip()


@pytest.mark.spec("004-FR-006")
def test_a_long_text_is_cut_into_windows_that_fit_and_that_cover_everything() -> None:
    body = long_body(300)  # ≈ 27 000 characters, like the RENAT annex

    windows = embedding_windows(passage(body=body))

    assert len(windows) > 5
    assert all(len(w) <= MAX_WINDOW_CHARS for w in windows)
    joined = " ".join(windows)
    assert all(f"{i}. El transportista" in joined for i in range(300))  # no sentence is lost


def test_every_window_carries_the_context_of_the_passage() -> None:
    windows = embedding_windows(passage(body=long_body(300)))

    assert all(w.startswith("Ley 27181 › Art. 2 › lit. e)\n") for w in windows)


def test_consecutive_windows_overlap_so_a_sentence_on_the_edge_is_not_orphaned() -> None:
    windows = split_body(long_body(300), 3000)

    for before, after in pairwise(windows):
        last_sentence = before.split(". ")[-2] if before.count(". ") > 1 else before
        assert last_sentence[-30:] in after, "the tail of a window must reappear in the next one"


def test_windows_start_and_end_at_sentence_boundaries() -> None:
    windows = split_body(long_body(300), 3000)

    assert all(
        w[0].isdigit() for w in windows
    )  # every window starts at the beginning of a sentence
    assert all(w.endswith(".") for w in windows)  # and ends at its end


def test_a_text_that_fits_is_not_cut_and_exactly_the_limit_is_not_cut_either() -> None:
    assert split_body("corto.", 100) == ["corto."]
    exact = "x" * 100
    assert split_body(exact, 100) == [exact]


def test_a_single_sentence_longer_than_a_window_is_cut_by_size_as_a_last_resort() -> None:
    windows = split_body("palabra " * 1000, 3000)

    assert len(windows) >= 3
    assert all(len(w) <= 3000 for w in windows)


def test_a_very_long_header_never_leaves_a_window_without_room_for_text() -> None:
    windows = embedding_windows(passage(breadcrumb="B" * 3000, body=long_body(40)), max_chars=3500)

    assert len(windows) >= 1
    assert all("El transportista" in w for w in windows)


# --------------------------------------------------------------------------- hashes
@pytest.mark.spec("004-FR-016")
def test_the_hash_is_stable_and_ignores_what_does_not_affect_indexing() -> None:
    base = content_hash(passage())

    assert base == content_hash(passage())
    assert base == content_hash(
        passage(page_start=9, page_end=9, citation="otra cita", unit_path="x")
    )


@pytest.mark.parametrize(
    "change",
    [
        {"body": "Otro texto."},
        {"lead": "Otro encabezado:"},
        {"title": "Un título"},
        {"breadcrumb": "Otra ruta"},
    ],
)
def test_the_hash_changes_when_the_indexed_text_changes(change: dict[str, object]) -> None:
    assert content_hash(passage(**change)) != content_hash(passage())


def test_fields_do_not_blur_into_each_other_in_the_hash() -> None:
    assert content_hash(passage(lead="ab", body="c")) != content_hash(passage(lead="a", body="bc"))


def test_a_window_hash_is_the_hash_of_its_text() -> None:
    assert window_hash("texto") == window_hash("texto")
    assert window_hash("texto") != window_hash("texto ")
