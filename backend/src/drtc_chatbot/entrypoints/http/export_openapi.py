"""Export the OpenAPI contract deterministically.

Usage: ``python -m drtc_chatbot.entrypoints.http.export_openapi [output]``.

CI regenerates the file and fails when it differs from the committed one (contract drift).

"""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from drtc_chatbot.bootstrap.settings import Environment, Settings
from drtc_chatbot.entrypoints.http.app import create_app


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", default="openapi.json", type=Path)
    args = parser.parse_args(argv)
    app = create_app(Settings(_env_file=None, environment=Environment.TEST))
    contract = json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True)
    args.output.write_text(contract + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
