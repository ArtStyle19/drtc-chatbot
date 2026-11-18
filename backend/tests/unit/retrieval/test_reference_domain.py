"""Text normalization, reference parsing, norm recognition and path matching (pure domain)."""

import pytest

from drtc_chatbot.contexts.retrieval.domain.matching import labels_equal, matches
from drtc_chatbot.contexts.retrieval.domain.norms import NormIndex, NormInfo
from drtc_chatbot.contexts.retrieval.domain.ordinals import ordinal_value
from drtc_chatbot.contexts.retrieval.domain.reference import Step, parse_reference_text
from drtc_chatbot.contexts.retrieval.domain.text import normalize

LEY = NormInfo(
    "ley-27181", "ley", "27181", "Ley General de Transporte y Tránsito Terrestre",
    "Ley 27181 (LGTTT)", ("lgttt", "ley general de transporte"),
)  # fmt: skip
RENAT = NormInfo(
    "ds-017-2009-mtc", "decreto_supremo", "017-2009-MTC",
    "Reglamento Nacional de Administración de Transporte", "RENAT (DS 017-2009-MTC)",
    ("renat", "reglamento de transporte"),
)  # fmt: skip
TUO = NormInfo(
    "tuo-ley-27444", "texto_unico_ordenado", "27444",
    "Texto Único Ordenado de la Ley N.° 27444, Ley del Procedimiento Administrativo General",
    "TUO de la Ley 27444 (LPAG)", ("lpag", "tuo", "tuo lpag"),
)  # fmt: skip
INDEX = NormIndex([LEY, RENAT, TUO])


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Art. 5° de la Ley N.° 27181", "art 5 de la ley n 27181"),
        ("ARTÍCULO  218.2 del TUO", "articulo 218.2 del tuo"),
        ("Ley Nº 27181", "ley n 27181"),
        ("ley n° 27181", "ley n 27181"),
        ("D.S. N° 017-2009-MTC", "d s n 017-2009-mtc"),
        ("lit. e) del art. 2", "lit e del art 2"),
        ("  art.    4-A  ", "art 4-a"),
        ("¿Qué dice el art. 5?", "que dice el art 5"),
    ],
)
def test_normalization_removes_case_accents_signs_and_stray_dots(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    ("words", "value"),
    [
        ("primera", 1),
        ("tercer", 3),
        ("decima", 10),
        ("decima primera", 11),
        ("decimo segunda", 12),
        ("undecima", 11),
        ("vigesima tercera", 23),
        ("unica", -1),
        ("segunda-parte", None),
    ],
)
def test_ordinals(words: str, value: int | None) -> None:
    assert ordinal_value(words) == value


def steps(raw: str) -> list[tuple[str, str] | tuple[str, str, tuple[str, ...]]]:
    return [
        (s.kind, s.value, s.group) if s.kind == "disposicion" else (s.kind, s.value)
        for s in parse_reference_text(raw).steps
    ]


@pytest.mark.spec("003-FR-007")
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("art. 5", [("articulo", "5")]),
        ("Artículo 5°", [("articulo", "5")]),
        ("arts 5", [("articulo", "5")]),
        ("art 4-A", [("articulo", "4-a")]),
        ("art. 2 lit. e)", [("articulo", "2"), ("literal", "e")]),
        ("art 2 inciso e", [("articulo", "2"), ("literal", "e")]),
        ("literal e del artículo 2", [("articulo", "2"), ("literal", "e")]),
        ("inciso b) del artículo 23", [("articulo", "23"), ("literal", "b")]),
        ("art 218.2", [("articulo", "218"), ("numeral", "218.2")]),
        ("218.2", [("articulo", "218"), ("numeral", "218.2")]),
        ("art 35 num 1", [("articulo", "35"), ("numeral", "1")]),
        ("numeral 5.2 del artículo 5", [("articulo", "5"), ("numeral", "5.2")]),
        ("art 35 num 35.1 inc 1", [("articulo", "35"), ("numeral", "35.1"), ("numeral", "1")]),
        (
            "inciso 1 del numeral 35.1 del art 35",
            [("articulo", "35"), ("numeral", "35.1"), ("numeral", "1")],
        ),
        ("anexo 2", [("anexo", "2")]),
        ("Anexo II", [("anexo", "ii")]),
        ("título IV", [("titulo", "iv")]),
        ("titulo preliminar", [("titulo", "preliminar")]),
        ("capítulo II del título IV", [("titulo", "iv"), ("capitulo", "ii")]),
        ("sección sexta", [("seccion", "sexta")]),
        (
            "primera disposición complementaria final",
            [("disposicion", "primera", ("complementaria", "final"))],
        ),
        (
            "disposición complementaria final primera",
            [("disposicion", "primera", ("complementaria", "final"))],
        ),
        ("tercera disposición final", [("disposicion", "tercera", ("final",))]),
        ("DCF tercera", [("disposicion", "tercera", ("complementaria", "final"))]),
        (
            "décima primera disposición complementaria transitoria",
            [("disposicion", "decima primera", ("complementaria", "transitoria"))],
        ),
        (
            "disposiciones complementarias finales",
            [("disposicion", "", ("complementaria", "final"))],
        ),
        ("única disposición complementaria", [("disposicion", "unica", ("complementaria",))]),
        (
            "primera disposición complementaria final lit. a",
            [("disposicion", "primera", ("complementaria", "final")), ("literal", "a")],
        ),
    ],
)
def test_structural_steps_are_understood_in_many_phrasings(
    raw: str, expected: list[object]
) -> None:
    assert steps(raw) == expected


@pytest.mark.parametrize(
    "raw", ["transporte de mercancías", "art civil", "hola", "5", "lit", "art", "inciso"]
)
def test_text_that_is_not_a_reference_yields_no_steps(raw: str) -> None:
    assert parse_reference_text(raw).steps == ()


def test_an_inciso_with_a_letter_is_a_literal() -> None:
    assert steps("inciso x y") == [("literal", "x")]


def test_a_bare_number_inside_an_article_reference_is_not_taken_twice() -> None:
    assert steps("art 218.2") == [("articulo", "218"), ("numeral", "218.2")]


@pytest.mark.parametrize(
    ("raw", "ids"),
    [
        ("art 5 de la Ley 27181", ["ley-27181"]),
        ("art 5 ley n° 27181", ["ley-27181"]),
        ("27181 art 5", ["ley-27181"]),
        ("art 5 LGTTT", ["ley-27181"]),
        ("art 5 Ley General de Transporte y Tránsito Terrestre", ["ley-27181"]),
        ("art 11 RENAT", ["ds-017-2009-mtc"]),
        ("art 11 DS 017-2009-MTC", ["ds-017-2009-mtc"]),
        ("art 11 D.S. N° 017-2009-MTC", ["ds-017-2009-mtc"]),
        ("art 11 decreto supremo 017-2009-mtc", ["ds-017-2009-mtc"]),
        ("art 218 TUO", ["tuo-ley-27444"]),
        ("art 218 LPAG", ["tuo-ley-27444"]),
        ("art 218 Ley 27444", ["tuo-ley-27444"]),
        ("art 218 ley del procedimiento administrativo general", ["tuo-ley-27444"]),
        ("art 5", []),
        ("art 5 ley 27181 y renat", ["ley-27181", "ds-017-2009-mtc"]),
    ],
)
def test_norms_are_recognized_by_acronym_number_title_and_alias(raw: str, ids: list[str]) -> None:
    assert list(INDEX.find(normalize(raw)).instrument_ids) == ids


@pytest.mark.parametrize(
    "raw", ["art 5 ley 99999", "art 3 ds 017-2020-mtc", "art 2 decreto legislativo 1272"]
)
def test_something_that_looks_like_a_norm_but_is_not_in_the_corpus_is_reported_not_guessed(
    raw: str,
) -> None:
    mentions = INDEX.find(normalize(raw))

    assert mentions.instrument_ids == ()
    assert mentions.unknown is not None


def test_a_number_inside_a_longer_token_is_not_a_norm() -> None:
    assert INDEX.find(normalize("art 5 num 127181-a")).instrument_ids == ()


def test_the_norm_mention_is_removed_from_the_remainder() -> None:
    assert INDEX.find(normalize("art 5 de la Ley 27181")).remainder == "art 5 de la"


def test_a_shared_alias_recognizes_both_norms() -> None:
    other = NormInfo("otra", "ley", "100", "Otra ley", "Otra", ("lpag",))
    assert list(NormIndex([TUO, other]).find("art 5 lpag").instrument_ids) == [
        "otra",
        "tuo-ley-27444",
    ]


@pytest.mark.parametrize(
    ("a", "b", "equal"),
    [
        ("05", "5", True),
        ("4-A", "4-a", True),
        ("IV", "iv", True),
        ("5", "6", False),
        ("4-A", "4", False),
    ],
)
def test_labels_compare_without_case_or_leading_zeros(a: str, b: str, equal: bool) -> None:
    assert labels_equal(a, b) is equal


def s(*args: object) -> tuple[Step, ...]:
    return tuple(Step(*args_) for args_ in args)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("path", "steps_", "expected"),
    [
        ("articulo:2", s(("articulo", "2")), True),
        ("articulo:2", s(("articulo", "3")), False),
        ("articulo:4-A", s(("articulo", "4")), False),
        ("articulo:4-A", s(("articulo", "4-a")), True),
        ("articulo:2/literal:e", s(("articulo", "2"), ("literal", "e")), True),
        ("articulo:2/literal:e", s(("articulo", "2")), False),  # the article itself is another path
        ("articulo:3/literal:e", s(("articulo", "2"), ("literal", "e")), False),
        ("articulo:218/numeral:218.2", s(("articulo", "218"), ("numeral", "218.2")), True),
        ("articulo:5/numeral:5.2", s(("articulo", "5"), ("numeral", "2")), True),
        (
            "articulo:35/numeral:35.1/numeral:1",
            s(("articulo", "35"), ("numeral", "35.1"), ("numeral", "1")),
            True,
        ),
        ("articulo:35/numeral:35.1/numeral:1", s(("articulo", "35"), ("numeral", "1")), True),
        ("articulo:4-A/numeral:4-A.1/literal:a", s(("articulo", "4-a"), ("literal", "a")), True),
        ("articulo:4-A/numeral:4-A.2/literal:a", s(("articulo", "4-a"), ("literal", "a")), True),
        ("anexo:2", s(("anexo", "2")), True),
        ("titulo:IV", s(("titulo", "iv")), True),
        ("titulo:IV/capitulo:II", s(("titulo", "iv"), ("capitulo", "ii")), True),
        ("titulo:IV/capitulo:II", s(("capitulo", "ii")), True),
        ("seccion:sexta", s(("seccion", "sexta")), True),
        ("disposiciones:finales/tercera", s(("disposicion", "tercera", ("final",))), True),
        ("disposiciones:finales/tercera", s(("disposicion", "segunda", ("final",))), False),
        ("disposiciones:finales/tercera", s(("disposicion", "tercera", ("transitoria",))), False),
        ("disposiciones:finales/tercera", s(("disposicion", "tercera", ())), True),
        (
            "seccion:sexta/disposiciones:complementarias-finales/primera",
            s(("disposicion", "primera", ("complementaria", "final"))),
            True,
        ),
        (
            "seccion:sexta/disposiciones:complementarias-finales/primera",
            s(("disposicion", "primera", ("final",))),
            True,
        ),
        (
            "seccion:sexta/disposiciones:complementarias-finales/primera",
            s(("disposicion", "primera", ("transitoria",))),
            False,
        ),
        (
            "seccion:sexta/disposiciones:complementarias-finales/decima-primera",
            s(("disposicion", "decima primera", ("final",))),
            True,
        ),
        (
            "disposiciones:complementarias/primera",
            s(("disposicion", "primera", ("complementaria", "final"))),
            False,
        ),
        ("disposiciones:finales", s(("disposicion", "", ("final",))), True),
        ("disposiciones:finales/primera", s(("disposicion", "", ("final",))), False),
        (
            "disposiciones:finales/primera/literal:a",
            s(("disposicion", "primera", ("final",)), ("literal", "a")),
            True,
        ),
        ("disposicion:unica", s(("disposicion", "unica", ())), True),
    ],
)
def test_paths_match_the_last_step_and_the_earlier_steps_in_order(
    path: str, steps_: tuple[Step, ...], expected: bool
) -> None:
    assert matches(path, steps_) is expected


def test_no_steps_never_match() -> None:
    assert matches("articulo:2", ()) is False
