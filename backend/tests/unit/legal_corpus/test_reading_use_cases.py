"""Reader use cases against an in-memory ReadingStore."""

from collections.abc import Sequence
from datetime import date
from pathlib import Path

import pytest

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionContext,
    IndexRow,
    OutlineEntry,
    RawNode,
    RawRevision,
    SourceRef,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.get_outline import GetOutline
from drtc_chatbot.contexts.legal_corpus.application.queries.get_reading_unit import GetReadingUnit
from drtc_chatbot.contexts.legal_corpus.application.queries.get_source_document import (
    GetSourceDocument,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.list_provision_index import (
    ListProvisionIndex,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import ApprovalMode
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    EventKind,
    LegalEvent,
    ProvisionKind,
    ReviewFlag,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    VerificationStatus,
)
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from drtc_chatbot.shared_kernel.domain import NotFoundError

ANONYMOUS = Actor("anonymous", ActorKind.ANONYMOUS)
DU_019 = LegalEvent(EventKind.SUBSTITUTED, "el Decreto de Urgencia Nº 019-2020", date(2020, 1, 24))

EDITION = EditionContext(
    instrument_id="ley-27181",
    instrument_type=InstrumentType.LAW,
    number="27181",
    title="Ley General de Transporte y Tránsito Terrestre",
    short_name="Ley 27181 (LGTTT)",
    version_id="ley-27181@2020-05",
    edition_label="Compilación no oficial con modificaciones hasta mayo de 2020",
    consolidated_as_of=None,
    verification_status=VerificationStatus.UNVERIFIED,
    approval_mode=ApprovalMode.AUTO_DEV,
    source_file_name="ley.pdf",
    page_count=36,
    alerts=("Modificada después de 2020.",),
)


def revision(n: int, text: str, page: int, event: LegalEvent | None = None) -> RawRevision:
    return RawRevision(n, None, text, page, page, (), event)


ARTICLE_2 = RawNode(
    path="articulo:2",
    kind=ProvisionKind.ARTICLE,
    label="2",
    parent_path="titulo:I",
    revision_count=2,
    current=revision(2, "Para efectos de la presente Ley (modificado)", 3, DU_019),
    history=(revision(1, "Para efectos de la presente Ley (original)", 2),),
    review_flags=(ReviewFlag.PARAGRAPH_REPLACEMENT_UNAPPLIED,),
)
LITERAL_E = RawNode(
    "articulo:2/literal:e", ProvisionKind.LITERAL, "e", "articulo:2", 1,
    revision(1, "Servicio de Transporte de Personas", 3),
)  # fmt: skip


class FakeReadingStore:
    def __init__(
        self, *, nodes: Sequence[RawNode] = (ARTICLE_2, LITERAL_E), approved: bool = True
    ) -> None:
        self.nodes = nodes
        self.approved = approved
        self.requested_unit: str | None = None

    async def get_edition(
        self, instrument_id: str, version_id: str | None
    ) -> EditionContext | None:
        if not self.approved or instrument_id != "ley-27181":
            return None
        return EDITION

    async def get_outline_entries(self, version_id: str) -> Sequence[OutlineEntry]:
        return [
            OutlineEntry(
                "articulo:2",
                ProvisionKind.ARTICLE,
                "2",
                "De las definiciones",
                "titulo:I",
                2,
                "articulo:2",
            )
        ]

    async def get_reading_nodes(self, version_id: str, unit_path: str) -> Sequence[RawNode]:
        self.requested_unit = unit_path
        return self.nodes

    async def get_child_entries(self, version_id: str, parent_path: str) -> Sequence[OutlineEntry]:
        return [
            OutlineEntry(
                "articulo:1", ProvisionKind.ARTICLE, "1", None, parent_path, 2, "articulo:1"
            )
        ]

    async def get_source_ref(self, version_id: str) -> SourceRef | None:
        return SourceRef(version_id, "ley.pdf", "a" * 64, 36) if self.approved else None

    async def get_index_rows(self, version_id: str) -> Sequence[IndexRow]:
        return [IndexRow("articulo:2/literal:e", ProvisionKind.LITERAL, "e", None, "Servicio…", 3)]


@pytest.mark.spec("003-FR-001")
async def test_the_outline_carries_the_edition_and_its_entries() -> None:
    outline = await GetOutline(FakeReadingStore()).execute(ANONYMOUS, "ley-27181")  # type: ignore[arg-type]

    assert outline.edition.verification_status is VerificationStatus.UNVERIFIED
    assert [e.path for e in outline.entries] == ["articulo:2"]


async def test_an_instrument_without_an_approved_edition_is_not_found() -> None:
    with pytest.raises(NotFoundError, match="no approved edition"):
        await GetOutline(FakeReadingStore(approved=False)).execute(ANONYMOUS, "ley-27181")  # type: ignore[arg-type]
    with pytest.raises(NotFoundError):
        await GetReadingUnit(FakeReadingStore(approved=False)).execute(
            ANONYMOUS, "ley-27181", "articulo:2"
        )  # type: ignore[arg-type]


@pytest.mark.spec("003-FR-002")
async def test_a_path_inside_an_article_opens_the_whole_article() -> None:
    store = FakeReadingStore()
    unit = await GetReadingUnit(store).execute(ANONYMOUS, "ley-27181", "articulo:2/literal:e")  # type: ignore[arg-type]

    assert store.requested_unit == "articulo:2"
    assert unit.requested_path == "articulo:2/literal:e"
    assert unit.unit_path == "articulo:2"
    assert [n.path for n in unit.nodes] == ["articulo:2", "articulo:2/literal:e"]
    assert unit.children == ()


@pytest.mark.spec("003-FR-004")
async def test_the_replaced_text_is_history_cited_as_not_in_force() -> None:
    unit = await GetReadingUnit(FakeReadingStore()).execute(ANONYMOUS, "ley-27181", "articulo:2")  # type: ignore[arg-type]
    article = unit.nodes[0]

    assert article.current.text.endswith("(modificado)")
    assert "no vigente" not in article.current.citation.formal
    [old] = article.history
    assert old.text.endswith("(original)")
    assert old.citation.short.endswith("(texto sustituido)")
    assert (
        "Texto sustituido por el Decreto de Urgencia Nº 019-2020 (24-01-2020): no vigente"
        in old.citation.formal
    )
    assert old.page_start == 2


@pytest.mark.spec("003-FR-003")
async def test_every_citation_comes_from_the_server_and_never_claims_force() -> None:
    unit = await GetReadingUnit(FakeReadingStore()).execute(ANONYMOUS, "ley-27181", "articulo:2")  # type: ignore[arg-type]
    literal = unit.nodes[1]

    assert literal.current.citation.short == "Ley N.° 27181, art. 2, lit. e)"
    assert "edición no verificada" in literal.current.citation.formal
    assert "p. 3 del PDF" in literal.current.citation.formal
    assert "verificado como vigente" not in literal.current.citation.formal


@pytest.mark.spec("003-FR-005")
async def test_review_flags_become_user_facing_warnings() -> None:
    unit = await GetReadingUnit(FakeReadingStore()).execute(ANONYMOUS, "ley-27181", "articulo:2")  # type: ignore[arg-type]

    [warning] = unit.nodes[0].warnings
    assert warning.code == "paragraph_replacement_unapplied"
    assert "párrafo" in warning.message
    assert unit.nodes[1].warnings == ()


async def test_a_container_lists_what_it_contains() -> None:
    title = RawNode("titulo:I", ProvisionKind.TITLE, "I", None, 1, revision(1, "", 2))
    unit = await GetReadingUnit(FakeReadingStore(nodes=[title])).execute(
        ANONYMOUS, "ley-27181", "titulo:I"
    )  # type: ignore[arg-type]

    assert [c.path for c in unit.children] == ["articulo:1"]


@pytest.mark.spec("003-FR-002")
async def test_an_unknown_path_is_not_found() -> None:
    with pytest.raises(NotFoundError, match="does not exist"):
        await GetReadingUnit(FakeReadingStore(nodes=[])).execute(
            ANONYMOUS, "ley-27181", "articulo:999"
        )  # type: ignore[arg-type]


class FakeStorage:
    def __init__(self) -> None:
        self.asked: tuple[str, str] | None = None

    def locate(self, file_name: str, sha256: str) -> tuple[Path, int]:
        self.asked = (file_name, sha256)
        return Path("/srv/corpus/sources") / file_name, 123


@pytest.mark.spec("003-FR-006")
async def test_the_source_is_located_by_registered_name_and_hash_never_by_a_client_path() -> None:
    storage = FakeStorage()
    document = await GetSourceDocument(FakeReadingStore(), storage).execute(
        ANONYMOUS, "ley-27181@2020-05"
    )  # type: ignore[arg-type]

    assert storage.asked == ("ley.pdf", "a" * 64)
    assert document.size == 123


@pytest.mark.spec("003-FR-013")
async def test_a_pending_edition_has_no_downloadable_source() -> None:
    with pytest.raises(NotFoundError):
        await GetSourceDocument(FakeReadingStore(approved=False), FakeStorage()).execute(
            ANONYMOUS, "ley-27181@2020-05"
        )  # type: ignore[arg-type]


async def test_the_index_entries_carry_the_unit_path_and_a_short_citation() -> None:
    index = await ListProvisionIndex(FakeReadingStore()).execute(ANONYMOUS, "ley-27181")  # type: ignore[arg-type]

    assert index is not None
    [entry] = index.entries
    assert (entry.unit_path, entry.citation) == ("articulo:2", "Ley N.° 27181, art. 2, lit. e)")
    assert (
        await ListProvisionIndex(FakeReadingStore(approved=False)).execute(ANONYMOUS, "ley-27181")
        is None
    )  # type: ignore[arg-type]
