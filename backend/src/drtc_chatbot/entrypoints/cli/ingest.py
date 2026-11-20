"""Console script ``drtc-ingest`` (see ``[project.scripts]``)."""

from drtc_chatbot.bootstrap.container import ingestion_module
from drtc_chatbot.contexts.ingestion.presentation.cli.app import build_app


def main() -> None:
    build_app(ingestion_module)()


if __name__ == "__main__":
    main()
