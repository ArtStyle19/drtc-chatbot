"""HTTP response models (the public API contract). Descriptions are user-facing, in Spanish."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionContext,
    EditionSummary,
    LegalInstrumentSummary,
    Outline,
    OutlineEntry,
    ProvisionDetail,
    ProvisionPage,
    ProvisionRevisionDetail,
    ProvisionSummary,
    ReadingNode,
    ReadingRevision,
    ReadingUnit,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import ApprovalMode, ApprovalStatus
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    EventKind,
    LegalEvent,
    PageBox,
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


# ----------------------------------------------------------------------------- reader
class EditionContextOut(BaseModel):
    """La norma y la edición aprobada que se está leyendo (encabezado del lector)."""

    model_config = ConfigDict(frozen=True)

    instrument_id: str
    type: InstrumentType
    number: str
    title: str
    short_name: str
    version_id: str
    edition_label: str
    consolidated_as_of: date | None
    verification_status: VerificationStatus
    may_be_presented_as_current: bool = Field(
        description="Solo es verdadero si el texto fue verificado como vigente."
    )
    approval_mode: ApprovalMode
    page_count: int
    alerts: list[str]
    source_url: str = Field(
        description="PDF original de esta edición (admite peticiones por rango)."
    )

    @classmethod
    def from_context(cls, edition: EditionContext) -> EditionContextOut:
        return cls(
            instrument_id=edition.instrument_id,
            type=edition.instrument_type,
            number=edition.number,
            title=edition.title,
            short_name=edition.short_name,
            version_id=edition.version_id,
            edition_label=edition.edition_label,
            consolidated_as_of=edition.consolidated_as_of,
            verification_status=edition.verification_status,
            may_be_presented_as_current=edition.verification_status.may_be_presented_as_current,
            approval_mode=edition.approval_mode,
            page_count=edition.page_count,
            alerts=list(edition.alerts),
            source_url=f"/api/v1/versions/{edition.version_id}/source",
        )


class OutlineEntryOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    kind: ProvisionKind
    label: str
    title: str | None
    parent_path: str | None
    page_start: int = Field(description="Página física del PDF donde empieza.")
    unit_path: str = Field(description="Unidad de lectura que se abre al elegir esta entrada.")

    @classmethod
    def from_entry(cls, entry: OutlineEntry) -> OutlineEntryOut:
        return cls(
            path=entry.path,
            kind=entry.kind,
            label=entry.label,
            title=entry.title,
            parent_path=entry.parent_path,
            page_start=entry.page_start,
            unit_path=entry.unit_path,
        )


class OutlineOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    edition: EditionContextOut
    entries: list[OutlineEntryOut] = Field(description="Índice plano en orden de documento.")

    @classmethod
    def from_outline(cls, outline: Outline) -> OutlineOut:
        return cls(
            edition=EditionContextOut.from_context(outline.edition),
            entries=[OutlineEntryOut.from_entry(e) for e in outline.entries],
        )


class BoxOut(BaseModel):
    """Rectángulo en puntos PDF (origen abajo-izquierda) de una línea del texto."""

    model_config = ConfigDict(frozen=True)

    page: int
    x0: float
    y0: float
    x1: float
    y1: float

    @classmethod
    def from_box(cls, box: PageBox) -> BoxOut:
        return cls(page=box.page, x0=box.x0, y0=box.y0, x1=box.x1, y1=box.y1)


class CitationOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    short: str = Field(description="Cita breve, p. ej. 'Ley N.° 27181, art. 2, lit. e)'.")
    formal: str = Field(description="Cita formal con edición, estado de verificación y fuente.")


class ReadingRevisionOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    revision: int
    title: str | None
    text: str
    page_start: int
    page_end: int
    boxes: list[BoxOut]
    event: LegalEventOut | None
    citation: CitationOut

    @classmethod
    def from_revision(cls, item: ReadingRevision) -> ReadingRevisionOut:
        return cls(
            revision=item.revision,
            title=item.title,
            text=item.text,
            page_start=item.page_start,
            page_end=item.page_end,
            boxes=[BoxOut.from_box(b) for b in item.boxes],
            event=LegalEventOut.from_domain(item.event),
            citation=CitationOut(short=item.citation.short, formal=item.citation.formal),
        )


class ReviewWarningOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str


class ReadingNodeOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
    kind: ProvisionKind
    label: str
    parent_path: str | None
    revision_count: int
    current: ReadingRevisionOut = Field(description="Texto vigente de la edición.")
    history: list[ReadingRevisionOut] = Field(
        description="Textos sustituidos (del más antiguo al más reciente): NO están vigentes."
    )
    warnings: list[ReviewWarningOut]
    notes: list[EditorialNoteOut]

    @classmethod
    def from_node(cls, node: ReadingNode) -> ReadingNodeOut:
        return cls(
            path=node.path,
            kind=node.kind,
            label=node.label,
            parent_path=node.parent_path,
            revision_count=node.revision_count,
            current=ReadingRevisionOut.from_revision(node.current),
            history=[ReadingRevisionOut.from_revision(r) for r in node.history],
            warnings=[ReviewWarningOut(code=w.code, message=w.message) for w in node.warnings],
            notes=[EditorialNoteOut(kind=n.kind, text=n.text, page=n.page) for n in node.notes],
        )


class ReadingUnitOut(BaseModel):
    model_config = ConfigDict(frozen=True)

    edition: EditionContextOut
    requested_path: str
    unit_path: str = Field(
        description="Artículo, disposición, anexo o contenedor que contiene la ruta."
    )
    nodes: list[ReadingNodeOut] = Field(
        description="La unidad y su subárbol vigente en orden de documento (anídelos con parent_path)."
    )
    children: list[OutlineEntryOut] = Field(description="Si es un contenedor: lo que contiene.")

    @classmethod
    def from_unit(cls, unit: ReadingUnit) -> ReadingUnitOut:
        return cls(
            edition=EditionContextOut.from_context(unit.edition),
            requested_path=unit.requested_path,
            unit_path=unit.unit_path,
            nodes=[ReadingNodeOut.from_node(n) for n in unit.nodes],
            children=[OutlineEntryOut.from_entry(e) for e in unit.children],
        )
