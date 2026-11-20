"""HTTP routes of the legal corpus: /api/v1/instruments and /api/v1/provisions."""

from typing import Annotated

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import FileResponse

from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind
from drtc_chatbot.contexts.legal_corpus.presentation.http.dependencies import LegalCorpus
from drtc_chatbot.contexts.legal_corpus.presentation.http.schemas import (
    LegalInstrumentListOut,
    LegalInstrumentOut,
    OutlineOut,
    ProvisionDetailOut,
    ProvisionListOut,
    ReadingUnitOut,
)
from drtc_chatbot.shared_kernel.presentation.http import CurrentActor

router = APIRouter(prefix="/instruments", tags=["Corpus normativo"])
provisions_router = APIRouter(prefix="/provisions", tags=["Corpus normativo"])
versions_router = APIRouter(prefix="/versions", tags=["Corpus normativo"])


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


@router.get(
    "/{instrument_id}/outline",
    summary="Índice de una norma",
    description=(
        "Títulos, capítulos, artículos, disposiciones y anexos de la edición aprobada (la más "
        "reciente por defecto), en orden de documento, con la página donde empieza cada uno."
    ),
    responses={404: {"description": "La norma no tiene una edición aprobada."}},
)
async def get_outline(
    actor: CurrentActor,
    use_cases: LegalCorpus,
    instrument_id: str,
    version_id: Annotated[str | None, Query(description="Edición concreta.")] = None,
) -> OutlineOut:
    outline = await use_cases.get_outline.execute(actor, instrument_id, version_id=version_id)
    return OutlineOut.from_outline(outline)


@router.get(
    "/{instrument_id}/reading-unit",
    summary="Leer una disposición con su subárbol",
    description=(
        "Devuelve la unidad de lectura que contiene la ruta pedida (el artículo, la disposición, el "
        "anexo o el contenedor) con su subárbol vigente, citas generadas por el servidor, notas "
        "editoriales, advertencias de revisión y las cajas de texto para resaltarlas en el PDF. "
        "Los textos sustituidos solo aparecen en `history`, rotulados como no vigentes."
    ),
    responses={
        404: {"description": "La norma o la disposición no existen en la edición aprobada."}
    },
)
async def get_reading_unit(
    actor: CurrentActor,
    use_cases: LegalCorpus,
    instrument_id: str,
    path: Annotated[
        str,
        Query(
            min_length=1,
            max_length=300,
            description="Ruta estructural, p. ej. 'articulo:2/literal:e'.",
        ),
    ],
    version_id: Annotated[str | None, Query(description="Edición concreta.")] = None,
) -> ReadingUnitOut:
    unit = await use_cases.get_reading_unit.execute(
        actor, instrument_id, path, version_id=version_id
    )
    return ReadingUnitOut.from_unit(unit)


def _etag_matches(if_none_match: str | None, etag: str) -> bool:
    """RFC 9110 weak comparison of an ``If-None-Match`` header against our strong ETag."""
    if not if_none_match:
        return False
    if if_none_match.strip() == "*":
        return True
    candidates = {item.strip().removeprefix("W/") for item in if_none_match.split(",")}
    return etag in candidates


@versions_router.get(
    "/{version_id}/source",
    summary="PDF original de una edición aprobada",
    description=(
        "Entrega el documento fuente tal como se registró (se verifica su SHA-256 antes de "
        "servirlo). Admite `Range` para que el visor descargue solo las páginas que muestra."
    ),
    response_class=FileResponse,
    responses={
        200: {"content": {"application/pdf": {}}},
        206: {
            "description": "Parte del PDF pedida con `Range` (`Content-Range` indica cuál).",
            "content": {"application/pdf": {}},
        },
        304: {"description": "El navegador ya tiene esta versión (ETag)."},
        404: {"description": "La edición no existe o no está aprobada."},
        416: {"description": "El rango pedido está fuera del archivo."},
    },
)
async def get_source_document(
    request: Request, actor: CurrentActor, use_cases: LegalCorpus, version_id: str
) -> Response:
    document = await use_cases.get_source_document.execute(actor, version_id)
    etag = f'"{document.sha256}"'
    headers = {
        "ETag": etag,
        "Cache-Control": "private, max-age=3600",
        "X-Content-Type-Options": "nosniff",
    }
    if _etag_matches(request.headers.get("if-none-match"), etag):
        return Response(status_code=304, headers=headers)
    return FileResponse(
        document.path,
        media_type="application/pdf",
        filename=document.file_name,
        content_disposition_type="inline",
        headers=headers,
    )
