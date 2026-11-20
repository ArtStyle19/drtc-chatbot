"""The parsers on the three real PDFs: structure, invariants and the golden set (SC-005)."""

import json
import re
from collections import Counter

import pytest

from drtc_chatbot.contexts.ingestion.domain.parsing.model import (
    ParsedKind,
    ParseResult,
    RevisionStatus,
)
from drtc_chatbot.contexts.ingestion.domain.parsing.profiles import build_parser
from drtc_chatbot.contexts.ingestion.infrastructure.pdfium_extractor import PdfiumTextExtractor
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_reader import (
    YamlManifestReader,
    ingestion_targets,
)
from tests.conftest import CORPUS_MANIFEST, REPO_ROOT

LEY = "ley-27181@2020-05"
RENAT = "ds-017-2009-mtc@2017-01-04"
TUO = "tuo-ley-27444@ds-004-2019-jus-ed2021"


@pytest.fixture(scope="module")
def parsed() -> dict[str, ParseResult]:
    results = {}
    for target in ingestion_targets(YamlManifestReader(CORPUS_MANIFEST).read()):
        pages = [p for first, last in target.normative_pages for p in range(first, last + 1)]
        lines = PdfiumTextExtractor().extract(target.source_file, pages)
        assert target.parser is not None
        results[target.version_id] = build_parser(target.parser).parse(lines)
    return results


def numeric_articles(result: ParseResult) -> list[int]:
    return sorted(
        int(p.label.split("-")[0])
        for p in result.current()
        if p.kind is ParsedKind.ARTICLE and p.label[0].isdigit()
    )


@pytest.mark.spec("002-FR-001")
@pytest.mark.parametrize(
    ("version", "total", "lettered"),
    [(LEY, 36, 4), (RENAT, 138, 1), (TUO, 265, 0)],
    ids=["ley-27181", "renat", "tuo-27444"],
)
def test_every_official_article_is_found_without_gaps(
    parsed: dict[str, ParseResult], version: str, total: int, lettered: int
) -> None:
    numbers = numeric_articles(parsed[version])

    assert sorted(set(numbers)) == list(range(1, total + 1))
    assert len(numbers) == total + lettered  # e.g. Ley 27181 also has 4-A, 9-A, 16-A and 26-A


@pytest.mark.spec("002-FR-003")
def test_no_provision_ever_has_two_current_texts(parsed: dict[str, ParseResult]) -> None:
    for version, result in parsed.items():
        current = Counter(p.path for p in result.provisions if p.status is RevisionStatus.CURRENT)
        assert [path for path, n in current.items() if n > 1] == [], version


@pytest.mark.spec("002-FR-003")
def test_replaced_articles_of_the_ley_keep_their_history(parsed: dict[str, ParseResult]) -> None:
    by_path: dict[str, list[tuple[int, str]]] = {}
    for p in parsed[LEY].provisions:
        if p.kind is ParsedKind.ARTICLE:
            by_path.setdefault(p.path, []).append((p.revision, p.status.value))

    assert by_path["articulo:2"] == [(1, "superseded"), (2, "current")]  # DU 019-2020
    assert [s for _, s in by_path["articulo:26"]] == ["superseded"] * 3 + ["current"]


def test_the_ley_flags_unapplied_paragraph_replacements_instead_of_guessing(
    parsed: dict[str, ParseResult],
) -> None:
    codes = Counter(a.code for a in parsed[LEY].anomalies)

    assert codes == {"paragraph_replacement_unapplied": 5}


@pytest.mark.spec("002-FR-006")
def test_the_tuo_manual_and_the_approving_decree_produce_no_provisions(
    parsed: dict[str, ParseResult],
) -> None:
    [target] = [
        t
        for t in ingestion_targets(YamlManifestReader(CORPUS_MANIFEST).read())
        if t.version_id == TUO
    ]
    pages = [p.page_start for p in parsed[TUO].provisions]

    assert target.normative_pages == ((71, 284),)  # the Manual (pp. 23-68) is not ingested at all
    assert min(pages) >= 78  # pp. 71-77 are the decree approving the TUO (kept as a preamble note)
    assert any(n.kind.value == "preamble" and n.page == 71 for n in parsed[TUO].notes)


def test_every_page_range_of_a_provision_is_inside_the_document(
    parsed: dict[str, ParseResult],
) -> None:
    limits = {LEY: 36, RENAT: 181, TUO: 284}
    for version, result in parsed.items():
        assert all(1 <= p.page_start <= p.page_end <= limits[version] for p in result.provisions)


def test_provisions_carry_the_boxes_needed_to_highlight_them_later(
    parsed: dict[str, ParseResult],
) -> None:
    article = next(p for p in parsed[LEY].current() if p.path == "articulo:1")

    assert article.boxes
    assert all(b.x0 < b.x1 and b.y0 < b.y1 for b in article.boxes)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@pytest.mark.spec("002-SC-005")
def test_every_golden_question_is_findable_in_the_parsed_provisions(
    parsed: dict[str, ParseResult],
) -> None:
    dataset = REPO_ROOT / "evaluation" / "datasets" / "golden-v1.jsonl"
    questions = [
        json.loads(line)
        for line in dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    missing = []
    for question in questions:
        for citation in question["expected"]["citations"]:
            result = parsed[citation["version_id"]]
            wanted = _normalize(citation["supporting_text"])
            pages = set(citation["pdf_pages"])
            in_provisions = any(
                wanted in _normalize(p.text) and pages & set(range(p.page_start, p.page_end + 1))
                for p in result.current()
            )
            in_notes = any(wanted in _normalize(n.text) and n.page in pages for n in result.notes)
            if not (in_provisions or in_notes):
                missing.append((question["id"], citation["provision"]))

    assert missing == []


@pytest.mark.spec("002-FR-003")
def test_cross_references_at_the_start_of_a_wrapped_line_never_replace_or_split_a_provision(
    parsed: dict[str, ParseResult],
) -> None:
    renat = {p.path: p for p in parsed[RENAT].current()}

    # RENAT art. 20.1 (technical conditions of buses) was "replaced" by the wrapped line
    # "20.1.1, 20.1.2, 20.1.3, 20.1.8 y 20.1.11, aplicándose…" and lost all its current texts.
    assert renat["articulo:20/numeral:20.1"].text.startswith("Son condiciones específicas mínimas")
    replaced = sorted(
        p.path
        for p in parsed[RENAT].provisions
        if p.status is RevisionStatus.SUPERSEDED and p.path.startswith("articulo:20/numeral:20.1/")
    )
    assert (
        replaced
        == [  # exactly the four numerals the PDF itself marks as modified (DS 010-2012-MTC)
            "articulo:20/numeral:20.1/numeral:20.1.10",
            "articulo:20/numeral:20.1/numeral:20.1.5",
            "articulo:20/numeral:20.1/numeral:20.1.6",
            "articulo:20/numeral:20.1/numeral:20.1.8",
        ]
    )
    # RENAT art. 108.2.1 lost "108.1.10, el transportista sustituye los neumáticos…" (read as a duplicate 108.1).
    assert "108.1.10, el transportista sustituye los neumáticos" in (
        renat["articulo:108/numeral:108.2/numeral:108.2.1"].text
    )
    for version, result in parsed.items():
        phantoms = [
            p.path
            for p in result.current()
            if p.kind is ParsedKind.NUMERAL and re.match(r"(?:y/o|y|o|e|u)\s+\d", p.text)
        ]
        assert phantoms == [], version


@pytest.mark.spec("002-FR-001")
def test_the_renat_annex_tables_keep_their_text_and_pages(parsed: dict[str, ParseResult]) -> None:
    annexes = {p.path: p for p in parsed[RENAT].current() if p.kind is ParsedKind.ANNEX}

    assert set(annexes) == {"anexo:1", "anexo:2"}
    assert (annexes["anexo:1"].page_start, annexes["anexo:1"].page_end) == (166, 170)
    assert (annexes["anexo:2"].page_start, annexes["anexo:2"].page_end) == (170, 181)
    assert len(annexes["anexo:2"].text) > 30_000  # the infractions and sanctions table
    assert "Prestar el servicio de transporte de personas" in annexes["anexo:2"].text
    assert annexes["anexo:2"].title == "TABLA DE INFRACCIONES Y SANCIONES"
    flagged = [a.path for a in parsed[RENAT].anomalies if a.code == "annex_table_unstructured"]
    assert flagged == ["anexo:1", "anexo:2"]


def test_a_section_title_is_not_mistaken_for_a_group_of_dispositions(
    parsed: dict[str, ParseResult],
) -> None:
    paths = {p.path for p in parsed[RENAT].provisions}
    groups = {
        p.split("/")[-2] for p in paths if "/disposiciones:" in p or p.startswith("disposiciones:")
    }

    assert "seccion:primera" in paths
    assert not any("disposiciones:generales" in p for p in paths)
    assert groups  # the real groups are still there (complementarias-finales, …)
