"""Recognition of editorial notes: which norm amended a text, and when."""

import re
from datetime import date

from drtc_chatbot.contexts.ingestion.domain.parsing.model import EventKind, ParsedEvent

MARKER = re.compile(r"\(\*+\)")
NOTE_START = re.compile(r"^(?:\(\*+\)\s*(?=\S)|NOTA\s+SPIJ\b)")
PARAGRAPH_NOTE = re.compile(r"^(?:\(\*+\)\s*)?(?:\w+\s+)?p[áa]rrafos?\b", re.IGNORECASE)

_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
    "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}  # fmt: skip
_DATE = re.compile(r"(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)\s+(?:de\s+)?(\d{4})", re.IGNORECASE)
_ACTION = re.compile(
    r"\b(?P<action>modificad[oa]s?|sustituid[oa]s?|restituid[oa]s?|incorporad[oa]s?|"
    r"derogad[oa]s?|precisad[oa]s?)\s+(?:expresamente\s+)?por\s+(?P<source>.+)",
    re.IGNORECASE | re.DOTALL,
)
FORWARD = re.compile(
    r"(cuyo\s+texto\s+es\s+el\s+siguiente|texto\s+(?:es\s+)?el\s+siguiente)\s*:?\s*$", re.I
)


def parse_date(text: str) -> date | None:
    """First 'dd <month> yyyy' date in the text (Spanish month names), if any."""
    for match in _DATE.finditer(text):
        month = _MONTHS.get(match.group(2).lower())
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(1)))
            except ValueError:
                return None
    return None


def parse_event(note_text: str) -> ParsedEvent | None:
    """Turn 'Artículo modificado por el Decreto ... publicado el ...' into an event."""
    match = _ACTION.search(note_text)
    if match is None:
        return None
    action = match.group("action").lower()
    if action.startswith("incorporad"):
        kind = EventKind.INCORPORATED
    elif action.startswith("derogad"):
        kind = EventKind.REPEALED
    else:
        kind = EventKind.SUBSTITUTED
    source = match.group("source")
    source = re.split(r",\s*(?:publicad[oa]|cuyo)\b", source, maxsplit=1)[0]
    return ParsedEvent(
        kind=kind,
        source=" ".join(source.split()).rstrip(".:;, "),
        published_on=parse_date(note_text),
    )


def is_forward(note_text: str) -> bool:
    """True when the note announces the replacement text that follows ('cuyo texto es...')."""
    return FORWARD.search(note_text.strip()) is not None


def is_paragraph_note(note_text: str) -> bool:
    """True for 'Párrafo modificado...' / 'Primer párrafo modificado...' (a partial replacement)."""
    return PARAGRAPH_NOTE.match(note_text.strip()) is not None
