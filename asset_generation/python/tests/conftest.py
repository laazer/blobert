"""
Root conftest — bpy/mathutils/bmesh stubs for all asset_generation/python tests.

Delegates to ``utils.blender_stubs`` (same shims as GET /api/meta/enemies) so
``src.enemies`` (including ``animated.registry``) can load outside Blender.
"""

from src.utils.blender_stubs import ensure_blender_stubs

ensure_blender_stubs()
