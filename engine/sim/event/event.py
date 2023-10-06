from abc import ABC, abstractmethod
from typing import Callable

import sim.simulator


class Event(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def execute(self, simulator: "sim.simulator.Simulator") -> None:
        pass

class TimedEvent(Event, ABC):
    def __init__(self, sim_time: float):
        super().__init__()
        self.sim_time = sim_time

class TimedEventImpl(TimedEvent):
    def __init__(self, sim_time: float, execute_func: Callable[["TimedEventImpl", "sim.simulator.Simulator"], None]):
        super().__init__(sim_time)

        self.execute_func = execute_func

    def execute(self, simulator: "sim.simulator.Simulator") -> None:
        self.execute_func(self, simulator)

class ConditionalEvent(Event, ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def check(self) -> bool:
        pass

class ConditionalEventImpl(ConditionalEvent):
    def __init__(self, check_func: Callable[[], bool], execute_func: Callable[["sim.simulator.Simulator"], None]):
        super().__init__()

        self.check_func = check_func
        self.execute_func = execute_func

    def check(self) -> bool:
        return self.check_func()

    def execute(self, simulator: "sim.simulator.Simulator") -> None:
        self.execute_func(simulator)
