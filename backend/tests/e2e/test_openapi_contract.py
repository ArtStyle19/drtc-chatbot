"""The committed OpenAPI file is the API contract the frontend types are generated from."""

import json
from pathlib import Path

from drtc_chatbot.entrypoints.http.export_openapi import main as export_openapi
from tests.conftest import BACKEND_ROOT


def test_export_is_deterministic_and_contains_the_public_routes(tmp_path: Path) -> None:
    first, second = tmp_path / "a.json", tmp_path / "b.json"

    assert export_openapi([str(first)]) == 0
    assert export_openapi([str(second)]) == 0

    assert first.read_bytes() == second.read_bytes()
    paths = json.loads(first.read_text(encoding="utf-8"))["paths"]
    assert {"/api/v1/instruments", "/health/live", "/health/ready"} <= set(paths)


def test_committed_contract_is_up_to_date(tmp_path: Path) -> None:
    fresh = tmp_path / "openapi.json"
    export_openapi([str(fresh)])

    committed = BACKEND_ROOT / "openapi.json"
    assert committed.read_text(encoding="utf-8") == fresh.read_text(encoding="utf-8"), (
        "openapi.json is stale: run `make openapi` and commit the result"
    )
