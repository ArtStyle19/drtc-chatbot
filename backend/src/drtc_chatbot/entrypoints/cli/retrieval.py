"""Console script ``drtc-retrieval`` (see ``[project.scripts]``)."""

from drtc_chatbot.bootstrap.container import retrieval_module
from drtc_chatbot.contexts.retrieval.presentation.cli.app import build_app


def main() -> None:
    build_app(retrieval_module)()


if __name__ == "__main__":
    main()
