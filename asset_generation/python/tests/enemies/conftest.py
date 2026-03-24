"""
conftest.py — bpy/mathutils/bmesh stub for tests/enemies/.

Registers lightweight stubs for Blender modules in sys.modules BEFORE any
test file is imported. This allows pure-Python import of
src.enemies.animated_enemies (and its transitive dependencies on
blender_utils, armature_builders, material_system) without a Blender
installation. The stubs are scoped to this conftest; they do not affect
any other test directory.

None of the enemy class methods that call bpy functions (create_body,
create_head, create_limbs, create_armature, apply_materials) are invoked
by the test suite — only class structure is tested via inspect.getsource
and hasattr introspection.
"""

import sys
import types
from unittest.mock import MagicMock


class _BlenderModuleStub(types.ModuleType):
    """A ModuleType subclass that returns MagicMock for any attribute access."""

    def __getattr__(self, name: str):
        value = MagicMock()
        # Cache the value so repeated access returns the same mock.
        setattr(self, name, value)
        return value


def _install_stub(name: str) -> None:
    if name not in sys.modules:
        stub = _BlenderModuleStub(name)
        sys.modules[name] = stub


# Register stubs before any src.* imports resolve.
for _mod_name in ('bpy', 'bmesh'):
    _install_stub(_mod_name)

# mathutils requires special handling: Euler and Vector must be callable
# classes (not MagicMock instances) so that `from mathutils import Euler`
# returns something that can be used as a class inside method bodies.
# The tests never call Euler() or Vector() directly.
if 'mathutils' not in sys.modules:
    _mathutils = _BlenderModuleStub('mathutils')

    class _Euler:
        def __init__(self, *args, **kwargs):
            pass

    class _Vector:
        def __init__(self, *args, **kwargs):
            pass

    _mathutils.Euler = _Euler
    _mathutils.Vector = _Vector
    sys.modules['mathutils'] = _mathutils
