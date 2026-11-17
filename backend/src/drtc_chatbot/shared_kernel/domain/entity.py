"""Entity base class: an object defined by its identity, not by its attributes."""


class Entity[IdT]:
    """Domain object with a stable identity.

    Two entities are equal when they have the same concrete type and the same id,
    regardless of their other attributes.
    """

    __slots__ = ("_id",)

    def __init__(self, entity_id: IdT) -> None:
        self._id = entity_id

    @property
    def id(self) -> IdT:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity) or type(other) is not type(self):
            return False
        return bool(self._id == other._id)

    def __hash__(self) -> int:
        return hash((type(self).__qualname__, self._id))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id!r})"
