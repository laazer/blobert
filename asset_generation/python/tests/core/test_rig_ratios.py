"""RIG_* layout ratios and build_options mesh overrides."""

from __future__ import annotations

import random

from mathutils import Vector
from src.core.rig_models.humanoid_simple import HumanoidRigLayout, HumanoidSimpleRig
from src.core.rig_models.import_rigs import imported_humanoid_rig
from src.enemies.animated_enemy import AnimatedEnemy, UsesSimpleRigMixin
from src.utils.constants import EnemyBodyTypes


class _TestHumanoidRig(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Minimal concrete enemy for rig_definition + _mesh without Blender."""

    body_height = 1.0

    def build_mesh_parts(self) -> None:
        self.parts = []

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID


def test_import_humanoid_rig_matches_layout_defaults() -> None:
    rig = imported_humanoid_rig()
    root = next(b for b in rig.bones if b.name == "root")
    assert root.tail == Vector((0, 0, HumanoidRigLayout.ROOT_TAIL_Z))


def test_rig_ratio_mesh_override_changes_spine_tail() -> None:
    rng = random.Random(0)
    t = _TestHumanoidRig("t", materials={}, rng=rng, build_options={"mesh": {"RIG_SPINE_TOP_Z": 0.91}})
    rig = t.get_rig_definition()
    spine = next(b for b in rig.bones if b.name == "spine")
    assert spine.tail == Vector((0, 0, 0.91))


def test_simple_rig_model_rig_ratio_without_mesh() -> None:
    class _Stub(HumanoidSimpleRig):
        body_height = 2.0

    s = _Stub()
    assert s._rig_ratio("RIG_ROOT_TAIL_Z") == HumanoidRigLayout.ROOT_TAIL_Z
