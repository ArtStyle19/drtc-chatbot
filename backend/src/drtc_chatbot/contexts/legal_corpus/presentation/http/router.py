"""HTTP routes of the legal corpus (/api/v1/instruments)."""

from fastapi import APIRouter

from drtc_chatbot.contexts.legal_corpus.presentation.http.dependencies import LegalCorpus
from drtc_chatbot.contexts.legal_corpus.presentation.http.schemas import (
    LegalInstrumentListOut,
    LegalInstrumentOut,
)
from drtc_chatbot.shared_kernel.presentation.http import CurrentActor

router = APIRouter(prefix="/instruments", tags=["Corpus normativo"])


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
