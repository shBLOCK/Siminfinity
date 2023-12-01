import enum
import struct
from math import ceil
from struct import pack
from typing import Any, Sequence, Mapping, Union

from gdmath import *


def _header(value_type: int, flags: int = 0) -> bytes:
    return struct.pack("<i", value_type + (flags << 16))

def _gd_float(n: int):
    return f"<{n}f"


class GDArrayType(enum.Enum):
    Any = enum.auto()
    Int32 = enum.auto()
    Int64 = enum.auto()
    Int = Int32
    Float32 = enum.auto()
    Float64 = enum.auto()
    Float = Float64
    String = enum.auto()
    Vec2 = enum.auto()
    Vec3 = enum.auto()
    Color = enum.auto()


def _pad(dat: bytes) -> bytes:
    if len(dat) % 4 == 0:
        return dat
    return dat + b"\x00" * (4 - len(dat) % 4)

_Serializable = Union[
    None,
    bool,
    int,
    float,
    str,
    Vec2,
    Vec3,
    Transform2D,
    Transform3D,
    Vec4,
    bytes
]
_Serializable = Union[_Serializable, Sequence[_Serializable], Mapping[_Serializable, _Serializable]]

def gd_serialize(value: _Serializable, array_type: GDArrayType = None) -> bytes:
    if value is None:
        return _header(0)

    if isinstance(value, bool):
        return _header(1) + pack("<i", int(value))

    if isinstance(value, int):
        if -0x80000000 <= value <= 0x7FFFFFFF:
            return _header(2, 0) + pack("<i", value)
        else:
            return _header(2, 1) + pack("<q", value)

    if isinstance(value, float):
        return _header(3, 1) + pack("<d", value)

    if isinstance(value, str):
        bytes_str = value.encode("utf8")
        return _header(4) + pack("<i", len(bytes_str)) + _pad(bytes_str)

    if isinstance(value, Vec2):
        return _header(5) + pack(_gd_float(2), *value)

    if isinstance(value, Vec3):
        return _header(9) + pack(_gd_float(3), *value)

    if isinstance(value, Transform2D):
        return _header(11) + pack(_gd_float(6), *value.x, *value.y, *value.origin)

    if isinstance(value, Transform3D):
        return _header(18) + pack(_gd_float(12), *value.x, *value.y, *value.z, *value.origin)

    if isinstance(value, Vec4):
        return _header(20) + pack(_gd_float(4), *value)

    if isinstance(value, Mapping):
        dat = _header(27) + pack("<i", len(value))
        for k, v in value.items():
            dat += gd_serialize(k)
            dat += gd_serialize(v)
        return dat

    if isinstance(value, Sequence):
        if array_type is None:
            array_type = GDArrayType.Any
        dat = {
            GDArrayType.Any: _header(28),
            # TODO: FIX GD SERIALIZE
            # GDArrayType.Int32: _header(21),
            # GDArrayType.Int64: _header(22),
            # GDArrayType.Float32: _header(23),
            # GDArrayType.Float64: _header(24),
            # GDArrayType.String: _header(25),
            # GDArrayType.Vec2: _header(26),
            # GDArrayType.Vec3: _header(27),
            # GDArrayType.Color: _header(28),
        }[array_type] + pack("<i", len(value))
        match array_type:
            case GDArrayType.Any:
                for v in value:
                    dat += gd_serialize(v)
            case GDArrayType.Int32, GDArrayType.Int64, GDArrayType.Float32, GDArrayType.Float64:
                fmt = "<" + {
                    GDArrayType.Int32: "i",
                    GDArrayType.Int64: "q",
                    GDArrayType.Float32: "f",
                    GDArrayType.Float64: "d",
                }[array_type] * len(array_type)
                dat += pack(fmt, *value)
            case GDArrayType.String:
                for v in value:
                    bytes_str = v.encode("utf8")
                    dat += pack("<i", len(bytes_str))
                    dat += _pad(bytes_str)
            case GDArrayType.Vec2, GDArrayType.Vec3, GDArrayType.Color:
                def it():
                    for vec in value:
                        for n in vec:
                            yield n
                cnt = {
                    GDArrayType.Vec2: 2,
                    GDArrayType.Vec3: 3,
                    GDArrayType.Color: 4
                }[array_type]
                dat += pack(_gd_float(len(value) * cnt), *it())
        return dat

    if isinstance(value, bytes) or isinstance(value, bytearray):
        if not isinstance(value, bytes):
            value = bytes(value)
        return _header(29) + pack("<i", len(value)) + _pad(value)
