"""Maps errors to RFC 9457 problem details (``application/problem+json``)."""

from http import HTTPStatus
from typing import Any

import structlog
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from drtc_chatbot.shared_kernel.domain import (
    DomainError,
    IntegrityViolationError,
    InvariantViolationError,
    NotFoundError,
)

PROBLEM_JSON = "application/problem+json"
logger = structlog.get_logger(__name__)


def problem_response(
    request: Request,
    *,
    status: int,
    code: str,
    detail: str | None = None,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"urn:drtc-chatbot:problem:{code}",
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
        "request_id": getattr(request.state, "request_id", None),
    }
    if extra:
        body.update(extra)
    return JSONResponse(status_code=status, content=jsonable_encoder(body), media_type=PROBLEM_JSON)


def _status_for(error: DomainError) -> int:
    if isinstance(error, NotFoundError):
        return HTTPStatus.NOT_FOUND
    if isinstance(error, InvariantViolationError):
        return HTTPStatus.UNPROCESSABLE_CONTENT
    return HTTPStatus.BAD_REQUEST


async def _on_domain_error(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, DomainError)  # noqa: S101 - registered only for DomainError
    if isinstance(error, IntegrityViolationError):
        logger.error("integrity.violation", path=request.url.path, detail=error.message)
        return problem_response(
            request,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            code=error.code,
            detail="El documento no pasó la verificación de integridad. Avise al equipo técnico.",
        )
    return problem_response(
        request, status=_status_for(error), code=error.code, detail=error.message
    )


async def _on_http_error(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, StarletteHTTPException)  # noqa: S101
    detail = error.detail if isinstance(error.detail, str) else None
    return problem_response(
        request, status=error.status_code, code=f"http_{error.status_code}", detail=detail
    )


async def _on_validation_error(request: Request, error: Exception) -> JSONResponse:
    assert isinstance(error, RequestValidationError)  # noqa: S101
    return problem_response(
        request,
        status=HTTPStatus.UNPROCESSABLE_CONTENT,
        code="validation_error",
        detail="La solicitud no es válida.",
        # Never echo what the person typed back (pydantic includes it as `input`): a search text may
        # hold personal data and must not travel anywhere it does not have to (constitution VI).
        extra={"errors": [{k: v for k, v in e.items() if k != "input"} for e in error.errors()]},
    )


async def _on_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    logger.exception("http.unhandled_error", path=request.url.path, error=type(error).__name__)
    return problem_response(
        request,
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="internal_error",
        detail="Ocurrió un error inesperado. Intente nuevamente.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _on_domain_error)
    app.add_exception_handler(StarletteHTTPException, _on_http_error)
    app.add_exception_handler(RequestValidationError, _on_validation_error)
    app.add_exception_handler(Exception, _on_unexpected_error)
