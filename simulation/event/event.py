from abc import ABC, abstractmethod


class Event(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass

class TimedEvent(Event, ABC):
    def __init__(self, time: float):
        self.time = time

class ConditionEvent(Event, ABC):
    def __init__(self):
        pass

    @abstractmethod
    def check(self) -> bool:
        pass
