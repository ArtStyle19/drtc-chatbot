"""FastAPI dependency that hands the router the retrieval use cases (see legal_corpus' version)."""

from typing import Annotated, Protocol, cast

from fastapi import Depends, Request

from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference


class RetrievalUseCases(Protocol):
    @property
    def lookup_reference(self) -> LookupReference: ...


def get_retrieval(request: Request) -> RetrievalUseCases:
    return cast(RetrievalUseCases, request.app.state.retrieval)


Retrieval = Annotated[RetrievalUseCases, Depends(get_retrieval)]
