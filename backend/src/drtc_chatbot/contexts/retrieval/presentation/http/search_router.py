"""HTTP route of the content search: GET /api/v1/search."""

from typing import Annotated

import structlog
from fastapi import APIRouter, Query, Request

from drtc_chatbot.contexts.retrieval.application.dto import SearchMode
from drtc_chatbot.contexts.retrieval.domain.query import MAX_QUERY_CHARS
from drtc_chatbot.contexts.retrieval.presentation.http.dependencies import Retrieval
from drtc_chatbot.contexts.retrieval.presentation.http.search_schemas import SearchOut
from drtc_chatbot.shared_kernel.presentation.http import CurrentActor

router = APIRouter(prefix="/search", tags=["Búsqueda por contenido"])
logger = structlog.get_logger(__name__)


@router.get(
    "",
    summary="Buscar disposiciones por su contenido",
    description=(
        "Encuentra disposiciones escribiendo lo que se busca con las propias palabras. Si el texto "
        "identifica una disposición por referencia («art. 5 Ley 27181») esa va primero y marcada; "
        "después, las coincidencias por palabras y por significado, fusionadas y agrupadas por "
        "unidad de lectura. **Son coincidencias, no una respuesta ni una opinión legal.** "
        "Siempre responde 200: si la búsqueda por significado no está disponible (sin clave, error o "
        "demora) responde con palabras e indica el motivo en `degraded`. El texto de la búsqueda no "
        "se guarda ni se registra."
    ),
)
async def search(
    request: Request,
    actor: CurrentActor,
    use_cases: Retrieval,
    q: Annotated[
        str,
        Query(min_length=1, max_length=MAX_QUERY_CHARS, description="Lo que se busca."),
    ],
    limit: Annotated[int, Query(ge=1, le=30, description="Unidades de lectura a devolver.")] = 10,
    instrument: Annotated[
        str | None,
        Query(
            pattern=r"^[a-z0-9-]{1,80}$",
            description="Limita la búsqueda a una norma (se aplica antes del límite).",
        ),
    ] = None,
    mode: Annotated[
        SearchMode,
        Query(
            description="hybrid (por defecto), lexical o vector; los dos últimos sirven para evaluar."
        ),
    ] = SearchMode.HYBRID,
    debug: Annotated[
        bool,
        Query(description="Muestra qué método halló cada resultado. Solo en desarrollo y prueba."),
    ] = False,
) -> SearchOut:
    show_debug = debug and bool(getattr(request.app.state, "search_debug_enabled", False))
    response = await use_cases.search_passages.execute(
        actor, q, limit=limit, instrument_id=instrument, mode=mode, debug=show_debug
    )
    # Privacy (constitution VI): never the text of the search, only its size and what happened.
    logger.info(
        "search",
        mode=response.mode.value,
        results=response.total,
        latency_ms=response.latency_ms,
        degraded=list(response.degraded),
        query_chars=len(response.query),
    )
    return SearchOut.from_response(response, include_debug=show_debug)
