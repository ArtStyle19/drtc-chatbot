"""Migrations and readiness against a real PostgreSQL + pgvector (see conftest fixtures)."""

import httpx
import pytest
from sqlalchemy import create_engine, text

from drtc_chatbot.entrypoints.http.app import create_app
from tests.conftest import make_settings

pytestmark = pytest.mark.docker


def test_migrations_enable_the_required_extensions(migrated_database: str) -> None:
    engine = create_engine(migrated_database)
    with engine.connect() as connection:
        installed = set(connection.execute(text("SELECT extname FROM pg_extension")).scalars())
    engine.dispose()

    assert {"vector", "unaccent", "pg_trgm"} <= installed


async def test_readiness_is_ok_with_a_reachable_database(migrated_database: str) -> None:
    app = create_app(make_settings(database_url=migrated_database))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "corpus_manifest": "ok"},
    }
