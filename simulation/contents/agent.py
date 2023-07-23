from ..event.event import Event


class Agent:
    def __init__(self, name: str):
        self.name = name
        self._children = []

    def add_child(self, child: "Agent"):
        self._children.append(child)

    def __imatmul__(self, other: "Agent"):
        other.add_child(self)
