"""Matching a parsed reference against the structural paths of a norm.

A path such as ``articulo:4-A/numeral:4-A.1/literal:a`` is matched when its LAST segment satisfies the
LAST step and the earlier steps appear, in order, among its earlier segments. So ``art 4-A lit a``
matches every literal ``a`` below article 4-A (they are all returned: the person chooses).
"""

from dataclasses import dataclass

from drtc_chatbot.contexts.retrieval.domain.ordinals import ordinal_value
from drtc_chatbot.contexts.retrieval.domain.reference import Step, canonical_group


@dataclass(frozen=True, slots=True)
class Segment:
    key: str  # "" for the ordinal of a disposition (``tercera``)
    value: str


def split_path(path: str) -> list[Segment]:
    segments = []
    for raw in path.split("/"):
        key, _, value = raw.partition(":")
        segments.append(Segment(key, value) if value else Segment("", key))
    return segments


def labels_equal(left: str, right: str) -> bool:
    """``05`` equals ``5``; ``4-A`` equals ``4-a``; ``IV`` equals ``iv``."""
    a, b = left.casefold().strip(), right.casefold().strip()
    if a.isdigit() and b.isdigit():
        return int(a) == int(b)
    return a == b


def matches(path: str, steps: tuple[Step, ...]) -> bool:
    if not steps:
        return False
    segments = split_path(path)
    article = next((s.value for s in segments if s.key == "articulo"), None)
    last = len(segments) - 1
    if not _step_matches(segments, last, steps[-1], article):
        return False
    index = 0
    for step in steps[:-1]:
        while index < last and not _step_matches(segments, index, step, article):
            index += 1
        if index >= last:
            return False
        index += 1
    return True


def _step_matches(segments: list[Segment], index: int, step: Step, article: str | None) -> bool:
    segment = segments[index]
    value = step.value
    kind = step.kind
    if kind in {"articulo", "anexo", "titulo", "capitulo", "seccion"}:
        return segment.key == kind and _label_matches(kind, segment.value, value)
    if kind == "literal":
        return segment.key == "literal" and segment.value.casefold() == value
    if kind == "numeral":
        if segment.key != "numeral":
            return False
        return labels_equal(segment.value, value) or (
            article is not None and labels_equal(segment.value, f"{article}.{value}")
        )
    if kind == "disposicion":
        return _disposition_matches(segments, index, step)
    return False


def _label_matches(kind: str, path_value: str, wanted: str) -> bool:
    if kind == "seccion":
        a, b = ordinal_value(path_value.casefold()), ordinal_value(wanted)
        return labels_equal(path_value, wanted) or (a is not None and a == b)
    return labels_equal(path_value, wanted)


def _disposition_matches(segments: list[Segment], index: int, step: Step) -> bool:
    segment = segments[index]
    if step.value == "":  # the group itself: "disposiciones complementarias finales"
        return segment.key == "disposiciones" and _group_matches(segment.value, step)
    wanted = ordinal_value(step.value)
    if segment.key == "disposicion":  # "disposicion:unica" (a norm with a single, ungrouped one)
        return wanted is not None and ordinal_value(segment.value) == wanted and not step.group
    if segment.key != "" or index == 0 or segments[index - 1].key != "disposiciones":
        return False
    group_ok = not step.group or _group_matches(segments[index - 1].value, step)
    return group_ok and wanted is not None and ordinal_value(segment.value) == wanted


def _group_matches(path_group: str, step: Step) -> bool:
    """Every word the person typed must be in the group (``final`` ⊂ ``complementaria final``)."""
    return set(step.group) <= set(canonical_group(path_group))
