"""Colinear multi-segment limb bones for RigDefinition (no Blender dependency)."""

from __future__ import annotations

from mathutils import Vector

from ..rig_types import BoneSpec

ALLOWED_END_SHAPES: tuple[str, ...] = ("none", "sphere", "box")


def limb_chain(
    head: Vector,
    tail: Vector,
    n: int,
    name: str,
    parent_name: str | None = None,
) -> list[BoneSpec]:
    """Return ``n`` contiguous bones from ``head`` to ``tail`` (``n`` clamped to 1..8).

    Segment 0 is named ``name``; further segments are ``name_1``, ``name_2``, ...
    """
    n_clamped = max(1, min(8, int(n)))
    bones: list[BoneSpec] = []
    prev_name: str | None = None
    for i in range(n_clamped):
        t0 = i / n_clamped
        t1 = (i + 1) / n_clamped
        p0 = head + (tail - head) * t0
        p1 = head + (tail - head) * t1
        bone_name = name if i == 0 else f"{name}_{i}"
        parent = parent_name if i == 0 else prev_name
        bones.append(BoneSpec(name=bone_name, head=p0, tail=p1, parent_name=parent))
        prev_name = bone_name
    return bones
