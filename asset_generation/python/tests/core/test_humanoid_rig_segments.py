# ruff: noqa: I001
"""
Tests for HumanoidSimpleRig refactored rig_definition() with multi-segment tuners.
Covers: LJEC-4 (new ClassVar tuners), LJEC-5 (rig_definition behavior), LJEC-9
(backward compatibility regression contract).

Red against current codebase:
- HumanoidSimpleRig does not yet have ARM_SEGMENTS, LEG_SEGMENTS, ARM_END_SHAPE,
  LEG_END_SHAPE, LIMB_JOINT_BALL_SCALE, LIMB_JOINT_VISUAL ClassVars.
- rig_definition() does not yet use limb_chain.

Spec: project_board/specs/limb_joints_and_end_caps_spec.md, requirements LJEC-4, LJEC-5, LJEC-9.
"""

from __future__ import annotations

import random

from src.utils.blender_stubs import ensure_blender_stubs

ensure_blender_stubs()

from mathutils import Vector  # noqa: E402
from src.core.rig_models.humanoid_simple import HumanoidRigLayout, HumanoidSimpleRig  # noqa: E402
from src.core.rig_types import BoneSpec, RigDefinition  # noqa: E402
from src.enemies.animated_enemy import AnimatedEnemy, UsesSimpleRigMixin  # noqa: E402
from src.utils.config import EnemyBodyTypes  # noqa: E402


# ---------------------------------------------------------------------------
# Test helper: minimal concrete enemy that can call rig_definition()
# ---------------------------------------------------------------------------

class _TestHumanoidRig(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Minimal concrete enemy; no Blender required."""

    body_height = 1.0

    def build_mesh_parts(self) -> None:
        self.parts = []

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID


def _make_rig(build_options=None, body_height=1.0) -> _TestHumanoidRig:
    rng = random.Random(0)
    t = _TestHumanoidRig("test", materials={}, rng=rng, build_options=build_options or {})
    t.body_height = body_height
    return t


def _get_bone(rig: RigDefinition, name: str) -> BoneSpec:
    matches = [b for b in rig.bones if b.name == name]
    assert matches, f"Bone '{name}' not found in rig. Bones: {[b.name for b in rig.bones]}"
    return matches[0]


def _v(x: float, y: float, z: float) -> Vector:
    return Vector((x, y, z))


# ---------------------------------------------------------------------------
# LJEC-4: New ClassVar tuners exist on HumanoidSimpleRig
# ---------------------------------------------------------------------------

class TestHumanoidSimpleRigClassVars:
    """LJEC-4-AC1 through LJEC-4-AC6: ClassVar tuners defined on HumanoidSimpleRig."""

    def test_ARM_SEGMENTS_exists(self):
        assert hasattr(HumanoidSimpleRig, "ARM_SEGMENTS")

    def test_ARM_SEGMENTS_default_is_1(self):
        """LJEC-4-AC1: default value is 1."""
        assert HumanoidSimpleRig.ARM_SEGMENTS == 1

    def test_ARM_SEGMENTS_is_int(self):
        assert isinstance(HumanoidSimpleRig.ARM_SEGMENTS, int)

    def test_LEG_SEGMENTS_exists(self):
        assert hasattr(HumanoidSimpleRig, "LEG_SEGMENTS")

    def test_LEG_SEGMENTS_default_is_1(self):
        """LJEC-4-AC2: default value is 1."""
        assert HumanoidSimpleRig.LEG_SEGMENTS == 1

    def test_LEG_SEGMENTS_is_int(self):
        assert isinstance(HumanoidSimpleRig.LEG_SEGMENTS, int)

    def test_ARM_END_SHAPE_exists(self):
        assert hasattr(HumanoidSimpleRig, "ARM_END_SHAPE")

    def test_ARM_END_SHAPE_default_is_none_string(self):
        """LJEC-4-AC3: default value is 'none'."""
        assert HumanoidSimpleRig.ARM_END_SHAPE == "none"

    def test_ARM_END_SHAPE_is_str(self):
        assert isinstance(HumanoidSimpleRig.ARM_END_SHAPE, str)

    def test_LEG_END_SHAPE_exists(self):
        assert hasattr(HumanoidSimpleRig, "LEG_END_SHAPE")

    def test_LEG_END_SHAPE_default_is_none_string(self):
        """LJEC-4-AC4: default value is 'none'."""
        assert HumanoidSimpleRig.LEG_END_SHAPE == "none"

    def test_LEG_END_SHAPE_is_str(self):
        assert isinstance(HumanoidSimpleRig.LEG_END_SHAPE, str)

    def test_LIMB_JOINT_BALL_SCALE_exists(self):
        assert hasattr(HumanoidSimpleRig, "LIMB_JOINT_BALL_SCALE")

    def test_LIMB_JOINT_BALL_SCALE_default_is_1_4(self):
        """LJEC-4-AC5: default value is 1.4."""
        assert HumanoidSimpleRig.LIMB_JOINT_BALL_SCALE == 1.4

    def test_LIMB_JOINT_BALL_SCALE_is_float(self):
        assert isinstance(HumanoidSimpleRig.LIMB_JOINT_BALL_SCALE, float)

    def test_LIMB_JOINT_VISUAL_exists(self):
        assert hasattr(HumanoidSimpleRig, "LIMB_JOINT_VISUAL")

    def test_LIMB_JOINT_VISUAL_default_is_True(self):
        """LJEC-4-AC6: default value is True."""
        assert HumanoidSimpleRig.LIMB_JOINT_VISUAL is True

    def test_LIMB_JOINT_VISUAL_is_bool(self):
        assert isinstance(HumanoidSimpleRig.LIMB_JOINT_VISUAL, bool)

    def test_ARM_SEGMENTS_not_bool(self):
        """ARM_SEGMENTS must not be bool (would prevent _mesh from treating it as int)."""
        assert type(HumanoidSimpleRig.ARM_SEGMENTS) is not bool

    def test_LEG_SEGMENTS_not_bool(self):
        assert type(HumanoidSimpleRig.LEG_SEGMENTS) is not bool


# ---------------------------------------------------------------------------
# LJEC-4-AC3/AC4: Default end shape values are in ALLOWED_END_SHAPES
# ---------------------------------------------------------------------------

class TestHumanoidSimpleRigEndShapeDefaults:
    """ARM_END_SHAPE and LEG_END_SHAPE defaults must be in ALLOWED_END_SHAPES."""

    def test_ARM_END_SHAPE_default_in_allowed(self):
        from src.core.rig_models.limb_chain import ALLOWED_END_SHAPES
        assert HumanoidSimpleRig.ARM_END_SHAPE in ALLOWED_END_SHAPES

    def test_LEG_END_SHAPE_default_in_allowed(self):
        from src.core.rig_models.limb_chain import ALLOWED_END_SHAPES
        assert HumanoidSimpleRig.LEG_END_SHAPE in ALLOWED_END_SHAPES


# ---------------------------------------------------------------------------
# LJEC-5-AC1 / LJEC-5-AC2: Default rig has 7 bones, named correctly
# ---------------------------------------------------------------------------

class TestRigDefinitionDefaultBoneCount:
    """LJEC-5-AC1 and LJEC-5-AC2: with default tuners, 7 bones in correct order."""

    def test_default_rig_has_7_bones(self):
        rig_model = _make_rig()
        rig = rig_model.rig_definition()
        assert len(rig.bones) == 7

    def test_default_rig_bone_names_in_order(self):
        """LJEC-5-AC2: bone names in insertion order."""
        rig_model = _make_rig()
        rig = rig_model.rig_definition()
        expected = ["root", "spine", "head", "arm_l", "arm_r", "leg_l", "leg_r"]
        actual = [b.name for b in rig.bones]
        assert actual == expected

    def test_rig_definition_returns_rig_definition_type(self):
        rig_model = _make_rig()
        rig = rig_model.rig_definition()
        assert isinstance(rig, RigDefinition)

    def test_rig_bones_is_tuple(self):
        rig_model = _make_rig()
        rig = rig_model.rig_definition()
        assert isinstance(rig.bones, tuple)


# ---------------------------------------------------------------------------
# LJEC-5-AC3 / LJEC-9-AC4: Bone positions match current implementation (n=1)
# ---------------------------------------------------------------------------

class TestRigDefinitionBonePositions:
    """
    LJEC-5-AC3 and LJEC-9-AC4: n=1 bone positions are numerically identical to
    current rig_from_bone_map output at body_height=1.0.
    """

    def _rig_at_h1(self) -> RigDefinition:
        return _make_rig(body_height=1.0).rig_definition()

    def test_root_head_is_origin(self):
        rig = self._rig_at_h1()
        root = _get_bone(rig, "root")
        assert root.head == _v(0, 0, 0)

    def test_root_tail_z_matches_layout(self):
        rig = self._rig_at_h1()
        root = _get_bone(rig, "root")
        assert root.tail == _v(0, 0, HumanoidRigLayout.ROOT_TAIL_Z)

    def test_spine_head_equals_root_tail(self):
        rig = self._rig_at_h1()
        root = _get_bone(rig, "root")
        spine = _get_bone(rig, "spine")
        assert spine.head == root.tail

    def test_spine_tail_z_matches_layout(self):
        rig = self._rig_at_h1()
        spine = _get_bone(rig, "spine")
        assert spine.tail == _v(0, 0, HumanoidRigLayout.SPINE_TOP_Z)

    def test_head_head_equals_spine_tail(self):
        rig = self._rig_at_h1()
        spine = _get_bone(rig, "spine")
        head_bone = _get_bone(rig, "head")
        assert head_bone.head == spine.tail

    def test_head_tail_z_matches_layout(self):
        rig = self._rig_at_h1()
        head_bone = _get_bone(rig, "head")
        assert head_bone.tail == _v(0, 0, HumanoidRigLayout.HEAD_TOP_Z)

    def test_arm_l_head_matches_layout(self):
        """LJEC-9-AC4: arm_l.head at h=1.0."""
        rig = self._rig_at_h1()
        arm_l = _get_bone(rig, "arm_l")
        expected_head = _v(
            0,
            HumanoidRigLayout.ARM_SHOULDER_Y,
            HumanoidRigLayout.ARM_UPPER_Z,
        )
        assert arm_l.head == expected_head

    def test_arm_l_tail_matches_layout(self):
        """LJEC-9-AC4: arm_l.tail at h=1.0."""
        rig = self._rig_at_h1()
        arm_l = _get_bone(rig, "arm_l")
        expected_tail = _v(
            0,
            HumanoidRigLayout.ARM_OUTER_Y,
            HumanoidRigLayout.ARM_LOWER_Z,
        )
        assert arm_l.tail == expected_tail

    def test_arm_r_head_matches_layout(self):
        rig = self._rig_at_h1()
        arm_r = _get_bone(rig, "arm_r")
        expected_head = _v(
            0,
            -HumanoidRigLayout.ARM_SHOULDER_Y,
            HumanoidRigLayout.ARM_UPPER_Z,
        )
        assert arm_r.head == expected_head

    def test_arm_r_tail_matches_layout(self):
        rig = self._rig_at_h1()
        arm_r = _get_bone(rig, "arm_r")
        expected_tail = _v(
            0,
            -HumanoidRigLayout.ARM_OUTER_Y,
            HumanoidRigLayout.ARM_LOWER_Z,
        )
        assert arm_r.tail == expected_tail

    def test_leg_l_head_matches_layout(self):
        rig = self._rig_at_h1()
        leg_l = _get_bone(rig, "leg_l")
        expected_head = _v(
            0,
            HumanoidRigLayout.LEG_INNER_Y,
            HumanoidRigLayout.LEG_UPPER_Z,
        )
        assert leg_l.head == expected_head

    def test_leg_l_tail_matches_layout(self):
        rig = self._rig_at_h1()
        leg_l = _get_bone(rig, "leg_l")
        expected_tail = _v(0, HumanoidRigLayout.LEG_INNER_Y, 0)
        assert leg_l.tail == expected_tail

    def test_leg_r_head_matches_layout(self):
        rig = self._rig_at_h1()
        leg_r = _get_bone(rig, "leg_r")
        expected_head = _v(
            0,
            -HumanoidRigLayout.LEG_INNER_Y,
            HumanoidRigLayout.LEG_UPPER_Z,
        )
        assert leg_r.head == expected_head

    def test_leg_r_tail_matches_layout(self):
        rig = self._rig_at_h1()
        leg_r = _get_bone(rig, "leg_r")
        expected_tail = _v(0, -HumanoidRigLayout.LEG_INNER_Y, 0)
        assert leg_r.tail == expected_tail


# ---------------------------------------------------------------------------
# LJEC-5-AC4: Parent names match current implementation
# ---------------------------------------------------------------------------

class TestRigDefinitionParentNames:
    """LJEC-5-AC4: parent names match current rig_from_bone_map output."""

    def _rig(self) -> RigDefinition:
        return _make_rig().rig_definition()

    def test_root_has_no_parent(self):
        rig = self._rig()
        root = _get_bone(rig, "root")
        assert root.parent_name is None

    def test_spine_parent_is_root(self):
        rig = self._rig()
        spine = _get_bone(rig, "spine")
        assert spine.parent_name == "root"

    def test_head_parent_is_spine(self):
        rig = self._rig()
        head = _get_bone(rig, "head")
        assert head.parent_name == "spine"

    def test_arm_l_parent_is_spine(self):
        """LJEC-5-AC4: arm chains attach to 'spine'."""
        rig = self._rig()
        arm_l = _get_bone(rig, "arm_l")
        assert arm_l.parent_name == "spine"

    def test_arm_r_parent_is_spine(self):
        rig = self._rig()
        arm_r = _get_bone(rig, "arm_r")
        assert arm_r.parent_name == "spine"

    def test_leg_l_parent_is_root(self):
        """LJEC-5-AC4: leg chains attach to 'root'."""
        rig = self._rig()
        leg_l = _get_bone(rig, "leg_l")
        assert leg_l.parent_name == "root"

    def test_leg_r_parent_is_root(self):
        rig = self._rig()
        leg_r = _get_bone(rig, "leg_r")
        assert leg_r.parent_name == "root"


# ---------------------------------------------------------------------------
# LJEC-5-AC5 / LJEC-5-AC6: ARM_SEGMENTS=2 bone count and names
# ---------------------------------------------------------------------------

class TestRigDefinitionArmSegments2:
    """LJEC-5-AC5 and LJEC-5-AC6: ARM_SEGMENTS=2 adds correct bones."""

    def _rig_arm2(self) -> RigDefinition:
        return _make_rig(
            build_options={"mesh": {"ARM_SEGMENTS": 2}}
        ).rig_definition()

    def test_arm_segments2_leg1_total_bone_count_is_9(self):
        """LJEC-5-AC5: 3 non-limb + 4 arm bones (2 per side) + 2 leg bones = 9."""
        rig = self._rig_arm2()
        assert len(rig.bones) == 9

    def test_arm_l_present(self):
        """LJEC-5-AC6: arm_l is still present as first arm-left bone."""
        rig = self._rig_arm2()
        names = [b.name for b in rig.bones]
        assert "arm_l" in names

    def test_arm_l_1_present(self):
        """LJEC-5-AC6: arm_l_1 is the second segment for left arm."""
        rig = self._rig_arm2()
        names = [b.name for b in rig.bones]
        assert "arm_l_1" in names

    def test_arm_r_present(self):
        rig = self._rig_arm2()
        names = [b.name for b in rig.bones]
        assert "arm_r" in names

    def test_arm_r_1_present(self):
        rig = self._rig_arm2()
        names = [b.name for b in rig.bones]
        assert "arm_r_1" in names

    def test_leg_l_present_without_extra_segment(self):
        """LEG_SEGMENTS=1 (default): leg_l present but not leg_l_1."""
        rig = self._rig_arm2()
        names = [b.name for b in rig.bones]
        assert "leg_l" in names
        assert "leg_l_1" not in names

    def test_leg_r_present_without_extra_segment(self):
        rig = self._rig_arm2()
        names = [b.name for b in rig.bones]
        assert "leg_r" in names
        assert "leg_r_1" not in names


# ---------------------------------------------------------------------------
# LJEC-5-AC7: Contiguous segments (arm chain end matches start of next)
# ---------------------------------------------------------------------------

class TestRigDefinitionSegmentContiguity:
    """LJEC-5-AC7: with ARM_SEGMENTS=2, arm_l.tail == arm_l_1.head."""

    def test_arm_l_tail_equals_arm_l_1_head(self):
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()
        arm_l = _get_bone(rig, "arm_l")
        arm_l_1 = _get_bone(rig, "arm_l_1")
        assert arm_l.tail == arm_l_1.head

    def test_arm_r_tail_equals_arm_r_1_head(self):
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()
        arm_r = _get_bone(rig, "arm_r")
        arm_r_1 = _get_bone(rig, "arm_r_1")
        assert arm_r.tail == arm_r_1.head

    def test_arm_l_1_tail_equals_original_arm_l_tail(self):
        """LJEC-5-AC7: the end of the chain equals the original single-bone tail."""
        rig_1 = _make_rig().rig_definition()
        rig_2 = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()
        original_arm_l_tail = _get_bone(rig_1, "arm_l").tail
        arm_l_1 = _get_bone(rig_2, "arm_l_1")
        assert arm_l_1.tail == original_arm_l_tail


# ---------------------------------------------------------------------------
# LJEC-5-AC8: Parent names with ARM_SEGMENTS=2
# ---------------------------------------------------------------------------

class TestRigDefinitionArmSegments2Parents:
    """LJEC-5-AC8: parent chain with ARM_SEGMENTS=2."""

    def _rig(self) -> RigDefinition:
        return _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()

    def test_arm_l_parent_is_spine(self):
        rig = self._rig()
        arm_l = _get_bone(rig, "arm_l")
        assert arm_l.parent_name == "spine"

    def test_arm_l_1_parent_is_arm_l(self):
        rig = self._rig()
        arm_l_1 = _get_bone(rig, "arm_l_1")
        assert arm_l_1.parent_name == "arm_l"

    def test_arm_r_parent_is_spine(self):
        rig = self._rig()
        arm_r = _get_bone(rig, "arm_r")
        assert arm_r.parent_name == "spine"

    def test_arm_r_1_parent_is_arm_r(self):
        rig = self._rig()
        arm_r_1 = _get_bone(rig, "arm_r_1")
        assert arm_r_1.parent_name == "arm_r"


# ---------------------------------------------------------------------------
# LJEC-5-AC9: Parents before children ordering constraint
# ---------------------------------------------------------------------------

class TestRigDefinitionParentOrdering:
    """LJEC-5-AC9: every bone appears after all its ancestors."""

    def _check_ordering(self, rig: RigDefinition) -> None:
        seen: set[str] = set()
        for bone in rig.bones:
            if bone.parent_name is not None:
                assert bone.parent_name in seen, (
                    f"Bone '{bone.name}' appears before its parent '{bone.parent_name}'. "
                    f"Seen so far: {seen}"
                )
            seen.add(bone.name)

    def test_default_ordering(self):
        rig = _make_rig().rig_definition()
        self._check_ordering(rig)

    def test_arm_segments_2_ordering(self):
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()
        self._check_ordering(rig)

    def test_leg_segments_2_ordering(self):
        rig = _make_rig(build_options={"mesh": {"LEG_SEGMENTS": 2}}).rig_definition()
        self._check_ordering(rig)

    def test_arm_segments_3_leg_segments_3_ordering(self):
        rig = _make_rig(
            build_options={"mesh": {"ARM_SEGMENTS": 3, "LEG_SEGMENTS": 3}}
        ).rig_definition()
        self._check_ordering(rig)

    def test_arm_segments_8_ordering(self):
        """Maximum segment count (8) ordering."""
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 8}}).rig_definition()
        self._check_ordering(rig)


# ---------------------------------------------------------------------------
# LJEC-4-AC9 / LJEC-4-AC10: ARM_SEGMENTS / LEG_SEGMENTS read via _mesh
# ---------------------------------------------------------------------------

class TestRigDefinitionReadsTunersViaMesh:
    """LJEC-4-AC9 and LJEC-4-AC10: segment counts are overridable via build_options."""

    def test_arm_segments_2_via_build_options(self):
        """ARM_SEGMENTS=2 via build_options["mesh"] produces 2-segment arms."""
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()
        names = [b.name for b in rig.bones]
        assert "arm_l_1" in names
        assert "arm_r_1" in names

    def test_leg_segments_2_via_build_options(self):
        """LEG_SEGMENTS=2 via build_options["mesh"] produces 2-segment legs."""
        rig = _make_rig(build_options={"mesh": {"LEG_SEGMENTS": 2}}).rig_definition()
        names = [b.name for b in rig.bones]
        assert "leg_l_1" in names
        assert "leg_r_1" in names

    def test_arm_segments_0_clamped_to_1(self):
        """Build options value 0 is clamped to 1 (no extra segments)."""
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 0}}).rig_definition()
        names = [b.name for b in rig.bones]
        assert "arm_l" in names
        assert "arm_l_1" not in names

    def test_arm_segments_9_clamped_to_8(self):
        """Build options value 9 is clamped to 8 (max 8 segments)."""
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 9}}).rig_definition()
        names = [b.name for b in rig.bones]
        # With 8 segments per arm: arm_l, arm_l_1 .. arm_l_7
        assert "arm_l_7" in names
        assert "arm_l_8" not in names

    def test_total_bones_arm2_leg1(self):
        """ARM_SEGMENTS=2, LEG_SEGMENTS=1: 3 + 4 + 2 = 9 total."""
        rig = _make_rig(build_options={"mesh": {"ARM_SEGMENTS": 2}}).rig_definition()
        assert len(rig.bones) == 9

    def test_total_bones_arm1_leg2(self):
        """ARM_SEGMENTS=1, LEG_SEGMENTS=2: 3 + 2 + 4 = 9 total."""
        rig = _make_rig(build_options={"mesh": {"LEG_SEGMENTS": 2}}).rig_definition()
        assert len(rig.bones) == 9

    def test_total_bones_arm2_leg2(self):
        """ARM_SEGMENTS=2, LEG_SEGMENTS=2: 3 + 4 + 4 = 11 total."""
        rig = _make_rig(
            build_options={"mesh": {"ARM_SEGMENTS": 2, "LEG_SEGMENTS": 2}}
        ).rig_definition()
        assert len(rig.bones) == 11


# ---------------------------------------------------------------------------
# LJEC-9-AC1 / LJEC-9: Regression — existing test_rig_ratios.py assertions hold
# ---------------------------------------------------------------------------

class TestRigRatiosRegression:
    """
    LJEC-9-AC1: The three tests from test_rig_ratios.py must pass.
    Reproduced here verbatim to make the contract explicit in this file.
    """

    def test_imported_humanoid_rig_root_tail_z(self):
        """Mirrors test_import_humanoid_rig_matches_layout_defaults."""
        from src.core.rig_models.import_rigs import imported_humanoid_rig

        rig = imported_humanoid_rig()
        root = next(b for b in rig.bones if b.name == "root")
        assert root.tail == Vector((0, 0, HumanoidRigLayout.ROOT_TAIL_Z))

    def test_rig_ratio_mesh_override_changes_spine_tail(self):
        """Mirrors test_rig_ratio_mesh_override_changes_spine_tail."""
        rng = random.Random(0)
        t = _TestHumanoidRig(
            "t",
            materials={},
            rng=rng,
            build_options={"mesh": {"RIG_SPINE_TOP_Z": 0.91}},
        )
        rig = t.get_rig_definition()
        spine = next(b for b in rig.bones if b.name == "spine")
        assert spine.tail == Vector((0, 0, 0.91))

    def test_simple_rig_model_rig_ratio_without_mesh(self):
        """Mirrors test_simple_rig_model_rig_ratio_without_mesh."""

        class _Stub(HumanoidSimpleRig):
            body_height = 2.0

        s = _Stub()
        assert s._rig_ratio("RIG_ROOT_TAIL_Z") == HumanoidRigLayout.ROOT_TAIL_Z
