"""Breadcrumb and inherited lead of a provision (spec 004)."""

import pytest

from drtc_chatbot.contexts.legal_corpus.domain.passages import (
    LEAD_LENGTH,
    ProvisionText,
    ancestors,
    breadcrumb,
    lead_of,
)
from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind as K


def row(
    path: str,
    kind: K,
    label: str,
    *,
    title: str | None = None,
    text: str = "",
    parent: str | None = None,
) -> ProvisionText:
    return ProvisionText(path, kind, label, title, text, 3, 3, parent)


ROWS = [
    row("titulo:I", K.TITLE, "I", title="Definiciones y ámbito"),
    row("capitulo:II", K.CHAPTER, "II", title="Del servicio", parent="titulo:I"),
    row("articulo:2", K.ARTICLE, "2", title="De las definiciones", text="Para efectos de la presente Ley, entiéndase por:", parent="capitulo:II"),
    row("articulo:2/literal:e", K.LITERAL, "e", text="Servicio de Transporte de Personas: …", parent="articulo:2"),
    row("articulo:218", K.ARTICLE, "218", parent=None),
    row("articulo:218/numeral:218.2", K.NUMERAL, "218.2", text="El término es de quince días.", parent="articulo:218"),
    row("articulo:35", K.ARTICLE, "35", parent=None),
    row("articulo:35/numeral:35.1", K.NUMERAL, "35.1", text="Los procedimientos están sujetos a silencio positivo, cuando:", parent="articulo:35"),
    row("articulo:35/numeral:35.1/numeral:1", K.NUMERAL, "1", text="Todos los procedimientos a instancia de parte.", parent="articulo:35/numeral:35.1"),
]  # fmt: skip
BY_PATH = {r.path: r for r in ROWS}


def of(path: str) -> ProvisionText:
    return BY_PATH[path]


@pytest.mark.spec("004-FR-006")
def test_the_breadcrumb_walks_from_the_norm_through_the_containers_to_the_provision() -> None:
    assert breadcrumb("Ley 27181 (LGTTT)", of("articulo:2/literal:e"), BY_PATH) == (
        "Ley 27181 (LGTTT) › Título I: Definiciones y ámbito › Capítulo II: Del servicio › "
        "Art. 2 – De las definiciones › lit. e)"
    )


def test_an_article_without_container_or_title_has_a_short_breadcrumb() -> None:
    assert (
        breadcrumb("TUO", of("articulo:218/numeral:218.2"), BY_PATH)
        == "TUO › Art. 218 › num. 218.2"
    )


def test_nested_numerals_keep_every_level() -> None:
    assert breadcrumb("TUO", of("articulo:35/numeral:35.1/numeral:1"), BY_PATH) == (
        "TUO › Art. 35 › num. 35.1 › num. 1"
    )


def test_annexes_and_dispositions_are_described_like_their_citation() -> None:
    annex = row("anexo:2", K.ANNEX, "2", title="TABLA DE INFRACCIONES")
    final = row("disposiciones:finales/tercera", K.DISPOSITION, "tercera")

    assert breadcrumb("RENAT", annex, {}) == "RENAT › Anexo 2 – TABLA DE INFRACCIONES"
    assert breadcrumb("RENAT", final, {}) == "RENAT › Tercera Disposición Final"


def test_ancestors_are_listed_outermost_first_and_stop_at_unknown_parents() -> None:
    assert [a.path for a in ancestors(of("articulo:2/literal:e"), BY_PATH)] == [
        "titulo:I",
        "capitulo:II",
        "articulo:2",
    ]
    orphan = row("articulo:9/numeral:9.1", K.NUMERAL, "9.1", parent="articulo:9")
    assert ancestors(orphan, {}) == []


def test_a_parent_loop_does_not_hang() -> None:
    a = row("articulo:1", K.ARTICLE, "1", parent="articulo:2")
    b = row("articulo:2", K.ARTICLE, "2", parent="articulo:1")

    assert [x.path for x in ancestors(a, {"articulo:1": a, "articulo:2": b})] == ["articulo:2"]


@pytest.mark.spec("004-FR-006")
def test_a_literal_inherits_the_lead_of_the_article_that_introduces_it() -> None:
    assert (
        lead_of(of("articulo:2/literal:e"), BY_PATH)
        == "Para efectos de la presente Ley, entiéndase por:"
    )


def test_a_numeral_under_an_article_without_text_has_no_lead_and_one_under_a_numeral_has_it() -> (
    None
):
    assert lead_of(of("articulo:218/numeral:218.2"), BY_PATH) is None
    assert lead_of(of("articulo:35/numeral:35.1/numeral:1"), BY_PATH) == (
        "Los procedimientos están sujetos a silencio positivo, cuando:"
    )


def test_articles_dispositions_and_annexes_have_no_lead() -> None:
    assert lead_of(of("articulo:2"), BY_PATH) is None


def test_a_long_lead_is_cut_and_whitespace_is_collapsed() -> None:
    parent = row("articulo:1", K.ARTICLE, "1", text=("palabra  larga\n" * 100))
    child = row("articulo:1/literal:a", K.LITERAL, "a", parent="articulo:1")

    lead = lead_of(child, {"articulo:1": parent, child.path: child})

    assert lead is not None
    assert len(lead) <= LEAD_LENGTH
    assert "  " not in lead
    assert "\n" not in lead
