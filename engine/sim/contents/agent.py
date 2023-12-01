from gdmath import *
from typing import Optional, MutableSequence, Sequence, Iterable
from abc import ABC, abstractmethod

from sim.contents.sim_obj import SimObj
from sim.data.property import SimInstanceProperty


class Agent(SimObj):
    name = SimInstanceProperty()

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self._children: MutableSequence[Agent] = []
        self._parent: Optional[Agent] = None

    def __repr__(self):
        return self.name

    def add_child(self, child: "Agent") -> None:
        assert child._parent is None, "The agent already has a parent."
        self._children.append(child)
        child._parent = self

    def remove_child(self, child: "Agent") -> None:
        assert child in self._children, "The agent is not a child of this agent."
        self._children.remove(child)
        child._parent = None

    def clear_child(self) -> None:
        for c in self._children:
            c._parent = None
        self._children.clear()

    def find_child(self, name: str) -> Optional["Agent"]:
        for c in self._children:
            if c.name == name:
                return c
        return None

    @property
    def children(self) -> Sequence["Agent"]:
        return tuple(self._children)

    @property
    def parent(self) -> Optional["Agent"]:
        return self._parent

    @parent.setter
    def parent(self, value: "Agent") -> None:
        if self._parent is not None:
            self._parent.remove_child(self)
        value.add_child(self)


    def _xform(self, transform: Transform3D) -> Transform3D:
        """
        Transform a Transform3D with this agent's local transform.
        :param transform: the Transform3D to be transformed, can be modified
        """
        return transform

    @property
    def transform(self) -> Transform3D:
        return Transform3D()

    @transform.setter
    def transform(self, value: Transform3D) -> None:
        raise AttributeError("This agent's transformation can't be set")

    @property
    def position(self) -> Vec3:
        return Vec3()

    @position.setter
    def position(self, value: Vec3) -> None:
        raise AttributeError("This agent's position can't be set")

    @property
    def global_transform(self) -> Transform3D:
        """
        Calculate the transform of this agent from the root of its branch.
        """
        transform = Transform3D(self.transform)
        agent = self._parent
        while agent is not None:
            transform @= agent.transform
            agent = agent._parent
        return transform

    @property
    def global_position(self) -> Vec3:
        """
            Calculate the translation of this agent from the root of its branch.
        """
        return self.global_transform.origin


class SpatialAgent(Agent):
    _transform: Transform3D = SimInstanceProperty()

    def __init__(self, name: str, transform: Transform3D):
        super().__init__(name)
        self._transform = transform

    def _xform(self, transform: Transform3D) -> Transform3D:
        transform @= self._transform
        return transform

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = value

    @property
    def position(self) -> Vec3:
        return self.transform.origin

    @position.setter
    def position(self, value: Vec3) -> None:
        self.transform.origin = value


class PositionalAgent(Agent):
    position: Vec3 = SimInstanceProperty()

    def __init__(self, name: str, position: Vec3):
        super().__init__(name)
        self.position = position

    def _xform(self, transform: Transform3D) -> Transform3D:
        transform.translate_ip(self.position)

    @property
    def transform(self) -> Transform3D:
        return Transform3D.translating(self.position)

    @transform.setter
    def transform(self, value: Transform3D) -> None:
        self.transform = value
