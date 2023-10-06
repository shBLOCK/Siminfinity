from weakref import WeakValueDictionary
from typing import Optional, Iterator


class SimObj:
    """
    Base object for all "data objects" of a simulation.

    Being a "data class" means that they are serializable and copyable,
    so that they can be saved and (potentially) be synced with the frontend.

    Override __getstate__ and __setstate__ to change the default behavior.
    """

    _next_id: int = 0
    _obj_by_id: WeakValueDictionary[int, "SimObj"] = WeakValueDictionary()

    @classmethod
    def next_id(cls) -> int:
        i = cls._next_id
        cls._next_id += 1
        return i

    @classmethod
    def from_id(cls, sim_id: int) -> Optional["SimObj"]:
        return cls._obj_by_id.get(sim_id)

    @classmethod
    def all_objs(cls) -> Iterator["SimObj"]:
        return cls._obj_by_id.values()

    __slots__ = "obj_id"

    def __init__(self):
        self.obj_id: int = SimObj.next_id()

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass

    def __del__(self):
        pass

    # TODO copy
