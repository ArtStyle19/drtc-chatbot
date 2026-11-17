"""Liveness and readiness probes (used by Docker/Compose health checks)."""

from typing import Literal, cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from drtc_chatbot.bootstrap.container import Container
from drtc_chatbot.shared_kernel.infrastructure.database import database_is_reachable

router = APIRouter(prefix="/health", tags=["Salud"])


class LivenessOut(BaseModel):
    status: Literal["ok"]


class ReadinessOut(BaseModel):
    status: Literal["ok", "degraded"]
    checks: dict[str, Literal["ok", "unavailable", "missing"]]


@router.get("/live", summary="El proceso está vivo")
async def live() -> LivenessOut:
    return LivenessOut(status="ok")


@router.get(
    "/ready",
    summary="El servicio puede atender solicitudes",
    responses={503: {"model": ReadinessOut, "description": "Alguna dependencia no está lista."}},
)
async def ready(request: Request, response: Response) -> ReadinessOut:
    container = cast(Container, request.app.state.container)
    checks: dict[str, Literal["ok", "unavailable", "missing"]] = {
        "database": "ok" if await database_is_reachable(container.engine) else "unavailable",
        "corpus_manifest": "ok" if container.settings.corpus_manifest_path.is_file() else "missing",
    }
    healthy = all(value == "ok" for value in checks.values())
    if not healthy:
        response.status_code = 503
    return ReadinessOut(status="ok" if healthy else "degraded", checks=checks)
