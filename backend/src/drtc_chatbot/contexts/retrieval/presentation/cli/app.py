"""``drtc-retrieval``: evaluate and operate the content search (spec 004; messages in Spanish)."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import Annotated, Protocol, TypeVar

import typer

from drtc_chatbot.contexts.retrieval.application.build_index import BuildIndex
from drtc_chatbot.contexts.retrieval.application.ports import (
    EvaluationStore,
    GoldenSet,
    PassageIndex,
    Retriever,
)
from drtc_chatbot.contexts.retrieval.application.run_evaluation import RunEvaluation
from drtc_chatbot.contexts.retrieval.domain.evaluation import MethodReport
from drtc_chatbot.contexts.retrieval.domain.metrics import (
    BASELINE_TOLERANCE,
    DEFAULT_KS,
    compare_to_baseline,
)
from drtc_chatbot.contexts.retrieval.domain.query import validate_query
from drtc_chatbot.contexts.retrieval.presentation.cli.render import render_markdown
from drtc_chatbot.shared_kernel.application import Actor, ActorKind, Clock
from drtc_chatbot.shared_kernel.domain import DomainError

T = TypeVar("T")
ACTOR = Actor("cli", ActorKind.SERVICE)


class RetrievalCliModule(Protocol):
    @property
    def run_evaluation(self) -> RunEvaluation: ...
    @property
    def build_index(self) -> BuildIndex: ...
    @property
    def passage_index(self) -> PassageIndex: ...
    @property
    def retrievers(self) -> Mapping[str, Retriever]: ...
    @property
    def default_dataset(self) -> Path: ...
    @property
    def store(self) -> EvaluationStore: ...
    @property
    def clock(self) -> Clock: ...

    def golden_set(self, path: Path) -> GoldenSet: ...


ModuleFactory = Callable[[], AbstractAsyncContextManager[RetrievalCliModule]]


def _parse_ks(text: str) -> tuple[int, ...]:
    try:
        ks = tuple(sorted({int(part) for part in text.split(",") if part.strip()}))
    except ValueError as error:
        raise typer.BadParameter("K debe ser una lista de enteros, p. ej. 1,3,5,10.") from error
    if not ks or ks[0] < 1:
        raise typer.BadParameter("K debe ser una lista de enteros positivos, p. ej. 1,3,5,10.")
    return ks


def _print_summary(report: MethodReport, ks: tuple[int, ...]) -> None:
    typer.secho(
        f"{report.method}: {report.questions} preguntas ({report.answerable} con respuesta) · "
        f"p50 {report.latency_ms['p50']:g} ms · p95 {report.latency_ms['p95']:g} ms",
        bold=True,
    )
    for name, metrics in (
        ("unidad", report.overall.unit),
        ("disposición", report.overall.provision),
    ):
        hits = " ".join(f"@{k} {metrics.hit[k] * 100:.0f}%" for k in ks)
        typer.echo(f"  {name:12} acierto {hits} · MRR {metrics.mrr:.3f}")
    for tag, sliced in report.by_tag.items():
        typer.echo(
            f"  etiqueta {tag}: acierto@1 (unidad) {sliced.unit.hit.get(1, 0) * 100:.0f}% de {sliced.unit.n}"
        )
    if report.degraded_questions:
        typer.secho(f"  {report.degraded_questions} preguntas degradadas", fg=typer.colors.YELLOW)


def build_app(factory: ModuleFactory) -> typer.Typer:
    app = typer.Typer(
        help="Búsqueda por contenido: evaluación y operación (Spec 004).", no_args_is_help=True
    )

    def run(action: Callable[[RetrievalCliModule], Awaitable[T]]) -> T:
        async def main() -> T:
            async with factory() as module:
                return await action(module)

        try:
            return asyncio.run(main())
        except DomainError as error:
            typer.secho(f"Error: {error.message}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from error

    @app.callback()
    def main() -> None:
        """Búsqueda por contenido: evaluación y operación (Spec 004)."""

    @app.command("index")
    def index_cmd() -> None:
        """Prepara el índice de la búsqueda con las ediciones aprobadas (se puede repetir sin riesgo)."""

        async def action(module: RetrievalCliModule) -> None:
            stats = await module.build_index.execute(ACTOR)
            typer.secho(
                f"Índice al día: {stats.total} pasajes · {stats.added} agregados, {stats.changed} "
                f"cambiados, {stats.removed} borrados, {stats.unchanged} sin cambios.",
                bold=True,
            )

        run(action)

    @app.command("search")
    def search_cmd(
        text: Annotated[str, typer.Argument(help="Lo que se busca, con sus propias palabras.")],
        limit: Annotated[
            int, typer.Option("--limit", min=1, max=30, help="Resultados a mostrar.")
        ] = 10,
    ) -> None:
        """Busca por palabras en el índice (mismas reglas que la búsqueda de la aplicación)."""
        query = validate_query(text)

        async def action(module: RetrievalCliModule) -> None:
            hits = await module.passage_index.lexical_search(query, instrument_id=None, limit=limit)
            if not hits:
                typer.echo("Sin coincidencias.")
            for number, hit in enumerate(hits, start=1):
                passage = hit.passage
                shown = "".join(f"**{s.text}**" if s.match else s.text for s in hit.snippet)
                typer.secho(
                    f"{number:>2}. {passage.citation} · p. {passage.page_start}  [{hit.score:.3f}]",
                    bold=True,
                )
                typer.echo(f"    {shown}")

        run(action)

    @app.command("eval")
    def evaluate(
        dataset: Annotated[
            Path | None, typer.Option(help="Archivo JSONL del golden set (por defecto golden-v1).")
        ] = None,
        modes: Annotated[
            str, typer.Option(help="Métodos a evaluar, separados por coma (exact, lexical, …).")
        ] = "exact",
        k: Annotated[
            str, typer.Option("--k", help="Valores de K, separados por coma.")
        ] = "1,3,5,10",
        out: Annotated[
            Path | None,
            typer.Option("--out", help="Directorio donde escribir el informe .json/.md."),
        ] = None,
        check_baseline: Annotated[
            bool,
            typer.Option(
                "--check-baseline", help="Falla si algo empeora respecto de la línea base."
            ),
        ] = False,
        write_baseline_option: Annotated[
            bool,
            typer.Option("--write-baseline", help="Fija estas cifras como la nueva línea base."),
        ] = False,
        reason: Annotated[
            str | None,
            typer.Option("--reason", help="Motivo del cambio de línea base (obligatorio)."),
        ] = None,
        tolerance: Annotated[
            float, typer.Option(help="Caída permitida antes de fallar.")
        ] = BASELINE_TOLERANCE,
    ) -> None:
        """Mide uno o más métodos con el golden set y, si se pide, compara con la línea base."""
        ks = _parse_ks(k)
        if (check_baseline or write_baseline_option) and ks != DEFAULT_KS:
            raise typer.BadParameter("La línea base usa K=1,3,5,10: no cambie --k al compararla.")
        if write_baseline_option and not (reason and reason.strip()):
            raise typer.BadParameter("--write-baseline exige --reason con el motivo del cambio.")
        names = [m.strip() for m in modes.split(",") if m.strip()]

        async def action(module: RetrievalCliModule) -> int:
            unknown = [n for n in names if n not in module.retrievers]
            if unknown:
                raise typer.BadParameter(
                    f"Método desconocido: {', '.join(unknown)}. Disponibles: {', '.join(module.retrievers)}."
                )
            path = dataset or module.default_dataset
            questions = list(module.golden_set(path).load())
            reports = [
                await module.run_evaluation.execute(
                    ACTOR, module.retrievers[name], questions, ks=ks
                )
                for name in names
            ]
            today = module.clock.now().date()
            for report in reports:
                _print_summary(report, ks)
            if out is not None:
                json_path, md_path = module.store.write_report(
                    out, "+".join(names), recorded_on=today,
                    payload={"dataset": path.stem, "recorded_on": today.isoformat(), "ks": list(ks),
                             "methods": {r.method: r.as_dict() for r in reports}},
                    markdown=render_markdown(title="Informe de evaluación de la búsqueda", dataset=path.stem,
                                             recorded_on=today.isoformat(), reports=reports, ks=ks),
                )  # fmt: skip
                typer.echo(f"Informe: {json_path} y {md_path}")
            if write_baseline_option:
                content = module.store.write_baseline(reports, dataset=path.stem, recorded_on=today,
                                         questions=len(questions))  # fmt: skip
                summary = {
                    r.method: f"unidad acierto@10 {r.overall.unit.hit[10] * 100:.0f} %, MRR {r.overall.unit.mrr:.3f}"
                    for r in reports
                }
                module.store.append_changelog(recorded_on=today,
                                 reason=reason or "", summary=summary)  # fmt: skip
                typer.secho(f"Línea base escrita ({len(content['methods'])} métodos) y registrada en CHANGELOG.md.",
                            fg=typer.colors.GREEN)  # fmt: skip
            if check_baseline:
                baseline = module.store.read_baseline()
                regressions = compare_to_baseline(reports, baseline["methods"], tolerance)
                if regressions:
                    typer.secho("EMPEORÓ respecto de la línea base:", fg=typer.colors.RED, err=True)
                    for regression in regressions:
                        typer.echo(f"  - {regression.describe()}", err=True)
                    return 1
                typer.secho("Sin empeoramientos respecto de la línea base.", fg=typer.colors.GREEN)
            return 0

        code = run(action)
        if code:
            raise typer.Exit(code)

    return app
