"""Parser behaviour on small passages taken from the real PDFs (Ley 27181, RENAT, TUO)."""

import pytest

from drtc_chatbot.contexts.ingestion.domain.parsing.model import (
    EventKind,
    ParsedKind,
    ParsedProvision,
    ParseResult,
    RevisionStatus,
    SourceLine,
    TextBox,
)
from drtc_chatbot.contexts.ingestion.domain.parsing.profiles import build_parser


def lines(text: str, *, page: int = 1, small_prefix: str | None = None) -> list[SourceLine]:
    return [
        SourceLine(page, line, small=bool(small_prefix and line.startswith(small_prefix)))
        for line in text.strip().splitlines()
    ]


def parse(text: str, profile: str = "ley-lgttt") -> ParseResult:
    return build_parser(profile).parse(lines(text))


def by_path(result: ParseResult, path: str) -> list[ParsedProvision]:
    return [p for p in result.provisions if p.path == path]


def current(result: ParseResult, path: str) -> ParsedProvision:
    [rev] = [p for p in by_path(result, path) if p.status is RevisionStatus.CURRENT]
    return rev


STRUCTURE = """
TITULO I
DEFINICIONES Y AMBITO DE APLICACION
Artículo 1.- Del ámbito de aplicación
1.1 La presente Ley establece los lineamientos generales del transporte y rige en
todo el territorio de la República.
1.2 No se encuentra comprendido el transporte por cable.
Artículo    3.-   Del     objetivo     de     la     acción     estatal
La acción estatal se orienta a la satisfacción de las necesidades de los usuarios.
Artículo 4.- De la libre competencia y rol del Estado
4.1 El rol estatal proviene de las definiciones nacionales.
a) Primera condición;
b) Segunda condición.
"""


@pytest.mark.spec("002-FR-001")
def test_articles_numerals_and_literals_get_stable_paths() -> None:
    result = parse(STRUCTURE)

    assert [p.path for p in result.provisions] == [
        "titulo:I",
        "articulo:1",
        "articulo:1/numeral:1.1",
        "articulo:1/numeral:1.2",
        "articulo:3",
        "articulo:4",
        "articulo:4/numeral:4.1",
        "articulo:4/numeral:4.1/literal:a",
        "articulo:4/numeral:4.1/literal:b",
    ]
    assert current(result, "titulo:I").title == "DEFINICIONES Y AMBITO DE APLICACION"
    assert (
        current(result, "articulo:4/numeral:4.1/literal:b").parent_path == "articulo:4/numeral:4.1"
    )


def test_irregular_heading_spacing_is_normalized_and_text_is_joined() -> None:
    result = parse(STRUCTURE)

    assert current(result, "articulo:3").title == "Del objetivo de la acción estatal"
    assert current(result, "articulo:1/numeral:1.1").text.endswith(
        "todo el territorio de la República."
    )


def test_a_cross_reference_at_line_start_is_not_a_heading() -> None:
    text = (
        STRUCTURE + "Artículo 1 de la Resolución Directoral prorroga la vigencia de los permisos.\n"
    )

    result = parse(text)

    assert [p.path for p in result.provisions if p.kind is ParsedKind.ARTICLE] == [
        "articulo:1",
        "articulo:3",
        "articulo:4",
    ]
    assert "Resolución Directoral" in current(result, "articulo:4/numeral:4.1/literal:b").text


ARTICLE_REPLACED = """
Artículo 15.- De las autoridades competentes
Son autoridades competentes según corresponda:
a) El Ministerio de Transportes, Comunicaciones, Vivienda y Construcción;
b) Las Municipalidades Provinciales.
(*) Artículo modificado por el Artículo 1 de la Ley Nº 28172, publicada el 17 febrero
2004, cuyo texto es el siguiente:
“Artículo 15.- De las autoridades competentes
Son autoridades competentes en materia de transporte:
a) El Ministerio de Transportes y Comunicaciones;
b) Los Gobiernos Regionales."
"c) El Ministerio de la Producción.”(*)
(*) Literal c) incorporado por el Artículo 18 del Decreto Legislativo Nº 1451,
publicado el 20 septiembre 2018.
Artículo 16.- De las competencias del Ministerio
Corresponde al Ministerio dictar los reglamentos nacionales.
"""


@pytest.mark.spec("002-FR-003")
def test_a_quoted_article_supersedes_the_original_and_everything_below_it() -> None:
    result = parse("Artículo 14.- Previo\nTexto previo.\n" + ARTICLE_REPLACED)

    original = by_path(result, "articulo:15")[0]
    replacement = current(result, "articulo:15")
    assert original.status is RevisionStatus.SUPERSEDED
    assert replacement.revision == 2
    assert replacement.text == "Son autoridades competentes en materia de transporte:"
    first_literal = by_path(result, "articulo:15/literal:a")
    assert [(p.revision, p.status) for p in first_literal] == [
        (1, RevisionStatus.SUPERSEDED),
        (2, RevisionStatus.CURRENT),
    ]


@pytest.mark.spec("002-FR-003")
def test_the_legal_source_of_each_revision_comes_from_the_notes() -> None:
    result = parse("Artículo 14.- Previo\nTexto previo.\n" + ARTICLE_REPLACED)

    replacement = current(result, "articulo:15")
    assert replacement.event is not None
    assert replacement.event.kind is EventKind.SUBSTITUTED
    assert "Ley Nº 28172" in replacement.event.source
    assert str(replacement.event.published_on) == "2004-02-17"
    incorporated = current(result, "articulo:15/literal:c")
    assert incorporated.event is not None
    assert incorporated.event.kind is EventKind.INCORPORATED
    assert "Decreto Legislativo Nº 1451" in incorporated.event.source


def test_a_single_line_quoted_literal_closes_and_text_after_it_is_not_swallowed() -> None:
    result = parse("Artículo 14.- Previo\nTexto previo.\n" + ARTICLE_REPLACED)

    assert current(result, "articulo:15/literal:c").text == "El Ministerio de la Producción."
    assert (
        current(result, "articulo:16").text
        == "Corresponde al Ministerio dictar los reglamentos nacionales."
    )


@pytest.mark.spec("002-FR-003")
def test_at_most_one_current_revision_per_path() -> None:
    result = parse("Artículo 14.- Previo\nTexto previo.\n" + ARTICLE_REPLACED)

    paths = [p.path for p in result.provisions if p.status is RevisionStatus.CURRENT]
    assert len(paths) == len(set(paths))


def test_a_quoted_article_with_a_letter_suffix_is_an_incorporation() -> None:
    text = """
Artículo 4.- De la libre competencia
Texto del artículo cuarto.
“Artículo 4-A. Impedimentos e incompatibilidades
4-A.1 Se encuentran impedidas para obtener título habilitante:
a) Las personas sancionadas con cancelación.
b) Los socios de personas sancionadas.”(*)
(*) Artículo incorporado por la Cuarta Disposición Complementaria Modificatoria del Decreto de
Urgencia Nº 019-2020, publicado el 24 enero 2020.
Artículo 5.- De la promoción de la inversión privada
Texto del artículo quinto.
"""
    result = parse(text)

    assert [p.revision for p in by_path(result, "articulo:4-A")] == [1]
    assert (
        current(result, "articulo:4-A/numeral:4-A.1/literal:b").text
        == "Los socios de personas sancionadas."
    )
    assert current(result, "articulo:4-A").event is not None
    assert current(result, "articulo:5").text == "Texto del artículo quinto."


PARTIAL = """
Artículo 7.- De la racionalización del uso de la infraestructura
7.1 El Estado promueve la utilización de técnicas modernas.
7.2 Con el fin de inducir racionalidad, se determinan cobros.
7.3 Los medios de transporte eficientes reciben trato preferencial del Estado.
(*) Numeral modificado por la Primera Disposición Modificatoria de la Ley Nº 30936,
publicada el 24 abril 2019, cuyo texto es el siguiente:
"7.3 Los medios de transporte que muestren mayor eficiencia son materia de trato preferencial
(bicicleta)”.
7.4 El Estado procure que las actividades contemplen espacio suficiente.
"""


def test_a_quoted_numeral_replaces_only_that_numeral() -> None:
    result = parse(PARTIAL)

    assert [(p.revision, p.status.value) for p in by_path(result, "articulo:7/numeral:7.3")] == [
        (1, "superseded"),
        (2, "current"),
    ]
    assert current(result, "articulo:7/numeral:7.3").text.endswith("(bicicleta).")
    assert current(result, "articulo:7/numeral:7.2").revision == 1
    assert current(result, "articulo:7/numeral:7.4").text.startswith("El Estado procure")


@pytest.mark.spec("002-FR-003")
def test_a_replaced_paragraph_is_flagged_and_never_applied_by_guessing() -> None:
    text = """
Artículo 23.- Del contenido de los reglamentos
Los reglamentos nacionales necesarios para la implementación de la presente ley incluyen lo siguiente.
(*) Párrafo modificado por el Decreto Legislativo Nº 1406, cuyo texto es el siguiente:
"Los reglamentos nacionales necesarios para la implementación de la presente Ley son los siguientes."
a) Reglamento de Licencias.
"""
    result = parse(text)

    [anomaly] = [a for a in result.anomalies if a.code == "paragraph_replacement_unapplied"]
    assert anomaly.path == "articulo:23"
    assert [(p.revision, p.status.value) for p in by_path(result, "articulo:23")] == [
        (1, "current")
    ]
    assert (
        "necesarios para la implementación de la presente ley incluyen"
        in current(result, "articulo:23").text
    )
    assert any("son los siguientes" in n.text for n in result.notes)
    assert current(result, "articulo:23/literal:a").text == "Reglamento de Licencias."


def test_concordances_and_notes_are_kept_as_editorial_notes_not_text() -> None:
    text = """
Artículo 3.- Del objetivo
La acción estatal se orienta a la satisfacción de las necesidades de los usuarios.
CONCORDANCIAS: D.S. Nº 035-2006-MTC
R.D. Nº 4000-2007-MTC-15
Artículo 4.- Rol del Estado
El rol estatal proviene de las definiciones nacionales.
"""
    result = parse(text)

    assert "035-2006" not in current(result, "articulo:3").text
    [note] = [n for n in result.notes if n.kind.value == "concordance"]
    assert "D.S. Nº 035-2006-MTC" in note.text
    assert note.path == "articulo:3"


def test_dispositions_get_their_own_section_paths() -> None:
    text = """
Artículo 36.- Transporte Ferroviario
Se rige por su ley especial.
DISPOSICIONES COMPLEMENTARIAS
Primera.- De la Comisión Consultiva
El Ministerio cuenta con una Comisión Consultiva.
a) Primer integrante;
b) Segundo integrante.
DISPOSICIONES FINALES
Primera.- De los reglamentos
El Poder Ejecutivo aprobará los reglamentos.
"""
    result = parse(text)

    assert (
        current(result, "disposiciones:complementarias/primera").title
        == "De la Comisión Consultiva"
    )
    assert (
        current(result, "disposiciones:complementarias/primera/literal:b").text
        == "Segundo integrante."
    )
    assert (
        current(result, "disposiciones:finales/primera").text
        == "El Poder Ejecutivo aprobará los reglamentos."
    )


def test_text_before_the_start_marker_is_preamble_not_provisions() -> None:
    text = """
DECRETO SUPREMO Nº 017-2009-MTC
Artículo 1.- Aprobación del Reglamento
Apruébese el Reglamento.
REGLAMENTO NACIONAL DE ADMINISTRACIÓN DE TRANSPORTE
SECCIÓN PRIMERA
DISPOSICIONES GENERALES
Artículo 1 Objeto
El presente Reglamento tiene por objeto regular el servicio de transporte terrestre.
"""
    result = parse(text, "renat")

    assert [p.path for p in result.provisions if p.kind is ParsedKind.ARTICLE] == ["articulo:1"]
    assert current(result, "articulo:1").title == "Objeto"
    assert any(n.kind.value == "preamble" and "Aprobación" in n.text for n in result.notes)


def test_page_footnotes_are_notes_and_do_not_leak_into_the_text() -> None:
    source = [
        SourceLine(7, "TÍTULO PRELIMINAR"),
        SourceLine(7, "Artículo I.- Ámbito"),
        SourceLine(7, "Texto del ámbito."),
        SourceLine(7, "Artículo 39.- Plazo máximo del procedimiento"),
        SourceLine(7, "El plazo no puede exceder de treinta (30) días hábiles, salvo que"),
        SourceLine(7, "30 Artículo incorporado por el Decreto Legislativo Nº 1272.", small=True),
        SourceLine(8, "por ley se establezcan procedimientos de mayor duración."),
        SourceLine(8, "Artículo 40.- Siguiente"),
        SourceLine(8, "Texto siguiente."),
    ]
    result = build_parser("tuo-lpag").parse(source)

    assert current(result, "articulo:39").text == (
        "El plazo no puede exceder de treinta (30) días hábiles, salvo que "
        "por ley se establezcan procedimientos de mayor duración."
    )
    assert current(result, "articulo:39").page_end == 8
    [note] = [n for n in result.notes if n.kind.value == "footnote"]
    assert "Decreto Legislativo Nº 1272" in note.text


def test_footnote_call_numbers_are_not_part_of_a_heading_title() -> None:
    source = [
        SourceLine(9, "TÍTULO PRELIMINAR"),
        SourceLine(9, "Artículo I.- Ámbito"),
        SourceLine(9, "Texto del ámbito."),
        SourceLine(9, "TÍTULO IV"),
        SourceLine(
            9,
            "Del procedimiento sancionador (Denominación modificada por el artículo 3 del "
            "Decreto Legislativo N° 1272)115",
        ),
        SourceLine(9, "CAPÍTULO II"),
        SourceLine(9, "Procedimiento (Capítulo incorporado por el Decreto Legislativo N° 1272)117"),
        SourceLine(9, "Artículo 229.- Ámbito"),
        SourceLine(9, "Texto del ámbito."),
    ]
    result = build_parser("tuo-lpag").parse(source)

    assert current(result, "titulo:IV").title == (
        "Del procedimiento sancionador (Denominación modificada por el artículo 3 del "
        "Decreto Legislativo N° 1272)"
    )
    assert current(result, "titulo:IV/capitulo:II").title == (
        "Procedimiento (Capítulo incorporado por el Decreto Legislativo N° 1272)"
    )


def test_a_title_that_ends_in_a_number_without_a_parenthesis_is_left_alone() -> None:
    source = [
        SourceLine(1, "TÍTULO PRELIMINAR"),
        SourceLine(1, "Artículo I.- Ámbito"),
        SourceLine(1, "Texto del ámbito."),
        SourceLine(1, "TÍTULO I"),
        SourceLine(1, "Régimen del Decreto Legislativo N° 1272"),
        SourceLine(1, "Artículo 1.- Objeto"),
        SourceLine(1, "Texto."),
    ]
    result = build_parser("tuo-lpag").parse(source)

    assert current(result, "titulo:I").title == "Régimen del Decreto Legislativo N° 1272"


def test_list_items_are_numerals_and_roman_preliminary_articles_are_recognized() -> None:
    text = """
TÍTULO PRELIMINAR
Del régimen jurídico
Artículo I.- Ámbito de aplicación de la ley
1. La presente Ley será de aplicación para todas las entidades.
2. Los procedimientos especiales no podrán imponer condiciones menos favorables.
Artículo II.- Contenido de la Ley
La presente Ley contiene normas comunes.
"""
    result = parse(text, "tuo-lpag")

    assert [p.path for p in result.provisions if p.kind is ParsedKind.ARTICLE] == [
        "articulo:I",
        "articulo:II",
    ]
    assert current(result, "articulo:I/numeral:2").text.startswith("Los procedimientos especiales")
    assert current(result, "titulo:PRELIMINAR").title == "Del régimen jurídico"


ANNEX_WITH_NOTES = """
Artículo 138.- Vigencia
El presente Reglamento entra en vigencia al día siguiente de su publicación.
ANEXO 1
TABLA DE INCUMPLIMIENTO
(*) C.4c El incumplimiento de las condiciones de acceso
Leve Suspensión de la autorización
“C.4b Texto de una fila modificada”
a) Primera condición
ANEXO 2
TABLA DE INFRACCIONES Y SANCIONES
F.1 Prestar el servicio sin autorización
Muy grave Multa de 1 UIT
"""


@pytest.mark.spec("002-FR-001")
def test_an_annex_keeps_all_of_its_table_text_instead_of_turning_it_into_notes() -> None:
    result = parse(ANNEX_WITH_NOTES, "ley-lgttt")

    annex_1, annex_2 = current(result, "anexo:1"), current(result, "anexo:2")
    assert annex_1.title == "TABLA DE INCUMPLIMIENTO"
    assert "TABLA DE INCUMPLIMIENTO" not in annex_1.text
    assert "C.4c El incumplimiento" in annex_1.text
    assert "Texto de una fila modificada" in annex_1.text
    assert "Primera condición" in annex_1.text
    assert "Muy grave Multa de 1 UIT" in annex_2.text
    assert "Muy grave" not in annex_1.text
    assert not [
        p for p in result.provisions if p.path.startswith("anexo:1/")
    ]  # no literals in tables
    assert result.notes == ()


def test_annexes_are_flagged_because_a_table_loses_its_structure_and_keep_no_boxes() -> None:
    boxed = [
        SourceLine(p, t, TextBox(p, 10, 10, 100, 20))
        for p, t in [
            (1, "Artículo 1.- Objeto"),
            (1, "Texto del artículo."),
            (2, "ANEXO 1"),
            (2, "TABLA"),
            (3, "Fila de la tabla"),
        ]
    ]
    result = build_parser("ley-lgttt").parse(boxed)

    assert [a.code for a in result.anomalies] == ["annex_table_unstructured"]
    annex = current(result, "anexo:1")
    assert (annex.page_start, annex.page_end) == (2, 3)
    assert len(annex.boxes) == 1  # only the heading: a highlighted table would be the whole page


def test_disposiciones_generales_is_a_section_title_not_a_group_of_dispositions() -> None:
    text = """
SECCIÓN PRIMERA
DISPOSICIONES GENERALES
TÍTULO PRELIMINAR
Artículo 1 Objeto
El presente Reglamento regula el servicio.
SECCIÓN SEXTA
DISPOSICIONES COMPLEMENTARIAS FINALES
Primera.- De la vigencia
Entra en vigencia mañana.
"""
    result = parse(text, "ley-lgttt")

    assert current(result, "seccion:primera").title == "DISPOSICIONES GENERALES"
    assert not [p for p in result.provisions if "generales" in p.path]
    assert (
        current(result, "seccion:sexta/disposiciones:complementarias-finales/primera").title
        == "De la vigencia"
    )
