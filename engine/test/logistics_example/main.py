import asyncio
import json
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
from sim.data.serialization import gd_serialize
from gdmath import *

import path_find

import pygame as pg

import websockets


simulator: Simulator = Simulator()


class Point(PositionalAgent):
    locked_nodes: set[path_find.Node] = set()
    _locked_by: SimInstanceProperty()

    def __init__(self, name: str, position: Vec3):
        super().__init__(name, position)

        self.is_dest = False

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

    def assign_task(self, shelf: "Shelf", dest: Point, finish_callback = lambda a,b: None):
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
            finish_callback(shelf, dest)
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
        self._unassigned_shelves = list(self.shelves)

    def execute(self, simulator: Simulator) -> None:
        dest_points = list(self.dest_points)
        for shelf in self.shelves:
            if shelf.destination in dest_points:
                dest_points.remove(shelf.destination)

        if dest_points and self._unassigned_shelves:
            shelf = simulator.random.choice(self._unassigned_shelves)
            for agv in sorted(self.agvs, key=lambda a: a.position | shelf.global_position):
                if not agv.can_do_next_task():
                    continue
                if agv.shelf is None:
                    dest = simulator.random.choice(dest_points)
                    shelf.destination = dest
                    self._unassigned_shelves.remove(shelf)
                    agv.assign_task(shelf, dest, lambda s,_: self._unassigned_shelves.append(s))
                    break
                else:
                    pass
                    # print("No free AGVs found, skipping a task!")

        self.sim_time += .05
        simulator.event_queue << self


class Main:
    def __init__(self):
        global simulator
        # simulator = Simulator()

        with open("cfg.json", "r") as f:
            cfg = json.loads(f.read())

        self.root = Agent("Root")

        self.network = Agent("Network")
        self.network.parent = self.root

        points = []
        for point in cfg["network"]["points"]:
            p = Point(point[0], Vec3(*point[1]))
            p.parent = self.network
            points.append(p)

        self.dest_points = []
        for dest in cfg["dest_points"]:
            points[dest].is_dest = True
            self.dest_points.append(points[dest])

        for path in cfg["network"]["paths"]:
            Path(path[0], points[path[1]], points[path[2]]).parent = self.network

        update_network(self.network)

        self.shelves = []
        for shelf in cfg["shelves"]:
            self.shelves.append(Shelf(shelf[0], points[shelf[1]]))

        self.agvs = Agent("AGVs")
        self.agvs.parent = self.root
        for i, params in enumerate(cfg["agvs"]):
            color = pg.Color.from_hsva(i / len(cfg["agvs"]) * 360, 100, 100, 100)
            AGV(params[0], points[params[1]], 0, color, self.shelves).parent = self.agvs

        self.source_event = SourceEvent(list(self.agvs.children), self.shelves, self.dest_points)
        simulator.event_queue << self.source_event

        self.screen = pg.display.set_mode((800, 700), pg.RESIZABLE)
        self.screen_transform = Transform2D.scaling(Vec2(50)).translated(Vec2(50, 50))
        # self.screen_transform.rotation = -math.pi * 0.5
        self.clock = pg.Clock()

        self._last_sim_time = time.perf_counter()
        self.speed = 10.0
        self.paused = False

        self._clients: list[websockets.WebSocketServerProtocol] = []

    async def _advance_sim(self):
        t = time.perf_counter()
        if not self.paused:
            simulator.advance((t - self._last_sim_time) * self.speed)
        self._last_sim_time = t
        self.clock.tick(60)

    async def _pygame_draw(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.MOUSEWHEEL:
                self.screen_transform @= Transform2D.scaling(Vec2(1 + event.y * 0.1))
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_DOWN:
                    self.speed *= 0.5
                elif event.key == pg.K_UP:
                    self.speed *= 1.5
                elif event.key == pg.K_SPACE:
                    self.paused = not self.paused

        self.screen.fill(0)

        self.draw_agvs()
        self.draw_network()
        self.draw_shelves()

        pg.display.set_caption(
            f"Logistics Demo - {simulator.sim_time:.2f}s - Spd:{self.speed:.2f} - E:{simulator.event_queue._test_temp_eid} - {self.clock.get_fps():.1f}FPS" + (" - PAUSED" if self.paused else ""))
        pg.display.flip()

        self.clock.tick(60)

    async def _send_to_clients(self):
        if not self._clients:
            return
        msg = {
            "agv_transforms": [agv.global_transform for agv in self.agvs.children],
            "shelf_transforms": [shelf.global_transform for shelf in self.shelves],
        }
        msg = gd_serialize(msg)
        for client in self._clients:
            try:
                await client.send(msg)
            except websockets.exceptions.ConnectionClosed:
                pass

    async def _handle_client(self, client: websockets.WebSocketServerProtocol):
        self._clients.append(client)
        print(f"Client connected: {client.remote_address}")
        try:
            while True:
                msg = await client.recv()
                match msg:
                    case "speed_up":
                        self.speed *= 1.5
                    case "slow_down":
                        self.speed *= 0.5
                    case "toggle_pause":
                        self.paused = not self.paused
                    case _:
                        print(f"Unknown msg from client : {msg}")
        except websockets.WebSocketException:
            pass
        finally:
            self._clients.remove(client)


    def sp(self, pos: Vec3) -> tuple[float, float]:
        """Global position to screen position"""
        return self.screen_transform(pos.xz)

    def ss(self, size: float) -> float:
        return size * self.screen_transform.scale.x

    def draw_network(self):
        for obj in self.network.children:
            if isinstance(obj, Path):
                pg.draw.aaline(
                    self.screen,
                    (255, 255, 255),
                    self.sp(obj.begin.position),
                    self.sp(obj.end.position)
                )

        for obj in self.network.children:
            if isinstance(obj, Point):
                # color = (200,0,0) if obj.locked_by is not None else (0,200,0)
                color = (255, 255, 255)
                if obj.locked_by is not None:
                    color = obj.locked_by.color
                if obj.is_dest:
                    color = (0, 0, 255)
                pg.draw.circle(
                    self.screen,
                    color,
                    self.sp(obj.position),
                    self.ss(0.1)
                )

    def draw_agvs(self):
        for agv in self.agvs.children:
            size = 0.3
            pts = (Vec3(-size, 0, -size), Vec3(size, 0, -size * 0.5), Vec3(size, 0, size * 0.5), Vec3(-size, 0, size))
            transform = agv.global_transform
            transform = transform.scaled(Vec3(1.0 + transform.origin.y / 10))
            r = random.Random(agv.obj_id)
            pg.draw.polygon(
                self.screen,
                agv.color,
                [self.sp(transform * p) for p in pts]
            )

            if agv.path is not None and len(agv.path) >= 2:
                pg.draw.lines(
                    self.screen,
                    agv.color,
                    False,
                    [self.sp(agv.position)] + [self.sp(node.pos) for node in agv.path],
                    max(1, int(self.ss(0.2)))
                )

    def draw_shelves(self):
        for shelf in self.shelves:
            r = random.Random(shelf.obj_id)
            color = pg.Color.from_hsva(r.random() * 360, 50, 80, 100)
            size = 0.4 if isinstance(shelf.parent, AGV) else 0.35
            pts = (Vec3(-size, 0, -size), Vec3(size, 0, -size), Vec3(size, 0, size), Vec3(-size, 0, size))
            transform = shelf.global_transform
            pg.draw.polygon(
                self.screen,
                color,
                [self.sp(transform * p) for p in pts],
                max(1, int(self.ss(0.06)))
            )

    async def _main_loop(self):
        while True:
            await self._advance_sim()
            await self._send_to_clients()
            await self._pygame_draw()
            await asyncio.sleep(0)

    async def _run(self):
        await asyncio.gather(
            self._main_loop(),
            websockets.serve(self._handle_client, "localhost", 31415),
        )

    def run(self):
        asyncio.run(self._run())


if __name__ == '__main__':
    # import viztracer
    # viz = viztracer.VizTracer()
    # viz.start()
    Main().run()
    # viz.stop()
    # viz.save()
