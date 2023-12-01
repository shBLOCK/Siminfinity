import random

from sim.event.event import TimedEvent, Event
from sim.event.event_queue import EventQueue


class Simulator:
    def __init__(self):
        self._sim_time = 0.0

        self.random = random.Random(1)

        self.event_queue = EventQueue(self)

    @property
    def sim_time(self) -> float:
        return self._sim_time

    def execute_next_event(self) -> Event:
        event = self.event_queue.pop_next_event()

        if event is None:
            return None

        if isinstance(event, TimedEvent):
            self._sim_time = event.sim_time

        event.execute(self)

        return event

    def run_until(self, until: float):
        while (event := self.event_queue.pop_next_event(until)) is not None:
            if isinstance(event, TimedEvent):
                self._sim_time = event.sim_time
            event.execute(self)
        self._sim_time = until

    def advance(self, time: float):
        self.run_until(self.sim_time + time)

    def run(self):
        while self.execute_next_event() is not None:
            pass

        print("Completed")
