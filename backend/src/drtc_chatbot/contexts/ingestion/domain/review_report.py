"""Review report: what the reviewer must look at before approving an ingested version."""

from collections import Counter
from dataclasses import dataclass
from typing import Any

from drtc_chatbot.contexts.ingestion.domain.parsing.model import (
    ParsedKind,
    ParseResult,
    RevisionStatus,
)

_SAMPLE = 5


@dataclass(frozen=True, slots=True)
class ReviewReport:
    version_id: str
    pages: tuple[tuple[int, int], ...]
    current_by_kind: dict[str, int]
    superseded: int
    revisions_without_event: int
    notes: int
    numeric_articles: int
    article_gaps: tuple[int, ...]
    anomalies_by_code: dict[str, int]
    anomaly_samples: dict[str, list[dict[str, Any]]]

    @property
    def needs_attention(self) -> bool:
        return bool(self.anomalies_by_code) or bool(self.article_gaps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version_id": self.version_id,
            "pages": [list(p) for p in self.pages],
            "current_by_kind": self.current_by_kind,
            "superseded": self.superseded,
            "revisions_without_event": self.revisions_without_event,
            "notes": self.notes,
            "numeric_articles": self.numeric_articles,
            "article_gaps": list(self.article_gaps),
            "anomalies_by_code": self.anomalies_by_code,
            "anomaly_samples": self.anomaly_samples,
        }


def build_report(
    version_id: str, result: ParseResult, pages: tuple[tuple[int, int], ...]
) -> ReviewReport:
    current = [p for p in result.provisions if p.status is RevisionStatus.CURRENT]
    numbers = sorted(
        {
            int(p.label.split("-")[0])
            for p in current
            if p.kind is ParsedKind.ARTICLE and p.label[:1].isdigit()
        }
    )
    gaps = tuple(n for n in range(1, (numbers[-1] if numbers else 0) + 1) if n not in numbers)
    samples: dict[str, list[dict[str, Any]]] = {}
    for anomaly in result.anomalies:
        bucket = samples.setdefault(anomaly.code, [])
        if len(bucket) < _SAMPLE:
            bucket.append({"page": anomaly.page, "path": anomaly.path, "excerpt": anomaly.excerpt})
    return ReviewReport(
        version_id=version_id,
        pages=pages,
        current_by_kind=dict(Counter(p.kind.value for p in current)),
        superseded=sum(p.status is RevisionStatus.SUPERSEDED for p in result.provisions),
        revisions_without_event=sum(
            p.revision > 1 and p.event is None and p.kind is not ParsedKind.NUMERAL
            for p in result.provisions
        ),
        notes=len(result.notes),
        numeric_articles=len(numbers),
        article_gaps=gaps,
        anomalies_by_code=dict(Counter(a.code for a in result.anomalies)),
        anomaly_samples=samples,
    )
