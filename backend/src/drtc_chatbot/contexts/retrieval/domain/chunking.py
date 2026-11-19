"""What gets indexed for a provision, and how a long one is cut for the embedding model.

A passage is the CURRENT text of one provision of an approved edition. For the words search it is
indexed whole (PostgreSQL has no practical limit); for the meaning search the text is prefixed with its
context (breadcrumb, lead of its parent, title) and a text longer than the model accepts is cut into
overlapping windows at paragraph / sentence boundaries, so no window starts or ends in the middle of
a word. Pure functions: the same passage always gives the same text and the same hash.
"""

import hashlib
import re
from dataclasses import dataclass

MAX_WINDOW_CHARS = 3500  # ≈ 1,200 tokens: far below the 8,191 an embedding input may have
OVERLAP_RATIO = 0.10
MIN_BODY_CHARS = 1000  # a window always has room for text, however long its header is
# Characters that mark highlighted words inside the database; they must never come from a text.
MARKERS = ("\x01", "\x02")
_BOUNDARY = re.compile(r"(?<=[.;:?!])\s+|\n+")


@dataclass(frozen=True, slots=True)
class PassageText:
    """A provision as the search sees it (its own type: the corpus' types stay behind the facade)."""

    instrument_id: str
    version_id: str
    path: str
    unit_path: str
    kind: str
    label: str
    title: str | None
    breadcrumb: str
    lead: str | None
    body: str
    page_start: int
    page_end: int
    citation: str


def clean(text: str) -> str:
    """Removes the highlight markers and collapses whitespace runs (but keeps line breaks)."""
    for marker in MARKERS:
        text = text.replace(marker, "")
    return text


def content_hash(passage: PassageText) -> str:
    """Hash of everything that changes how the passage is indexed (not its pages or citation)."""
    parts = [passage.breadcrumb, passage.lead or "", passage.title or "", passage.body]
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _header(passage: PassageText) -> str:
    lines = [passage.breadcrumb, passage.lead or "", passage.title or ""]
    return "\n".join(line for line in lines if line.strip())


def _pieces(body: str) -> list[str]:
    return [piece for piece in _BOUNDARY.split(body) if piece.strip()]


def _hard_cut(piece: str, size: int) -> list[str]:
    """Last resort for a single sentence longer than a window (it should not happen in legal text)."""
    return [piece[i : i + size] for i in range(0, len(piece), size)]


def split_body(body: str, size: int, overlap_ratio: float = OVERLAP_RATIO) -> list[str]:
    """Cuts ``body`` into windows of at most ``size`` characters, with overlap, at sentence boundaries."""
    if len(body) <= size:
        return [body]
    overlap = int(size * overlap_ratio)
    pieces: list[str] = []
    for piece in _pieces(body):
        pieces.extend(_hard_cut(piece, size) if len(piece) > size else [piece])
    windows: list[str] = []
    current: list[str] = []
    length = 0
    for piece in pieces:
        extra = len(piece) + (1 if current else 0)
        if current and length + extra > size:
            windows.append(" ".join(current))
            # the next window starts with the tail of this one (whole sentences, up to the overlap)
            tail: list[str] = []
            tail_length = 0
            for previous in reversed(current):
                if tail_length + len(previous) + 1 > overlap:
                    break
                tail.insert(0, previous)
                tail_length += len(previous) + 1
            current, length = tail, sum(len(t) + 1 for t in tail)
            extra = len(piece) + (1 if current else 0)
        current.append(piece)
        length += extra
    if current:
        windows.append(" ".join(current))
    return windows


def embedding_windows(passage: PassageText, max_chars: int = MAX_WINDOW_CHARS) -> list[str]:
    """The texts to embed for a passage: header (context) + a window of the body; one per window."""
    header = _header(passage)
    body = " ".join(clean(passage.body).split()) if passage.body else ""
    if not body:
        return [clean(header)]
    room = max(MIN_BODY_CHARS, max_chars - len(header) - 1)
    return [clean(f"{header}\n{window}" if header else window) for window in split_body(body, room)]


def window_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
