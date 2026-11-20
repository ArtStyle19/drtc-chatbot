"""Use case: parse a version WITHOUT storing anything, for the reviewer's spot check."""

import random
from dataclasses import dataclass

from drtc_chatbot.contexts.ingestion.application.commands.run_ingestion import (
    ParsedTarget,
    parse_target,
)
from drtc_chatbot.contexts.ingestion.application.ports import CorpusGateway, PdfTextExtractor
from drtc_chatbot.contexts.ingestion.domain.parsing.model import (
    ParsedKind,
    ParsedProvision,
    RevisionStatus,
)
from drtc_chatbot.shared_kernel.domain import NotFoundError


@dataclass(frozen=True, slots=True)
class Preview:
    parsed: ParsedTarget
    sample: tuple[ParsedProvision, ...]


class PreviewIngestion:
    def __init__(self, gateway: CorpusGateway, extractor: PdfTextExtractor) -> None:
        self._gateway = gateway
        self._extractor = extractor

    async def execute(
        self, version_id: str, *, sample_size: int = 20, seed: int | None = None
    ) -> Preview:
        target = next(
            (t for t in await self._gateway.targets() if t.version_id == version_id), None
        )
        if target is None:
            raise NotFoundError(f"Unknown instrument version: {version_id}")
        parsed = parse_target(target, self._extractor)
        pool = [
            p
            for p in parsed.result.provisions
            if p.status is RevisionStatus.CURRENT and p.kind is not ParsedKind.SECTION and p.text
        ]
        chosen = random.Random(seed).sample(pool, min(sample_size, len(pool)))
        return Preview(parsed, tuple(sorted(chosen, key=lambda p: p.ordinal)))
