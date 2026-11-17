"""ASGI entry point: ``uvicorn drtc_chatbot.main:app``."""

from drtc_chatbot.entrypoints.http.app import create_app

app = create_app()
