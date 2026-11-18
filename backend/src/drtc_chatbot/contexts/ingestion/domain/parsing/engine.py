"""Generic parser for Peruvian legal texts organised in articles, numerals and literals.

The parser is a single pass over lines. Structure decides what is current:

* an unquoted ``Artículo N`` heading opens the original text of an article;
* a quoted block (``“Artículo N ...”``, ``“5.2 ...”``, ``"g) ..."``) is a substitution or an
  incorporation by a later norm: it supersedes the current text of that unit (and of everything
  below it) or adds a new unit;
* ``(*)`` notes only explain *why* (which norm, when): they never decide supersession.

Anything it cannot interpret with confidence becomes an :class:`Anomaly` for the reviewer; text is
never silently dropped and replacements are never guessed.
"""

import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from drtc_chatbot.contexts.ingestion.domain.parsing.model import (
    Anomaly,
    NoteKind,
    ParsedEvent,
    ParsedKind,
    ParsedNote,
    ParsedProvision,
    ParseResult,
    RevisionStatus,
    SourceLine,
    TextBox,
)
from drtc_chatbot.contexts.ingestion.domain.parsing.notes import (
    MARKER,
    NOTE_START,
    is_forward,
    is_paragraph_note,
    parse_event,
)

_OPEN_QUOTES = '“"'
_CLOSE_QUOTES = '”"'
_WS = re.compile(r"\s+")
_ARTICLE = re.compile(
    r"^(?P<q>[“\"])?\s*Art[íi]culo\s+(?P<label>\d+(?:\s*-\s*[A-Z])?|[IVX]+)\s*[°º]?"
    r"(?P<punct>\s*[.\-–]+)?\s*(?P<title>.*)$"
)
_STRUCT = re.compile(
    r"^(?P<kind>T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N|SUBCAP[ÍI]TULO)\s+"
    r"(?P<label>PRELIMINAR|[IVXLCl]+|[ÚU]NIC[OA]|PRIMER[OA]|SEGUND[OA]|TERCER[OA]|CUART[OA]|QUINT[OA]|"
    r"SEXT[OA]|S[ÉE]PTIM[OA]|OCTAV[OA]|NOVEN[OA]|D[ÉE]CIM[OA]|\d+)\s*$",
    re.IGNORECASE,
)
_DISPOSITION_SECTION = re.compile(r"^DISPOSICIONES\s+(?P<which>[A-ZÁÉÍÓÚÑ ]+)$")
_DISPOSITION = re.compile(
    r"^(?P<q>[“\"])?\s*(?P<ord>(?:D[ée]cim[oa]\s+)?(?:Primer[oa]?|Segunda|Tercera|Cuarta|Quinta|Sexta|"
    r"S[ée]ptima|Octava|Novena|D[ée]cim[oa]|[ÚU]nica))\s*[.\-–]+\s*(?P<title>.*)$"
)
_ANNEX = re.compile(r"^ANEXO\s+(?P<label>\d+|[IVX]+|[ÚU]NICO)\b\s*(?P<title>.*)$")
_ITEM = re.compile(r"^(?P<n>\d{1,2})\.\s+(?P<rest>\S.*)$")
_LITERAL = re.compile(r"^(?P<label>[a-zñ])\)\s+(?P<rest>.*)$")
_CONCORDANCE = re.compile(r"^(?:OTRAS\s+)?CONCORDANCIAS?\s*:?\s*(?P<rest>.*)$")
_EPILOGUE = re.compile(
    r"^(POR\s+TANTO|Mando\s+se\s+publique|Comun[íi]quese|Dado\s+en\s+la\s+Casa)\b"
)
_TRAILING_MARKERS = re.compile(r"(?:\s*\(\*+\))+\s*$")
_TITLE_TAIL = re.compile(
    r"(?:,|\b(?:de|del|la|las|los|el|y|e|o|en|a|al|para|por|con|que|sobre))\s*$", re.I
)
_MAX_QUOTE_LINES = 400


def _slug(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")


def normalize_line(text: str) -> str:
    return _WS.sub(" ", text.replace("\xa0", " ")).strip()


def _roman(label: str) -> str:
    return label.replace("l", "I") if set(label) <= set("IVXLCl") else label


@dataclass(slots=True)
class _Draft:
    kind: ParsedKind
    label: str
    title: str | None
    path: str
    parent_path: str | None
    quoted: bool
    lines: list[str] = field(default_factory=list)
    page_start: int = 0
    page_end: int = 0
    boxes: list[TextBox] = field(default_factory=list)

    def add(self, line: SourceLine, text: str) -> None:
        if text:
            self.lines.append(text)
        self.page_end = max(self.page_end, line.page)
        if line.box is not None:
            self.boxes.append(line.box)


@dataclass(slots=True)
class _Rev:
    path: str
    kind: ParsedKind
    label: str
    title: str | None
    parent_path: str | None
    text: str
    revision: int
    status: RevisionStatus
    page_start: int
    page_end: int
    ordinal: int
    boxes: tuple[TextBox, ...]
    event: ParsedEvent | None = None


@dataclass(frozen=True, slots=True)
class ParserOptions:
    """Per-norm tuning of the generic parser."""

    is_noise: Callable[[str], bool] | None = None
    start_marker: re.Pattern[str] | None = (
        None  # lines before it are preamble (e.g. an approving decree)
    )
    roman_articles: bool = False  # 'Artículo I.' ... 'Artículo IX.' (preliminary title)
    footnotes: bool = False  # numbered page footnotes and inline '(Texto según ...)' notes


_ROMAN = re.compile(r"^[IVX]+$")
_ROMAN_VALUES = {"I": 1, "V": 5, "X": 10}
_INLINE_NOTE_START = re.compile(
    r"^\((?:Texto|Art[íi]culo|Numeral|Literal|P[áa]rrafo|Inciso|Disposici[óo]n)\b"
)
_INLINE_NOTE_END = re.compile(r"\)\s*(?:\d{1,3}\s*)*$")
_REF_DIGITS = re.compile(r"(?<=\))\s*(?:\d{1,3}\s*)+$")


def _roman_value(label: str) -> int:
    total = 0
    for current, nxt in zip(label, label[1:] + " ", strict=True):
        value = _ROMAN_VALUES[current]
        total += -value if nxt != " " and _ROMAN_VALUES.get(nxt, 0) > value else value
    return total


class ArticleDocumentParser:
    """Parses one normative document. Create a new instance per document."""

    def __init__(self, options: ParserOptions | None = None) -> None:
        self._opts = options or ParserOptions()
        self._is_noise = self._opts.is_noise or (lambda _text: False)
        self._max_roman = 0
        self._marker_seen = False
        self._all: list[SourceLine] = []
        self._index = 0
        self._revs: list[_Rev] = []
        self._by_path: dict[str, list[_Rev]] = {}
        self._notes: list[ParsedNote] = []
        self._anomalies: list[Anomaly] = []
        self._containers: list[tuple[int, str]] = []  # (rank, path)
        self._in_dispositions = False
        self._dispo_section_path: str | None = None
        self._max_article = 0
        self._art_label: str | None = None
        self._art_path: str | None = None
        self._unit_path: str | None = None  # article, disposition or annex being parsed
        self._numerals: list[tuple[str, str, bool]] = []  # (label, path, is_item), shallow to deep
        self._last_literal: dict[str, str] = {}
        self._last_item: dict[str, int] = {}
        self._cur: _Draft | None = None
        self._depth = 0
        self._quote_lines = 0
        self._inner: list[str] | None = None
        self._pending_event: ParsedEvent | None = None
        self._pending_paragraph = False
        self._last_quoted: _Rev | None = None
        self._mode: str | None = None  # None | "note" | "concordance" | "epilogue"
        self._buffer: list[str] = []
        self._buffer_page = 0
        self._started = False
        self._preamble: list[str] = []
        self._preamble_page = 0
        self._ordinal = 0
        self._pending_title: str | None = None
        self._title_lines = 0
        self._block_root: _Rev | None = None
        self._tail: _Rev | None = None  # last emitted non-container revision
        self._in_continuation = False

    # ------------------------------------------------------------------ public API
    def parse(self, source: Sequence[SourceLine]) -> ParseResult:
        lines = [
            SourceLine(item.page, normalize_line(item.text), item.box, item.small)
            for item in source
            if item.text.strip()
        ]
        lines = [item for item in lines if item.text and not self._is_noise(item.text)]
        self._all = lines
        for index, item in enumerate(lines):
            self._index = index
            self._feed(item)
        self._finish()
        provisions = tuple(
            ParsedProvision(
                path=r.path, kind=r.kind, label=r.label, title=r.title, parent_path=r.parent_path,
                text=r.text, revision=r.revision, status=r.status, page_start=r.page_start,
                page_end=r.page_end, ordinal=r.ordinal, boxes=r.boxes, event=r.event,
            )
            for r in sorted(self._revs, key=lambda r: (r.ordinal))
        )  # fmt: skip
        metrics = {
            "provisions_current": sum(p.status is RevisionStatus.CURRENT for p in provisions),
            "provisions_superseded": sum(p.status is RevisionStatus.SUPERSEDED for p in provisions),
            "articles_current": sum(
                p.status is RevisionStatus.CURRENT and p.kind is ParsedKind.ARTICLE
                for p in provisions
            ),
            "notes": len(self._notes),
            "anomalies": len(self._anomalies),
        }
        return ParseResult(provisions, tuple(self._notes), tuple(self._anomalies), metrics)

    # ------------------------------------------------------------------ line dispatch
    def _feed(self, item: SourceLine) -> None:
        text = item.text
        if MARKER.fullmatch(text.replace(" ", "")):
            return  # lone (*) markers carry no text
        if self._mode == "epilogue":
            self._buffer.append(text)
            return
        if self._opts.footnotes and item.small:
            if self._mode == "footnote":
                self._buffer.append(text)
            else:
                if self._mode:
                    self._flush_buffer_note()
                self._mode, self._buffer, self._buffer_page = "footnote", [text], item.page
            return
        if self._mode == "footnote":
            self._flush_buffer_note()
        kind, match = self._classify(text)
        if self._mode == "inline":
            if kind == "text":
                self._buffer.append(text)
                if _INLINE_NOTE_END.search(text):
                    self._flush_buffer_note()
                return
            self._flush_buffer_note()
            kind, match = self._classify(text)
        elif self._mode in {"note", "concordance"}:
            forward_quote = (
                self._mode == "note"
                and kind == "text"
                and text[0] in _OPEN_QUOTES
                and is_forward(" ".join(self._buffer))
            )
            if kind == "text" and not forward_quote:
                self._buffer.append(text)
                return
            self._flush_buffer_note()
            kind, match = self._classify(text)
        if self._pending_title is not None:
            if kind == "text" and self._is_title_line(text) and self._title_lines < 3:
                self._title_lines += 1
                self._set_container_title(text)
                return
            self._pending_title = None
        if not self._started:
            marker = self._opts.start_marker
            if marker is not None and not self._marker_seen:
                if marker.search(text):
                    self._marker_seen = True
                self._preamble.append(text)
                self._preamble_page = self._preamble_page or item.page
                return
            if kind in {"struct", "article", "dispo_section", "annex"}:
                self._started = True
                self._flush_preamble()
            else:
                self._preamble.append(text)
                self._preamble_page = self._preamble_page or item.page
                return
        self._dispatch(kind, match, item)

    @staticmethod
    def _is_title_line(text: str) -> bool:
        """Container titles are short lines without a final period (often UPPERCASE)."""
        return len(text) < 160 and not text.endswith(".") and text[0] not in _OPEN_QUOTES

    def _set_container_title(self, text: str) -> None:
        for rev in reversed(self._revs):
            if rev.path == self._pending_title:
                rev.title = f"{rev.title} {text}".strip() if rev.title else text
                return

    def _dispatch(self, kind: str, match: re.Match[str] | None, item: SourceLine) -> None:
        text = item.text
        if kind == "epilogue":
            self._close_draft()
            self._mode = "epilogue"
            self._buffer = [text]
            self._buffer_page = item.page
        elif kind == "struct":
            self._close_draft()
            assert match is not None
            self._container(match, item)
        elif kind == "dispo_section":
            self._close_draft()
            assert match is not None
            self._disposition_section(match, item)
        elif kind == "annex":
            self._close_draft()
            assert match is not None
            self._annex(match, item)
        elif kind == "note":
            self._mode = "note"
            self._buffer = [NOTE_START.sub("", text) if text.startswith("(") else text]
            self._buffer_page = item.page
        elif kind == "inline_note":
            self._mode, self._buffer, self._buffer_page = "inline", [text], item.page
            if _INLINE_NOTE_END.search(text):
                self._flush_buffer_note()
        elif kind == "concordance":
            assert match is not None
            self._mode = "concordance"
            self._buffer = [match.group("rest")] if match.group("rest") else []
            self._buffer_page = item.page
        elif kind == "quote_unknown":
            self._paragraph_replacement(item)
        elif kind == "inner":
            self._inner_line(item)
        else:
            self._unit_or_text(kind, match, item)
        if self._depth > 0 and kind not in {
            "note",
            "concordance",
            "struct",
            "epilogue",
            "inner",
            "quote_unknown",
            "inline_note",
        }:
            self._after_quoted_line(item, opened=kind.startswith("q_"))

    def _classify(self, text: str) -> tuple[str, re.Match[str] | None]:
        if self._inner is not None:
            if NOTE_START.match(text):
                return "note", None
            return "inner", None
        if self._opts.footnotes:
            if _INLINE_NOTE_START.match(text):
                return "inline_note", None
        if NOTE_START.match(text):
            return "note", None
        if match := _CONCORDANCE.match(text):
            return "concordance", match
        if _EPILOGUE.match(text) and self._started:
            return "epilogue", None
        if match := _STRUCT.match(text):
            return "struct", match
        if match := _DISPOSITION_SECTION.match(text):
            return "dispo_section", match
        if match := _ANNEX.match(text):
            return "annex", match
        if text[0] in _OPEN_QUOTES and self._pending_paragraph:
            return "quote_unknown", None
        if text[0] in _OPEN_QUOTES:
            body = text[1:].lstrip()
            shape, shape_match = self._shape(body, quoted=True)
            if shape != "text":
                return "q_" + shape, shape_match
            if self._opens_marked_block():
                return "quote_unknown", None
            if self._pending_event is not None:
                return "quote_unknown", None
            return "text", None
        shape, shape_match = self._shape(text, quoted=False)
        return shape, shape_match

    def _opens_marked_block(self) -> bool:
        """Lookahead: a quote that closes within a few lines on a '(*)' marker is an inserted block."""
        for offset in range(60):
            at = self._index + offset
            if at >= len(self._all):
                return False
            text = self._all[at].text
            if offset and (_STRUCT.match(text) or _ARTICLE.match(text.lstrip('“" '))):
                return False
            if self._closes_block(text, drop_opener=offset == 0):
                return bool(MARKER.search(text[-12:]))
        return False

    def _shape(self, text: str, *, quoted: bool) -> tuple[str, re.Match[str] | None]:
        """Classify a line (quote stripped) as article / numeral / literal / disposition / text."""
        if match := _ARTICLE.match(text):
            if quoted or self._accept_article(match):
                return "article", match
        if self._art_label is not None:
            prefix = r"\d{1,2}" if _ROMAN.match(self._art_label) else re.escape(self._art_label)
            numeral = re.match(
                rf"^(?P<label>{prefix}(?:\.\d{{1,2}})+)(?:\.\s*|\s+|$)(?P<rest>.*)$",
                text,
            )
            if numeral:
                return "numeral", numeral
        if self._art_label is not None and (item := _ITEM.match(text)):
            if self._accept_item(int(item.group("n"))):
                return "item", item
        if match := _LITERAL.match(text):
            if quoted or self._accept_literal(match.group("label")):
                return "literal", match
        if self._in_dispositions and (match := _DISPOSITION.match(text)):
            return "disposition", match
        return "text", None

    def _accept_article(self, match: re.Match[str]) -> bool:
        label = match.group("label")
        if _ROMAN.match(label):
            return (
                self._opts.roman_articles
                and bool(match.group("punct"))
                and _roman_value(label) == self._max_roman + 1
            )
        number = int(re.match(r"\d+", label).group())  # type: ignore[union-attr]
        if match.group("punct"):
            return number > self._max_article
        title = match.group("title")
        return number == self._max_article + 1 and bool(title) and title[0].isupper()

    def _item_parent(self) -> str | None:
        for _, path, is_item in reversed(self._numerals):
            if not is_item:
                return path
        return self._unit_path

    def _accept_item(self, number: int) -> bool:
        if self._cur is None and not self._numerals:
            return False
        return number == self._last_item.get(self._item_parent() or "", 0) + 1

    def _accept_literal(self, letter: str) -> bool:
        if self._cur is None and not self._numerals and self._unit_path is None:
            return False
        if self._unit_path is not None and self._unit_path.startswith("anexo:"):
            return False  # annex tables repeat a) b) c) lists: kept as plain text
        parent = self._literal_parent()
        last = self._last_literal.get(parent)
        return letter == "a" or (last is not None and ord(letter) == ord(last) + 1)

    def _literal_parent(self) -> str:
        if self._numerals:
            return self._numerals[-1][1]
        return self._unit_path or ""

    # ------------------------------------------------------------------ units
    def _unit_or_text(self, kind: str, match: re.Match[str] | None, item: SourceLine) -> None:
        quoted_open = kind.startswith("q_")
        base = kind[2:] if quoted_open else kind
        if quoted_open and self._depth == 0:
            self._close_draft()
            self._depth, self._quote_lines, self._block_root = 1, 0, None
        if base == "text":
            self._append_text(item)
            return
        assert match is not None
        quoted = self._depth > 0
        self._close_draft()
        if base == "article":
            self._open_article(match, item, quoted=quoted)
        elif base == "numeral":
            self._open_numeral(match, item, quoted=quoted)
        elif base == "item":
            self._open_item(match, item, quoted=quoted)
        elif base == "literal":
            self._open_literal(match, item, quoted=quoted)
        else:
            self._open_disposition(match, item, quoted=quoted)

    def _append_text(self, item: SourceLine) -> None:
        text = _TRAILING_MARKERS.sub("", MARKER.sub("", item.text)).strip()
        if self._opts.footnotes:
            text = _REF_DIGITS.sub("", text)
        if self._depth > 0:
            text = self._strip_closing_quote(text, first=False)
        if self._cur is None:
            self._continue_tail(item, text)
            return
        if self._title_continues(self._cur):
            self._cur.title = f"{self._cur.title} {text}".strip()
            self._cur.add(item, "")
            return
        self._cur.add(item, text)

    def _continue_tail(self, item: SourceLine, text: str) -> None:
        """Text after a quoted block belongs to the unit it interrupts: keep it, flag it."""
        tail = self._tail
        if tail is None:
            self._anomaly("orphan_text", "Text outside any provision", item, text)
            return
        tail.text = f"{tail.text} {text}".strip()
        tail.page_end = max(tail.page_end, item.page)
        if not self._in_continuation:
            self._in_continuation = True
            self._anomaly(
                "continuation_after_quote",
                "Text continues after a quoted block and was appended to the preceding provision; "
                "check that it belongs there",
                item, text, path=tail.path,
            )  # fmt: skip

    @staticmethod
    def _title_continues(draft: _Draft) -> bool:
        if draft.lines or not draft.title or draft.kind.is_container:
            return False
        title = draft.title
        wraps = _TITLE_TAIL.search(title) or title.count("(") > title.count(")")
        return bool(wraps) and not title.endswith((".", ":", ";")) and len(draft.title) < 200

    def _new_draft(
        self, kind: ParsedKind, label: str, title: str | None, path: str, parent: str | None,
        item: SourceLine, *, quoted: bool, first_text: str = "",
    ) -> None:  # fmt: skip
        self._in_continuation = False
        draft = _Draft(
            kind, label, title, path, parent, quoted, page_start=item.page, page_end=item.page
        )
        if item.box is not None:
            draft.boxes.append(item.box)
        if first_text:
            draft.lines.append(first_text)
        self._cur = draft

    def _clean(self, text: str, *, first: bool) -> str:
        text = _TRAILING_MARKERS.sub("", MARKER.sub("", text)).strip()
        if self._depth > 0:
            text = self._strip_closing_quote(text, first=first)
        return text

    def _open_article(self, match: re.Match[str], item: SourceLine, *, quoted: bool) -> None:
        label = _WS.sub("", match.group("label"))
        if _ROMAN.match(label):
            self._max_roman = max(self._max_roman, _roman_value(label))
        else:
            number = int(re.match(r"\d+", label).group())  # type: ignore[union-attr]
            self._max_article = max(self._max_article, number)
        path = f"articulo:{label}"
        parent = self._containers[-1][1] if self._containers else None
        self._art_label, self._art_path, self._numerals = label, path, []
        self._unit_path = path
        title = self._clean(match.group("title"), first=quoted) or None
        self._new_draft(ParsedKind.ARTICLE, label, title, path, parent, item, quoted=quoted)

    def _open_numeral(self, match: re.Match[str], item: SourceLine, *, quoted: bool) -> None:
        label = match.group("label")
        while self._numerals and (
            self._numerals[-1][2] or not label.startswith(self._numerals[-1][0] + ".")
        ):
            self._numerals.pop()
        parent = self._numerals[-1][1] if self._numerals else self._unit_path
        path = f"{parent}/numeral:{label}"
        self._numerals.append((label, path, False))
        rest = self._clean(match.group("rest"), first=quoted)
        self._new_draft(
            ParsedKind.NUMERAL, label, None, path, parent, item, quoted=quoted, first_text=rest
        )

    def _open_item(self, match: re.Match[str], item: SourceLine, *, quoted: bool) -> None:
        """A list item '1.', '2.' inside an article or numeral: stored as a numeral."""
        while self._numerals and self._numerals[-1][2]:
            self._numerals.pop()
        parent = self._numerals[-1][1] if self._numerals else self._unit_path
        label = match.group("n")
        self._last_item[parent or ""] = int(label)
        path = f"{parent}/numeral:{label}"
        self._numerals.append((label, path, True))
        rest = self._clean(match.group("rest"), first=quoted)
        self._new_draft(
            ParsedKind.NUMERAL, label, None, path, parent, item, quoted=quoted, first_text=rest
        )

    def _open_literal(self, match: re.Match[str], item: SourceLine, *, quoted: bool) -> None:
        label = match.group("label")
        parent = self._literal_parent() or None
        self._last_literal[parent or ""] = label
        path = f"{parent}/literal:{label}" if parent else f"literal:{label}"
        rest = self._clean(match.group("rest"), first=quoted)
        self._new_draft(
            ParsedKind.LITERAL, label, None, path, parent, item, quoted=quoted, first_text=rest
        )

    def _open_disposition(self, match: re.Match[str], item: SourceLine, *, quoted: bool) -> None:
        ordinal = _slug(match.group("ord"))
        parent = self._dispo_section_path
        path = f"{parent}/{ordinal}" if parent else f"disposicion:{ordinal}"
        title = self._clean(match.group("title"), first=quoted) or None
        self._art_label = self._art_path = None
        self._unit_path = path
        self._numerals = []
        self._new_draft(ParsedKind.DISPOSITION, ordinal, title, path, parent, item, quoted=quoted)

    # ------------------------------------------------------------------ containers
    _RANKS = {"seccion": 0, "titulo": 1, "capitulo": 2, "subcapitulo": 3}

    def _container(self, match: re.Match[str], item: SourceLine) -> None:
        kind_word = _slug(match.group("kind"))
        label = (
            _roman(match.group("label").upper())
            if kind_word != "seccion"
            else _slug(match.group("label"))
        )
        rank = self._RANKS[kind_word]
        while self._containers and self._containers[-1][0] >= rank:
            self._containers.pop()
        parent = self._containers[-1][1] if self._containers else None
        path = f"{parent}/{kind_word}:{label}" if parent else f"{kind_word}:{label}"
        self._containers.append((rank, path))
        self._in_dispositions = False
        kind = {0: ParsedKind.SECTION, 1: ParsedKind.TITLE}.get(rank, ParsedKind.CHAPTER)
        self._emit(
            kind, label, None, path, parent, "", item.page, item.page, (), None, current=True
        )
        self._art_label = self._art_path = None
        self._unit_path = None
        self._numerals = []
        self._pending_title, self._title_lines = path, 0

    def _disposition_section(self, match: re.Match[str], item: SourceLine) -> None:
        slug = _slug(match.group("which"))
        while self._containers and self._containers[-1][0] >= 1:
            self._containers.pop()
        parent = self._containers[-1][1] if self._containers else None
        path = f"{parent}/disposiciones:{slug}" if parent else f"disposiciones:{slug}"
        self._containers.append((1, path))
        self._in_dispositions = True
        self._dispo_section_path = path
        self._emit(ParsedKind.SECTION, slug, match.group("which").title(), path, parent, "",
                   item.page, item.page, (), None, current=True)  # fmt: skip
        self._art_label = self._art_path = None
        self._unit_path = None
        self._numerals = []

    def _annex(self, match: re.Match[str], item: SourceLine) -> None:
        label = _slug(match.group("label"))
        path = f"anexo:{label}"
        self._art_label = self._art_path = None
        self._unit_path = None
        self._numerals = []
        title = match.group("title").strip() or None
        self._unit_path = path
        self._new_draft(ParsedKind.ANNEX, label, title, path, None, item, quoted=False)

    # ------------------------------------------------------------------ quotes
    def _after_quoted_line(self, item: SourceLine, *, opened: bool = False) -> None:
        self._quote_lines += 1
        if self._inner is None and self._closes_block(item.text, drop_opener=opened):
            self._depth = 0
            self._close_draft()
        elif self._quote_lines > _MAX_QUOTE_LINES:
            self._anomaly("runaway_quote", "Quoted block never closed", item, item.text)
            self._depth = 0
            self._close_draft()

    _CLOSER = re.compile(r"([”\"])[\s.,;]*$")

    def _closer_index(self, text: str, *, drop_opener: bool = False) -> int | None:
        """Index of the quote that closes a block at the end of the line, or None."""
        offset = 1 if drop_opener and text and text[0] in _OPEN_QUOTES else 0
        body = _TRAILING_MARKERS.sub("", text[offset:]).rstrip()
        match = self._CLOSER.search(body)
        if match is None:
            return None
        head = body[: match.end(1)]
        opens = head.count("“")
        closes = head.count("”") + head.count('"')
        return offset + match.start(1) if (closes - opens) % 2 == 1 else None

    def _closes_block(self, text: str, *, drop_opener: bool = False) -> bool:
        return self._closer_index(text, drop_opener=drop_opener) is not None

    def _strip_closing_quote(self, text: str, *, first: bool) -> str:
        text = text.strip()
        if first and text and text[0] in _OPEN_QUOTES:
            text = text[1:].lstrip()
        index = self._closer_index(text)
        if index is not None:
            text = (text[:index] + text[index + 1 :]).rstrip()
        return text

    def _paragraph_replacement(self, item: SourceLine) -> None:
        """A quoted paragraph without a label: kept as a note, flagged, never applied."""
        self._inner = [item.text[1:].lstrip()]
        if self._closes_block(item.text, drop_opener=True):
            self._finish_inner(item)

    def _inner_line(self, item: SourceLine) -> None:
        assert self._inner is not None
        self._inner.append(item.text)
        if self._closes_block(item.text):
            self._finish_inner(item)

    def _finish_inner(self, item: SourceLine) -> None:
        assert self._inner is not None
        text = _TRAILING_MARKERS.sub("", " ".join(self._inner)).strip().rstrip('”"').strip()
        path = self._cur.path if self._cur else self._art_path
        self._notes.append(
            ParsedNote(
                NoteKind.AMENDMENT, f"Texto sustituto de un párrafo: {text}", item.page, path
            )
        )
        self._anomaly(
            "paragraph_replacement_unapplied",
            "A paragraph was replaced by a later norm; the current text of this provision still "
            "contains the original paragraph and needs manual review",
            item, text[:160], path=path,
        )  # fmt: skip
        self._inner = None
        self._pending_event = None
        self._pending_paragraph = False

    # ------------------------------------------------------------------ notes and buffers
    def _flush_buffer_note(self) -> None:
        text = " ".join(self._buffer).strip()
        mode, self._mode, self._buffer = self._mode, None, []
        if not text:
            return
        path = self._art_path
        if mode == "concordance":
            self._notes.append(ParsedNote(NoteKind.CONCORDANCE, text, self._buffer_page, path))
            return
        if mode in {"inline", "footnote"}:
            self._notes.append(
                ParsedNote(NoteKind.FOOTNOTE, _REF_DIGITS.sub("", text), self._buffer_page, path)
            )
            return
        self._notes.append(ParsedNote(NoteKind.AMENDMENT, text, self._buffer_page, path))
        if event := parse_event(text):
            if is_forward(text):
                self._pending_event = event
                self._pending_paragraph = is_paragraph_note(text)
            elif self._last_quoted is not None and self._last_quoted.event is None:
                self._last_quoted.event = event
                self._last_quoted = None

    def _flush_preamble(self) -> None:
        if self._preamble:
            self._notes.append(
                ParsedNote(NoteKind.PREAMBLE, " ".join(self._preamble), self._preamble_page)
            )
        self._preamble = []

    def _finish(self) -> None:
        if self._inner is not None:
            self._anomaly(
                "unclosed_inner_quote",
                "Quoted paragraph never closed",
                SourceLine(0, ""),
                " ".join(self._inner)[:160],
            )
        self._close_draft()
        if self._mode == "epilogue":
            self._notes.append(
                ParsedNote(NoteKind.EPILOGUE, " ".join(self._buffer), self._buffer_page)
            )
        elif self._mode:
            self._flush_buffer_note()
        if not self._started:
            self._flush_preamble()
            self._anomalies.append(
                Anomaly("no_structure", "No articles or headings were found", 0, "")
            )

    # ------------------------------------------------------------------ revisions
    def _close_draft(self) -> None:
        draft, self._cur = self._cur, None
        if draft is None:
            return
        text = " ".join(" ".join(draft.lines).split())
        existing = self._by_path.get(draft.path, [])
        current = next((r for r in existing if r.status is RevisionStatus.CURRENT), None)
        if current is not None and not draft.quoted:
            self._anomalies.append(Anomaly(
                "duplicate_unquoted_unit", "The same unit appears twice without being a quoted replacement",
                draft.page_start, text[:160], draft.path,
            ))  # fmt: skip
            return
        if current is not None:
            self._supersede_tree(draft.path)
        rev = self._emit(
            draft.kind, draft.label, draft.title, draft.path, draft.parent_path, text,
            draft.page_start, draft.page_end, tuple(draft.boxes), None, current=True,
        )  # fmt: skip
        self._tail = rev
        if draft.quoted and self._block_root is None:
            self._block_root = rev
            if self._pending_event is not None:
                rev.event = self._pending_event
                self._pending_event = None
            else:
                self._last_quoted = rev

    def _supersede_tree(self, path: str) -> None:
        prefix = path + "/"
        for revs in self._by_path.values():
            for rev in revs:
                if rev.status is RevisionStatus.CURRENT and (
                    rev.path == path or rev.path.startswith(prefix)
                ):
                    rev.status = RevisionStatus.SUPERSEDED

    def _emit(
        self, kind: ParsedKind, label: str, title: str | None, path: str, parent: str | None, text: str,
        page_start: int, page_end: int, boxes: tuple[TextBox, ...], event: ParsedEvent | None, *, current: bool,
    ) -> _Rev:  # fmt: skip
        self._ordinal += 1
        revs = self._by_path.setdefault(path, [])
        rev = _Rev(
            path, kind, label, title, parent, text, len(revs) + 1,
            RevisionStatus.CURRENT if current else RevisionStatus.SUPERSEDED,
            page_start, page_end, self._ordinal, boxes, event,
        )  # fmt: skip
        revs.append(rev)
        self._revs.append(rev)
        return rev

    def _anomaly(
        self, code: str, message: str, item: SourceLine, excerpt: str, *, path: str | None = None
    ) -> None:
        self._anomalies.append(Anomaly(code, message, item.page, excerpt[:160], path))
