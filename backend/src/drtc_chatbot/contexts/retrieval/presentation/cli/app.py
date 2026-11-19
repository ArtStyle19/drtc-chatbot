"""``drtc-retrieval``: evaluate and operate the content search (spec 004; messages in Spanish)."""

import asyncio
import sys
from collections.abc import Awaitable, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import replace
from pathlib import Path
from typing import Annotated, Protocol, TypeVar

import typer

from drtc_chatbot.contexts.retrieval.application.build_index import BuildIndex
from drtc_chatbot.contexts.retrieval.application.dto import SearchMode
from drtc_chatbot.contexts.retrieval.application.embed_passages import EmbedPassages
from drtc_chatbot.contexts.retrieval.application.ports import (
    EmbeddingProvider,
    EvaluationStore,
    GoldenSet,
    PassageIndex,
    Retriever,
)
from drtc_chatbot.contexts.retrieval.application.run_evaluation import RunEvaluation
from drtc_chatbot.contexts.retrieval.application.search_passages import SearchPassages
from drtc_chatbot.contexts.retrieval.domain.evaluation import GoldenQuestion, MethodReport
from drtc_chatbot.contexts.retrieval.domain.metrics import (
    BASELINE_TOLERANCE,
    DEFAULT_KS,
    compare_to_baseline,
)
from drtc_chatbot.contexts.retrieval.domain.pricing import estimate_cost_usd, estimate_tokens
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
    def embed_passages(self) -> EmbedPassages | None: ...
    @property
    def embedding(self) -> EmbeddingProvider | None: ...
    @property
    def search_passages(self) -> SearchPassages: ...
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


NEEDS_MEANING = frozenset({"vector", "hybrid"})
_DEGRADED_TEXT = {
    "vector_unavailable": "la búsqueda por significado no está disponible; se muestran coincidencias de palabras.",
    "vector_not_indexed": "aún no se calcularon los vectores (ejecute `drtc-retrieval embed`); se muestran coincidencias de palabras.",
}
NO_PROVIDER = (
    "No hay proveedor de significado: ponga DRTC_OPENAI_API_KEY en su archivo .env "
    "(nunca en el código ni en la línea de comandos)."
)


def _money(value: float | None) -> str:
    return "precio desconocido" if value is None else f"≈ {value:.4f} USD"


def _confirm_sending(*, yes: bool, what: str) -> None:
    """Nothing leaves the server without a visible estimate and an explicit yes (FR-005)."""
    if yes:
        return
    if sys.stdin.isatty():
        if typer.confirm(f"{what} ¿Continuar?", default=False):
            return
        raise typer.Exit(1)
    typer.secho(
        "Nada se envió. Para continuar sin preguntar, repita con --yes.",
        fg=typer.colors.YELLOW,
        err=True,
    )
    raise typer.Exit(2)


def _question_cost(
    provider: EmbeddingProvider, questions: Sequence[GoldenQuestion]
) -> tuple[int, float | None]:
    tokens = estimate_tokens(sum(len(q.text) for q in questions))
    return tokens, estimate_cost_usd(tokens, provider.model)


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

    @app.command("embed")
    def embed_cmd(
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Solo estima: no envía nada.")
        ] = False,
        yes: Annotated[
            bool, typer.Option("--yes", help="Confirma el envío (sin esto se pide confirmación).")
        ] = False,
        limit: Annotated[
            int | None, typer.Option("--limit", min=1, help="Solo las N primeras ventanas.")
        ] = None,
    ) -> None:
        """Calcula los vectores de los pasajes que no tienen (muestra antes el costo estimado)."""

        async def action(module: RetrievalCliModule) -> None:
            embed, provider = module.embed_passages, module.embedding
            if embed is None or provider is None:
                typer.secho(f"Error: {NO_PROVIDER}", fg=typer.colors.RED, err=True)
                raise typer.Exit(1)
            verify = getattr(provider, "verify", None)
            if provider.external and verify is not None:
                await verify()  # the model exists for this key (free: it lists, it does not embed)
            plan = await embed.plan(limit=limit)
            destination = (
                "se enviarían a un servicio externo"
                if plan.external
                else "se calcularían en este servidor"
            )
            typer.secho(f"Modelo: {plan.model}", bold=True)
            typer.echo(
                f"Pendientes: {plan.windows} fragmentos · {plan.characters:,} caracteres · "
                f"≈ {plan.tokens:,} tokens (cota superior) · costo {_money(plan.cost_usd)} · {destination}."
            )
            if plan.windows == 0:
                typer.secho(
                    "No hay nada pendiente: todos los pasajes ya tienen su vector.",
                    fg=typer.colors.GREEN,
                )
                return
            if dry_run:
                typer.echo("(--dry-run: no se envió nada)")
                return
            if plan.external:
                _confirm_sending(
                    yes=yes,
                    what=f"Se enviarán {plan.windows} fragmentos del corpus (texto público de las normas).",
                )
            outcome = await embed.run(
                limit=limit, progress=lambda done, total: typer.echo(f"  {done}/{total} fragmentos")
            )
            typer.secho(
                f"Listo: {outcome.windows} fragmentos en {outcome.batches} lotes · {outcome.tokens:,} tokens reales "
                f"(estimado {plan.tokens:,}) · costo {_money(outcome.cost_usd)}.",
                fg=typer.colors.GREEN,
            )

        run(action)

    @app.command("search")
    def search_cmd(
        text: Annotated[str, typer.Argument(help="Lo que se busca, con sus propias palabras.")],
        limit: Annotated[
            int, typer.Option("--limit", min=1, max=30, help="Resultados a mostrar.")
        ] = 10,
        mode: Annotated[
            SearchMode, typer.Option("--mode", help="hybrid | lexical | vector")
        ] = SearchMode.HYBRID,
        debug: Annotated[
            bool, typer.Option("--debug", help="Muestra qué método halló cada resultado.")
        ] = False,
    ) -> None:
        """Busca con las mismas reglas que la aplicación: referencia, palabras y significado."""

        async def action(module: RetrievalCliModule) -> None:
            response = await module.search_passages.execute(
                ACTOR, text, limit=limit, mode=mode, debug=debug
            )
            if response.reference:
                typer.echo(f"Entendí la referencia: {response.reference}")
            for code in response.degraded:
                typer.secho(f"Aviso: {_DEGRADED_TEXT.get(code, code)}", fg=typer.colors.YELLOW)
            if not response.results:
                typer.echo("Sin coincidencias.")
            for number, result in enumerate(response.results, start=1):
                marks = "+".join(result.via)
                typer.secho(
                    f"{number:>2}. [{marks}] {result.citation} · p. {result.page_start}", bold=True
                )
                typer.echo(
                    f"    {result.instrument_short_name} · {result.edition_label} · {result.verification_status}"
                )
                shown = "".join(f"**{s.text}**" if s.match else s.text for s in result.snippet)
                if shown:
                    typer.echo(f"    {shown}")
                if debug and result.debug:
                    typer.echo(f"    debug: {result.debug}")
            typer.echo(f"{response.total} resultados · {response.latency_ms:g} ms")

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
        yes: Annotated[
            bool,
            typer.Option("--yes", help="Confirma el envío de las preguntas al proveedor externo."),
        ] = False,
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
            provider = module.embedding
            meaning = [n for n in names if n in NEEDS_MEANING]
            if meaning and provider is None:
                typer.secho(
                    f"Error: {', '.join(meaning)} {NO_PROVIDER}", fg=typer.colors.RED, err=True
                )
                raise typer.Exit(1)
            if meaning and provider is not None:
                if await module.passage_index.embedded_passages(provider.model) == 0:
                    typer.secho(
                        f"Error: no hay vectores del modelo {provider.model}: ejecute `drtc-retrieval embed`.",
                        fg=typer.colors.RED,
                        err=True,
                    )
                    raise typer.Exit(1)
                if provider.external:
                    tokens, cost = _question_cost(provider, questions)
                    typer.echo(
                        f"Se enviarán {len(questions)} preguntas a {provider.model}: ≈ {tokens:,} tokens, "
                        f"costo {_money(cost)} por método ({', '.join(meaning)})."
                    )
                    _confirm_sending(
                        yes=yes, what="Los textos de las preguntas salen del servidor."
                    )
            before = provider.tokens_used if provider else 0
            reports = [
                await module.run_evaluation.execute(
                    ACTOR, module.retrievers[name], questions, ks=ks
                )
                for name in names
            ]
            if meaning and provider is not None:
                used = provider.tokens_used - before
                cost = estimate_cost_usd(used, provider.model)
                info = {"model": provider.model, "tokens": used, "estimated_cost_usd": cost}
                reports = [
                    replace(r, extra={"provider": info}) if r.method in NEEDS_MEANING else r
                    for r in reports
                ]
                typer.echo(f"Uso real del proveedor: {used:,} tokens · costo {_money(cost)}.")
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
