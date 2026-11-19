"""Reciprocal Rank Fusion: one ordered list out of several, without comparing their scores.

``ts_rank_cd`` and a cosine similarity live on different scales, so their raw scores cannot be added.
RRF only uses the POSITION in each list: an item gets ``1 / (k + rank)`` from every list that has it.
What two methods both rank well rises above what only one of them found, and nothing is duplicated.
"""

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeVar

Key = TypeVar("Key", bound=Hashable)
DEFAULT_K = 60


@dataclass(frozen=True, slots=True)
class Fused[Key: Hashable]:
    key: Key
    score: float
    ranks: Mapping[str, int]  # 1-based position of the item in each list that has it


def reciprocal_rank_fusion[Key: Hashable](
    rankings: Mapping[str, Sequence[Key]],
    *,
    k: int = DEFAULT_K,
    weights: Mapping[str, float] | None = None,
) -> list[Fused[Key]]:
    """Fuses ``rankings`` (arm name → items, best first). A repeated item keeps its best position.

    Ties are broken by the best individual position, then by the order of the arms, so the result is
    always the same for the same input.
    """
    if k < 1:
        raise ValueError("k must be at least 1")
    weights = weights or {}
    scores: dict[Key, float] = {}
    ranks: dict[Key, dict[str, int]] = {}
    first_seen: dict[Key, int] = {}
    for arm, items in rankings.items():
        position = 0
        for item in items:
            if arm in ranks.get(item, {}):
                continue  # the same item twice in one list counts once, at its best position
            position += 1
            scores[item] = scores.get(item, 0.0) + weights.get(arm, 1.0) / (k + position)
            ranks.setdefault(item, {})[arm] = position
            first_seen.setdefault(item, len(first_seen))
    ordered = sorted(
        scores,
        key=lambda item: (-scores[item], min(ranks[item].values()), first_seen[item]),
    )
    return [Fused(item, scores[item], dict(ranks[item])) for item in ordered]
