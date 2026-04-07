"""Tests for core.rig_types (typed rigs)."""

from __future__ import annotations

from mathutils import Vector
from src.core.rig_types import BoneSpec, RigDefinition, rig_from_bone_map


def test_rig_from_bone_map_builds_ordered_bones() -> None:
    rig = rig_from_bone_map(
        {
            "a": (Vector((0, 0, 0)), Vector((0, 0, 1)), None),
            "b": (Vector((0, 0, 1)), Vector((1, 0, 1)), "a"),
        }
    )
    assert isinstance(rig, RigDefinition)
    assert len(rig.bones) == 2
    assert rig.bones[0] == BoneSpec(name="a", head=Vector((0, 0, 0)), tail=Vector((0, 0, 1)), parent_name=None)
    assert rig.bones[1].parent_name == "a"
