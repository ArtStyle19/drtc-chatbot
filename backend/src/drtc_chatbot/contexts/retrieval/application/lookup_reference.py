"""Use case: find a provision by the legal reference a person typed (``art. 5 Ley 27181``).

Deterministic and exact (constitution I.6): no similarity, no guessing. When a reference could mean
several things (an article 5 exists in every norm) every candidate is returned and the person
chooses; when it names a norm we do not have, we say so instead of searching the others.
"""

from drtc_chatbot.contexts.retrieval.application.dto import LookupHit, LookupResult, LookupStatus
from drtc_chatbot.contexts.retrieval.application.ports import IndexedEdition, ProvisionDirectory
from drtc_chatbot.contexts.retrieval.domain.matching import matches
from drtc_chatbot.contexts.retrieval.domain.norms import NormIndex, NormInfo
from drtc_chatbot.contexts.retrieval.domain.reference import Step, parse_steps
from drtc_chatbot.contexts.retrieval.domain.text import normalize
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError

MAX_QUERY_LENGTH = 200
MAX_HITS = 20
EXAMPLES = "«art. 5 Ley 27181», «218.2 TUO», «anexo 2 RENAT» o «primera disposición final LGTTT»"
# Words that may surround a reference without being part of it ("el art. 5 de la ley ...").
_FILLER = frozenset(
    [
        "a",
        "al",
        "con",
        "de",
        "del",
        "dice",
        "el",
        "en",
        "la",
        "las",
        "lo",
        "los",
        "norma",
        "ley",
        "decreto",
        "supremo",
        "reglamento",
        "texto",
        "unico",
        "ordenado",
        "para",
        "por",
        "favor",
        "que",
        "quiero",
        "busco",
        "ver",
        "segun",
        "se",
        "y",
        "e",
        "o",
        "u",
        "mostrar",
        "muestrame",
        "abrir",
        "ir",
    ]
)


class LookupReference:
    def __init__(self, directory: ProvisionDirectory) -> None:
        self._directory = directory

    async def execute(self, actor: Actor, query: str) -> LookupResult:
        text = query.strip()
        if not text:
            raise InvariantViolationError("The reference to look up is empty")
        if len(text) > MAX_QUERY_LENGTH:
            raise InvariantViolationError(
                f"The reference is longer than {MAX_QUERY_LENGTH} characters"
            )
        norms = list(await self._directory.norms(actor))
        by_id = {norm.instrument_id: norm for norm in norms}
        mentions = NormIndex(norms).find(normalize(text))
        parsed = parse_steps(mentions.remainder)
        named = tuple(by_id[i].short_name for i in mentions.instrument_ids)
        words = self._meaningful_words(parsed.leftover, mentions.unknown)

        if mentions.unknown and not mentions.instrument_ids:
            return self._result(
                LookupStatus.NOT_FOUND, text, norms=named,
                message=f"No reconozco la norma «{mentions.unknown}». Normas disponibles: "
                f"{'; '.join(n.short_name for n in norms)}.",
            )  # fmt: skip
        if not parsed.steps:
            if mentions.instrument_ids and not words:
                return self._whole_norms(text, [by_id[i] for i in mentions.instrument_ids])
            return self._result(
                LookupStatus.UNRECOGNIZED, text, norms=named,
                message=f"Por ahora solo busco por referencia: pruebe {EXAMPLES}. "
                "La búsqueda por significado llegará en una próxima versión.",
            )  # fmt: skip
        return await self._search(actor, text, norms, mentions.instrument_ids, parsed.steps, words)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _meaningful_words(leftover: str, unknown: str | None) -> str:
        words = [w for w in leftover.split() if w not in _FILLER]
        if unknown:
            dropped = set(unknown.split())
            words = [w for w in words if w not in dropped]
        return " ".join(words)

    @staticmethod
    def _result(status: LookupStatus, query: str, *, message: str = "", reference: str | None = None,
                norms: tuple[str, ...] = (), hits: tuple[LookupHit, ...] = (), total: int = 0,
                ignored: str | None = None) -> LookupResult:  # fmt: skip
        return LookupResult(status, query, message, reference, norms, total, hits, ignored or None)

    def _whole_norms(self, query: str, norms: list[NormInfo]) -> LookupResult:
        hits = tuple(
            LookupHit(n.instrument_id, n.short_name, n.title, citation=n.short_name) for n in norms
        )
        status = LookupStatus.RESOLVED if len(hits) == 1 else LookupStatus.AMBIGUOUS
        message = "" if len(hits) == 1 else "Varias normas coinciden con ese nombre; elija una."
        return self._result(status, query, message=message, norms=tuple(n.short_name for n in norms),
                            hits=hits, total=len(hits))  # fmt: skip

    async def _search(self, actor: Actor, query: str, norms: list[NormInfo], mentioned: tuple[str, ...],
                      steps: tuple[Step, ...], ignored: str) -> LookupResult:  # fmt: skip
        reference = ", ".join(step.describe() for step in steps)
        targets = [n for n in norms if not mentioned or n.instrument_id in mentioned]
        hits: list[LookupHit] = []
        editions: dict[str, IndexedEdition] = {}
        for norm in targets:
            edition = await self._directory.edition(actor, norm.instrument_id)
            if edition is None:
                continue
            editions[norm.instrument_id] = edition
            hits.extend(self._hits(norm, edition, steps))
        named = tuple(n.short_name for n in targets) if mentioned else ()
        total = len(hits)
        shown = tuple(hits[:MAX_HITS])
        if total == 0:
            message = self._not_found_message(
                reference, targets, editions, explicit=bool(mentioned)
            )
            return self._result(LookupStatus.NOT_FOUND, query, reference=reference, norms=named,
                                ignored=ignored, message=message)  # fmt: skip
        status = LookupStatus.RESOLVED if total == 1 else LookupStatus.AMBIGUOUS
        message = ""
        if total > 1:
            message = f"{total} disposiciones coinciden con «{reference}»; elija una."
            if total > MAX_HITS:
                message += f" Se muestran las primeras {MAX_HITS}."
        return self._result(status, query, reference=reference, norms=named, hits=shown, total=total,
                            message=message, ignored=ignored)  # fmt: skip

    @staticmethod
    def _hits(norm: NormInfo, edition: IndexedEdition, steps: tuple[Step, ...]) -> list[LookupHit]:
        return [
            LookupHit(
                instrument_id=norm.instrument_id, instrument_short_name=norm.short_name,
                instrument_title=norm.title, citation=entry.citation, version_id=edition.version_id,
                edition_label=edition.edition_label, verification_status=edition.verification_status,
                path=entry.path, unit_path=entry.unit_path, kind=entry.kind, label=entry.label,
                title=entry.title, snippet=entry.snippet, page_start=entry.page_start,
            )
            for entry, match_path in edition.match_paths()
            if matches(match_path, steps)
        ]  # fmt: skip

    @staticmethod
    def _not_found_message(
        reference: str,
        targets: list[NormInfo],
        editions: dict[str, IndexedEdition],
        *,
        explicit: bool,
    ) -> str:
        if not editions:
            return "Ninguna de las normas tiene una edición aprobada todavía."
        if not explicit:
            return f"Ninguna norma del corpus tiene «{reference}»."
        parts = []
        for norm in targets:
            edition = editions.get(norm.instrument_id)
            if edition is None:
                parts.append(f"{norm.short_name} no tiene una edición aprobada todavía")
            else:
                parts.append(
                    f"{norm.short_name} no tiene «{reference}» en la edición cargada "
                    f"({edition.edition_label})"
                )
        return "; ".join(parts) + "."
