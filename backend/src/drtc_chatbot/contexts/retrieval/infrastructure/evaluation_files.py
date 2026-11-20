"""Files of the evaluation: reports, the committed baseline and its changelog (``evaluation/``)."""

import json
from collections.abc import Iterable, Mapping
from datetime import date
from pathlib import Path
from typing import Any

from drtc_chatbot.contexts.retrieval.domain.evaluation import MethodReport
from drtc_chatbot.contexts.retrieval.domain.metrics import baseline_of
from drtc_chatbot.shared_kernel.domain import InvariantViolationError

CHANGELOG_HEADER = """# Registro de cambios de la línea base de evaluación

Cada vez que cambia `baseline.json` se agrega aquí una entrada con la fecha, el motivo y las cifras
nuevas (lo hace `drtc-retrieval eval --write-baseline --reason "…"`). La compuerta de CI compara contra
esa línea base: empeorar más que la tolerancia falla; cambiar la línea base exige dejar esta constancia.

"""


def read_baseline(path: Path) -> dict[str, Any]:
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError as error:
        raise InvariantViolationError(
            f"No hay línea base en {path}: ejecute `drtc-retrieval eval --write-baseline --reason …`."
        ) from error


def write_baseline(
    path: Path,
    reports: Iterable[MethodReport],
    *,
    dataset: str,
    recorded_on: date,
    questions: int,
) -> dict[str, Any]:
    """Pins the evaluated methods; methods already pinned and not re-evaluated are kept as they were."""
    try:
        existing = read_baseline(path)
    except InvariantViolationError:
        existing = {"methods": {}}
    methods: dict[str, Any] = dict(existing.get("methods", {}))
    methods.update(baseline_of(reports))
    content = {
        "dataset": dataset,
        "recorded_on": recorded_on.isoformat(),
        "questions": questions,
        "methods": dict(sorted(methods.items())),
    }
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return content


def append_changelog(
    path: Path, *, recorded_on: date, reason: str, summary: Mapping[str, str]
) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else CHANGELOG_HEADER
    lines = [f"## {recorded_on.isoformat()}", "", reason.strip(), ""]
    lines += [f"- **{method}**: {numbers}" for method, numbers in summary.items()]
    path.write_text(text.rstrip("\n") + "\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def write_report(
    directory: Path, label: str, *, recorded_on: date, payload: Mapping[str, Any], markdown: str
) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{recorded_on.isoformat()}-{label}"
    json_path, md_path = directory / f"{stem}.json", directory / f"{stem}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


class FileEvaluationStore:
    """EvaluationStore over the ``evaluation/`` directory of the repository."""

    def __init__(self, evaluation_dir: Path) -> None:
        self._baseline = evaluation_dir / "baseline.json"
        self._changelog = evaluation_dir / "CHANGELOG.md"

    def read_baseline(self) -> Mapping[str, Any]:
        return read_baseline(self._baseline)

    def write_baseline(
        self, reports: Iterable[MethodReport], *, dataset: str, recorded_on: date, questions: int
    ) -> Mapping[str, Any]:
        return write_baseline(
            self._baseline, reports, dataset=dataset, recorded_on=recorded_on, questions=questions
        )

    def append_changelog(
        self, *, recorded_on: date, reason: str, summary: Mapping[str, str]
    ) -> None:
        append_changelog(self._changelog, recorded_on=recorded_on, reason=reason, summary=summary)

    def write_report(
        self,
        directory: Path,
        label: str,
        *,
        recorded_on: date,
        payload: Mapping[str, Any],
        markdown: str,
    ) -> tuple[Path, Path]:
        return write_report(
            directory, label, recorded_on=recorded_on, payload=payload, markdown=markdown
        )
