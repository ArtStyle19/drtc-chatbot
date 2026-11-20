"""Markdown rendering of an evaluation report (Spanish, for the reviewer)."""

from collections.abc import Mapping, Sequence

from drtc_chatbot.contexts.retrieval.domain.evaluation import MethodReport, Metrics, SliceMetrics


def _pct(value: float) -> str:
    return f"{value * 100:.0f} %"


def _row(label: str, metrics: Metrics, ks: Sequence[int]) -> str:
    cells = [label, str(metrics.n)]
    cells += [_pct(metrics.hit[k]) for k in ks]
    cells.append(f"{metrics.mrr:.3f}")
    return "| " + " | ".join(cells) + " |"


def _table(
    title: str, rows: Mapping[str, SliceMetrics], ks: Sequence[int], level: str
) -> list[str]:
    head = ["Grupo", "Preguntas", *[f"Acierto@{k}" for k in ks], "MRR"]
    lines = [f"**{title}**", "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for label, sliced in rows.items():
        metrics = sliced.unit if level == "unit" else sliced.provision
        if metrics.n:  # a group with no scored question says nothing
            lines.append(_row(label, metrics, ks))
    return [*lines, ""]


def render_markdown(
    *,
    title: str,
    dataset: str,
    recorded_on: str,
    reports: Sequence[MethodReport],
    ks: Sequence[int],
) -> str:
    lines = [
        f"# {title}",
        "",
        f"Golden set: `{dataset}` · fecha: {recorded_on}. *Acierto@K* = porcentaje de preguntas con "
        "respuesta cuya disposición esperada aparece entre los K primeros resultados; *MRR* = rango "
        "recíproco medio. **Unidad** cuenta como acierto cualquier resultado del mismo artículo, "
        "disposición o anexo (lo que abre el lector); **disposición** exige la disposición esperada "
        "o una que esté debajo de ella.",
        "",
    ]
    for report in reports:
        lines += [
            f"## Método: {report.method}",
            "",
            f"{report.questions} preguntas ({report.answerable} con respuesta) · latencia p50 "
            f"{report.latency_ms['p50']:g} ms, p95 {report.latency_ms['p95']:g} ms",
        ]
        if report.degraded_questions:
            lines.append(f"· **{report.degraded_questions} preguntas degradadas**")
        lines.append("")
        for level, name in (
            ("unit", "Nivel unidad de lectura"),
            ("provision", "Nivel disposición"),
        ):
            groups = {"Todas": report.overall}
            groups.update({f"etiqueta: {k}": v for k, v in report.by_tag.items()})
            groups.update({f"intención: {k}": v for k, v in report.by_intent.items()})
            groups.update({f"revisión: {k}": v for k, v in report.by_review_status.items()})
            lines += _table(name, groups, ks, level)
        unanswerable = report.unanswerable
        lines.append(
            f"**Sin respuesta en el corpus**: {unanswerable['n']} preguntas; "
            f"{unanswerable['with_results']} devolvieron algún resultado."
        )
        if "top_score" in unanswerable:
            lines.append(f"Mejor puntaje devuelto: {unanswerable['top_score']}.")
        lines.append("")
        if report.worst:
            lines += ["**Peor resueltas** (las que no quedaron en 1.er lugar):", ""]
            for item in report.worst:
                lines.append(
                    f"- `{item['id']}` {item['question']} — esperada: {', '.join(item['expected'])} · "  # type: ignore[arg-type]
                    f"rangos de unidad: {item['unit_ranks']} · devolvió: {', '.join(item['top']) or '—'}"  # type: ignore[arg-type]
                )
            lines.append("")
    return "\n".join(lines)
