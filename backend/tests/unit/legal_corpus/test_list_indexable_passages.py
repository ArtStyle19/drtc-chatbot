"""Which provisions the content search indexes, and with what context (spec 004)."""

from collections.abc import Sequence

import pytest

from drtc_chatbot.contexts.legal_corpus.application.dto import EditionContext
from drtc_chatbot.contexts.legal_corpus.application.queries.list_indexable_passages import (
    ListIndexablePassages,
)
from drtc_chatbot.contexts.legal_corpus.domain.passages import ProvisionText
from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind as K
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.unit.legal_corpus.test_reading_use_cases import EDITION

ANONYMOUS = Actor("anonymous", ActorKind.ANONYMOUS)


def row(
    path: str,
    kind: K,
    label: str,
    *,
    title: str | None = None,
    text: str = "",
    parent: str | None = None,
    page: int = 3,
) -> ProvisionText:
    return ProvisionText(path, kind, label, title, text, page, page, parent)


ROWS = [
    row("titulo:I", K.TITLE, "I", title="Definiciones"),
    row("articulo:2", K.ARTICLE, "2", title="De las definiciones", text="Para efectos de la presente Ley, entiéndase por:", parent="titulo:I"),
    row("articulo:2/literal:e", K.LITERAL, "e", text="Servicio de Transporte de Personas.", parent="articulo:2", page=4),
    row("articulo:7", K.ARTICLE, "7", title="Sin texto propio", parent="titulo:I"),
    row("articulo:8", K.ARTICLE, "8", parent="titulo:I"),  # neither text nor title: nothing to find
    row("anexo:2", K.ANNEX, "2", title="TABLA", text="infracciones y sanciones"),
]  # fmt: skip


class Store:
    def __init__(self, *, approved: bool = True) -> None:
        self.approved = approved

    async def get_edition(
        self, instrument_id: str, version_id: str | None
    ) -> EditionContext | None:
        return EDITION if self.approved and instrument_id == "ley-27181" else None

    async def get_provision_texts(self, version_id: str) -> Sequence[ProvisionText]:
        return ROWS


async def passages(store: Store | None = None):
    return await ListIndexablePassages(store or Store()).execute(ANONYMOUS, "ley-27181")  # type: ignore[arg-type]


@pytest.mark.spec("004-FR-012")
async def test_only_provisions_with_something_to_find_are_indexed_and_containers_are_not() -> None:
    result = await passages()

    assert result is not None
    assert [p.path for p in result.passages] == [
        "articulo:2",
        "articulo:2/literal:e",
        "articulo:7",
        "anexo:2",
    ]


async def test_each_passage_carries_its_context_unit_pages_and_server_citation() -> None:
    result = await passages()
    assert result is not None
    literal = next(p for p in result.passages if p.path == "articulo:2/literal:e")

    assert (
        literal.breadcrumb
        == f"{EDITION.short_name} › Título I: Definiciones › Art. 2 – De las definiciones › lit. e)"
    )
    assert literal.lead == "Para efectos de la presente Ley, entiéndase por:"
    assert literal.unit_path == "articulo:2"
    assert (literal.page_start, literal.page_end) == (4, 4)
    assert literal.citation == "Ley N.° 27181, art. 2, lit. e)"
    assert literal.body == "Servicio de Transporte de Personas."


async def test_an_article_without_text_is_still_findable_by_its_title() -> None:
    result = await passages()
    assert result is not None
    seven = next(p for p in result.passages if p.path == "articulo:7")

    assert (seven.body, seven.title) == ("", "Sin texto propio")


@pytest.mark.spec("004-FR-012")
async def test_a_norm_without_an_approved_edition_has_nothing_to_index() -> None:
    assert await passages(Store(approved=False)) is None


async def test_the_result_names_the_edition_so_the_index_knows_what_it_is_made_of() -> None:
    result = await passages()

    assert result is not None
    assert result.edition.version_id == EDITION.version_id
