"""GoldenSet adapter: ``evaluation/datasets/*.jsonl`` (one question per line, schema v1)."""

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from drtc_chatbot.contexts.retrieval.domain.evaluation import GoldenCitation, GoldenQuestion
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class JsonlGoldenSet:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> Sequence[GoldenQuestion]:
        try:
            lines = self._path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError as error:
            raise InvariantViolationError(f"Golden set not found: {self._path}") from error
        questions = [
            self._parse(json.loads(line), number)
            for number, line in enumerate(lines, 1)
            if line.strip()
        ]
        ids = [q.id for q in questions]
        if len(ids) != len(set(ids)):
            raise InvariantViolationError(f"Duplicated question ids in {self._path.name}")
        return questions

    @staticmethod
    def _parse(raw: dict[str, Any], line: int) -> GoldenQuestion:
        try:
            return GoldenQuestion(
                id=raw["id"],
                text=raw["question"],
                intent=raw["intent"],
                answerable=bool(raw["answerable"]),
                review_status=raw["review_status"],
                tags=tuple(raw.get("tags", ())),
                citations=tuple(
                    GoldenCitation(c["version_id"], c["path"], c["provision"])
                    for c in raw["expected"]["citations"]
                ),
            )
        except KeyError as error:
            raise InvariantViolationError(f"Line {line}: missing field {error}") from error
