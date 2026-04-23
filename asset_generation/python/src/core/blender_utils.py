"""Compatibility surface for split blender utility modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from . import creature_parts as _creature_parts
from .mesh_ops import (
    apply_smooth_shading,
    bind_mesh_manually,
    bind_mesh_to_armature,
    clear_scene,
    detect_body_scale_from_mesh,
    ensure_mesh_integrity,
    fix_body_part_bindings,
    identify_vertex_body_part,
    join_objects,
    random_variance,
)
from .primitives import create_box, create_cone, create_cylinder, create_sphere

if TYPE_CHECKING:
    from bpy.types import Object

Vector3 = tuple[float, float, float]

# Re-export creature-part tuning constants for compatibility with tests and
# existing consumers that introspect this module directly.
_EYE_OVAL_SCALE_X = _creature_parts._EYE_OVAL_SCALE_X
_EYE_OVAL_SCALE_Z = _creature_parts._EYE_OVAL_SCALE_Z
_EYE_SLIT_SCALE_Y = _creature_parts._EYE_SLIT_SCALE_Y

_PUPIL_DOT_Z_RATIO = _creature_parts._PUPIL_DOT_Z_RATIO
_PUPIL_SLIT_X_RATIO = _creature_parts._PUPIL_SLIT_X_RATIO
_PUPIL_SLIT_Z_RATIO = _creature_parts._PUPIL_SLIT_Z_RATIO
_PUPIL_DIAMOND_X_RATIO = _creature_parts._PUPIL_DIAMOND_X_RATIO
_PUPIL_DIAMOND_Y_RATIO = _creature_parts._PUPIL_DIAMOND_Y_RATIO
_PUPIL_DIAMOND_Z_RATIO = _creature_parts._PUPIL_DIAMOND_Z_RATIO

_MOUTH_SMILE_X_RATIO = _creature_parts._MOUTH_SMILE_X_RATIO
_MOUTH_SMILE_Y_RATIO = _creature_parts._MOUTH_SMILE_Y_RATIO
_MOUTH_SMILE_Z_RATIO = _creature_parts._MOUTH_SMILE_Z_RATIO
_MOUTH_GRIMACE_X_RATIO = _creature_parts._MOUTH_GRIMACE_X_RATIO
_MOUTH_GRIMACE_Y_RATIO = _creature_parts._MOUTH_GRIMACE_Y_RATIO
_MOUTH_GRIMACE_Z_RATIO = _creature_parts._MOUTH_GRIMACE_Z_RATIO
_MOUTH_FLAT_X_RATIO = _creature_parts._MOUTH_FLAT_X_RATIO
_MOUTH_FLAT_Y_RATIO = _creature_parts._MOUTH_FLAT_Y_RATIO
_MOUTH_FLAT_Z_RATIO = _creature_parts._MOUTH_FLAT_Z_RATIO
_MOUTH_FANG_X_RATIO = _creature_parts._MOUTH_FANG_X_RATIO
_MOUTH_FANG_Z_RATIO = _creature_parts._MOUTH_FANG_Z_RATIO
_MOUTH_BEAK_X_RATIO = _creature_parts._MOUTH_BEAK_X_RATIO
_MOUTH_BEAK_Z_RATIO = _creature_parts._MOUTH_BEAK_Z_RATIO

_TAIL_WHIP_XY_RATIO = _creature_parts._TAIL_WHIP_XY_RATIO
_TAIL_SEG_XY_RATIO = _creature_parts._TAIL_SEG_XY_RATIO
_TAIL_CLUB_Z_RATIO = _creature_parts._TAIL_CLUB_Z_RATIO
_TAIL_CURLED_X_RATIO = _creature_parts._TAIL_CURLED_X_RATIO
_TAIL_CURLED_Z_RATIO = _creature_parts._TAIL_CURLED_Z_RATIO


def create_eye_mesh(shape: str, location: Vector3, eye_scale: float) -> "Object":
    """Compatibility wrapper for eye mesh builder with patchable primitive calls."""
    if shape == "square":
        return create_box(location=location, scale=(eye_scale, eye_scale, eye_scale))
    if shape == "oval":
        return create_sphere(
            location=location,
            scale=(eye_scale * _EYE_OVAL_SCALE_X, eye_scale, eye_scale * _EYE_OVAL_SCALE_Z),
        )
    if shape == "slit":
        return create_sphere(
            location=location,
            scale=(eye_scale, eye_scale * _EYE_SLIT_SCALE_Y, eye_scale),
        )
    return create_sphere(location=location, scale=(eye_scale, eye_scale, eye_scale))


def create_pupil_mesh(
    shape: str, location: Vector3, pupil_scale: float
) -> "Object":
    """Compatibility wrapper for pupil mesh builder with patchable primitive calls."""
    if shape == "slit":
        return create_cylinder(
            location=location,
            scale=(
                pupil_scale * _PUPIL_SLIT_X_RATIO,
                pupil_scale,
                pupil_scale * _PUPIL_SLIT_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
        )
    if shape == "diamond":
        return create_box(
            location=location,
            scale=(
                pupil_scale * _PUPIL_DIAMOND_X_RATIO,
                pupil_scale * _PUPIL_DIAMOND_Y_RATIO,
                pupil_scale * _PUPIL_DIAMOND_Z_RATIO,
            ),
        )
    return create_sphere(
        location=location,
        scale=(pupil_scale, pupil_scale, pupil_scale * _PUPIL_DOT_Z_RATIO),
    )


def create_mouth_mesh(shape: str, location: Vector3, head_scale: float) -> "Object":
    """Compatibility wrapper for mouth mesh builder with patchable primitive calls."""
    if shape == "fang":
        return create_cone(
            location=location,
            scale=(
                head_scale * _MOUTH_FANG_X_RATIO,
                head_scale * _MOUTH_FANG_X_RATIO,
                head_scale * _MOUTH_FANG_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
            radius1=head_scale * _MOUTH_FANG_X_RATIO,
            radius2=0.0,
        )
    if shape == "beak":
        return create_cone(
            location=location,
            scale=(
                head_scale * _MOUTH_BEAK_X_RATIO,
                head_scale * _MOUTH_BEAK_X_RATIO,
                head_scale * _MOUTH_BEAK_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
            radius1=head_scale * _MOUTH_BEAK_X_RATIO,
            radius2=0.0,
        )
    if shape == "flat":
        return create_box(
            location=location,
            scale=(
                head_scale * _MOUTH_FLAT_X_RATIO,
                head_scale * _MOUTH_FLAT_Y_RATIO,
                head_scale * _MOUTH_FLAT_Z_RATIO,
            ),
        )
    if shape == "grimace":
        return create_cylinder(
            location=location,
            scale=(
                head_scale * _MOUTH_GRIMACE_X_RATIO,
                head_scale * _MOUTH_GRIMACE_Y_RATIO,
                head_scale * _MOUTH_GRIMACE_Z_RATIO,
            ),
            vertices=8,
            depth=2.0,
        )
    return create_cylinder(
        location=location,
        scale=(
            head_scale * _MOUTH_SMILE_X_RATIO,
            head_scale * _MOUTH_SMILE_Y_RATIO,
            head_scale * _MOUTH_SMILE_Z_RATIO,
        ),
        vertices=8,
        depth=2.0,
    )


def create_tail_mesh(shape: str, length: float, location: Vector3) -> "Object":
    """Compatibility wrapper for tail mesh builder with patchable primitive calls."""
    if shape == "spike":
        return create_cone(
            location=location,
            scale=(length * 0.25, length * 0.25, length * 1.2),
            vertices=8,
            depth=2.0,
            radius1=length * 0.25,
            radius2=0.0,
        )
    if shape == "whip":
        return create_cylinder(
            location=location,
            scale=(
                length * _TAIL_WHIP_XY_RATIO,
                length * _TAIL_WHIP_XY_RATIO,
                length * 1.5,
            ),
            vertices=8,
            depth=2.0,
        )
    if shape == "club":
        return create_sphere(
            location=location,
            scale=(length * 0.4, length * 0.4, length * _TAIL_CLUB_Z_RATIO),
        )
    if shape == "segmented":
        return create_cylinder(
            location=location,
            scale=(length * _TAIL_SEG_XY_RATIO, length * _TAIL_SEG_XY_RATIO, length),
            vertices=12,
            depth=2.0,
        )
    return create_sphere(
        location=location,
        scale=(
            length * _TAIL_CURLED_X_RATIO,
            length * _TAIL_CURLED_X_RATIO,
            length * _TAIL_CURLED_Z_RATIO,
        ),
    )

__all__ = [
    "create_sphere",
    "create_cylinder",
    "create_cone",
    "create_box",
    "create_eye_mesh",
    "create_pupil_mesh",
    "create_mouth_mesh",
    "create_tail_mesh",
    "clear_scene",
    "detect_body_scale_from_mesh",
    "apply_smooth_shading",
    "join_objects",
    "random_variance",
    "bind_mesh_to_armature",
    "bind_mesh_manually",
    "ensure_mesh_integrity",
    "fix_body_part_bindings",
    "identify_vertex_body_part",
]
