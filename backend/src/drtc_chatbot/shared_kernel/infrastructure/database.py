"""Async SQLAlchemy engine factory and connectivity check."""

import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_database_engine(url: str, *, echo: bool = False) -> AsyncEngine:
    """Create the application's engine. It does not connect until first used."""
    return create_async_engine(url, echo=echo, pool_pre_ping=True)


async def database_is_reachable(engine: AsyncEngine, *, timeout_seconds: float = 2.0) -> bool:
    """Return True when a trivial query succeeds within the timeout."""
    try:
        async with asyncio.timeout(timeout_seconds), engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError, OSError, TimeoutError:
        return False
    return True
