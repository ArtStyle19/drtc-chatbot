"""Structural paths and reading units.

A provision is identified inside its norm by a structural path such as ``articulo:2/literal:e`` (see
docs/architecture/ingestion.md). The reader shows one *reading unit* at a time: the article, the
disposition or the annex that contains the requested path.
"""

from dataclasses import dataclass

CONTAINER_KEYS = frozenset({"seccion", "titulo", "capitulo", "subcapitulo", "disposiciones"})


@dataclass(frozen=True, slots=True)
class PathSegment:
    """One ``key:value`` step of a path. Disposition ordinals have no key (``tercera``)."""

    key: str
    value: str


def split_path(path: str) -> list[PathSegment]:
    """Split a structural path into its segments (``articulo:2/literal:e`` → 2 segments)."""
    segments = []
    for raw in path.split("/"):
        key, _, value = raw.partition(":")
        segments.append(PathSegment(key, value) if value else PathSegment("", key))
    return segments


def reading_unit_path(path: str) -> str:
    """The path of the unit the reader shows for ``path``.

    * article / annex → the article or annex (``articulo:2/literal:e`` → ``articulo:2``)
    * a disposition or anything inside it → the disposition (``…/disposiciones:finales/tercera``)
    * a container (section, title, chapter, group of dispositions) → itself
    """
    segments = split_path(path)
    for index, segment in enumerate(segments):
        if segment.key in {"articulo", "anexo"} and index == 0:
            return "/".join(_raw(s) for s in segments[: index + 1])
        if segment.key == "disposicion":
            return "/".join(_raw(s) for s in segments[: index + 1])
        if segment.key == "" and index > 0 and segments[index - 1].key == "disposiciones":
            return "/".join(_raw(s) for s in segments[: index + 1])
    return path


def is_container_path(path: str) -> bool:
    """True for sections, titles, chapters and groups of dispositions (their text is only a title)."""
    last = split_path(path)[-1]
    return last.key in CONTAINER_KEYS


def _raw(segment: PathSegment) -> str:
    return f"{segment.key}:{segment.value}" if segment.key else segment.value
