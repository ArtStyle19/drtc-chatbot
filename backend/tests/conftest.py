"""Shared fixtures. Tests never read the developer's .env file."""

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from drtc_chatbot.bootstrap.settings import Environment, Settings
from drtc_chatbot.entrypoints.http.app import create_app

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
CORPUS_MANIFEST = REPO_ROOT / "corpus" / "manifest.yaml"
UNREACHABLE_DATABASE_URL = "postgresql+psycopg://nobody:nothing@127.0.0.1:9/none"


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "environment": Environment.TEST,
        "database_url": UNREACHABLE_DATABASE_URL,
        "corpus_manifest_path": CORPUS_MANIFEST,
        "log_level": "WARNING",
        "catalog_backend": "manifest",  # fast tests need no database; DB tests override this
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)  # type: ignore[arg-type]


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
async def client(settings: Settings) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(settings)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


def _docker_is_available() -> bool:
    try:
        import docker  # noqa: PLC0415 - optional dependency of testcontainers

        docker.from_env().ping()
    except Exception:  # noqa: BLE001 - any failure means "no usable Docker"
        return False
    return True


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("DRTC_TEST_DATABASE_URL"):
        return  # an explicit database was provided: Docker is not needed
    if not any(item.get_closest_marker("docker") for item in items) or _docker_is_available():
        return
    skip = pytest.mark.skip(reason="Docker is not available")
    for item in items:
        if item.get_closest_marker("docker"):
            item.add_marker(skip)


POSTGRES_IMAGE = "pgvector/pgvector:0.8.7-pg18-trixie"


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    """A PostgreSQL + pgvector database: ``DRTC_TEST_DATABASE_URL`` (see ``make test-db``) or a
    testcontainers one. Skips locally when neither is available; fails in CI."""
    explicit = os.environ.get("DRTC_TEST_DATABASE_URL")
    if explicit:
        yield explicit
        return
    from testcontainers.community.postgres import PostgresContainer  # noqa: PLC0415

    postgres = PostgresContainer(POSTGRES_IMAGE, driver="psycopg")
    try:
        postgres.start()
    except Exception as error:  # Docker answers pings but cannot run containers
        if os.environ.get("CI"):
            raise
        pytest.skip(
            f"No test database: run `make test-db` and export DRTC_TEST_DATABASE_URL "
            f"({type(error).__name__}); see docs/operations/local-setup.md"
        )
    try:
        yield postgres.get_connection_url()
    finally:
        postgres.stop()


@pytest.fixture(scope="session")
def migrated_database(database_url: str) -> str:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    return database_url


@pytest.fixture
def clean_database(migrated_database: str) -> str:
    """The migrated schema with every corpus table emptied."""
    engine = create_engine(migrated_database)
    with engine.begin() as connection:
        tables = connection.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
            )
        ).scalars()
        names = ", ".join(f'"{name}"' for name in tables)
        if names:
            connection.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    engine.dispose()
    return migrated_database


@pytest.fixture
async def db_engine(clean_database: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(clean_database)
    yield engine
    await engine.dispose()


@pytest.fixture
def db_sessions(db_engine: AsyncEngine) -> async_sessionmaker:  # type: ignore[type-arg]
    return async_sessionmaker(db_engine, expire_on_commit=False)
