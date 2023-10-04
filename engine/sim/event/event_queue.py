import bisect
import random
from enum import IntEnum
from typing import Optional, Iterator, MutableSequence, MutableMapping, TYPE_CHECKING

from sim.event.event import Event, TimedEvent, ConditionEvent
if TYPE_CHECKING:
    from sim.simulator import Simulator


class OrderingMode(IntEnum):
    FIFO = 0
    LIFO = 1
    RANDOM = 2


class EventQueue:
    def __init__(self, simulator: "Simulator", ordering_mode: OrderingMode = OrderingMode.FIFO):
        self.sim = simulator

        self.ordering_mode = ordering_mode

        self._timed_events_queue: MutableSequence[TimedEvent] = []
        self._condition_events: MutableSequence[ConditionEvent] = []

        self._event_id_to_time: MutableMapping[int, float] = {}
        self._time_to_event_id: MutableMapping[float, MutableSequence[int]] = {}

    def _add_timed_event(self, event: TimedEvent):
        assert event.sim_time >= self.sim.sim_time
        match self.ordering_mode:
            case OrderingMode.FIFO:
                bisect.insort_right(self._timed_events_queue, event, key=lambda e: e.sim_time)
            case OrderingMode.LIFO:
                bisect.insort_left(self._timed_events_queue, event, key=lambda e: e.sim_time)
            case OrderingMode.RANDOM:
                # noinspection PyTypeChecker
                self._timed_events_queue.insert(
                    self.sim.rng.randint(
                        bisect.bisect_left(self._timed_events_queue, event, key=lambda e: e.sim_time),
                        bisect.bisect_right(self._timed_events_queue, event, key=lambda e: e.sim_time)
                    ),
                    event
                )

    def _add_condition_event(self, event: ConditionEvent):
        self._condition_events.append(event)

    def _remove_timed_event(self, event: TimedEvent):
        self._timed_events_queue.remove(event)

    def _remove_condition_event(self, event: ConditionEvent):
        self._condition_events.remove(event)

    def add(self, event: Event) -> None:
        assert event is Event
        if isinstance(event, TimedEvent):
            self._add_timed_event(event)
        elif isinstance(event, ConditionEvent):
            self._add_condition_event(event)
        else:
            assert False

    def remove(self, event: Event) -> None:
        assert event is Event
        if isinstance(event, TimedEvent):
            self._remove_timed_event(event)
        elif isinstance(event, ConditionEvent):
            self._remove_condition_event(event)
        else:
            assert False

    def __ilshift__(self, other: Event) -> None:
        self.add(other)

    def __delitem__(self, key) -> None:
        self.remove(key)

    def __contains__(self, item: Event) -> bool:
        assert item is Event
        if isinstance(item, TimedEvent):
            return item in self._timed_events_queue
        if isinstance(item, ConditionEvent):
            return item in self._condition_events
        assert False

    def __iter__(self) -> Iterator[Event]:
        def gen():
            for e in self._timed_events_queue:
                yield e
            for e in self._condition_events:
                yield e
        return gen()

    def __len__(self) -> int:
        return len(self._timed_events_queue) + len(self._condition_events)

    def next_timed_event(self) -> Optional[TimedEvent]:
        return self._timed_events_queue[0] if self._timed_events_queue else None

    def pop_next_timed_event(self) -> Optional[TimedEvent]:
        return self._timed_events_queue.pop(0) if self._timed_events_queue else None
