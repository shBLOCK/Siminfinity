import math
import pathlib
import sys
import random
import time
from enum import Enum
from itertools import permutations, product
from typing import Sequence, Optional, Callable, MutableSequence

import tqdm

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


def update_network(network: Agent):
    for obj in network.children:
        if isinstance(obj, Point):
            obj.node = path_find.Node(obj.position)
            obj.node.point = obj  # Hacky stuff!

    for obj in network.children:
        if isinstance(obj, Path):
            obj.begin.node.neighbors.append(obj.end.node)


def normalize_rotation(rot: float) -> float:
    return rot % (math.pi * 2)

def rotation_diff(a: float, b: float) -> float:
    d = abs(a - b) % (math.pi * 2)
    return min(d, math.pi * 2 - d)


class AGVState(Enum):
    IDLE = 0
    TO_HOME = 1
    GRAB_SHELF = 2
    TO_DEST = 3
    WAITING = 4
    RETURN_SHELF = 5

class AGV(Agent):
    state = SimInstanceProperty()
    home = SimInstanceProperty()
    point = SimInstanceProperty()
    destination = SimInstanceProperty()
    move_event = SimInstanceProperty()

    def __init__(self, name: str, point: Point, rotation: float, color: pg.Color, shelves: Sequence["Shelf"]):
        super().__init__(name)

        self.state = AGVState.IDLE
        self.home = point
        self.point: Point = point
        self.point.locked_by = self
        self.rotation = rotation
        self.color = color
        self.move_begin_time = simulator.sim_time
        self.destination: Point = point
        self.path: Optional[MutableSequence[Point]] = None
        self.move_event: AGVMoveEvent = None
        self.unblock_wait_event = None
        self.unblock_timeout_event = None
        self.arrive_callback = None
        self.locked_points = [self.point]

        self.shelves = shelves

    def _lerp(self):
        if self.move_event.sim_time == self.move_begin_time:
            return 0
        l = (simulator.sim_time - self.move_begin_time) / (self.move_event.sim_time - self.move_begin_time)
        return l
        # return math.cos(l * math.pi * 3) * -0.5 + 0.5

    @property
    def transform(self) -> Transform3D:
        rotation = self.rotation
        if self.move_event is not None:
            rotation1 = self.move_event.rotation
            rotation = rotation + (rotation1 - rotation) * self._lerp()
            rotation = normalize_rotation(rotation)
        return Transform3D.rotating(Vec3(0, 1, 0), rotation, origin=self.position)

    @property
    def position(self) -> Vec3:
        pos = self.point.position
        if self.move_event is not None:
            pos1 = self.move_event.point.position
            pos = pos + (pos1 - pos) * self._lerp()
        return pos

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
        def grab_arrived_callback():
            simulator.event_queue << TimedEventImpl(simulator.sim_time + 3, grab_done_callback)
        def grab_done_callback(*_):
            shelf.parent = self
            self.state = AGVState.TO_DEST
            self._set_destination(dest, dest_callback)
        def dest_callback():
            wait_time = 16
            self.state = AGVState.WAITING
            def put_shelf(*_):
                shelf.parent = dest
            def pick_shelf(*_):
                shelf.parent = self
            simulator.event_queue << TimedEventImpl(simulator.sim_time + 3, put_shelf)
            simulator.event_queue << TimedEventImpl(simulator.sim_time + wait_time - 3, pick_shelf)
            simulator.event_queue << TimedEventImpl(simulator.sim_time + wait_time, waiting_complete_callback)
        def waiting_complete_callback(*_):
            self.state = AGVState.RETURN_SHELF
            self._set_destination(shelf.point, return_arrived_callback)
            shelf.destination = shelf.point
        def return_arrived_callback():
            simulator.event_queue << TimedEventImpl(simulator.sim_time + 3, return_done_callback)
        def return_done_callback(*_):
            shelf.parent = shelf.point
            self.state = AGVState.TO_HOME
            self._set_destination(self.home, arrived_at_home_callback)
        def arrived_at_home_callback():
            self.state = AGVState.IDLE

        self.state = AGVState.GRAB_SHELF
        self._set_destination(shelf.parent, grab_arrived_callback)

    def update_locked_points(self) -> bool:
        for lp in self.locked_points:
            lp.locked_by = None
        self.locked_points.clear()
        self.point.locked_by = self
        self.locked_points.append(self.point)
        success = True
        if self.path is not None:
            for i in range(1, 3):
                if len(self.path) > i:
                    if self.path[i].point.locked_by is None:
                        self.path[i].point.locked_by = self
                        self.locked_points.append(self.path[i].point)
                    else:
                        success = False
        return success

    def navigate(self):
        if self.point == self.destination:
            self.path = None
            self.move_event = None
            self.update_locked_points()
            callback = self.arrive_callback
            self.arrive_callback = None
            callback()
            return

        if self.path is None or False:
            if self.shelf is not None:
                ignore_nodes = {s.parent.node for s in self.shelves if isinstance(s.parent, Point)}
            else:
                ignore_nodes = set()
            self.path = path_find.path_find(self.point.node, self.destination.node, ignore_nodes.union(filter(lambda n: n.point not in self.locked_points, Point.locked_nodes)))
            if self.path is None:
                # print("No valid path considering locked points")
                self.path = path_find.path_find(self.point.node, self.destination.node, ignore_nodes)

            if self.path is not None:
                self.path = list(self.path)

        if self.path is not None:
            assert self.path[0] == self.point.node and self.path[-1] == self.destination.node

        locking_succeed = self.update_locked_points()

        if self.path is not None and (next_point := self.path[1].point).locked_by == self and locking_succeed:
            direction = (next_point.position - self.point.position).xz
            next_rotation = normalize_rotation(math.atan2(-direction.y, direction.x))
            if rotation_diff(next_rotation, self.rotation) < 1e-7:
                self.move_event = AGVMoveEvent(self, next_point, self.rotation)
                # print(f"{self.name} moving to {next_point} at {next_point.position}")
                simulator.event_queue << self.move_event
                del self.path[0]
            else:
                if abs(self.rotation - next_rotation) <= math.pi:
                    rot = next_rotation
                else:
                    if next_rotation < self.rotation:
                        rot = next_rotation + math.pi * 2
                    else:
                        rot = next_rotation - math.pi * 2
                self.move_event = AGVMoveEvent(self, self.point, rot)
                simulator.event_queue << self.move_event
            self.move_begin_time = simulator.sim_time
        else:
            self.move_event = None
            if self.path is not None:
                def wait_callback(*_):
                    self._clear_unblock_wait_events()
                    # print("Conflict resolved", self)
                    self.navigate()
                self.unblock_wait_event = ConditionalEventImpl(lambda: next_point.locked_by is None, wait_callback)
                simulator.event_queue << self.unblock_wait_event
            def timeout_callback(*_):
                self._clear_unblock_wait_events()
                # print("Conflict timeout, Rerouting...")
                self.path = None
                self.navigate()
            timeout = 5 if self.path is not None else 1
            self.unblock_timeout_event = TimedEventImpl(simulator.sim_time + timeout, timeout_callback)
            simulator.event_queue << self.unblock_timeout_event


class AGVMoveEvent(TimedEvent):
    def __init__(self, agv: "AGV", point: Point, rotation: float):
        if agv.point != point:
            t = (agv.position | point.position) / 1.0
        else:
            t = abs(agv.rotation - rotation) / (math.pi * 0.5)
        super().__init__(simulator.sim_time + t)
        self.agv = agv
        self.point = point
        self.rotation = rotation

    def execute(self, _: Simulator) -> None:
        self.agv.point = self.point
        self.agv.rotation = normalize_rotation(self.rotation)
        self.agv.navigate()


class Shelf(Agent):
    point = SimInstanceProperty()

    def __init__(self, name: str, point: Point):
        super().__init__(name)
        self.point = point
        self.parent = point
        self.destination = point


class SourceEvent(TimedEvent):
    def __init__(self, agvs: Sequence[AGV], shelves: Sequence[Shelf], dest_points: Sequence[Point]):
        super().__init__(0)
        self.agvs = agvs
        self.shelves = shelves
        self.dest_points = dest_points

    def execute(self, simulator: Simulator) -> None:
        grounded_shelves = [s for s in self.shelves if isinstance(s.parent, Point) and s.parent not in self.dest_points]
        dest_points = list(self.dest_points)
        for shelf in self.shelves:
            if shelf.destination in dest_points:
                dest_points.remove(shelf.destination)

        if dest_points and grounded_shelves:
            shelf = simulator.random.choice(grounded_shelves)
            for agv in sorted(self.agvs, key=lambda a: a.position | shelf.global_position):
                if not agv.can_do_next_task():
                    continue
                if agv.shelf is None:
                    dest = simulator.random.choice(dest_points)
                    shelf.destination = dest
                    agv.assign_task(shelf, dest)
                    break
                else:
                    pass
                    # print("No free AGVs found, skipping a task!")

        self.sim_time += .05
        simulator.event_queue << self


def create_network(begin: Vec2i, end: Vec2i) -> Agent:
    network = Agent("Network")

    cnt = -1
    points = {}
    for x in range(begin.x, end.x + 1):
        for z in range(begin.y, end.y + 1):
            pos = Vec3i(x, 0, z)
            ap = Vec3(pos)
            # o = Vec3(6, 0, 6)
            # ap = Transform3D.translating(-o) * ap
            # ap = Transform3D.rotating(Vec3(0, 1, 0), ap.length * 0.1) * ap
            # ap = Transform3D.translating(o) * ap

            # import random
            # ap += Vec3(0, random.random() * 10, 0)

            point = Point(f"Point{(cnt:=cnt+1)}", ap)
            points[pos] = point
            point.parent = network

    cnt = -1
    added_paths = set()
    def path(begin, end):
        nonlocal cnt
        key = (begin, end)
        if key in added_paths:
            return
        added_paths.add(key)
        # for obj in network.children:
        #     if isinstance(obj, Path):
        #         if obj.begin == begin and obj.end == end:
        #             return
        Path(f"Path{(cnt := cnt + 1)}", begin, end).parent = network

    # for x in range(begin.x, end.x):
    #     for y in range(begin.y, end.y):
    #         # pa pb
    #         # pc pd
    #         pa = points[Vec3i(x, 0, y)]
    #         pb = points[Vec3i(x+1, 0, y)]
    #         pc = points[Vec3i(x, 0, y+1)]
    #         pd = points[Vec3i(x+1, 0, y+1)]
    #
    #         for a, b in permutations((pa, pb, pc, pd), 2):
    #             path(a, b)
    #
    #         # path(pa, pb)
    #         # path(pb, pa)
    #         # path(pc, pd)
    #         # path(pd, pc)
    #         # path(pa, pc)
    #         # path(pc, pa)
    #         # path(pb, pd)
    #         # path(pd, pb)

    # values = tuple(points.values())

    # for i in range(300):
    #     a = random.choice(values)
    #     b = random.choice(values)
    #     path(a, b)
    #     path(b, a)

    for x, y in tqdm.tqdm(tuple(product(range(begin.x, end.x - 0), range(begin.y, end.y - 0)))):
        # for a, b in permutations((points[Vec3i(x+dx, 0, y+dy)] for dx,dy in product(range(2), repeat=2)), 2):
        #     path(a, b)

        a = points[Vec3i(x+0, 0, y+0)]
        b = points[Vec3i(x+1, 0, y+0)]
        c = points[Vec3i(x+0, 0, y+1)]
        d = points[Vec3i(x+1, 0, y+1)]
        path(a, b)
        path(b, a)
        path(a, c)
        path(c, a)
        path(c, d)
        path(d, c)
        path(b, d)
        path(d, b)

    # for pos, point in points.items():
    #     if pos.x > 0:
    #         other = points[pos - Vec3i(1, 0, 0)]
    #         Path(f"Path{(cnt:=cnt+1)}", point, other).parent = network
    #         Path(f"Path{(cnt:=cnt+1)}", other, point).parent = network
    #     if pos.z > 0:
    #         other = points[pos - Vec3i(0, 0, 1)]
    #         Path(f"Path{(cnt:=cnt+1)}", point, other).parent = network
    #         Path(f"Path{(cnt:=cnt+1)}", other, point).parent = network

    return network

def create_agvs(network: Agent, validator: Callable[[Point], bool], shelves: Sequence[Shelf]) -> Agent:
    agvs = Agent("AGVs")
    cnt = -1
    points = []
    for obj in network.children:
        if isinstance(obj, Point):
            if validator(obj):
                points.append(obj)
    for i, point in enumerate(points):
        color = pg.Color.from_hsva(i/len(points)*360, 100, 100, 100)
        agv = AGV(f"AGV{(cnt:=cnt+1)}", point, 0, color, shelves)
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


screen_transform = Transform2D.scaling(Vec2(50)).translated(Vec2(50, 1050))
screen_transform.rotation = -math.pi * 0.5
screen = None

def sp(pos: Vec3) -> tuple[float, float]:
    """Global position to screen position"""
    return screen_transform(pos.xz)

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
            # color = (200,0,0) if obj.locked_by is not None else (0,200,0)
            color = (255,255,255)
            if obj.locked_by is not None:
                color = obj.locked_by.color
            if hasattr(obj, "dest"):
                color = (0,0,255)
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
        pts = (Vec3(-size, 0, -size), Vec3(size, 0, -size*0.5), Vec3(size, 0, size*0.5), Vec3(-size, 0, size))
        transform = agv.global_transform
        transform = transform.scaled(Vec3(1.0+transform.origin.y/10))
        r = random.Random(agv.obj_id)
        pg.draw.polygon(
            screen,
            agv.color,
            [sp(transform * p) for p in pts]
        )

        if agv.path is not None and len(agv.path) >= 2:
            pg.draw.lines(
                screen,
                agv.color,
                False,
                [sp(agv.position)] + [sp(node.pos) for node in agv.path],
                max(1, int(ss(0.2)))
            )

def draw_shelves(shelves: Sequence[Shelf]):
    for shelf in shelves:
        r = random.Random(shelf.obj_id)
        color = pg.Color.from_hsva(r.random() * 360, 50, 80, 100)
        size = 0.4 if isinstance(shelf.parent, AGV) else 0.35
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

    # network = create_network(Vec2i(0, 0), Vec2i(13, 12))
    network = create_network(Vec2i(0, 0), Vec2i(13+7, 100))
    dest_points = [p for p in network.children if isinstance(p, Point) and p.position.x >= 13+7]
    for d in dest_points:
        d.dest = True

    # for dp in dest_points:
    #     for dpp in dest_points:
    #         p = dp.find_path(dpp)
    #         if p is not None:
    #             network.remove_child(p)

    update_network(network)

    def shelf_pos_validator(point: Point):
        p = point.position
        if not 2 <= p.x <= 8+7:
            return False
        return int(p.z % 3) in (1, 2)
    shelves = cerate_shelves(network, shelf_pos_validator)
    print(len(shelves))
    agvs = create_agvs(network, lambda point: point.position.x < 1 and point.position.z <= 1000000, shelves)

    source_event = SourceEvent(list(agvs.children), shelves, dest_points)
    simulator.event_queue << source_event

    screen = pg.display.set_mode((800, 700), pg.RESIZABLE)
    clock = pg.Clock()

    # t = time.time()
    # simulator.run_until(3600)
    # print(time.time() - t)

    ft = 0.0
    speed = 10
    while True:
        ft += clock.get_time() / 1000 * speed
        simulator.run_until(ft)
        # for _ in range(50):
        #     simulator.execute_next_event()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
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
        clock.tick(0)


if __name__ == '__main__':
    # import viztracer
    # viz = viztracer.VizTracer()
    # viz.start()
    main()
    # viz.stop()
    # viz.save()
