from weakref import WeakSet
from abc import ABC, abstractmethod
from typing import MutableSequence


class SimProperty(ABC):
    __slots__ = "owner", "name"

    all_properties: MutableSequence["SimProperty"] = []

    def __init__(self):
        SimProperty.all_properties.append(self)

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    @abstractmethod
    def __get__(self, instance, owner):
        pass

    @abstractmethod
    def __set__(self, instance, value):
        pass

    def __delete__(self, instance):
        raise AttributeError(
            f"SimProperty {self.name} of {self.owner if instance is None else instance} may not be deleted"
        )


class SimClassProperty(SimProperty):
    __slots__ = "value", "dirty"

    def __get__(self, instance, owner):
        if instance is not None:
            raise AttributeError(f"Can not access SimClassProperty {self.name} of {self.owner} from an instance")
        return self.value

    def __set__(self, instance, value):
        if instance is not None:
            raise AttributeError(f"Can not access SimClassProperty {self.name} of {self.owner} from an instance")
        self.value = value
        self.dirty = True


class SimInstanceProperty(SimProperty):
    __slots__ = (
        "value_name",
        "dirty_name",
        "instances",
    )

    def __set_name__(self, owner, name):
        super().__set_name__(owner, name)

        from sim.contents.sim_obj import SimObj
        if not issubclass(owner, SimObj):
            raise AttributeError("SimInstanceProperty may only be used in SimObj")

        self.value_name: str = f"_sim_value_{name}"
        self.dirty_name: str = f"_sim_dirty_{name}"

        self.instances: WeakSet = WeakSet()

    def __get__(self, instance, owner):
        return getattr(instance, self.value_name)

    def __set__(self, instance, value):
        setattr(instance, self.value_name, value)
        setattr(instance, self.dirty_name, True)
