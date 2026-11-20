"""The ``drtc-ingest`` command line against a real database."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from typer.testing import CliRunner

from drtc_chatbot.bootstrap.container import IngestionModule, build_container
from drtc_chatbot.contexts.ingestion.presentation.cli.app import build_app
from tests.conftest import make_settings

pytestmark = pytest.mark.docker

LEY = "ley-27181@2020-05"


@pytest.fixture
def cli(clean_database: str, monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    settings = make_settings(
        database_url=clean_database.replace("postgresql://", "postgresql+psycopg://"),
        catalog_backend="database",
        ingestion_approval_policy="auto_dev",
    )

    @asynccontextmanager
    async def module() -> AsyncIterator[IngestionModule]:
        container = build_container(settings)
        try:
            yield container.ingestion
        finally:
            await container.aclose()

    runner = CliRunner()
    app = build_app(module)
    return lambda *args: runner.invoke(app, list(args))


@pytest.mark.spec("002-FR-005")
def test_run_ingests_and_says_loudly_that_the_dev_policy_approved_it(cli) -> None:  # type: ignore[no-untyped-def]
    result = cli("run", LEY)

    assert result.exit_code == 0, result.output
    assert "actualizada" in result.output
    assert "Artículos numerados: 36 (sin saltos)" in result.output
    assert "paragraph_replacement_unapplied: 5" in result.output
    assert "Aprobada automáticamente (auto_dev): solo desarrollo." in result.output


@pytest.mark.spec("002-FR-004")
def test_a_second_run_reports_no_changes(cli) -> None:  # type: ignore[no-untyped-def]
    cli("run", LEY)

    again = cli("run", LEY)

    assert "sin cambios" in again.output


def test_report_shows_the_last_job_and_sample_prints_provisions_without_storing(cli) -> None:  # type: ignore[no-untyped-def]
    cli("run", LEY)

    report = cli("report", LEY)
    sample = cli("sample", LEY, "-n", "5", "--seed", "1")

    assert '"numeric_articles": 36' in report.output
    assert sample.output.count("[p.") + sample.output.count("[pp.") == 5


def test_errors_are_reported_without_a_traceback(cli) -> None:  # type: ignore[no-untyped-def]
    unknown = cli("run", "ley-inventada@2020")
    approve_nothing = cli("approve", LEY, "--reviewer", "Ana")  # never ingested

    assert unknown.exit_code == 1
    assert "Unknown instrument version" in unknown.output
    assert approve_nothing.exit_code == 1
    assert "no ingested provisions" in approve_nothing.output
    assert cli("run").exit_code != 0  # needs a version or --all
