"""PassageIndex over PostgreSQL: synchronisation and the words search.

The words search turns the question into an OR of stemmed terms (``plainto_tsquery`` with the
``spanish`` configuration gives AND; every ``&`` becomes ``|``) so a long question matches the
passages that share MOST of its words rather than none; ``ts_rank_cd`` orders them by how many terms
match and how close together. Snippets come from ``ts_headline`` with control characters as markers and
are returned as segments, never as HTML.
"""

import re
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from sqlalchemy import bindparam, delete, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from drtc_chatbot.contexts.retrieval.application.ports import (
    IndexStats,
    PassageHit,
    Segment,
    StoredEmbedding,
    WindowToEmbed,
)
from drtc_chatbot.contexts.retrieval.domain.chunking import (
    MARKERS,
    PassageText,
    clean,
    content_hash,
    embedding_windows,
    window_hash,
)
from drtc_chatbot.contexts.retrieval.domain.lexical import (
    accent_pairs,
    expand_query,
    has_accent,
    words,
)
from drtc_chatbot.contexts.retrieval.infrastructure.models import (
    SEARCH_CONFIG,
    AccentRow,
    EmbeddingRow,
    PassageRow,
)

_START, _STOP = MARKERS
_MARKED = re.compile(f"({_START}.*?{_STOP})", re.DOTALL)
_BATCH = 500


@dataclass(frozen=True, slots=True)
class LexicalTuning:
    """Knobs of the words search; their values are chosen with the golden set (not by opinion)."""

    # ts_rank_cd weights for text labelled D, C, B, A (A = title, B = text, C = breadcrumb and lead).
    # Chosen with the golden set (evaluation/reports/2026-11-19-lexical-tuning.md): the title weighs as
    # much as the text, the context (C) matters (without it MRR drops from 0.445 to 0.340) and D is
    # irrelevant: (0.0/0.1/0.2, 0.2, 0.4, 0.4) all give identical results, a stable plateau.
    weights: tuple[float, float, float, float] = (0.1, 0.2, 0.4, 0.4)
    # ts_rank_cd normalisation flags. 2 = divide by the length of the passage: it nearly doubled the MRR
    # (0.226 -> 0.397) because a 35,000-character annex no longer wins just by accumulating matches.
    normalization: int = 2
    headline_options: str = (
        f"StartSel={_START}, StopSel={_STOP}, MaxWords=35, MinWords=15, ShortWord=3, MaxFragments=1"
    )


# S608: only the constant name of the search configuration is interpolated; the person's text is a bound parameter.
_SEARCH = text(
    f"""
    WITH query AS (
        SELECT replace(plainto_tsquery('{SEARCH_CONFIG}', :text)::text, ' & ', ' | ')::tsquery AS tsq
    ), ranked AS (
        SELECT p.id,
               ts_rank_cd(CAST(:weights AS float4[]), p.search_vector, query.tsq, :normalization) AS score
        FROM retrieval_passages p, query
        WHERE p.search_vector @@ query.tsq
          AND (CAST(:instrument AS text) IS NULL OR p.instrument_id = CAST(:instrument AS text))
        ORDER BY score DESC, p.instrument_version_id, p.provision_path
        LIMIT :limit
    )
    SELECT p.instrument_id, p.instrument_version_id, p.provision_path, p.unit_path, p.kind, p.label,
           p.title, p.breadcrumb, p.lead, p.body, p.page_start, p.page_end, p.citation,
           ranked.score,
           ts_headline('{SEARCH_CONFIG}', coalesce(nullif(p.body, ''), p.title, ''), query.tsq, :options)
               AS headline
    FROM ranked
    JOIN retrieval_passages p ON p.id = ranked.id
    CROSS JOIN query
    ORDER BY ranked.score DESC, p.instrument_version_id, p.provision_path
    """  # noqa: S608
).bindparams(
    bindparam("text"),
    bindparam("weights"),
    bindparam("normalization"),
    bindparam("instrument"),
    bindparam("limit"),
    bindparam("options"),
)


_VECTOR_SEARCH = text(
    """
    WITH nearest AS (
        SELECT e.passage_id, min(e.embedding <=> CAST(:vector AS vector)) AS distance
        FROM retrieval_embeddings e
        JOIN retrieval_passages p ON p.id = e.passage_id
        WHERE e.model = :model
          AND (CAST(:instrument AS text) IS NULL OR p.instrument_id = CAST(:instrument AS text))
        GROUP BY e.passage_id
        ORDER BY distance, e.passage_id
        LIMIT :limit
    )
    SELECT p.instrument_id, p.instrument_version_id, p.provision_path, p.unit_path, p.kind, p.label,
           p.title, p.breadcrumb, p.lead, p.body, p.page_start, p.page_end, p.citation,
           1 - nearest.distance AS score
    FROM nearest
    JOIN retrieval_passages p ON p.id = nearest.passage_id
    ORDER BY nearest.distance, p.instrument_version_id, p.provision_path
    """
)
SNIPPET_CHARS = 240


def _plain_snippet(body: str, title: str | None) -> tuple[Segment, ...]:
    """The beginning of the text (no words are highlighted: the match is by meaning, not by words)."""
    source = " ".join((body or title or "").split())
    if len(source) <= SNIPPET_CHARS:
        return (Segment(source),) if source else ()
    cut = source[:SNIPPET_CHARS].rsplit(" ", 1)[0]
    return (Segment(f"{cut}…"),)


def segments(headline: str) -> tuple[Segment, ...]:
    """``a \\x01b\\x02 c`` → ``(Segment("a "), Segment("b", match=True), Segment(" c"))``."""
    pieces: list[Segment] = []
    for part in _MARKED.split(headline):
        if not part:
            continue
        if part.startswith(_START):
            pieces.append(Segment(part.removeprefix(_START).removesuffix(_STOP), match=True))
        else:
            pieces.append(Segment(part))
    return tuple(pieces)


def _row_values(passage: PassageText) -> dict[str, Any]:
    return {
        "instrument_id": passage.instrument_id,
        "instrument_version_id": passage.version_id,
        "provision_path": passage.path,
        "unit_path": passage.unit_path,
        "kind": passage.kind,
        "label": passage.label,
        "title": clean(passage.title) if passage.title else None,
        "breadcrumb": clean(passage.breadcrumb),
        "lead": clean(passage.lead) if passage.lead else None,
        "body": clean(passage.body),
        "page_start": passage.page_start,
        "page_end": passage.page_end,
        "citation": passage.citation,
        "content_hash": content_hash(passage),
    }


def _passage(row: PassageRow) -> PassageText:
    return PassageText(
        instrument_id=row.instrument_id,
        version_id=row.instrument_version_id,
        path=row.provision_path,
        unit_path=row.unit_path,
        kind=row.kind,
        label=row.label,
        title=row.title,
        breadcrumb=row.breadcrumb,
        lead=row.lead,
        body=row.body,
        page_start=row.page_start,
        page_end=row.page_end,
        citation=row.citation,
    )


def _passage_from_columns(row: Any) -> PassageText:
    return PassageText(
        instrument_id=row.instrument_id,
        version_id=row.instrument_version_id,
        path=row.provision_path,
        unit_path=row.unit_path,
        kind=row.kind,
        label=row.label,
        title=row.title,
        breadcrumb=row.breadcrumb,
        lead=row.lead,
        body=row.body,
        page_start=row.page_start,
        page_end=row.page_end,
        citation=row.citation,
    )


class SqlPassageIndex:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], tuning: LexicalTuning | None = None
    ) -> None:
        self._sessions = sessions
        self._tuning = tuning or LexicalTuning()

    async def sync(self, passages: Sequence[PassageText]) -> IndexStats:
        desired = {(p.version_id, p.path): p for p in passages}
        async with self._sessions() as session, session.begin():
            existing = {
                (row.instrument_version_id, row.provision_path): row
                for row in (
                    await session.execute(
                        select(
                            PassageRow.id,
                            PassageRow.instrument_version_id,
                            PassageRow.provision_path,
                            PassageRow.content_hash,
                            PassageRow.unit_path,
                            PassageRow.page_start,
                            PassageRow.page_end,
                            PassageRow.citation,
                            PassageRow.instrument_id,
                        )
                    )
                ).all()
            }
            gone = [row.id for key, row in existing.items() if key not in desired]
            for start in range(0, len(gone), _BATCH):
                await session.execute(
                    delete(PassageRow).where(PassageRow.id.in_(gone[start : start + _BATCH]))
                )

            new: list[dict[str, Any]] = []
            changed = unchanged = 0
            for key, passage in desired.items():
                values = _row_values(passage)
                current = existing.get(key)
                if current is None:
                    new.append({"id": uuid.uuid4(), **values})
                elif current.content_hash != values["content_hash"]:
                    changed += 1
                    await session.execute(
                        update(PassageRow).where(PassageRow.id == current.id).values(**values)
                    )
                    # the vectors were computed from the old text: they are stale
                    await session.execute(
                        delete(EmbeddingRow).where(EmbeddingRow.passage_id == current.id)
                    )
                else:
                    unchanged += 1
                    if (current.unit_path, current.page_start, current.page_end, current.citation, current.instrument_id) != (
                        values["unit_path"], values["page_start"], values["page_end"], values["citation"], values["instrument_id"],
                    ):  # fmt: skip
                        meta = {
                            k: values[k]
                            for k in (
                                "unit_path",
                                "page_start",
                                "page_end",
                                "citation",
                                "instrument_id",
                            )
                        }
                        await session.execute(
                            update(PassageRow).where(PassageRow.id == current.id).values(**meta)
                        )
            for start in range(0, len(new), _BATCH):
                await session.execute(insert(PassageRow), new[start : start + _BATCH])
            await self._replace_accents(session, desired.values())
        return IndexStats(added=len(new), changed=changed, removed=len(gone), unchanged=unchanged)

    @staticmethod
    async def _replace_accents(session: AsyncSession, passages: Iterable[PassageText]) -> None:
        """The accented words the corpus really has, to extend what people type without accents."""
        pairs = accent_pairs(f"{p.title or ''} {p.body}" for p in passages)
        await session.execute(delete(AccentRow))
        rows = [{"plain": plain, "accented": accented} for plain, accented in sorted(pairs)]
        for start in range(0, len(rows), _BATCH):
            await session.execute(insert(AccentRow), rows[start : start + _BATCH])

    async def count(self) -> int:
        async with self._sessions() as session:
            return int(
                (
                    await session.execute(text("SELECT count(*) FROM retrieval_passages"))
                ).scalar_one()
            )

    @staticmethod
    async def _expand(session: AsyncSession, query: str) -> str:
        typed = sorted({w for w in words(query) if not has_accent(w)})
        if not typed:
            return query
        found = (
            await session.execute(select(AccentRow).where(AccentRow.plain.in_(typed)))
        ).scalars()
        variants: dict[str, list[str]] = {}
        for row in found:
            variants.setdefault(row.plain, []).append(row.accented)
        return expand_query(query, variants)

    async def lexical_search(
        self, text: str, *, instrument_id: str | None, limit: int
    ) -> Sequence[PassageHit]:
        async with self._sessions() as session:
            expanded = await self._expand(session, text)
        params = {
            "text": expanded,
            "weights": list(self._tuning.weights),
            "normalization": self._tuning.normalization,
            "instrument": instrument_id,
            "limit": limit,
            "options": self._tuning.headline_options,
        }
        async with self._sessions() as session:
            rows = (await session.execute(_SEARCH, params)).all()
        return [
            PassageHit(
                passage=_passage_from_columns(row),
                score=float(row.score),
                snippet=segments(row.headline or ""),
            )
            for row in rows
        ]

    # ---- the meaning search: vectors
    async def missing_windows(self, model: str) -> Sequence[WindowToEmbed]:
        async with self._sessions() as session:
            rows = (await session.execute(select(PassageRow))).scalars().all()
            known = {
                (row.passage_id, row.window): row.content_hash
                for row in (
                    await session.execute(
                        select(
                            EmbeddingRow.passage_id, EmbeddingRow.window, EmbeddingRow.content_hash
                        ).where(EmbeddingRow.model == model)
                    )
                ).all()
            }
        pending: list[WindowToEmbed] = []
        for row in rows:
            passage = _passage(row)
            for number, window in enumerate(embedding_windows(passage)):
                digest = window_hash(window)
                if known.get((row.id, number)) != digest:
                    pending.append(WindowToEmbed(str(row.id), number, window, digest))
        return pending

    async def store_embeddings(self, model: str, items: Sequence[StoredEmbedding]) -> None:
        if not items:
            return
        async with self._sessions() as session, session.begin():
            for start in range(0, len(items), _BATCH):
                values = [
                    {
                        "passage_id": uuid.UUID(item.passage_id),
                        "model": model,
                        "window": item.window,
                        "dims": len(item.vector),
                        "content_hash": item.content_hash,
                        "embedding": list(item.vector),
                    }
                    for item in items[start : start + _BATCH]
                ]
                statement = pg_insert(EmbeddingRow).values(values)
                await session.execute(
                    statement.on_conflict_do_update(
                        index_elements=["passage_id", "model", "window"],
                        set_={
                            "dims": statement.excluded.dims,
                            "content_hash": statement.excluded.content_hash,
                            "embedding": statement.excluded.embedding,
                        },
                    )
                )

    async def embedded_passages(self, model: str) -> int:
        async with self._sessions() as session:
            return int(
                (
                    await session.execute(
                        text(
                            "SELECT count(DISTINCT passage_id) FROM retrieval_embeddings WHERE model = :m"
                        ),
                        {"m": model},
                    )
                ).scalar_one()
            )

    async def vector_search(
        self, model: str, vector: Sequence[float], *, instrument_id: str | None, limit: int
    ) -> Sequence[PassageHit]:
        literal = "[" + ",".join(f"{value:.7g}" for value in vector) + "]"
        params = {"vector": literal, "model": model, "instrument": instrument_id, "limit": limit}
        async with self._sessions() as session:
            rows = (await session.execute(_VECTOR_SEARCH, params)).all()
        return [
            PassageHit(
                passage=_passage_from_columns(row),
                score=float(row.score),
                snippet=_plain_snippet(row.body, row.title),
            )
            for row in rows
        ]
