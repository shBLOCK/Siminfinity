import pathlib
import sys
import random
from enum import Enum
from typing import Sequence, Optional, Callable, MutableSequence

from sim.simulator import Simulator
from sim.contents.sim_obj import SimObj
from sim.contents.agent import Agent, PositionalAgent, SpatialAgent
from sim.data.property import SimInstanceProperty
from sim.event.event import TimedEvent, ConditionalEvent, ConditionalEventImpl, TimedEventImpl
from gdmath import *

import path_find

import pygame as pg


simulator: Simulator = None


class Point(PositionalAgent):
    locked_nodes: set[path_find.Node] = set()
    _locked_by: SimInstanceProperty()

    def __init__(self, name: str, position: Vec3):
        super().__init__(name, position)

        self._locked_by: Optional["AGV"] = None

        self.node = path_find.Node(self.position)
        self.node.point = self  # Hacky stuff!
        self.outgoing_paths = []

    @property
    def locked_by(self) -> Optional["AGV"]:
        return self._locked_by

    @locked_by.setter
    def locked_by(self, value: Optional["AGV"]):
        self._locked_by = value
        if value is not None:
            Point.locked_nodes.add(self.node)
        else:
            if self.node in Point.locked_nodes:
                Point.locked_nodes.remove(self.node)

    def find_path(self, connected_to: "Point") -> Optional["Path"]:
        for path in self.outgoing_paths:
            if path.end == connected_to:
                return path
        return None

class Path(Agent):
    begin = SimInstanceProperty()
    end = SimInstanceProperty()

    def __init__(self, name: str, begin: Point, end: Point):
        super().__init__(name)
        self.begin = begin
        self.end = end

        self.begin.node.neighbors.append(self.end.node)
        self.begin.outgoing_paths.append(self)


class AGVState(Enum):
    IDLE = 0
    TO_HOME = 1
    GRAB_SHELF = 2
    TO_DEST = 3
    WAITING = 4
    RETURN_SHELF = 5

class AGV(SpatialAgent):
    state = SimInstanceProperty()
    home = SimInstanceProperty()
    point = SimInstanceProperty()
    destination = SimInstanceProperty()
    move_event = SimInstanceProperty()

    def __init__(self, name: str, point: Point):
        super().__init__(name, Transform3D.translating(point.position))

        self.state = AGVState.IDLE
        self.home = point
        self.point: Point = point
        self.point.locked_by = self
        self.last_point_time = simulator.sim_time
        self.destination: Point = point
        self.path: Optional[MutableSequence[Point]] = None
        self.move_event: AGVMoveEvent = None
        self.unblock_wait_event = None
        self.unblock_timeout_event = None
        self.arrive_callback = None

    @property
    def transform(self) -> Transform3D:
        if self.move_event is None:
            return self._transform
        if simulator.sim_time == self.move_event.sim_time:
            return self.move_event.transform
        a = self._transform
        b = self.move_event.transform
        f = (simulator.sim_time - self.last_point_time) / (self.move_event.sim_time - self.last_point_time)
        return Transform3D(
            a.x + (b.x - a.x) * f,
            a.y + (b.y - a.y) * f,
            a.z + (b.z - a.z) * f,
            a.origin + (b.origin - a.origin) * f
        )

    @transform.setter
    def transform(self, value: Transform3D):
        self._transform = value

    @property
    def shelf(self):
        children = self.children
        return children[0] if len(children) > 0 else None

    @shelf.setter
    def shelf(self, value: "Shelf"):
        self.clear_child()
        value.parent = self

    def _clear_unblock_wait_events(self):
        eq = simulator.event_queue
        eq.try_remove(self.unblock_wait_event)
        eq.try_remove(self.unblock_timeout_event)
        self.unblock_wait_event = None
        self.unblock_timeout_event = None

    def _set_destination(self, dest: Point, callback: Callable[[], None]):
        self.destination = dest
        self.path = None
        self.arrive_callback = callback

        if self.move_event is None:
            self._clear_unblock_wait_events()
            self.navigate()

    def can_do_next_task(self) -> bool:
        return self.state == AGVState.IDLE or self.state == AGVState.TO_HOME

    def assign_task(self, shelf: "Shelf", dest: Point):
        assert self.can_do_next_task()
        self.state = AGVState.GRAB_SHELF
        def grab_callback():
            shelf.parent = self
            self.state = AGVState.TO_DEST
            self._set_destination(dest, dest_callback)
        def dest_callback():
            shelf.parent = dest
            self.state = AGVState.WAITING
            simulator.event_queue << TimedEventImpl(simulator.sim_time + 10, waiting_complete_callback)
        def waiting_complete_callback(*_):
            shelf.parent = self
            self.state = AGVState.RETURN_SHELF
            self._set_destination(shelf.point, returned_callback)
        def returned_callback():
            shelf.parent = shelf.point
            self.state = AGVState.TO_HOME
            self._set_destination(self.home, arrived_at_home_callback)
        def arrived_at_home_callback():
            self.state = AGVState.IDLE

        self.state = AGVState.GRAB_SHELF
        self._set_destination(shelf.parent, grab_callback)

    def navigate(self):
        if self.point == self.destination:
            self.path = None
            self.move_event = None
            callback = self.arrive_callback
            self.arrive_callback = None
            callback()
            return

        if self.path is None:
            self.path = path_find.path_find(self.point.node, self.destination.node, Point.locked_nodes)
            if self.path is None:
                # print("No valid path considering locked points")
                self.path = path_find.path_find(self.point.node, self.destination.node)
            assert self.path is not None, "No valid path!"
            self.path = list(self.path)

        assert self.path[0] == self.point.node and self.path[-1] == self.destination.node

        next_point = self.path[1].point
        if next_point.locked_by is None:
            next_point.locked_by = self
            # TODO: rotate
            self.move_event = AGVMoveEvent(self, next_point, Transform3D.translating(next_point.position))
            # print(f"{self.name} moving to {next_point} at {next_point.position}")
            simulator.event_queue << self.move_event
            del self.path[0]
        else:
            self.move_event = None
            def wait_callback(*_):
                self._clear_unblock_wait_events()
                # print("Conflict resolved", self)
                self.navigate()
            self.unblock_wait_event = ConditionalEventImpl(lambda: next_point.locked_by is None, wait_callback)
            def timeout_callback(*_):
                self._clear_unblock_wait_events()
                # print("Conflict timeout, Rerouting...")
                self.path = None
                self.navigate()
            self.unblock_timeout_event = TimedEventImpl(simulator.sim_time + 5, timeout_callback)
            simulator.event_queue << self.unblock_wait_event << self.unblock_timeout_event


class AGVMoveEvent(TimedEvent):
    def __init__(self, agv: "AGV", dest_point: Point, dest_transform: Transform3D):
        super().__init__(simulator.sim_time + (agv.position | dest_point.position) / 1.0)
        self.agv = agv
        self.point = dest_point
        self.transform = dest_transform

    def execute(self, _: Simulator) -> None:
        self.agv.point.locked_by = None
        self.agv.point = self.point
        self.agv.transform = self.transform
        self.agv.last_point_time = simulator.sim_time
        self.agv.navigate()


class Shelf(Agent):
    point = SimInstanceProperty()

    def __init__(self, name: str, point: Point):
        super().__init__(name)
        self.point = point
        self.parent = point


class SourceEvent(TimedEvent):
    def __init__(self, agvs: Sequence[AGV], shelves: Sequence[Shelf], dest_points: Sequence[Point]):
        super().__init__(0)
        self.agvs = agvs
        self.shelves = shelves
        self.dest_points = dest_points

    def execute(self, simulator: Simulator) -> None:
        grounded_shelves = [s for s in self.shelves if isinstance(s.parent, Point)]
        if grounded_shelves:
            shelf = simulator.random.choice(grounded_shelves)
            for agv in sorted(self.agvs, key=lambda a: a.position | shelf.global_position):
                if not agv.can_do_next_task():
                    continue
                if agv.shelf is None:
                    agv.assign_task(shelf, simulator.random.choice(self.dest_points))
                    break
            else:
                pass
                # print("No free AGVs found, skipping a task!")

        self.sim_time += 8
        simulator.event_queue << self


def create_network(begin: Vec2i, end: Vec2i) -> Agent:
    network = Agent("Network")

    cnt = -1
    points = {}
    for x in range(begin.x, end.x + 1):
        for z in range(begin.y, end.y + 1):
            pos = Vec3i(x, 0, z)
            point = Point(f"Point{(cnt:=cnt+1)}", Vec3(pos))
            points[pos] = point
            point.parent = network

    cnt = -1
    for pos, point in points.items():
        if pos.x > 0:
            other = points[pos - Vec3i(1, 0, 0)]
            Path(f"Path{(cnt:=cnt+1)}", point, other).parent = network
            Path(f"Path{(cnt:=cnt+1)}", other, point).parent = network
        if pos.z > 0:
            other = points[pos - Vec3i(0, 0, 1)]
            Path(f"Path{(cnt:=cnt+1)}", point, other).parent = network
            Path(f"Path{(cnt:=cnt+1)}", other, point).parent = network

    return network

def create_agvs(network: Agent, validator: Callable[[Point], bool]) -> Agent:
    agvs = Agent("AGVs")
    cnt = -1
    for obj in network.children:
        if isinstance(obj, Point):
            if validator(obj):
                agv = AGV(f"AGV{(cnt:=cnt+1)}", obj)
                agv.parent = agvs
    return agvs

def cerate_shelves(network: Agent, validator: Callable[[Point], bool]) -> list[Shelf]:
    shelves = []
    cnt = -1
    for obj in network.children:
        if isinstance(obj, Point):
            if validator(obj):
                shelve = Shelf(f"Shelf{(cnt:=cnt+1)}", obj)
                shelves.append(shelve)
    return shelves


screen_transform = Transform2D.scaling(Vec2(50)).translated(Vec2(50))
screen = None

def sp(pos: Vec3) -> tuple[float, float]:
    """Global position to screen position"""
    return tuple(screen_transform(pos.xz))

def ss(size: float) -> float:
    return size * screen_transform.scale.x


def draw_network(network):
    for obj in network.children:
        if isinstance(obj, Path):
            pg.draw.aaline(
                screen,
                (255,255,255),
                sp(obj.begin.position),
                sp(obj.end.position)
            )

    for obj in network.children:
        if isinstance(obj, Point):
            color = (200,0,0) if obj.locked_by is not None else (0,200,0)
            pg.draw.circle(
                screen,
                color,
                sp(obj.position),
                ss(0.1)
            )

# def agv_transform(agv: AGV, ft: float):
#     if agv.move_event is None:
#         return agv.transform
#

def draw_agvs(agvs: Agent):
    for agv in agvs.children:
        size = 0.3
        pts = (Vec3(-size, 0, -size), Vec3(size, 0, -size), Vec3(size, 0, size), Vec3(-size, 0, size))
        transform = agv.global_transform
        r = random.Random(agv.obj_id)
        color = pg.color.Color.from_hsva(r.random() * 360, 100, 100, 100)
        pg.draw.polygon(
            screen,
            color,
            [sp(transform * p) for p in pts]
        )

        if agv.path is not None and len(agv.path) >= 2:
            pg.draw.lines(
                screen,
                color,
                False,
                [sp(agv.position)] + [sp(node.pos) for node in agv.path],
                max(1, int(ss(0.2)))
            )

def draw_shelves(shelves: Sequence[Shelf]):
    for shelf in shelves:
        r = random.Random(shelf.obj_id)
        color = pg.color.Color.from_hsva(r.random() * 360, 50, 80, 100)
        size = 0.4
        pts = (Vec3(-size, 0, -size), Vec3(size, 0, -size), Vec3(size, 0, size), Vec3(-size, 0, size))
        transform = shelf.global_transform
        pg.draw.polygon(
            screen,
            color,
            [sp(transform * p) for p in pts],
            max(1, int(ss(0.06)))
        )


def main():
    global simulator, screen, screen_transform
    simulator = Simulator()

    network = create_network(Vec2i(0, 0), Vec2i(13, 12))
    agvs = create_agvs(network, lambda point: point.position.x < 1 and point.position.z < 100)
    def shelf_pos_validator(point: Point):
        p = point.position
        if not 2 <= p.x <= 8:
            return False
        return int(p.z % 3) in (1, 2)
    shelves = cerate_shelves(network, shelf_pos_validator)

    dest_points = [p for p in network.children if isinstance(p, Point) and p.position.x >= 13]
    source_event = SourceEvent(list(agvs.children), shelves, dest_points)
    simulator.event_queue << source_event


    screen = pg.display.set_mode((800, 700), pg.RESIZABLE)
    clock = pg.Clock()

    ft = 0.0
    speed = 1
    while True:
        ft += clock.get_time() / 1000 * speed
        simulator.run_until(ft)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEWHEEL:
                screen_transform @= Transform2D.scaling(Vec2(1 + event.y * 0.1))
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_DOWN:
                    speed *= 0.5
                elif event.key == pg.K_UP:
                    speed *= 1.5

        screen.fill(0)

        draw_agvs(agvs)
        draw_network(network)
        draw_shelves(shelves)

        pg.display.set_caption(f"Logistics Demo - {simulator.sim_time:.2f}s - Spd:{speed:.2f} - E:{simulator.event_queue._test_temp_eid} - {clock.get_fps():.1f}FPS")
        pg.display.flip()
        clock.tick(20)


if __name__ == '__main__':
    main()
