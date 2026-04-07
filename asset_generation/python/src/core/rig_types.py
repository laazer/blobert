"""Typed rig and animated build results (shared by animations + enemies)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mathutils import Vector


@dataclass(frozen=True)
class BoneSpec:
    """Single bone in edit-bone space."""

    name: str
    head: Vector
    tail: Vector
    parent_name: str | None = None


@dataclass(frozen=True)
class RigDefinition:
    """Ordered bone list: parents must appear before children."""

    bones: tuple[BoneSpec, ...]


@dataclass(frozen=True)
class AnimatedBuildResult:
    """Result of building one animated enemy (mesh + armature + combat data)."""

    armature: Any
    mesh: Any
    attack_profile: list[Any]


def rig_from_bone_map(
    bone_map: dict[str, tuple[Vector, Vector, str | None]],
) -> RigDefinition:
    """Convert legacy dict[str, (head, tail, parent)] to RigDefinition (preserves insertion order)."""
    bones: list[BoneSpec] = []
    for name, (head, tail, parent) in bone_map.items():
        bones.append(BoneSpec(name=name, head=head, tail=tail, parent_name=parent))
    return RigDefinition(bones=tuple(bones))


def quadruped_simple_rig_definition(body_scale: float) -> RigDefinition:
    """Shared quadruped 9-bone layout (spider, claw crawler, example spider)."""
    s = body_scale
    return rig_from_bone_map(
        {
            "root": (Vector((0, 0, 0)), Vector((0, 0, s * 0.2)), None),
            "spine": (Vector((0, 0, s * 0.2)), Vector((s * 0.5, 0, s * 0.4)), "root"),
            "head": (Vector((s * 0.5, 0, s * 0.4)), Vector((s * 0.8, 0, s * 0.6)), "spine"),
            "leg_fl": (Vector((s * 0.3, s * 0.3, s * 0.3)), Vector((s * 0.3, s * 0.3, 0)), "spine"),
            "leg_fr": (Vector((s * 0.3, -s * 0.3, s * 0.3)), Vector((s * 0.3, -s * 0.3, 0)), "spine"),
            "leg_ml": (Vector((0, s * 0.4, s * 0.3)), Vector((0, s * 0.4, 0)), "spine"),
            "leg_mr": (Vector((0, -s * 0.4, s * 0.3)), Vector((0, -s * 0.4, 0)), "spine"),
            "leg_bl": (Vector((-s * 0.2, s * 0.3, s * 0.3)), Vector((-s * 0.2, s * 0.3, 0)), "root"),
            "leg_br": (Vector((-s * 0.2, -s * 0.3, s * 0.3)), Vector((-s * 0.2, -s * 0.3, 0)), "root"),
        }
    )


def humanoid_simple_rig_definition(body_height: float) -> RigDefinition:
    """Shared 7-bone humanoid layout used by several animated enemies (imp, carapace husk, examples)."""
    h = body_height
    return rig_from_bone_map(
        {
            "root": (Vector((0, 0, 0)), Vector((0, 0, h * 0.2)), None),
            "spine": (Vector((0, 0, h * 0.2)), Vector((0, 0, h * 0.7)), "root"),
            "head": (Vector((0, 0, h * 0.7)), Vector((0, 0, h * 1.0)), "spine"),
            "arm_l": (Vector((0, h * 0.2, h * 0.6)), Vector((0, h * 0.5, h * 0.3)), "spine"),
            "arm_r": (Vector((0, -h * 0.2, h * 0.6)), Vector((0, -h * 0.5, h * 0.3)), "spine"),
            "leg_l": (Vector((0, h * 0.1, h * 0.2)), Vector((0, h * 0.1, 0)), "root"),
            "leg_r": (Vector((0, -h * 0.1, h * 0.2)), Vector((0, -h * 0.1, 0)), "root"),
        }
    )
