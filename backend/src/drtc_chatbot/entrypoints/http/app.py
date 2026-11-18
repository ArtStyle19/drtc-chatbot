"""FastAPI application factory (HTTP entry point)."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from drtc_chatbot import __version__
from drtc_chatbot.bootstrap.container import build_container
from drtc_chatbot.bootstrap.logging import configure_logging
from drtc_chatbot.bootstrap.settings import Settings
from drtc_chatbot.contexts.legal_corpus.presentation.http.router import (
    provisions_router,
)
from drtc_chatbot.contexts.legal_corpus.presentation.http.router import (
    router as legal_corpus_router,
)
from drtc_chatbot.entrypoints.http.errors import register_exception_handlers
from drtc_chatbot.entrypoints.http.health import router as health_router
from drtc_chatbot.entrypoints.http.middleware import REQUEST_ID_HEADER, RequestIdMiddleware

API_DESCRIPTION = (
    "API del asistente normativo de la DRTC Puno. Toda respuesta jurídica se apoya en "
    "disposiciones citadas con su norma, versión y página; un texto no verificado nunca se "
    "presenta como vigente."
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings.log_level, json=settings.log_json)
    container = build_container(settings)
    logger = structlog.get_logger(__name__)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("app.startup", environment=settings.environment.value)
        yield
        await container.aclose()
        logger.info("app.shutdown")

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=API_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.container = container
    app.state.identity_provider = container.identity_provider
    app.state.legal_corpus = container.legal_corpus

    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    app.add_middleware(RequestIdMiddleware)  # outermost: every response carries a request id

    api_v1 = APIRouter(prefix="/api/v1")
    api_v1.include_router(legal_corpus_router)
    api_v1.include_router(provisions_router)
    app.include_router(health_router)
    app.include_router(api_v1)
    return app
