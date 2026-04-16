"""Module-level geometry helpers for AnimatedSpider eye placement (extracted for class size limits)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from mathutils import Vector

from ..utils.placement_clustering import placement_prng

if TYPE_CHECKING:
    from .animated_spider import AnimatedSpider


def point_on_ellipsoid_surface(
    center: Vector, radii: Vector, direction: Vector
) -> Vector:
    """Project a direction from center to the ellipsoid surface."""
    if direction.length <= 1e-8:
        return Vector((center.x + radii.x, center.y, center.z))
    dx, dy, dz = direction.x, direction.y, direction.z
    rx = max(1e-8, radii.x)
    ry = max(1e-8, radii.y)
    rz = max(1e-8, radii.z)
    denom = (
        ((dx * dx) / (rx * rx)) + ((dy * dy) / (ry * ry)) + ((dz * dz) / (rz * rz))
    )
    if denom <= 1e-12:
        return Vector((center.x + radii.x, center.y, center.z))
    t = 1.0 / math.sqrt(denom)
    return Vector((center.x + dx * t, center.y + dy * t, center.z + dz * t))


def separate_eye_dirs(eye_dirs: list[Vector], min_distance: float) -> list[Vector]:
    """Push nearby eye directions apart on the head sphere to avoid overlap."""
    if len(eye_dirs) < 2:
        return eye_dirs
    out = [Vector((v.x, v.y, v.z)).normalized() for v in eye_dirs]
    for _ in range(6):
        moved = False
        for i in range(len(out)):
            for j in range(i + 1, len(out)):
                d = out[i] - out[j]
                dist = d.length
                if dist >= min_distance:
                    continue
                if dist <= 1e-8:
                    d = Vector((0.0, 1.0, 0.0))
                    dist = 1.0
                push = d.normalized() * ((min_distance - dist) * 0.5)
                out[i] = (out[i] + push).normalized()
                out[j] = (out[j] - push).normalized()
                moved = True
        if not moved:
            break
    return out


def eye_dirs_uniform(
    spider: "AnimatedSpider", eye_count: int, head_center: Vector, head_scale: float
) -> list[Vector]:
    """Compute uniformly-distributed eye direction vectors for the given spider instance."""
    cl = spider._eye_clustering()
    spread = 1.0 - cl * 0.92
    eye_base_z = spider._mesh("EYE_Z")
    if eye_count == 1:
        eyes = [
            Vector((1.0, 0.0, (eye_base_z - head_center.z) / max(1e-8, head_scale)))
        ]
    elif eye_count == 2:
        eye_y = head_scale * spider._mesh("EYE_Y_SIDE") * spread
        eyes = [
            Vector(
                (
                    1.0,
                    eye_y / max(1e-8, head_scale),
                    (eye_base_z - head_center.z) / max(1e-8, head_scale),
                )
            ),
            Vector(
                (
                    1.0,
                    -eye_y / max(1e-8, head_scale),
                    (eye_base_z - head_center.z) / max(1e-8, head_scale),
                )
            ),
        ]
    else:
        span = max(1, eye_count - 1)
        eye_arc = spider._mesh("EYE_Y_SIDE")
        eyes = []
        for i in range(eye_count):
            t = (i / span) * 2.0 - 1.0
            angle = t * (math.pi * 0.42) * spread
            eye_y = head_scale * eye_arc * math.sin(angle)
            eye_z = eye_base_z + head_scale * 0.30 * math.cos(angle)
            eye_x = head_center.x + head_scale
            eyes.append(
                Vector(
                    (
                        (eye_x - head_center.x) / max(1e-8, head_scale),
                        eye_y / max(1e-8, head_scale),
                        (eye_z - head_center.z) / max(1e-8, head_scale),
                    )
                )
            )
    return eyes


def eye_dirs_random(
    spider: "AnimatedSpider", eye_count: int, head_center: Vector, head_scale: float
) -> list[Vector]:
    """Compute randomly-distributed eye direction vectors for the given spider instance."""
    prng = placement_prng(spider)
    cl = spider._eye_clustering()
    spread = max(0.08, (1.0 - cl * 0.92) * 0.62)
    eye_base_z = spider._mesh("EYE_Z")
    rel_z0 = (eye_base_z - head_center.z) / max(1e-8, head_scale)
    hs = max(1e-8, head_scale)
    eyes: list[Vector] = []
    if eye_count == 1:
        eyes.append(Vector((1.0, 0.0, rel_z0)))
        return eyes
    for _ in range(eye_count):
        jy = (prng.random() - 0.5) * 2.0 * spread * spider._mesh("EYE_Y_SIDE")
        jz = (prng.random() - 0.5) * 0.55 * spread
        eyes.append(Vector((1.0, jy / hs, rel_z0 + jz)))
    return eyes
