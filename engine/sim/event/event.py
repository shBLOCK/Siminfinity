from abc import ABC, abstractmethod
from typing import Callable


class Event(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self) -> None:
        pass

class TimedEvent(Event, ABC):
    def __init__(self, sim_time: float):
        super().__init__()
        self.sim_time = sim_time

class TimedEventImpl(TimedEvent):
    def __init__(self, sim_time: float, execute_func: Callable[[], None]):
        super().__init__(sim_time)

        self.execute_func = execute_func

    def execute(self) -> None:
        self.execute_func()

class ConditionEvent(Event, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def check(self) -> bool:
        pass

class ConditionEventImpl(ConditionEvent):
    def __init__(self, check_func: Callable[[], bool], execute_func: Callable[[], None]):
        super().__init__()

        self.check_func = check_func
        self.execute_func = execute_func

    def check(self) -> bool:
        return self.check_func()

    def execute(self) -> None:
        self.execute_func()
