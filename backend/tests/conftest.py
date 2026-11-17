"""Shared fixtures. Tests never read the developer's .env file."""

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest

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
    if not any(item.get_closest_marker("docker") for item in items) or _docker_is_available():
        return
    skip = pytest.mark.skip(reason="Docker is not available")
    for item in items:
        if item.get_closest_marker("docker"):
            item.add_marker(skip)
