"""HTTP routes of the legal corpus: /api/v1/instruments and /api/v1/provisions."""

from typing import Annotated

from fastapi import APIRouter, Query

from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind
from drtc_chatbot.contexts.legal_corpus.presentation.http.dependencies import LegalCorpus
from drtc_chatbot.contexts.legal_corpus.presentation.http.schemas import (
    LegalInstrumentListOut,
    LegalInstrumentOut,
    ProvisionDetailOut,
    ProvisionListOut,
)
from drtc_chatbot.shared_kernel.presentation.http import CurrentActor

router = APIRouter(prefix="/instruments", tags=["Corpus normativo"])
provisions_router = APIRouter(prefix="/provisions", tags=["Corpus normativo"])


@router.get(
    "",
    summary="Listar las normas del corpus",
    description=(
        "Devuelve las normas disponibles con el estado de verificación de su edición de "
        "referencia. Un texto no verificado nunca se marca como vigente."
    ),
)
async def list_instruments(actor: CurrentActor, use_cases: LegalCorpus) -> LegalInstrumentListOut:
    summaries = await use_cases.list_legal_instruments.execute(actor)
    return LegalInstrumentListOut(items=[LegalInstrumentOut.from_summary(s) for s in summaries])


@router.get(
    "/{instrument_id}/provisions",
    summary="Listar las disposiciones vigentes de una norma",
    description=(
        "Disposiciones (artículos, numerales, literales…) del texto vigente de la edición aprobada "
        "más reciente, en orden de documento y con su página exacta. Las ediciones pendientes de "
        "aprobación no son visibles. La respuesta indica el estado de verificación de la edición."
    ),
    responses={404: {"description": "La norma no tiene una edición aprobada con disposiciones."}},
)
async def list_provisions(
    actor: CurrentActor,
    use_cases: LegalCorpus,
    instrument_id: str,
    version_id: Annotated[
        str | None, Query(description="Edición concreta; por defecto la más reciente aprobada.")
    ] = None,
    kind: Annotated[
        ProvisionKind | None, Query(description="Filtra por tipo de disposición.")
    ] = None,
    parent: Annotated[str | None, Query(description="Ruta del padre, p. ej. 'articulo:2'.")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProvisionListOut:
    page = await use_cases.list_provisions.execute(
        actor,
        instrument_id,
        version_id=version_id,
        kind=kind,
        parent_path=parent,
        limit=limit,
        offset=offset,
    )
    return ProvisionListOut.from_page(page)


@provisions_router.get(
    "/{provision_id}",
    summary="Leer una disposición con su historial de revisiones",
    responses={404: {"description": "No existe o su edición no está aprobada."}},
)
async def get_provision(
    actor: CurrentActor, use_cases: LegalCorpus, provision_id: str
) -> ProvisionDetailOut:
    detail = await use_cases.get_provision.execute(actor, provision_id)
    return ProvisionDetailOut.from_detail(detail)
