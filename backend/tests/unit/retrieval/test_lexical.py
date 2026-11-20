"""Accent handling for the words search."""

import pytest

from drtc_chatbot.contexts.retrieval.domain.lexical import (
    accent_pairs,
    expand_query,
    has_accent,
    strip_accents,
    words,
)


@pytest.mark.spec("004-FR-006")
def test_words_are_runs_of_letters_in_lower_case_keeping_the_enye() -> None:
    assert words("¿Cuántos DÍAS tiene el año? (15) art. 5-A, daños") == [
        "cuántos",
        "días",
        "tiene",
        "el",
        "año",
        "art",
        "a",
        "daños",
    ]


@pytest.mark.parametrize(
    ("word", "plain"),
    [
        ("apelación", "apelacion"),
        ("vehículo", "vehiculo"),
        ("pingüino", "pinguino"),
        ("año", "año"),
        ("daños", "daños"),
        ("tránsito", "transito"),
    ],
)
def test_only_acute_accents_and_diaeresis_are_removed_never_the_enye(word: str, plain: str) -> None:
    assert strip_accents(word) == plain


def test_has_accent() -> None:
    assert has_accent("sanción")
    assert not has_accent("sancion")
    assert not has_accent("año")


def test_the_corpus_vocabulary_gives_the_pairs_of_accented_words() -> None:
    texts = [
        "El recurso de apelación y la resolución.",
        "Resolución de la APELACIÓN en tránsito",
        "sin acentos",
    ]

    assert accent_pairs(texts) == {
        ("apelacion", "apelación"),
        ("resolucion", "resolución"),
        ("transito", "tránsito"),
    }


@pytest.mark.spec("004-FR-006")
def test_a_word_typed_without_accent_gets_its_accented_form_added() -> None:
    variants = {"apelacion": ["apelación"], "transito": ["tránsito"]}

    assert (
        expand_query("plazo de apelacion en transito", variants)
        == "plazo de apelacion en transito apelación tránsito"
    )


def test_a_word_with_several_accented_forms_gets_all_of_them_once() -> None:
    variants = {"publico": ["público", "publicó"]}

    assert expand_query("publico y publico", variants) == "publico y publico público publicó"


def test_accented_or_unknown_words_and_texts_without_variants_are_left_alone() -> None:
    variants = {"apelacion": ["apelación"]}

    assert (
        expand_query("apelación del recurso", variants) == "apelación del recurso"
    )  # already accented
    assert expand_query("criptomonedas", variants) == "criptomonedas"
    assert expand_query("", variants) == ""


@pytest.mark.spec("004-FR-006")
@pytest.mark.parametrize(
    ("typed", "expanded"),
    [
        ("apelacion", "apelacion apelación"),
        ("resolucion y notificacion", "resolucion y notificacion resolución notificación"),
        ("decision region", "decision region decisión región"),
        ("opinion", "opinion opinión"),
        ("ion", "ion"),  # no consonant before: not part of the family
        ("lesion", "lesion lesión"),
        ("organizacion", "organizacion organización"),
        ("camion", "camion camión"),
        ("aereo", "aereo"),  # other endings are not touched
    ],
)
def test_the_ion_family_is_restored_even_if_the_corpus_has_only_the_plural(
    typed: str, expanded: str
) -> None:
    assert expand_query(typed, {}) == expanded


def test_the_corpus_form_and_the_rule_do_not_repeat_each_other() -> None:
    assert expand_query("apelacion", {"apelacion": ["apelación"]}) == "apelacion apelación"
