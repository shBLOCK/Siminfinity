from typing import Optional, Sequence, Collection, Iterable
from bisect import insort_left

from gdmath import *


class Node:
    def __init__(self, pos: Vec3):
        self.pos = pos
        self.neighbors: list[Node] = []
        self.parent: Optional[Node] = None
        self.h_cost: Optional[float] = None
        self.g_cost: Optional[float] = None


def path_find(begin: Node, end: Node, ignore_nodes: Collection[Node] = ()) -> Optional[Iterable[Node]]:
    opened = [begin]
    closed = set()

    while len(opened) > 0:
        current = opened.pop(0)

        if current == end:
            path = [current]
            while (current := current.parent) is not None:
                path.append(current)

            for node in opened:
                node.parent = None
            for node in closed:
                node.parent = None

            return reversed(path)

        closed.add(current)

        for neighbor in current.neighbors:
            if neighbor in ignore_nodes or neighbor in closed:
                continue

            neighbor_open = neighbor in opened

            g_cost = neighbor.pos | current.pos
            node = current
            while node.parent is not None:
                g_cost += node.pos | node.parent.pos
                node = node.parent

            if not neighbor_open or g_cost < neighbor.g_cost:
                neighbor.h_cost = neighbor.pos | end.pos
                neighbor.g_cost = g_cost
                neighbor.parent = current
                if not neighbor_open:
                    insort_left(opened, neighbor, key=lambda n: n.h_cost + n.g_cost)
                    opened.append(neighbor)

    for node in closed:
        node.parent = None

    return None
