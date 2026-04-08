"""Procedural segmented limb meshes (cylinders, optional joint spheres, end caps)."""

from __future__ import annotations

from mathutils import Vector

from ..blender_utils import create_box, create_cylinder, create_sphere


def _align_cylinder_z_to_direction(obj, direction: Vector) -> None:
    if direction.length < 1e-12:
        return
    dn = direction.normalized()
    quat = Vector((0, 0, 1)).rotation_difference(dn)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = quat


def append_segmented_limb_mesh(
    parts: list,
    head: Vector,
    tail: Vector,
    n_segments: int,
    radius: float,
    *,
    vertices: int = 6,
    depth: float = 2.0,
    joint_visual: bool = True,
    joint_ball_scale: float = 1.4,
    end_shape: str = "none",
    end_scale: tuple[float, float, float] = (0.15, 0.15, 0.15),
) -> None:
    """Append cylinder segments along ``head``→``tail``, optional interior balls, optional end primitive."""
    n = max(1, min(8, int(n_segments)))
    delta = tail - head
    length = delta.length
    if length < 1e-12:
        return
    direction = delta / length

    for i in range(n):
        t0 = i / n
        t1 = (i + 1) / n
        p0 = head + delta * t0
        p1 = head + delta * t1
        mid = (p0 + p1) * 0.5
        seg_len = (p1 - p0).length
        if seg_len < 1e-12:
            continue
        z_scale = seg_len / depth
        cyl = create_cylinder(
            location=mid,
            scale=(radius, radius, z_scale),
            vertices=vertices,
            depth=depth,
        )
        _align_cylinder_z_to_direction(cyl, direction)
        parts.append(cyl)
        if joint_visual and i < n - 1:
            br = radius * joint_ball_scale
            ball = create_sphere(location=p1, scale=(br, br, br))
            parts.append(ball)

    if end_shape == "sphere":
        parts.append(create_sphere(location=tail, scale=end_scale))
    elif end_shape == "box":
        parts.append(create_box(location=tail, scale=end_scale))
