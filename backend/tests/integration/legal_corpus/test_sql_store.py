"""The PostgreSQL adapter against a real database (needs DRTC_TEST_DATABASE_URL or Docker)."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from drtc_chatbot.contexts.legal_corpus.application.commands.approve_version import (
    ApproveInstrumentVersion,
)
from drtc_chatbot.contexts.legal_corpus.application.commands.publish_provisions import (
    PublishProvisions,
)
from drtc_chatbot.contexts.legal_corpus.application.commands.sync_corpus_manifest import (
    SyncCorpusManifest,
)
from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EventRequest,
    NoteDraft,
    PublishRequest,
    RevisionRequest,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import (
    ApprovalMode,
    ApprovalPolicy,
    ApprovalPolicyName,
)
from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind
from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_reader import YamlManifestReader
from drtc_chatbot.contexts.legal_corpus.infrastructure.sql_store import SqlLegalCorpusStore
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from drtc_chatbot.shared_kernel.domain import InvariantViolationError
from tests.conftest import CORPUS_MANIFEST

pytestmark = pytest.mark.docker

LEY = "ley-27181@2020-05"
LEY_SHA = "b428febd1a0fe72e3d505fb186fbc7ac418c24c20c61bd59e6b3e39581a034bb"
ANONYMOUS = Actor("anonymous", ActorKind.ANONYMOUS)


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 11, 18, 9, 0, tzinfo=UTC)


def rev(path: str, kind: str, n: int = 1, status: str = "current", *, parent: str | None = None,
        ordinal: int = 1, text: str = "texto", page: int = 2, event: EventRequest | None = None) -> RevisionRequest:  # fmt: skip
    return RevisionRequest(
        path,
        kind,
        path.rsplit(":", maxsplit=1)[-1],
        None,
        parent,
        text,
        n,
        status,
        page,
        page,
        ordinal,
        event=event,
    )


def ley_request(
    digest: str = "d1", *, art2_text: str = "Para efectos de la presente Ley"
) -> PublishRequest:
    """Article 2 replaced once (r1 superseded, r2 current) and one literal below it."""
    event = EventRequest("substituted", "el Decreto de Urgencia Nº 019-2020", None)
    return PublishRequest(
        LEY, LEY_SHA, 36, digest,
        (
            rev("titulo:I", "title", ordinal=1, page=2),
            rev("articulo:2", "article", 1, "superseded", parent="titulo:I", ordinal=2, text="original"),
            rev("articulo:2/literal:a", "literal", 1, "superseded", parent="articulo:2", ordinal=3),
            rev("articulo:2", "article", 2, "current", parent="titulo:I", ordinal=4, text=art2_text, page=3, event=event),
            rev("articulo:2/literal:a", "literal", 2, "current", parent="articulo:2", ordinal=5, page=3),
        ),
        (NoteDraft("amendment", "(*) Artículo modificado por el DU 019-2020", 3, "articulo:2"),),
    )  # fmt: skip


@pytest.fixture
async def corpus(db_sessions: async_sessionmaker):  # type: ignore[type-arg]
    store = SqlLegalCorpusStore(db_sessions)
    await SyncCorpusManifest(YamlManifestReader(CORPUS_MANIFEST), store).execute()
    return store


@pytest.mark.spec("002-FR-004")
async def test_sync_is_idempotent_and_keeps_the_catalog_order(corpus: SqlLegalCorpusStore) -> None:
    again = SyncCorpusManifest(YamlManifestReader(CORPUS_MANIFEST), corpus)
    await again.execute()
    await again.execute()

    instruments = await corpus.list_instruments()

    assert [str(i.id) for i in instruments] == ["ley-27181", "ds-017-2009-mtc", "tuo-ley-27444"]
    assert {i.latest_version.verification_status.value for i in instruments} == {"unverified"}


@pytest.mark.spec("002-FR-004")
async def test_a_source_whose_fingerprint_changed_is_refused(
    db_sessions: async_sessionmaker, corpus: SqlLegalCorpusStore
) -> None:  # type: ignore[type-arg]
    async with db_sessions.begin() as session:
        await session.execute(
            text("UPDATE source_documents SET sha256 = :s WHERE id = 'src-ley-27181-2020-06'"),
            {"s": "f" * 64},
        )

    with pytest.raises(InvariantViolationError, match="originals are immutable"):
        await SyncCorpusManifest(YamlManifestReader(CORPUS_MANIFEST), corpus).execute()


@pytest.mark.spec("002-FR-010")
async def test_a_published_version_is_invisible_until_approved(corpus: SqlLegalCorpusStore) -> None:
    publish = PublishProvisions(corpus, Clock())
    outcome = await publish.execute(ley_request())

    assert (outcome.changed, outcome.current, outcome.superseded) == (True, 3, 2)
    assert (
        await corpus.list_provisions(
            "ley-27181", version_id=None, kind=None, parent_path=None, limit=50, offset=0
        )
        is None
    )

    approve = ApproveInstrumentVersion(
        corpus, Clock(), ApprovalPolicy(ApprovalPolicyName.MANUAL, "local")
    )
    await approve.approve(LEY, reviewer="Ana Quispe")
    page = await corpus.list_provisions(
        "ley-27181", version_id=None, kind=None, parent_path=None, limit=50, offset=0
    )

    assert page is not None
    assert page.approval_mode is ApprovalMode.HUMAN
    assert page.verification_status.value == "unverified"  # approving is not verifying
    assert [(i.path, i.revision, i.revision_count) for i in page.items] == [
        ("titulo:I", 1, 1), ("articulo:2", 2, 2), ("articulo:2/literal:a", 2, 2),
    ]  # fmt: skip
    assert page.items[1].event is not None
    assert page.items[1].event.source == "el Decreto de Urgencia Nº 019-2020"


@pytest.mark.spec("002-FR-003")
async def test_only_current_text_is_listed_and_history_is_in_the_detail(
    corpus: SqlLegalCorpusStore,
) -> None:
    await PublishProvisions(corpus, Clock()).execute(ley_request())
    await ApproveInstrumentVersion(
        corpus, Clock(), ApprovalPolicy(ApprovalPolicyName.AUTO_DEV, "local")
    ).apply_policy(LEY)
    page = await corpus.list_provisions(
        "ley-27181",
        version_id=None,
        kind=ProvisionKind.ARTICLE,
        parent_path=None,
        limit=10,
        offset=0,
    )
    assert page is not None
    assert [i.text for i in page.items] == ["Para efectos de la presente Ley"]

    detail = await corpus.get_provision(page.items[0].provision_id)

    assert detail is not None
    assert [(r.revision, r.status.value, r.text) for r in detail.revisions] == [
        (1, "superseded", "original"), (2, "current", "Para efectos de la presente Ley"),
    ]  # fmt: skip
    assert detail.current is not None
    assert detail.current.page_start == 3
    assert detail.parent_path == "titulo:I"
    assert [n.kind for n in detail.notes] == ["amendment"]


async def test_filters_and_paging(corpus: SqlLegalCorpusStore) -> None:
    await PublishProvisions(corpus, Clock()).execute(ley_request())
    await ApproveInstrumentVersion(
        corpus, Clock(), ApprovalPolicy(ApprovalPolicyName.AUTO_DEV, "local")
    ).apply_policy(LEY)

    children = await corpus.list_provisions(
        "ley-27181", version_id=None, kind=None, parent_path="articulo:2", limit=10, offset=0
    )
    first = await corpus.list_provisions(
        "ley-27181", version_id=None, kind=None, parent_path=None, limit=1, offset=1
    )

    assert children is not None
    assert [i.path for i in children.items] == ["articulo:2/literal:a"]
    assert first is not None
    assert (first.total, [i.path for i in first.items]) == (3, ["articulo:2"])
    assert await corpus.get_provision("not-a-uuid") is None


@pytest.mark.spec("002-FR-004")
async def test_publishing_the_same_digest_is_a_noop_and_new_content_needs_a_new_approval(
    corpus: SqlLegalCorpusStore,
) -> None:
    publish = PublishProvisions(corpus, Clock())
    approve = ApproveInstrumentVersion(
        corpus, Clock(), ApprovalPolicy(ApprovalPolicyName.MANUAL, "local")
    )
    await publish.execute(ley_request("d1"))
    await approve.approve(LEY, reviewer="Ana")

    same = await publish.execute(ley_request("d1"))
    assert same.changed is False
    assert (await corpus.get_approval(LEY)).is_approved  # type: ignore[union-attr]

    changed = await publish.execute(ley_request("d2", art2_text="Texto corregido"))
    assert changed.changed is True
    assert not (await corpus.get_approval(LEY)).is_approved  # type: ignore[union-attr]


@pytest.mark.spec("002-FR-004")
async def test_publishing_a_file_that_is_not_the_registered_source_is_refused(
    corpus: SqlLegalCorpusStore,
) -> None:
    wrong = ley_request()
    wrong = PublishRequest(
        wrong.version_id, "e" * 64, wrong.page_count, wrong.content_digest, wrong.revisions
    )

    with pytest.raises(InvariantViolationError, match="SHA-256"):
        await PublishProvisions(corpus, Clock()).execute(wrong)


@pytest.mark.spec("002-FR-003")
async def test_the_database_itself_refuses_two_current_texts(
    db_sessions: async_sessionmaker, corpus: SqlLegalCorpusStore
) -> None:  # type: ignore[type-arg]
    await PublishProvisions(corpus, Clock()).execute(ley_request())

    with pytest.raises(IntegrityError):
        async with db_sessions.begin() as session:
            await session.execute(
                text(
                    "UPDATE provision_versions SET status = 'current' WHERE status = 'superseded' AND revision = 1"
                )
            )
