import random

from event.event_queue import EventQueue


class Simulator:
    def __init__(self):
        self._time = 0.0

        self.rng = random.Random()

        self.event_queue = EventQueue(self)

    @property
    def time(self) -> float:
        return self._time

    def process(self):
        event = self.event_queue.pop_next_timed_event()
        if event is None:
            self.complete()

        event.execute()

    def run(self):
        while True:
            self.process()

    def complete(self):
        pass
