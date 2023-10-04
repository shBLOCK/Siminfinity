from sim.contents.sim_obj import SimObj
from sim.event.event import Event


class Agent(SimObj):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self._children = []

    def add_child(self, child: "Agent"):
        self._children.append(child)

    def __imatmul__(self, other: "Agent"):
        other.add_child(self)