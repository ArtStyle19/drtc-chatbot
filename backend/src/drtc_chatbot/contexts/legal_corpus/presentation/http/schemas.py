"""HTTP response models (the public API contract). Descriptions are user-facing, in Spanish."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionSummary,
    LegalInstrumentSummary,
    ProvisionDetail,
    ProvisionPage,
    ProvisionRevisionDetail,
    ProvisionSummary,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import ApprovalMode, ApprovalStatus
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    EventKind,
    LegalEvent,
    ProvisionKind,
    RevisionStatus,
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
    approval_status: ApprovalStatus = Field(
        description="Si la edición fue aprobada para su uso (no equivale a vigencia verificada)."
    )
    approval_mode: ApprovalMode | None = Field(
        description="'human' = revisión de una persona; 'auto_dev' = automática, solo desarrollo."
    )
    provision_count: int = Field(description="Disposiciones vigentes ingeridas de esta edición.")

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
            approval_status=summary.approval_status,
            approval_mode=summary.approval_mode,
            provision_count=summary.provision_count,
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
    aliases: list[str] = Field(
        description="Nombres con que el personal conoce la norma (siglas, títulos cortos)."
    )

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
            aliases=list(summary.aliases),
        )


class LegalInstrumentListOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[LegalInstrumentOut]


class LegalEventOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: EventKind = Field(
        description="Cómo cambió el texto: sustituido, incorporado, modificado o derogado."
    )
    source: str = Field(description="Norma que produjo el cambio, según las notas editoriales.")
    published_on: date | None

    @classmethod
    def from_domain(cls, event: LegalEvent | None) -> LegalEventOut | None:
        return (
            None
            if event is None
            else cls(kind=event.kind, source=event.source, published_on=event.published_on)
        )


class ProvisionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    path: str = Field(description="Ruta estructural estable, p. ej. 'articulo:2/literal:e'.")
    kind: ProvisionKind
    label: str = Field(description="Etiqueta dentro de su nivel, p. ej. '2', '2.1', 'e'.")
    title: str | None
    parent_path: str | None
    text: str = Field(description="Texto vigente de la disposición en esta edición.")
    page_start: int = Field(description="Primera página física del PDF.")
    page_end: int
    revision: int = Field(description="Revisión vigente (1 = texto original).")
    revision_count: int = Field(
        description="Revisiones de esta disposición en la edición (incluye sustituidas)."
    )
    event: LegalEventOut | None

    @classmethod
    def from_summary(cls, item: ProvisionSummary) -> ProvisionOut:
        return cls(
            id=item.provision_id,
            path=item.path,
            kind=item.kind,
            label=item.label,
            title=item.title,
            parent_path=item.parent_path,
            text=item.text,
            page_start=item.page_start,
            page_end=item.page_end,
            revision=item.revision,
            revision_count=item.revision_count,
            event=LegalEventOut.from_domain(item.event),
        )


class ProvisionListOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    instrument_id: str
    version_id: str
    edition_label: str
    verification_status: VerificationStatus
    may_be_presented_as_current: bool
    approval_mode: ApprovalMode
    total: int
    items: list[ProvisionOut]

    @classmethod
    def from_page(cls, page: ProvisionPage) -> ProvisionListOut:
        return cls(
            instrument_id=page.instrument_id,
            version_id=page.version_id,
            edition_label=page.edition_label,
            verification_status=page.verification_status,
            may_be_presented_as_current=page.verification_status.may_be_presented_as_current,
            approval_mode=page.approval_mode,
            total=page.total,
            items=[ProvisionOut.from_summary(i) for i in page.items],
        )


class RevisionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    revision: int
    status: RevisionStatus
    title: str | None
    text: str
    page_start: int
    page_end: int
    event: LegalEventOut | None

    @classmethod
    def from_detail(cls, item: ProvisionRevisionDetail) -> RevisionOut:
        return cls(
            revision=item.revision,
            status=item.status,
            title=item.title,
            text=item.text,
            page_start=item.page_start,
            page_end=item.page_end,
            event=LegalEventOut.from_domain(item.event),
        )


class EditorialNoteOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    text: str
    page: int


class ProvisionDetailOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    instrument_id: str
    version_id: str
    edition_label: str
    verification_status: VerificationStatus
    may_be_presented_as_current: bool
    approval_mode: ApprovalMode
    path: str
    kind: ProvisionKind
    label: str
    parent_path: str | None
    revisions: list[RevisionOut] = Field(
        description="De la más antigua a la más reciente; solo una es vigente."
    )
    notes: list[EditorialNoteOut]

    @classmethod
    def from_detail(cls, detail: ProvisionDetail) -> ProvisionDetailOut:
        return cls(
            id=detail.provision_id,
            instrument_id=detail.instrument_id,
            version_id=detail.version_id,
            edition_label=detail.edition_label,
            verification_status=detail.verification_status,
            may_be_presented_as_current=detail.verification_status.may_be_presented_as_current,
            approval_mode=detail.approval_mode,
            path=detail.path,
            kind=detail.kind,
            label=detail.label,
            parent_path=detail.parent_path,
            revisions=[RevisionOut.from_detail(r) for r in detail.revisions],
            notes=[EditorialNoteOut(kind=n.kind, text=n.text, page=n.page) for n in detail.notes],
        )
