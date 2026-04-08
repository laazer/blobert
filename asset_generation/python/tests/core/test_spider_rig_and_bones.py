from __future__ import annotations

import random

from src.body_families.bones import BoneNames
from src.enemies.animated_spider import AnimatedSpider
from src.utils.blender_stubs import ensure_blender_stubs

ensure_blender_stubs()


def test_spider_bone_helpers_groups() -> None:
    assert BoneNames.get_spider_group_a_roots() == ["leg_0", "leg_2", "leg_4", "leg_6"]
    assert BoneNames.get_spider_group_b_roots() == ["leg_1", "leg_3", "leg_5", "leg_7"]


def test_spider_rig_has_8_leg_roots_and_3_segments_each() -> None:
    s = AnimatedSpider("spider", materials={}, rng=random.Random(0), build_options={})
    s.body_height = 1.0
    rig = s.get_rig_definition()
    names = [b.name for b in rig.bones]
    roots = BoneNames.get_spider_leg_roots()
    for root in roots:
        assert root in names
        assert f"{root}_1" in names
        assert f"{root}_2" in names
    assert len(rig.bones) == 3 + (8 * 3)

