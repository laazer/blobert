"""
Install bpy / bmesh / mathutils shims so ``enemies.*`` can import outside Blender.

Used by: pytest, GET /api/meta/enemies (asset editor), and any headless code that
introspects enemy ClassVars. When real ``bpy`` is already loaded (inside Blender),
this is a no-op.
"""

from __future__ import annotations

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

    m.Euler = _Euler
    m.Vector = _Vector
    sys.modules["mathutils"] = m
