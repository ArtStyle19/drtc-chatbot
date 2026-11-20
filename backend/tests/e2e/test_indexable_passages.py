"""What the content search indexes, over the three real norms in PostgreSQL (spec 004)."""

import pytest

from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker

ACTOR = Actor("test", ActorKind.SERVICE)
NORMS = ("ley-27181", "ds-017-2009-mtc", "tuo-ley-27444")


@pytest.mark.spec("004-FR-012")
async def test_the_real_norms_give_current_provisions_of_approved_editions_only(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        results = {
            norm: await container.legal_corpus.list_indexable_passages.execute(ACTOR, norm)
            for norm in NORMS
        }

    for norm, result in results.items():
        assert result is not None, norm
        passages = result.passages
        paths = [p.path for p in passages]
        assert len(paths) == len(set(paths)), f"{norm}: a provision appears twice"
        # containers give context, they are not passages
        assert {p.kind for p in passages} <= {
            ProvisionKind.ARTICLE,
            ProvisionKind.NUMERAL,
            ProvisionKind.LITERAL,
            ProvisionKind.DISPOSITION,
            ProvisionKind.ANNEX,
        }
        assert all(p.breadcrumb.startswith(result.edition.short_name) for p in passages)
        assert all(p.page_start <= p.page_end for p in passages)
        assert all(p.citation for p in passages)
        assert all(p.body or p.title for p in passages)
    assert sum(len(r.passages) for r in results.values() if r) > 2500


@pytest.mark.spec("004-FR-006")
async def test_a_literal_is_findable_with_the_context_of_the_article_that_introduces_it(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus) as (_, container):
        result = await container.legal_corpus.list_indexable_passages.execute(ACTOR, "ley-27181")

    assert result is not None
    literal = next(p for p in result.passages if p.path == "articulo:2/literal:e")
    assert "Art. 2 – De las definiciones › lit. e)" in literal.breadcrumb
    assert literal.lead is not None
    assert literal.lead.startswith("Para efectos de la aplicación de la presente Ley")
    assert literal.unit_path == "articulo:2"
    assert literal.citation == "Ley N.° 27181, art. 2, lit. e)"


@pytest.mark.spec("004-FR-012")
async def test_replaced_texts_are_not_indexed(full_corpus: str) -> None:
    async with open_stack(full_corpus) as (_, container):
        result = await container.legal_corpus.list_indexable_passages.execute(ACTOR, "ley-27181")

    assert result is not None
    article_2 = next(p for p in result.passages if p.path == "articulo:2")
    # the text of art. 2 before the DU 019-2020 amendment was replaced: only the current one is indexed
    assert article_2.body.startswith("Para efectos de la aplicación de la presente Ley")
    assert sum(1 for p in result.passages if p.path == "articulo:2") == 1


async def test_the_long_renat_annex_is_indexed_whole(full_corpus: str) -> None:
    async with open_stack(full_corpus) as (_, container):
        result = await container.legal_corpus.list_indexable_passages.execute(
            ACTOR, "ds-017-2009-mtc"
        )

    assert result is not None
    annex = next(p for p in result.passages if p.path == "anexo:2")
    assert len(annex.body) > 30_000
