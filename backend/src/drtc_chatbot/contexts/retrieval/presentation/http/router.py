"""HTTP routes of the retrieval context: /api/v1/lookup."""

from typing import Annotated

from fastapi import APIRouter, Query

from drtc_chatbot.contexts.retrieval.application.lookup_reference import MAX_QUERY_LENGTH
from drtc_chatbot.contexts.retrieval.presentation.http.dependencies import Retrieval
from drtc_chatbot.contexts.retrieval.presentation.http.schemas import LookupOut
from drtc_chatbot.shared_kernel.presentation.http import CurrentActor

router = APIRouter(prefix="/lookup", tags=["Búsqueda por referencia"])


@router.get(
    "",
    summary="Encontrar una disposición por su referencia",
    description=(
        "Resuelve referencias como «art. 5 Ley 27181», «218.2 TUO», «lit. e del art. 2 LGTTT» o "
        "«anexo 2 RENAT». Es una búsqueda exacta, sin similitud: si la referencia puede significar "
        "varias cosas devuelve todas (`ambiguous`) para que la persona elija, y si nombra una norma "
        "que no está en el corpus lo dice (`not_found`) en lugar de buscar en otras."
    ),
)
async def lookup(
    actor: CurrentActor,
    use_cases: Retrieval,
    q: Annotated[
        str,
        Query(
            min_length=1,
            max_length=MAX_QUERY_LENGTH,
            description="Referencia escrita por la persona.",
        ),
    ],
) -> LookupOut:
    result = await use_cases.lookup_reference.execute(actor, q)
    return LookupOut.from_result(result)
