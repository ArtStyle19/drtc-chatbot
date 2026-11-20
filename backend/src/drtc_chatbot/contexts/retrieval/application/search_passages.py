"""Use case: find provisions by what a person writes (spec 004, the content search).

Order of precedence (constitution I.6): a provision that the text IDENTIFIES by reference ("art. 5 Ley
27181") comes first and is marked as such; only then the content arms, fused with Reciprocal Rank
Fusion: the words search (always available) and the meaning search (needs the embeddings provider). The
result is a list of READING UNITS (article, disposition, annex), each with its best passage and the
other passages of the unit that matched.

The meaning arm is optional by design (FR-013): no key, a provider error or a timeout never fails the
search, it answers with words and says so in ``degraded``. The text of the question is never logged
here or stored (constitution VI).
"""

import asyncio
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace

from drtc_chatbot.contexts.retrieval.application.dto import (
    DEGRADED_VECTOR_NOT_INDEXED,
    DEGRADED_VECTOR_UNAVAILABLE,
    LookupHit,
    MatchedPassage,
    SearchFacet,
    SearchMode,
    SearchResponse,
    SearchResult,
)
from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference
from drtc_chatbot.contexts.retrieval.application.ports import (
    EditionCatalog,
    EditionInfo,
    EmbeddingProvider,
    EmbeddingPurpose,
    PassageHit,
    PassageIndex,
    Segment,
)
from drtc_chatbot.contexts.retrieval.domain.errors import EmbeddingUnavailableError
from drtc_chatbot.contexts.retrieval.domain.fusion import reciprocal_rank_fusion
from drtc_chatbot.contexts.retrieval.domain.query import validate_query
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError

ARM_TOP_N = 50
# Fusion defaults, chosen with the golden set (evaluation/reports/2026-11-19-fusion-tuning.md): the meaning
# arm found the expected unit in the top 10 for 100 % of the questions and the words arm for 67 %, so with
# equal weights the weaker arm dragged the stronger one down (hybrid 98 % < meaning alone 100 %). Counting
# the meaning arm six times as much, with a small k, keeps the words as the tie-breaker that rescues
# questions with an exact term (SOAT, multa, plazo) and makes the hybrid as good as the meaning alone.
DEFAULT_RRF_K = 5
DEFAULT_VECTOR_WEIGHT = 6.0
MAX_MATCHED = 5
DEFAULT_LIMIT = 10
VECTOR_TIMEOUT_SECONDS = 3.0
GRACE_SECONDS = (
    0.5  # the provider is asked for VECTOR_TIMEOUT_SECONDS; this is the safety net around it
)

Key = tuple[str, str]  # (edition, provision path)
UnitKey = tuple[str, str]  # (edition, reading unit path)


@dataclass(slots=True)
class _Unit:
    """A reading unit being assembled from the passages that matched."""

    key: UnitKey
    passages: list[PassageHit] = field(default_factory=list)
    score: float = 0.0
    arms: dict[str, int] = field(default_factory=dict)  # arm -> best rank among the unit's passages
    via: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class _Arms:
    lexical: Sequence[PassageHit]
    vector: Sequence[PassageHit]
    degraded: tuple[str, ...]


class SearchPassages:
    def __init__(
        self,
        lookup: LookupReference,
        index: PassageIndex,
        editions: EditionCatalog,
        provider: EmbeddingProvider | None,
        *,
        rrf_k: int = DEFAULT_RRF_K,
        vector_weight: float = DEFAULT_VECTOR_WEIGHT,
        arm_top_n: int = ARM_TOP_N,
        vector_timeout_seconds: float = VECTOR_TIMEOUT_SECONDS,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._lookup = lookup
        self._index = index
        self._editions = editions
        self._provider = provider
        self._k = rrf_k
        self._vector_weight = vector_weight
        self._top_n = arm_top_n
        self._timeout = vector_timeout_seconds
        self._timer = timer

    async def execute(
        self,
        actor: Actor,
        text: str,
        *,
        limit: int = DEFAULT_LIMIT,
        instrument_id: str | None = None,
        mode: SearchMode = SearchMode.HYBRID,
        debug: bool = False,
    ) -> SearchResponse:
        started = self._timer()
        query = validate_query(text)
        reference_hits, reference, content_text = await self._reference(actor, query)
        editions = await self._editions.editions(actor)

        degraded: tuple[str, ...] = ()
        pool_units: list[_Unit] = []
        shown_units: list[_Unit] = []
        if content_text:
            vector, degraded = await self._embed(content_text, mode)
            pool = await self._arms(
                content_text, vector, mode, instrument_id=None, degraded=degraded
            )
            pool_units = self._units(pool)
            shown_units = (
                pool_units
                if instrument_id is None
                else self._units(
                    await self._arms(
                        content_text,
                        vector,
                        mode,
                        instrument_id=instrument_id,
                        degraded=pool.degraded,
                    )
                )
            )
            degraded = pool.degraded

        exact = self._reference_results(reference_hits, debug=debug)
        content = self._content_results(shown_units, editions, debug=debug)
        results = self._merge(exact, content, instrument_id)
        facets = self._facets([*exact, *self._content_results(pool_units, editions, debug=False)])
        return SearchResponse(
            query=query,
            mode=mode,
            degraded=degraded,
            total=len(results),
            results=tuple(results[:limit]),
            facets=facets,
            reference=reference,
            latency_ms=round((self._timer() - started) * 1000, 1),
        )

    # ------------------------------------------------------------------ the exact arm
    async def _reference(self, actor: Actor, query: str) -> tuple[list[LookupHit], str | None, str]:
        """The provisions a reference in the text identifies, what was understood, and the rest of the text."""
        try:
            found = await self._lookup.execute(actor, query)
        except InvariantViolationError:
            return [], None, query
        hits = [h for h in found.hits if h.path is not None and h.version_id is not None]
        if found.reference is None:
            return [], None, query  # not a reference: everything is content
        return hits, found.reference, (found.ignored_text or "").strip()

    # ------------------------------------------------------------------ the content arms
    async def _embed(
        self, text: str, mode: SearchMode
    ) -> tuple[tuple[float, ...] | None, tuple[str, ...]]:
        if mode is SearchMode.LEXICAL:
            return None, ()
        if self._provider is None:
            return None, (DEGRADED_VECTOR_UNAVAILABLE,)
        try:
            batch = await asyncio.wait_for(
                self._provider.embed(
                    [text], purpose=EmbeddingPurpose.QUERY, timeout_seconds=self._timeout
                ),
                timeout=self._timeout + GRACE_SECONDS,
            )
        except EmbeddingUnavailableError, TimeoutError:
            return None, (DEGRADED_VECTOR_UNAVAILABLE,)
        return batch.vectors[0], ()

    async def _arms(
        self,
        text: str,
        vector: tuple[float, ...] | None,
        mode: SearchMode,
        *,
        instrument_id: str | None,
        degraded: tuple[str, ...],
    ) -> _Arms:
        lexical: Sequence[PassageHit] = ()
        if mode is not SearchMode.VECTOR:
            lexical = await self._index.lexical_search(
                text, instrument_id=instrument_id, limit=self._top_n
            )
        found: Sequence[PassageHit] = ()
        if vector is not None and self._provider is not None:
            found = await self._index.vector_search(
                self._provider.model, vector, instrument_id=instrument_id, limit=self._top_n
            )
            if not found and await self._index.embedded_passages(self._provider.model) == 0:
                degraded = (*degraded, DEGRADED_VECTOR_NOT_INDEXED)
        return _Arms(lexical, found, degraded)

    def _units(self, arms: _Arms) -> list[_Unit]:
        """Fuse the arms at passage level, then group by reading unit (the best passage represents it)."""
        by_key: dict[Key, PassageHit] = {}
        for hit in [*arms.vector, *arms.lexical]:  # a lexical hit (with highlighted words) wins
            by_key[(hit.passage.version_id, hit.passage.path)] = hit
        fused = reciprocal_rank_fusion(
            {
                "lexical": [(h.passage.version_id, h.passage.path) for h in arms.lexical],
                "vector": [(h.passage.version_id, h.passage.path) for h in arms.vector],
            },
            k=self._k,
            weights={"vector": self._vector_weight},
        )
        units: dict[UnitKey, _Unit] = {}
        for item in fused:
            hit = by_key[item.key]
            unit_key = (hit.passage.version_id, hit.passage.unit_path)
            unit = units.setdefault(unit_key, _Unit(unit_key, score=item.score))
            if len(unit.passages) < MAX_MATCHED:
                unit.passages.append(hit)
            for arm, rank in item.ranks.items():
                unit.arms[arm] = min(rank, unit.arms.get(arm, rank))
                if arm not in unit.via:
                    unit.via.append(arm)
        return list(units.values())

    # ------------------------------------------------------------------ building results
    @staticmethod
    def _reference_results(hits: Sequence[LookupHit], *, debug: bool) -> list[SearchResult]:
        results = []
        for rank, hit in enumerate(hits, start=1):
            if hit.version_id is None or hit.path is None:
                continue  # the whole norm, not a provision
            snippet = (Segment(hit.snippet),) if hit.snippet else ()
            results.append(
                SearchResult(
                    instrument_id=hit.instrument_id,
                    instrument_short_name=hit.instrument_short_name,
                    version_id=hit.version_id,
                    edition_label=hit.edition_label or "",
                    verification_status=hit.verification_status or "unknown",
                    unit_path=hit.unit_path or hit.path,
                    path=hit.path,
                    kind=hit.kind or "",
                    label=hit.label or "",
                    title=hit.title,
                    citation=hit.citation,
                    page_start=hit.page_start or 0,
                    page_end=hit.page_start or 0,
                    snippet=snippet,
                    matched=(),
                    via=("reference",),
                    score=1.0,
                    debug={"reference_rank": rank} if debug else None,
                )
            )
        return results

    @staticmethod
    def _content_results(
        units: Sequence[_Unit], catalog: Mapping[str, EditionInfo], *, debug: bool
    ) -> list[SearchResult]:
        results = []
        for unit in units:
            best = unit.passages[0].passage
            info = catalog.get(best.version_id)
            results.append(
                SearchResult(
                    instrument_id=best.instrument_id,
                    instrument_short_name=info.instrument_short_name
                    if info
                    else best.instrument_id,
                    version_id=best.version_id,
                    edition_label=info.edition_label if info else "",
                    verification_status=info.verification_status if info else "unknown",
                    unit_path=best.unit_path,
                    path=best.path,
                    kind=best.kind,
                    label=best.label,
                    title=best.title,
                    citation=best.citation,
                    page_start=best.page_start,
                    page_end=best.page_end,
                    snippet=unit.passages[0].snippet,
                    matched=tuple(
                        MatchedPassage(
                            h.passage.path,
                            h.passage.citation,
                            h.passage.page_start,
                            h.passage.page_end,
                            h.snippet,
                        )
                        for h in unit.passages
                    ),
                    via=tuple(unit.via),
                    score=round(unit.score, 6),
                    debug=(
                        {
                            "reference_rank": None,
                            "lexical_rank": unit.arms.get("lexical"),
                            "vector_rank": unit.arms.get("vector"),
                            "score": round(unit.score, 6),
                        }
                        if debug
                        else None
                    ),
                )
            )
        return results

    @staticmethod
    def _merge(
        exact: list[SearchResult], content: list[SearchResult], instrument_id: str | None
    ) -> list[SearchResult]:
        """References first; a unit found by reference AND by content appears once, with both marks."""
        pinned = {(r.version_id, r.unit_path): i for i, r in enumerate(exact)}
        merged = [r for r in exact if instrument_id is None or r.instrument_id == instrument_id]
        for result in content:
            position = pinned.get((result.version_id, result.unit_path))
            if position is not None:
                original = exact[position]
                for index, candidate in enumerate(merged):
                    if candidate is original:
                        merged[index] = replace(
                            original,
                            via=(*original.via, *result.via),
                            matched=result.matched,
                            # the highlighted words belong to the content passage: show them when it IS the one
                            # the reference identified (the reader opens the reference's own path)
                            snippet=result.snippet
                            if result.path == original.path
                            else original.snippet,
                            debug={**(original.debug or {}), **(result.debug or {})} or None,
                        )
                continue
            merged.append(result)
        return merged

    @staticmethod
    def _facets(results: Sequence[SearchResult]) -> tuple[SearchFacet, ...]:
        counts: dict[str, int] = {}
        names: dict[str, str] = {}
        seen: set[UnitKey] = set()
        for result in results:
            key = (result.version_id, result.unit_path)
            if key in seen:
                continue
            seen.add(key)
            counts[result.instrument_id] = counts.get(result.instrument_id, 0) + 1
            names[result.instrument_id] = result.instrument_short_name
        return tuple(
            SearchFacet(instrument_id, names[instrument_id], count)
            for instrument_id, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        )
