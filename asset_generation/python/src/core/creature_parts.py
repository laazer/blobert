"""Creature-specific part builders composed from primitive mesh constructors."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .primitives import create_box, create_cone, create_cylinder, create_sphere

if TYPE_CHECKING:
    from bpy.types import Object

Vector3 = tuple[float, float, float]

# Eye shape scale constants (non-trivial tuning values must be named).
_EYE_OVAL_SCALE_X: float = 1.4  # elongate along X (forward-facing axis)
_EYE_OVAL_SCALE_Z: float = 0.85  # compress along Z slightly
_EYE_SLIT_SCALE_Y: float = 0.35  # narrow along Y for vertical-slit silhouette

# Pupil scale constants.
_PUPIL_DOT_Z_RATIO: float = 0.3  # Z squish for flat disc dot pupil
_PUPIL_SLIT_X_RATIO: float = 0.25  # X width for slit pupil cylinder
_PUPIL_SLIT_Z_RATIO: float = 0.05  # Z depth (thin coin)
_PUPIL_DIAMOND_X_RATIO: float = 0.6  # X width for diamond box
_PUPIL_DIAMOND_Y_RATIO: float = 0.25  # Y depth for diamond box
_PUPIL_DIAMOND_Z_RATIO: float = 0.9  # Z height for diamond box

_MOUTH_SMILE_X_RATIO: float = 1.2
_MOUTH_SMILE_Y_RATIO: float = 1.0
_MOUTH_SMILE_Z_RATIO: float = 0.15

_MOUTH_GRIMACE_X_RATIO: float = 1.3
_MOUTH_GRIMACE_Y_RATIO: float = 0.9
_MOUTH_GRIMACE_Z_RATIO: float = 0.12

_MOUTH_FLAT_X_RATIO: float = 1.0
_MOUTH_FLAT_Y_RATIO: float = 0.6
_MOUTH_FLAT_Z_RATIO: float = 0.1

_MOUTH_FANG_X_RATIO: float = 0.35
_MOUTH_FANG_Z_RATIO: float = 0.8

_MOUTH_BEAK_X_RATIO: float = 0.55
_MOUTH_BEAK_Z_RATIO: float = 0.9

_TAIL_WHIP_XY_RATIO: float = 0.15
_TAIL_SEG_XY_RATIO: float = 0.45
_TAIL_CLUB_Z_RATIO: float = 0.7
_TAIL_CURLED_X_RATIO: float = 0.6
_TAIL_CURLED_Z_RATIO: float = 0.3


def create_eye_mesh(shape: str, location: Vector3, eye_scale: float) -> "Object":
    """Create an eye mesh primitive dispatched by shape."""
    if shape == "square":
        return create_box(location=location, scale=(eye_scale, eye_scale, eye_scale))
    if shape == "oval":
        return create_sphere(
            location=location,
            scale=(
                eye_scale * _EYE_OVAL_SCALE_X,
                eye_scale,
                eye_scale * _EYE_OVAL_SCALE_Z,
            ),
        )
    if shape == "slit":
        return create_sphere(
            location=location,
            scale=(eye_scale, eye_scale * _EYE_SLIT_SCALE_Y, eye_scale),
        )
    # Default: 'circle' (uniform sphere) — also the fallback for unknown shapes.
    return create_sphere(location=location, scale=(eye_scale, eye_scale, eye_scale))


def create_pupil_mesh(shape: str, location: Vector3, pupil_scale: float) -> "Object":
    """Create a pupil mesh primitive dispatched by shape."""
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
    # Default: 'dot' (flat disc sphere) — also the fallback for unknown shapes.
    return create_sphere(
        location=location,
        scale=(pupil_scale, pupil_scale, pupil_scale * _PUPIL_DOT_Z_RATIO),
    )


def create_mouth_mesh(shape: str, location: Vector3, head_scale: float) -> "Object":
    """Create a mouth mesh primitive dispatched by shape."""
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
    # Default: 'smile' (thin disc cylinder) — also the fallback for unknown shapes.
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
    """Create a tail mesh primitive dispatched by shape."""
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
            scale=(
                length * _TAIL_SEG_XY_RATIO,
                length * _TAIL_SEG_XY_RATIO,
                length * 1.0,
            ),
            vertices=12,
            depth=2.0,
        )
    # Default: 'curled' (flattened sphere) — also the fallback for unknown shapes.
    return create_sphere(
        location=location,
        scale=(
            length * _TAIL_CURLED_X_RATIO,
            length * _TAIL_CURLED_X_RATIO,
            length * _TAIL_CURLED_Z_RATIO,
        ),
    )


__all__ = [
    "create_eye_mesh",
    "create_pupil_mesh",
    "create_mouth_mesh",
    "create_tail_mesh",
]
