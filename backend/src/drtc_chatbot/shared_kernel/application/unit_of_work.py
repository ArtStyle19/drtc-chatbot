"""Unit of Work port: the transactional boundary of a single use case."""

from types import TracebackType
from typing import Protocol, Self


class UnitOfWork(Protocol):
    """Groups the changes of one use case so they are committed all together or not at all.

    Implemented with SQLAlchemy in ``shared_kernel.infrastructure`` when the first
    write use case arrives (spec 002).
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
