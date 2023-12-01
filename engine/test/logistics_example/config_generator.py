import json
from itertools import product
from random import randint


def generate() -> dict:
    size = (13, 13)

    _ppos = {}
    points = []
    cnt = 0
    for x in range(size[0]):
        for z in range(size[1]):
            points.append((f"Point{cnt}", [x, 0, z]))
            cnt += 1

    def point_pos(p):
        return p[1]

    def find_point(p):
        for index, pt in enumerate(points):
            if tuple(point_pos(pt)) == p:
                return index
        assert False, f"Can't find point with pos {p}"

    paths = []
    cnt = 0
    def path(start, end):
        nonlocal cnt
        paths.append((
            f"Path[{start}, {end}]",
            start,
            end
        ))
        cnt += 1
    for x, y in tuple(product(range(size[0]-1), range(size[1]-1))):
        a = find_point((x + 0, 0, y + 0))
        b = find_point((x + 1, 0, y + 0))
        c = find_point((x + 0, 0, y + 1))
        d = find_point((x + 1, 0, y + 1))
        path(a, b); path(b, a)
        path(a, c); path(c, a)
        path(c, d); path(d, c)
        path(b, d); path(d, b)

    dest_points = []
    for i, point in enumerate(points):
        if point_pos(point)[0] >= 12:
            dest_points.append(i)

    agvs = []
    cnt = 0
    for i, point in enumerate(points):
        if point_pos(point)[0] < 0.5:
            agvs.append((f"AGV{cnt}", i))
            cnt += 1

    shelves = []
    cnt = 0
    for i, point in enumerate(points):
        if not 2 <= point_pos(point)[0] <= 8:
            continue
        if not int(point_pos(point)[2] % 3) in (1, 2):
            continue

        shelves.append((f"Shelf{cnt}", i))
        cnt += 1



    for p in points:
        p[1][0] *= 1.5
        p[1][1] *= 1.5
        p[1][2] *= 1.5




    return {
        "network": {
            "points": points,
            "paths": paths
        },
        "dest_points": dest_points,
        "agvs": agvs,
        "shelves": shelves,
    }


def main():
    cfg = generate()
    with open("cfg.json", "w") as f:
        f.write(json.dumps(cfg))

if __name__ == '__main__':
    main()
