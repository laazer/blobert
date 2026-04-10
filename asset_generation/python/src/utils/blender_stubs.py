"""
Install bpy / bmesh / mathutils shims so ``enemies.*`` can import outside Blender.

Used by: pytest, GET /api/meta/enemies (asset editor), and any headless code that
introspects enemy ClassVars. When real ``bpy`` is already loaded (inside Blender),
this is a no-op.
"""

from __future__ import annotations

import math
import sys
import types
from unittest.mock import MagicMock


class _BlenderModuleStub(types.ModuleType):
    """Returns MagicMock for any attribute (enough for import-time references)."""

    def __getattr__(self, name: str):
        value = MagicMock()
        setattr(self, name, value)
        return value


def ensure_blender_stubs() -> None:
    """If ``bpy`` is not loaded, register lightweight stand-ins for bpy, bmesh, mathutils."""
    if "bpy" in sys.modules:
        return

    for name in ("bpy", "bmesh"):
        if name not in sys.modules:
            sys.modules[name] = _BlenderModuleStub(name)

    if "mathutils" in sys.modules:
        return

    m = _BlenderModuleStub("mathutils")

    class _Euler:
        def __init__(self, *args, **kwargs):
            pass

    class _Quaternion:
        __slots__ = ("w", "x", "y", "z")

        def __init__(self, w: float = 1.0, x: float = 0.0, y: float = 0.0, z: float = 0.0):
            self.w, self.x, self.y, self.z = float(w), float(x), float(y), float(z)

    class _Vector:
        __slots__ = ("_t",)

        def __init__(self, *args, **kwargs):
            if len(args) == 1 and isinstance(args[0], (tuple, list)):
                self._t = tuple(float(x) for x in args[0])
            elif len(args) == 3:
                self._t = tuple(float(x) for x in args)
            else:
                self._t = (0.0, 0.0, 0.0)

        def __eq__(self, other):
            if isinstance(other, _Vector):
                return self._t == other._t
            return NotImplemented

        def __repr__(self) -> str:
            return f"_Vector{self._t}"

        def __add__(self, other):
            if isinstance(other, _Vector):
                return _Vector(tuple(a + b for a, b in zip(self._t, other._t)))
            return NotImplemented

        def __sub__(self, other):
            if isinstance(other, _Vector):
                return _Vector(tuple(a - b for a, b in zip(self._t, other._t)))
            return NotImplemented

        def __mul__(self, scalar):
            if isinstance(scalar, (int, float)):
                return _Vector(tuple(a * scalar for a in self._t))
            return NotImplemented

        def __rmul__(self, scalar):
            return self.__mul__(scalar)

        def __truediv__(self, scalar):
            if isinstance(scalar, (int, float)) and scalar != 0:
                return _Vector(tuple(a / scalar for a in self._t))
            return NotImplemented

        def dot(self, other):
            if isinstance(other, _Vector):
                return float(sum(a * b for a, b in zip(self._t, other._t)))
            return NotImplemented

        def __iter__(self):
            return iter(self._t)

        @property
        def x(self) -> float:
            return float(self._t[0])

        @property
        def y(self) -> float:
            return float(self._t[1])

        @property
        def z(self) -> float:
            return float(self._t[2])

        @property
        def length(self) -> float:
            return float(math.sqrt(sum(x * x for x in self._t)))

        def normalized(self):
            ln = self.length
            if ln < 1e-12:
                return _Vector(0.0, 0.0, 0.0)
            return self / ln

        def rotation_difference(self, other):
            if not isinstance(other, _Vector):
                return _Quaternion(1.0, 0.0, 0.0, 0.0)
            return _Quaternion(1.0, 0.0, 0.0, 0.0)

    m.Euler = _Euler
    m.Quaternion = _Quaternion
    m.Vector = _Vector
    sys.modules["mathutils"] = m
