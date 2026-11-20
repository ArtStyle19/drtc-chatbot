"""Structural paths, reading units and citations (pure domain)."""

from datetime import date

import pytest

from drtc_chatbot.contexts.legal_corpus.domain.citations import (
    CitationSubject,
    describe_location,
    format_citation,
    short_citation,
)
from drtc_chatbot.contexts.legal_corpus.domain.provisions import EventKind, LegalEvent
from drtc_chatbot.contexts.legal_corpus.domain.reading import (
    is_container_path,
    reading_unit_path,
    split_path,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    VerificationStatus,
)


@pytest.mark.parametrize(
    ("path", "unit"),
    [
        ("articulo:2", "articulo:2"),
        ("articulo:2/literal:e", "articulo:2"),
        ("articulo:4-A/numeral:4-A.1/literal:a", "articulo:4-A"),
        ("articulo:IV/numeral:1.15", "articulo:IV"),
        ("anexo:2", "anexo:2"),
        ("disposiciones:finales/tercera", "disposiciones:finales/tercera"),
        ("disposiciones:finales/tercera/literal:a", "disposiciones:finales/tercera"),
        (
            "seccion:sexta/disposiciones:complementarias-finales/primera/literal:b",
            "seccion:sexta/disposiciones:complementarias-finales/primera",
        ),
        ("disposicion:unica", "disposicion:unica"),
        ("titulo:I/capitulo:II", "titulo:I/capitulo:II"),
        (
            "seccion:sexta/disposiciones:complementarias-finales",
            "seccion:sexta/disposiciones:complementarias-finales",
        ),
    ],
)
def test_the_reading_unit_is_the_article_disposition_or_annex_that_contains_the_path(
    path: str, unit: str
) -> None:
    assert reading_unit_path(path) == unit


@pytest.mark.parametrize(
    ("path", "container"),
    [
        ("titulo:I", True),
        ("titulo:I/capitulo:II", True),
        ("seccion:sexta", True),
        ("seccion:sexta/disposiciones:complementarias-finales", True),
        ("articulo:2", False),
        ("disposiciones:finales/tercera", False),
        ("anexo:1", False),
    ],
)
def test_containers_are_recognized(path: str, container: bool) -> None:
    assert is_container_path(path) is container


def test_split_path_keeps_disposition_ordinals_as_keyless_segments() -> None:
    segments = split_path("disposiciones:finales/tercera/literal:a")

    assert [(s.key, s.value) for s in segments] == [
        ("disposiciones", "finales"),
        ("", "tercera"),
        ("literal", "a"),
    ]


@pytest.mark.parametrize(
    ("path", "text"),
    [
        ("articulo:2", "art. 2"),
        ("articulo:2/literal:e", "art. 2, lit. e)"),
        ("articulo:4-A/numeral:4-A.1/literal:a", "art. 4-A, num. 4-A.1, lit. a)"),
        ("articulo:3/numeral:3.1/numeral:3.1.1", "art. 3, num. 3.1, num. 3.1.1"),
        ("articulo:35/numeral:35.1/numeral:1", "art. 35, num. 35.1, inc. 1"),
        ("articulo:248/numeral:1/literal:a", "art. 248, num. 1, lit. a)"),
        ("articulo:IV", "art. IV"),
        ("disposiciones:finales/tercera", "Tercera Disposición Final"),
        (
            "seccion:sexta/disposiciones:complementarias-finales/primera",
            "Sección Sexta, Primera Disposición Complementaria Final",
        ),
        (
            "disposiciones:complementarias/primera/literal:a",
            "Primera Disposición Complementaria, lit. a)",
        ),
        ("anexo:2", "Anexo 2"),
        ("titulo:IV", "Título IV"),
        ("titulo:PRELIMINAR", "Título Preliminar"),
        ("titulo:I/capitulo:II", "Título I, Capítulo II"),
    ],
)
def test_location_is_written_the_way_lawyers_cite(path: str, text: str) -> None:
    assert describe_location(path) == text


def subject(**overrides: object) -> CitationSubject:
    values: dict[str, object] = {
        "instrument_type": InstrumentType.LAW,
        "number": "27181",
        "title": "Ley General de Transporte y Tránsito Terrestre",
        "edition_label": "Compilación no oficial con modificaciones hasta mayo de 2020",
        "consolidated_as_of": None,
        "verification_status": VerificationStatus.UNVERIFIED,
        "source_file_name": "ley-27181-lgttt-texto-2020-06.pdf",
        "page_start": 3,
        "page_end": 3,
    }
    values.update(overrides)
    return CitationSubject(**values)  # type: ignore[arg-type]


@pytest.mark.spec("003-FR-003")
def test_the_short_citation_names_the_norm_and_the_location() -> None:
    assert short_citation(subject(), "articulo:2/literal:e") == "Ley N.° 27181, art. 2, lit. e)"
    renat = subject(instrument_type=InstrumentType.SUPREME_DECREE, number="017-2009-MTC")
    assert short_citation(renat, "articulo:11") == "D.S. N.° 017-2009-MTC, art. 11"
    tuo = subject(instrument_type=InstrumentType.SINGLE_ORDERED_TEXT, number="27444")
    assert (
        short_citation(tuo, "articulo:218/numeral:218.2")
        == "TUO de la Ley N.° 27444, art. 218, num. 218.2"
    )


@pytest.mark.spec("003-FR-003")
def test_the_formal_citation_states_edition_verification_and_page() -> None:
    citation = format_citation(subject(), "articulo:2/literal:e")

    assert citation.formal == (
        "Ley N.° 27181, Ley General de Transporte y Tránsito Terrestre, art. 2, lit. e). "
        "Edición: Compilación no oficial con modificaciones hasta mayo de 2020 "
        "(edición no verificada frente a la fuente oficial). "
        "Fuente: ley-27181-lgttt-texto-2020-06.pdf, p. 3 del PDF."
    )


@pytest.mark.spec("003-FR-003")
@pytest.mark.parametrize(
    "status", [s for s in VerificationStatus if s is not VerificationStatus.VERIFIED_CURRENT]
)
def test_no_citation_of_an_unverified_edition_claims_it_is_in_force(
    status: VerificationStatus,
) -> None:
    formal = format_citation(subject(verification_status=status), "articulo:2").formal

    assert "verificado como vigente" not in formal
    assert "vigente" not in formal.replace("no vigente", "")


def test_only_a_verified_edition_is_cited_as_verified() -> None:
    formal = format_citation(
        subject(verification_status=VerificationStatus.VERIFIED_CURRENT), "articulo:2"
    ).formal

    assert "(texto verificado como vigente)" in formal


def test_consolidation_date_and_multi_page_ranges_are_cited() -> None:
    formal = format_citation(
        subject(consolidated_as_of=date(2017, 1, 4), page_start=18, page_end=19), "articulo:11"
    ).formal

    assert "actualizada al 04-01-2017" in formal
    assert "pp. 18-19 del PDF" in formal


@pytest.mark.spec("003-FR-004")
def test_a_superseded_text_is_cited_as_not_in_force() -> None:
    event = LegalEvent(
        EventKind.SUBSTITUTED, "el Decreto de Urgencia Nº 019-2020", date(2020, 1, 24)
    )
    citation = format_citation(subject(superseded_by=event), "articulo:2")

    assert citation.short.endswith("(texto sustituido)")
    assert (
        "Texto sustituido por el Decreto de Urgencia Nº 019-2020 (24-01-2020): no vigente"
        in citation.formal
    )
