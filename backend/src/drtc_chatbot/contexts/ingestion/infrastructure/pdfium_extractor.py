"""PDF text extraction with pypdfium2 (ADR-0012): reading-order lines with boxes and type size."""

import statistics
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import pypdfium2 as pdfium

from drtc_chatbot.contexts.ingestion.domain.parsing.model import SourceLine, TextBox

_SMALL_RATIO = 0.88  # a line set in < 88 % of the body character height is a footnote line


class PdfiumTextExtractor:
    """Implements the PdfTextExtractor port."""

    def extract(self, pdf_path: Path, pages: Sequence[int]) -> list[SourceLine]:
        """Lines of the given 1-based physical pages, in reading order."""
        document = pdfium.PdfDocument(str(pdf_path))
        try:
            raw: list[tuple[int, str, TextBox | None, float | None]] = []
            for number in pages:
                raw.extend(self._page_lines(document[number - 1], number))
        finally:
            document.close()
        heights = [round(h, 1) for _, _, _, h in raw if h is not None]
        body = Counter(heights).most_common(1)[0][0] if heights else 0.0
        return [
            SourceLine(page, text, box, small=height is not None and height < body * _SMALL_RATIO)
            for page, text, box, height in raw
        ]

    @staticmethod
    def _page_lines(
        page: pdfium.PdfPage, number: int
    ) -> list[tuple[int, str, TextBox | None, float | None]]:
        textpage = page.get_textpage()
        text = textpage.get_text_range()
        rows: list[tuple[int, str, TextBox | None, float | None]] = []
        cursor = 0
        for line in text.replace("\r\n", "\n").split("\n"):
            if not line.strip():
                continue
            start = text.find(line, cursor)
            if start < 0:
                rows.append((number, line, None, None))
                continue
            cursor = start
            boxes = [
                textpage.get_charbox(i) for i in range(start, start + len(line)) if text[i].strip()
            ]
            if not boxes:
                continue
            heights = [
                textpage.get_charbox(i)[3] - textpage.get_charbox(i)[1]
                for i in range(start, start + len(line))
                if text[i].isalpha()
            ][:60] or [top - bottom for _, bottom, _, top in boxes[:60]]
            box = TextBox(
                number,
                min(b[0] for b in boxes),
                min(b[1] for b in boxes),
                max(b[2] for b in boxes),
                max(b[3] for b in boxes),
            )
            rows.append((number, line, box, statistics.median(heights)))
        return rows
