"""HTTP response models of the reference search (the public API contract, in Spanish)."""

from pydantic import BaseModel, ConfigDict, Field

from drtc_chatbot.contexts.retrieval.application.dto import LookupHit, LookupResult, LookupStatus


class LookupHitOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    instrument_short_name: str
    instrument_title: str
    citation: str = Field(description="Cita breve generada por el servidor.")
    version_id: str | None = Field(description="Edición aprobada en la que se encontró.")
    edition_label: str | None
    verification_status: str | None = Field(
        description="Estado de verificación de la edición; solo 'verified_current' es vigente verificado."
    )
    path: str | None = Field(
        description="Ruta estructural; nula si el resultado es la norma completa."
    )
    unit_path: str | None = Field(
        description="Unidad de lectura que se abre para esta disposición."
    )
    kind: str | None
    label: str | None
    title: str | None
    snippet: str | None = Field(description="Comienzo del texto vigente.")
    page_start: int | None

    @classmethod
    def from_hit(cls, hit: LookupHit) -> LookupHitOut:
        return cls(
            instrument_id=hit.instrument_id,
            instrument_short_name=hit.instrument_short_name,
            instrument_title=hit.instrument_title,
            citation=hit.citation,
            version_id=hit.version_id,
            edition_label=hit.edition_label,
            verification_status=hit.verification_status,
            path=hit.path,
            unit_path=hit.unit_path,
            kind=hit.kind,
            label=hit.label,
            title=hit.title,
            snippet=hit.snippet,
            page_start=hit.page_start,
        )


class LookupOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: LookupStatus = Field(
        description=(
            "resolved: una sola coincidencia · ambiguous: varias, elige la persona · "
            "not_found: se entendió pero no existe · unrecognized: el texto no es una referencia."
        )
    )
    query: str
    message: str = Field(
        description="Explicación para la persona (vacía si se resolvió sin dudas)."
    )
    reference: str | None = Field(description="Lo que se entendió, p. ej. 'art. 2, lit. e)'.")
    norms: list[str] = Field(description="Normas que se reconocieron en el texto.")
    total: int
    hits: list[LookupHitOut]
    ignored_text: str | None = Field(description="Palabras que no formaron parte de la referencia.")

    @classmethod
    def from_result(cls, result: LookupResult) -> LookupOut:
        return cls(
            status=result.status,
            query=result.query,
            message=result.message,
            reference=result.reference,
            norms=list(result.norms),
            total=result.total,
            hits=[LookupHitOut.from_hit(h) for h in result.hits],
            ignored_text=result.ignored_text,
        )
