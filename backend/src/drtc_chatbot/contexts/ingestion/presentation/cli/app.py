"""``drtc-ingest``: ingest the corpus PDFs into reviewable provisions (messages in Spanish)."""

import asyncio
import json
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import Annotated, Protocol, TypeVar

import typer

from drtc_chatbot.contexts.ingestion.application.commands.preview_ingestion import PreviewIngestion
from drtc_chatbot.contexts.ingestion.application.commands.run_ingestion import RunIngestion
from drtc_chatbot.contexts.ingestion.application.ports import (
    CorpusGateway,
    IngestionJobRepository,
)
from drtc_chatbot.contexts.ingestion.domain.review_report import ReviewReport
from drtc_chatbot.shared_kernel.domain import DomainError

T = TypeVar("T")
_PREVIEW = 400  # characters of a provision shown by `sample`


class IngestionCliModule(Protocol):
    @property
    def run_ingestion(self) -> RunIngestion: ...
    @property
    def preview(self) -> PreviewIngestion: ...
    @property
    def gateway(self) -> CorpusGateway: ...
    @property
    def jobs(self) -> IngestionJobRepository: ...


ModuleFactory = Callable[[], AbstractAsyncContextManager[IngestionCliModule]]


def _print_report(report: ReviewReport) -> None:
    typer.echo(f"  Páginas normativas: {', '.join(f'{a}-{b}' for a, b in report.pages)}")
    kinds = ", ".join(f"{k}: {v}" for k, v in sorted(report.current_by_kind.items()))
    typer.echo(f"  Vigentes por tipo: {kinds}")
    typer.echo(f"  Textos sustituidos: {report.superseded} · notas editoriales: {report.notes}")
    typer.echo(
        f"  Artículos numerados: {report.numeric_articles}"
        + (f" · FALTAN: {list(report.article_gaps)}" if report.article_gaps else " (sin saltos)")
    )
    if report.anomalies_by_code:
        typer.secho("  A REVISAR:", fg=typer.colors.YELLOW)
        for code, count in sorted(report.anomalies_by_code.items()):
            typer.echo(f"    - {code}: {count}")
            for sample in report.anomaly_samples.get(code, [])[:2]:
                typer.echo(
                    f"        p. {sample['page']} {sample['path'] or ''} | {sample['excerpt'][:70]}"
                )
    else:
        typer.secho("  Sin anomalías.", fg=typer.colors.GREEN)


def build_app(factory: ModuleFactory) -> typer.Typer:
    app = typer.Typer(help="Ingesta del corpus normativo (Spec 002).", no_args_is_help=True)

    def run(action: Callable[[IngestionCliModule], Awaitable[T]]) -> T:
        async def main() -> T:
            async with factory() as module:
                return await action(module)

        try:
            return asyncio.run(main())
        except DomainError as error:
            typer.secho(f"Error: {error.message}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1) from error

    @app.command()
    def sync() -> None:
        """Carga el manifiesto (normas, versiones, documentos fuente) en la base de datos."""
        count = run(lambda m: m.gateway.sync_manifest())
        typer.echo(f"Manifiesto sincronizado: {count} versiones.")

    @app.command("run")
    def run_cmd(
        version_id: Annotated[
            str | None, typer.Argument(help="Id de la versión (ver `sync`).")
        ] = None,
        all_versions: Annotated[
            bool, typer.Option("--all", help="Ingerir todas las versiones.")
        ] = False,
    ) -> None:
        """Extrae, analiza y publica las disposiciones de una versión (o de todas)."""
        if bool(version_id) == all_versions:
            raise typer.BadParameter("Indique una versión o use --all.")

        async def action(module: IngestionCliModule) -> None:
            ids = (
                [t.version_id for t in await module.gateway.targets()]
                if all_versions
                else [version_id or ""]
            )
            for vid in ids:
                outcome = await module.run_ingestion.execute(vid)
                state = "actualizada" if outcome.changed else "sin cambios"
                typer.secho(f"{vid}: {state} (digest {outcome.content_digest[:12]})", bold=True)
                _print_report(outcome.report)
                if outcome.approval:
                    typer.secho(
                        f"  Aprobada automáticamente ({outcome.approval.mode}): solo desarrollo.",
                        fg=typer.colors.YELLOW,
                    )
                else:
                    typer.echo("  Pendiente de aprobación: use `drtc-ingest approve`.")

        run(action)

    @app.command()
    def report(version_id: str) -> None:
        """Muestra el reporte de la última ingesta de una versión."""

        async def action(module: IngestionCliModule) -> None:
            job = await module.jobs.latest(version_id)
            if job is None:
                typer.echo("No hay ingestas registradas para esa versión.")
                raise typer.Exit(1)
            typer.echo(f"{job.version_id} · {job.status.value} · {job.started_at:%Y-%m-%d %H:%M}")
            typer.echo(json.dumps(job.report, ensure_ascii=False, indent=2))

        run(action)

    @app.command()
    def approve(
        version_id: str,
        reviewer: Annotated[str, typer.Option("--reviewer", help="Nombre de quien revisó.")],
    ) -> None:
        """Aprueba una versión ingerida (revisión humana). No cambia su estado de vigencia."""
        outcome = run(lambda m: m.gateway.approve(version_id, reviewer))
        typer.echo(f"{version_id} aprobada por {outcome.approved_by} ({outcome.mode}).")

    @app.command()
    def sample(
        version_id: str,
        count: Annotated[int, typer.Option("-n", help="Cantidad de disposiciones.")] = 20,
        seed: Annotated[int | None, typer.Option(help="Semilla para repetir la muestra.")] = None,
    ) -> None:
        """Muestra disposiciones al azar (sin guardar nada) para revisarlas contra el PDF."""

        async def action(module: IngestionCliModule) -> None:
            preview = await module.preview.execute(version_id, sample_size=count, seed=seed)
            typer.secho(
                f"Muestra de {len(preview.sample)} disposiciones de {version_id}", bold=True
            )
            for p in preview.sample:
                pages = (
                    f"p. {p.page_start}"
                    if p.page_start == p.page_end
                    else f"pp. {p.page_start}-{p.page_end}"
                )
                typer.secho(f"\n[{pages}] {p.path}", fg=typer.colors.CYAN)
                if p.title:
                    typer.echo(f"  Título: {p.title}")
                typer.echo(f"  {p.text[:_PREVIEW]}{'…' if len(p.text) > _PREVIEW else ''}")

        run(action)

    return app
