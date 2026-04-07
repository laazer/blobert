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
