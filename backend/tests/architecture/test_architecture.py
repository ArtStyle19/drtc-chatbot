"""Architecture fitness functions (ADR-0002). They run with the normal test suite."""

from pathlib import Path

import pytest
from importlinter.cli import lint_imports

from tests.conftest import BACKEND_ROOT

PACKAGE_ROOT = BACKEND_ROOT / "src" / "drtc_chatbot"
CONTEXTS = sorted(
    path for path in (PACKAGE_ROOT / "contexts").iterdir() if (path / "__init__.py").is_file()
)
LAYERS = ("domain", "application", "infrastructure", "presentation")


def test_import_contracts_are_kept() -> None:
    exit_code = lint_imports(
        config_filename=str(BACKEND_ROOT / "pyproject.toml"), no_cache=True, no_logo=True
    )
    assert exit_code == 0, "An architecture contract is broken: run `uv run lint-imports`"


@pytest.mark.parametrize("context", CONTEXTS, ids=lambda path: path.name)
def test_every_bounded_context_follows_the_standard_layout(context: Path) -> None:
    for layer in LAYERS:
        assert (context / layer / "__init__.py").is_file(), f"{context.name} lacks {layer}/"
    assert (context / "api.py").is_file(), f"{context.name} lacks its public facade api.py"
    assert (context / "README.md").is_file(), f"{context.name} lacks a README.md"
