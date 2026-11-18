"""Shared fixtures for the API tests that need the real corpus in PostgreSQL."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
import pytest

from drtc_chatbot.bootstrap.container import Container
from drtc_chatbot.entrypoints.http.app import create_app
from tests.conftest import make_settings

LEY = "ley-27181@2020-05"
Stack = tuple[httpx.AsyncClient, Container]


@asynccontextmanager
async def open_stack(database_url: str, **overrides: Any) -> AsyncIterator[Stack]:
    """The real application (database catalog, manual approval) behind an in-process client."""
    settings = make_settings(
        database_url=database_url.replace("postgresql://", "postgresql+psycopg://"),
        catalog_backend="database",
        ingestion_approval_policy="manual",
        **overrides,
    )
    app = create_app(settings)
    container = cast(Container, app.state.container)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, container
    await container.aclose()


@pytest.fixture
async def stack(clean_database: str) -> AsyncIterator[Stack]:
    async with open_stack(clean_database) as opened:
        yield opened


@pytest.fixture
async def approved_ley(stack: Stack) -> Stack:
    """The Ley 27181 ingested from the real PDF and approved by a (test) reviewer."""
    _, container = stack
    await container.ingestion.run_ingestion.execute(LEY)
    await container.ingestion.gateway.approve(LEY, "Ana Quispe")
    return stack
