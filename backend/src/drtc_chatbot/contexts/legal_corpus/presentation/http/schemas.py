"""HTTP response models (the public API contract). Descriptions are user-facing, in Spanish."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionSummary,
    LegalInstrumentSummary,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    VerificationStatus,
)


class EditionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    version_id: str = Field(description="Identificador estable de la versión o edición.")
    edition_label: str = Field(description="Edición tal como se muestra al usuario.")
    consolidated_as_of: date | None = Field(
        description="Fecha hasta la que el texto está actualizado, si se conoce."
    )
    verification_status: VerificationStatus = Field(
        description="Estado de verificación del texto frente a la fuente oficial."
    )
    may_be_presented_as_current: bool = Field(
        description="Solo es verdadero si el texto fue verificado como vigente."
    )
    page_count: int = Field(description="Número de páginas del PDF fuente.")
    alerts: list[str] = Field(description="Advertencias que la interfaz debe mostrar.")

    @classmethod
    def from_summary(cls, summary: EditionSummary) -> EditionOut:
        return cls(
            version_id=summary.version_id,
            edition_label=summary.edition_label,
            consolidated_as_of=summary.consolidated_as_of,
            verification_status=summary.verification_status,
            may_be_presented_as_current=summary.may_be_presented_as_current,
            page_count=summary.page_count,
            alerts=list(summary.alerts),
        )


class LegalInstrumentOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Identificador estable de la norma, p. ej. 'ley-27181'.")
    type: InstrumentType = Field(description="Tipo de norma.")
    number: str = Field(description="Número oficial, p. ej. '27181' o '017-2009-MTC'.")
    title: str
    short_name: str = Field(description="Nombre corto para citas y listados.")
    issuing_authority: str
    publication_date: date | None
    current_edition: EditionOut = Field(description="Edición de referencia (la más reciente).")
    version_count: int

    @classmethod
    def from_summary(cls, summary: LegalInstrumentSummary) -> LegalInstrumentOut:
        return cls(
            id=summary.instrument_id,
            type=summary.instrument_type,
            number=summary.number,
            title=summary.title,
            short_name=summary.short_name,
            issuing_authority=summary.issuing_authority,
            publication_date=summary.publication_date,
            current_edition=EditionOut.from_summary(summary.current_edition),
            version_count=summary.version_count,
        )


class LegalInstrumentListOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[LegalInstrumentOut]
