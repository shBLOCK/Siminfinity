import weakref
from abc import ABC, abstractmethod

from sim.contents.sim_obj import SimObj
from sim.data.property import SimInstanceProperty


class SimCmd(ABC):
    __slots__ = ()

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass


class SimCmdNewSimObj(SimCmd):
    def run(self) -> None:
        pass

    def undo(self) -> None:
        pass


class SimCmdDelSimObj(SimCmd):
    pass


class SimCmdPropertyChanged(SimCmd):
    def __init__(self, prop: SimInstanceProperty, obj: SimObj, value):
        self.prop: SimInstanceProperty = prop
        self.obj: weakref.ProxyType[SimObj] = weakref.proxy(obj)
        self.obj_id: int = obj.obj_id

    def run(self):
        pass

    def undo(self):
        pass
