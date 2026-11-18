"""FastAPI dependencies that hand the router its use cases.

The router never imports the composition root: it reads a module object that the root stored
in ``app.state.legal_corpus`` and only knows it through this structural Protocol.
"""

from typing import Annotated, Protocol, cast

from fastapi import Depends, Request

from drtc_chatbot.contexts.legal_corpus.application.queries.get_provision import GetProvision
from drtc_chatbot.contexts.legal_corpus.application.queries.list_legal_instruments import (
    ListLegalInstruments,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.list_provisions import ListProvisions


class LegalCorpusUseCases(Protocol):
    @property
    def list_legal_instruments(self) -> ListLegalInstruments: ...

    @property
    def list_provisions(self) -> ListProvisions: ...

    @property
    def get_provision(self) -> GetProvision: ...


def get_legal_corpus(request: Request) -> LegalCorpusUseCases:
    return cast(LegalCorpusUseCases, request.app.state.legal_corpus)


LegalCorpus = Annotated[LegalCorpusUseCases, Depends(get_legal_corpus)]
