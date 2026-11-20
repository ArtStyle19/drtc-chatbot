"""PDF text extraction with pypdfium2 (ADR-0012): reading-order lines with boxes and type size.

Page footnotes are set in a smaller type than the body. The extractor flags them (``small``) so a
parser never has to guess from the text. Mixed-case lines are classified from their lowercase
letters; all-caps lines (e.g. an old title quoted in a footnote) are calibrated against the capital
letters of the lines already classified.
"""

import statistics
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium

from drtc_chatbot.contexts.ingestion.domain.parsing.model import SourceLine, TextBox

_SMALL_RATIO = 0.88  # a line set in < 88 % of the body height is a footnote line
_MIN_LOWER = 3  # lowercase letters needed to measure a line by them
_SAMPLE = 60  # characters measured per line


@dataclass(frozen=True, slots=True)
class _RawLine:
    page: int
    text: str
    box: TextBox | None
    lower: float | None  # median height of the lowercase letters
    upper: float | None  # median height of the capital letters


class PdfiumTextExtractor:
    """Implements the PdfTextExtractor port."""

    def extract(self, pdf_path: Path, pages: Sequence[int]) -> list[SourceLine]:
        """Lines of the given 1-based physical pages, in reading order."""
        document = pdfium.PdfDocument(str(pdf_path))
        try:
            raw: list[_RawLine] = []
            for number in pages:
                raw.extend(self._page_lines(document[number - 1], number))
        finally:
            document.close()
        small = self._classify(raw)
        return [
            SourceLine(r.page, r.text, r.box, small=flag)
            for r, flag in zip(raw, small, strict=True)
        ]

    @staticmethod
    def _classify(raw: Sequence[_RawLine]) -> list[bool]:
        mixed = [r for r in raw if r.lower is not None]
        if not mixed:
            return [False] * len(raw)
        body = Counter(round(r.lower, 1) for r in mixed if r.lower is not None).most_common(1)[0][0]
        flags = {id(r): r.lower is not None and r.lower < body * _SMALL_RATIO for r in mixed}
        caps_body = [r.upper for r in mixed if r.upper is not None and not flags[id(r)]]
        caps_small = [r.upper for r in mixed if r.upper is not None and flags[id(r)]]
        midpoint = (
            (statistics.median(caps_body) + statistics.median(caps_small)) / 2
            if caps_body and caps_small
            else None
        )
        result = []
        for r in raw:
            if id(r) in flags:
                result.append(flags[id(r)])
            else:  # no lowercase letters: compare its capitals with the calibrated midpoint
                result.append(midpoint is not None and r.upper is not None and r.upper < midpoint)
        return result

    @staticmethod
    def _page_lines(page: pdfium.PdfPage, number: int) -> list[_RawLine]:
        textpage = page.get_textpage()
        text = textpage.get_text_range()
        rows: list[_RawLine] = []
        cursor = 0
        for line in text.replace("\r\n", "\n").split("\n"):
            if not line.strip():
                continue
            start = text.find(line, cursor)
            if start < 0:
                rows.append(_RawLine(number, line, None, None, None))
                continue
            cursor = start
            boxes = {
                i: textpage.get_charbox(i)
                for i in range(start, start + len(line))
                if text[i].strip()
            }
            if not boxes:
                continue
            lower = [b[3] - b[1] for i, b in boxes.items() if text[i].islower()][:_SAMPLE]
            upper = [b[3] - b[1] for i, b in boxes.items() if text[i].isupper()][:_SAMPLE]
            box = TextBox(
                number,
                min(b[0] for b in boxes.values()),
                min(b[1] for b in boxes.values()),
                max(b[2] for b in boxes.values()),
                max(b[3] for b in boxes.values()),
            )
            rows.append(
                _RawLine(
                    number,
                    line,
                    box,
                    statistics.median(lower) if len(lower) >= _MIN_LOWER else None,
                    statistics.median(upper) if upper else None,
                )
            )
        return rows
