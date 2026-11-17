"""Runs the migrations against a real PostgreSQL + pgvector (needs Docker)."""

import os
from collections.abc import Iterator

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from testcontainers.community.postgres import PostgresContainer

from drtc_chatbot.entrypoints.http.app import create_app
from tests.conftest import BACKEND_ROOT, make_settings

POSTGRES_IMAGE = "pgvector/pgvector:0.8.7-pg18-trixie"
pytestmark = pytest.mark.docker


@pytest.fixture(scope="module")
def database_url() -> Iterator[str]:
    postgres = PostgresContainer(POSTGRES_IMAGE, driver="psycopg")
    try:
        postgres.start()
    except Exception as error:  # Docker answers pings but cannot run containers
        if os.environ.get("CI"):
            raise
        pytest.skip(
            f"Docker cannot start containers on this host ({type(error).__name__}); "
            "see docs/operations/local-setup.md"
        )
    try:
        yield postgres.get_connection_url()
    finally:
        postgres.stop()


@pytest.fixture(scope="module")
def migrated_database_url(database_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    return database_url


def test_migrations_enable_the_required_extensions(migrated_database_url: str) -> None:
    engine = create_engine(migrated_database_url)
    with engine.connect() as connection:
        installed = set(connection.execute(text("SELECT extname FROM pg_extension")).scalars())
    engine.dispose()

    assert {"vector", "unaccent", "pg_trgm"} <= installed


async def test_readiness_is_ok_with_a_reachable_database(migrated_database_url: str) -> None:
    app = create_app(make_settings(database_url=migrated_database_url))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "corpus_manifest": "ok"},
    }
