from numbers import Real
from typing import Union
from dynamic_overload import overload
from functools import wraps
from math import sqrt


# noinspection PyRedeclaration
class Vec2:
    __slots__ = ("x", "y")

    x: float
    y: float

    @overload
    def __init__(self):
        self.x = self.y = 0.0

    @overload
    def __init__(self, value: Real):
        self.x = self.y = float(value)

    @overload
    def __init__(self, x: Real, y: Real):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self) -> str:
        return f"Vec2({self.x}, {self.y})"

    def __getattr__(self, item: str) -> Union["AnyVec", Real]:
        return _swizzle(self, item)

    def __pos__(self) -> "Vec2":
        """Returns a copy of this vector."""
        return Vec2(self.x, self.y)

    def __neg__(self) -> "Vec2":
        return Vec2(-self.x, -self.y)

    def __add__(self, other: "Vec2") -> "Vec2":
        assert isinstance(other, Vec2)
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        assert isinstance(other, Vec2)
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Union["Vec2", Real]) -> "Vec2":
        assert isinstance(other, Vec2 | Real)
        is_num = isinstance(other, Real)
        return Vec2(
            self.x * (other if is_num else other.x),
            self.y * (other if is_num else other.y)
        )

    def __truediv__(self, other: Union["Vec2", Real]) -> "Vec2":
        assert isinstance(other, Vec2 | Real)
        is_num = isinstance(other, Real)
        return Vec2(
            self.x / (other if is_num else other.x),
            self.y / (other if is_num else other.y)
        )

    __iadd__ = wraps(__add__)

    __isub__ = wraps(__sub__)

    __imul__ = wraps(__mul__)

    __itruediv__ = wraps(__truediv__)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> "Vec2":
        return +self / self.length()


# noinspection PyRedeclaration
class Vec3:
    __slots__ = ("x", "y", "z")

    x: float
    y: float
    z: float

    @overload
    def __init__(self):
        self.x = self.y = self.z = 0.0

    @overload
    def __init__(self, value: Real):
        self.x = self.y = self.z = float(value)

    @overload
    def __init__(self, x: Real, y: Real, z: Real):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self) -> str:
        return f"Vec3({self.x}, {self.y}, {self.z})"

    def __getattr__(self, item: str) -> Union["AnyVec", Real]:
        return _swizzle(self, item)

    def __pos__(self) -> "Vec3":
        """Returns a copy of this vector."""
        return Vec3(self.x, self.y, self.z)

    def __neg__(self) -> "Vec3":
        return Vec3(-self.x, -self.y, -self.z)

    def __add__(self, other: "Vec3") -> "Vec3":
        assert isinstance(other, Vec3)
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "Vec3") -> "Vec3":
        assert isinstance(other, Vec3)
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, other: Union["Vec3", Real]) -> "Vec3":
        assert isinstance(other, Vec3 | Real)
        is_num = isinstance(other, Real)
        return Vec3(
            self.x * (other if is_num else other.x),
            self.y * (other if is_num else other.y),
            self.z * (other if is_num else other.z)
        )

    def __truediv__(self, other: Union["Vec3", Real]) -> "Vec3":
        assert isinstance(other, Vec3 | Real)
        is_num = isinstance(other, Real)
        return Vec3(
            self.x / (other if is_num else other.x),
            self.y / (other if is_num else other.y),
            self.z / (other if is_num else other.z)
        )

    __iadd__ = __add__

    __isub__ = __sub__

    __imul__ = __mul__

    __itruediv__ = __truediv__

    def dot(self, other: "Vec3") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    # def cross(self, other: "Vector3") -> "Vector3":
    #     return

    def length(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> "Vec3":
        return +self / self.length()


# noinspection PyRedeclaration
class Vec4:
    __slots__ = ("x", "y", "z", "w")

    x: float
    y: float
    z: float
    w: float

    @overload
    def __init__(self):
        self.x = self.y = self.z = self.w = 0.0

    @overload
    def __init__(self, value: Real):
        self.x = self.y = self.z = self.w = float(value)

    @overload
    def __init__(self, x: Real, y: Real, z: Real, w: Real):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.w = float(w)

    def __repr__(self) -> str:
        return f"Vec4({self.x}, {self.y}, {self.z}, {self.w})"

    def __getattr__(self, item: str) -> Union["AnyVec", Real]:
        return _swizzle(self, item)

    def __pos__(self) -> "Vec4":
        """Returns a copy of this vector."""
        return Vec4(self.x, self.y, self.z, self.w)

    def __neg__(self) -> "Vec4":
        return Vec4(-self.x, -self.y, -self.z, -self.w)

    def __add__(self, other: "Vec4") -> "Vec4":
        assert isinstance(other, Vec3)
        return Vec4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other: "Vec4") -> "Vec4":
        assert isinstance(other, Vec3)
        return Vec4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, other: Union["Vec4", Real]) -> "Vec4":
        assert isinstance(other, Vec4 | Real)
        is_num = isinstance(other, Real)
        return Vec4(
            self.x * (other if is_num else other.x),
            self.y * (other if is_num else other.y),
            self.z * (other if is_num else other.z),
            self.w * (other if is_num else other.w)
        )

    def __truediv__(self, other: Union["Vec4", Real]) -> "Vec4":
        assert isinstance(other, Vec3 | Real)
        is_num = isinstance(other, Real)
        return Vec4(
            self.x / (other if is_num else other.x),
            self.y / (other if is_num else other.y),
            self.z / (other if is_num else other.z),
            self.w / (other if is_num else other.w)
        )

    __iadd__ = __add__

    __isub__ = __sub__

    __imul__ = __mul__

    __itruediv__ = __truediv__

    def dot(self, other: "Vec4") -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w

    def length(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z + self.w * self.w)

    def normalize(self) -> "Vec4":
        return +self / self.length()


class Vec2i:
    pass


class Vec3i:
    pass


class Vec4i:
    pass


Vec = Union[Vec2, Vec3, Vec4]
Veci = Union[Vec2i, Vec3i, Vec4i]
AnyVec = Vec | Veci


_SWIZZLE_MAP = {
    "x": "x",
    "y": "y",
    "z": "z",
    "w": "w",

    "u": "x",
    "v": "y",

    "r": "x",
    "g": "y",
    "b": "z",
    "a": "w",
}

def _swizzle(vec: AnyVec, swiz: str) -> AnyVec | Real:
    if len(swiz) > 4 or len(swiz) < 1:
        raise ValueError(f"Invalid vector swizzling length: {len(swiz)}")

    mapped_swiz = ""

    for c in swiz:
        mapped_c = _SWIZZLE_MAP.get(c)
        if mapped_c is None or mapped_c not in vec.__slots__:
            raise ValueError(f"Invalid vector swizzle item: {c}")
        mapped_swiz += mapped_c

    if len(mapped_swiz) == 1:
        return getattr(vec, mapped_swiz)

    items = tuple(getattr(vec, c) for c in mapped_swiz)

    match len(items):
        case 2:
            return Vec2(*items) if isinstance(vec, Vec) else Vec2i(*items)
        case 3:
            return Vec3(*items) if isinstance(vec, Vec) else Vec3i(*items)
        case 4:
            return Vec4(*items) if isinstance(vec, Vec) else Vec4i(*items)


if __name__ == '__main__':
    vec = Vec2(1, 2)
    print(vec)
    print(vec.yxy)
