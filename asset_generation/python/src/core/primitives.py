"""Primitive mesh constructors for Blender object creation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import bpy

if TYPE_CHECKING:
    from bpy.types import Object

Vector3 = tuple[float, float, float]


def create_sphere(
    location: Vector3 = (0, 0, 0),
    scale: Vector3 = (1, 1, 1),
    subdivisions: int = 1,
) -> "Object":
    """Create a UV sphere with specified parameters."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=location, scale=scale)
    obj = bpy.context.active_object

    # Add subdivision if requested.
    if subdivisions > 1:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.subdivide(number_cuts=subdivisions - 1)
        bpy.ops.object.mode_set(mode="OBJECT")

    return obj


def create_cylinder(
    location: Vector3 = (0, 0, 0),
    scale: Vector3 = (1, 1, 1),
    vertices: int = 8,
    depth: float = 2.0,
) -> "Object":
    """Create a cylinder with specified parameters."""
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices,
        depth=depth,
        location=location,
        scale=scale,
    )
    return bpy.context.active_object


def create_cone(
    location: Vector3 = (0, 0, 0),
    scale: Vector3 = (1, 1, 1),
    *,
    vertices: int = 16,
    depth: float = 2.0,
    radius1: float = 1.0,
    radius2: float = 0.0,
) -> "Object":
    """Create a cone mesh; use ``vertices=4`` for a pyramid."""
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices,
        radius1=radius1,
        radius2=radius2,
        depth=depth,
        location=location,
        scale=scale,
    )
    return bpy.context.active_object


def create_box(
    location: Vector3 = (0, 0, 0),
    scale: Vector3 = (1, 1, 1),
) -> "Object":
    """Create a box mesh with the specified dimensions.

    Uses Blender's unit cube (size=1.0) so scale maps directly to edge lengths:
    scale=(width, depth, height) produces a box of exactly that size.
    """
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, scale=scale)
    return bpy.context.active_object


__all__ = [
    "create_sphere",
    "create_cylinder",
    "create_cone",
    "create_box",
]
