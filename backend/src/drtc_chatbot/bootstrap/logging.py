"""Structured logging (structlog): JSON in deployed environments, readable console locally."""

import logging

import structlog


def configure_logging(level: str, *, json: bool) -> None:
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]
    if json:
        processors += [structlog.processors.format_exc_info, structlog.processors.JSONRenderer()]
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=False,
    )
    logging.basicConfig(level=log_level, format="%(message)s")
