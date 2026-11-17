from datetime import UTC, datetime

from drtc_chatbot.shared_kernel.domain import AggregateRoot, DomainEvent, Entity


class Norm(Entity[str]):
    __slots__ = ("title",)

    def __init__(self, entity_id: str, title: str) -> None:
        super().__init__(entity_id)
        self.title = title


class OtherNorm(Entity[str]):
    __slots__ = ()


def test_entities_with_the_same_id_are_equal_even_if_attributes_differ() -> None:
    assert Norm("ley-27181", "A") == Norm("ley-27181", "B")
    assert hash(Norm("ley-27181", "A")) == hash(Norm("ley-27181", "B"))


def test_entities_of_different_types_are_never_equal() -> None:
    assert Norm("x", "A") != OtherNorm("x")


class Changed(DomainEvent):
    pass


class Aggregate(AggregateRoot[str]):
    __slots__ = ()

    def change(self) -> None:
        self._record_event(Changed(occurred_at=datetime(2026, 1, 1, tzinfo=UTC)))


def test_aggregate_events_are_returned_once_and_cleared() -> None:
    aggregate = Aggregate("a-1")
    aggregate.change()

    assert len(aggregate.pull_events()) == 1
    assert aggregate.pull_events() == []
