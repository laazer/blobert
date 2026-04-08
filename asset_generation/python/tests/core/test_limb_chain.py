# ruff: noqa: I001
"""
Tests for limb_chain() and ALLOWED_END_SHAPES — LJEC-1, LJEC-2.

Red against current codebase (limb_chain module does not exist yet).
Covers: length, naming convention, parent chain, linear interpolation, clamping,
        n=1 identity, return type, signature, ALLOWED_END_SHAPES constant.

Spec: project_board/specs/limb_joints_and_end_caps_spec.md
"""

from __future__ import annotations

import sys

# Ensure stubs are installed before any src import.
from src.utils.blender_stubs import ensure_blender_stubs

ensure_blender_stubs()

# Extend _Vector stub with arithmetic operators needed for interpolation tests.
# The spec (LJEC-1 Risk) explicitly identifies this as a requirement.
# We patch the stub BEFORE importing limb_chain so the module sees the extended class.
_mathutils = sys.modules["mathutils"]
_VectorCls = _mathutils.Vector


def _patch_vector_arithmetic() -> None:
    """Extend the stub _Vector with __add__, __sub__, __mul__, __rmul__ if missing."""
    if hasattr(_VectorCls, "__add__"):
        return  # already patched (re-entrant safety)

    def _add(self, other):
        return _VectorCls((a + b for a, b in zip(self._t, other._t)))

    def _sub(self, other):
        return _VectorCls((a - b for a, b in zip(self._t, other._t)))

    def _mul(self, scalar):
        return _VectorCls((a * scalar for a in self._t))

    def _rmul(self, scalar):
        return _VectorCls((a * scalar for a in self._t))

    def _truediv(self, scalar):
        return _VectorCls((a / scalar for a in self._t))

    _VectorCls.__add__ = _add
    _VectorCls.__sub__ = _sub
    _VectorCls.__mul__ = _mul
    _VectorCls.__rmul__ = _rmul
    _VectorCls.__truediv__ = _truediv


_patch_vector_arithmetic()


# ---------------------------------------------------------------------------
# Module-under-test import (will fail — red — until implementation exists)
# ---------------------------------------------------------------------------
from mathutils import Vector  # noqa: E402
from src.core.rig_models.limb_chain import ALLOWED_END_SHAPES, limb_chain  # noqa: E402
from src.core.rig_types import BoneSpec  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _v(x: float, y: float, z: float) -> Vector:
    return Vector((x, y, z))


def _make_arm_chain(head, tail, n, name="arm_l", parent_name=None):
    return limb_chain(head=head, tail=tail, n=n, name=name, parent_name=parent_name)


# ---------------------------------------------------------------------------
# LJEC-1-AC1: Return length equals n (after clamping)
# ---------------------------------------------------------------------------

class TestLimbChainLength:
    """LJEC-1-AC1: length of returned list equals n (after clamping)."""

    def test_n1_returns_one_bone(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=1)
        assert len(result) == 1

    def test_n2_returns_two_bones(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2)
        assert len(result) == 2

    def test_n8_returns_eight_bones(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=8)
        assert len(result) == 8

    def test_n3_returns_three_bones(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=3)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# LJEC-1-AC7 / LJEC-1-AC8: Clamping
# ---------------------------------------------------------------------------

class TestLimbChainClamping:
    """LJEC-1-AC7 (clamp below min) and LJEC-1-AC8 (clamp above max)."""

    def test_n0_clamped_to_1(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=0)
        assert len(result) == 1

    def test_n_negative_clamped_to_1(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=-5)
        assert len(result) == 1

    def test_n_negative_large_clamped_to_1(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=-100)
        assert len(result) == 1

    def test_n9_clamped_to_8(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=9)
        assert len(result) == 8

    def test_n100_clamped_to_8(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=100)
        assert len(result) == 8


# ---------------------------------------------------------------------------
# LJEC-1-AC2 / LJEC-1-AC3: Naming convention
# ---------------------------------------------------------------------------

class TestLimbChainNaming:
    """LJEC-1-AC2 (segment-0 name) and LJEC-1-AC3 (subsequent names)."""

    def test_n1_first_name_equals_base_name(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=1, name="arm_l")
        assert result[0].name == "arm_l"

    def test_n2_first_name_equals_base_name(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="arm_l")
        assert result[0].name == "arm_l"

    def test_n2_second_name_is_name_underscore_1(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="arm_l")
        assert result[1].name == "arm_l_1"

    def test_n3_naming_convention(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=3, name="arm_l")
        assert result[0].name == "arm_l"
        assert result[1].name == "arm_l_1"
        assert result[2].name == "arm_l_2"

    def test_n4_naming_convention(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=4, name="leg_l")
        assert result[0].name == "leg_l"
        assert result[1].name == "leg_l_1"
        assert result[2].name == "leg_l_2"
        assert result[3].name == "leg_l_3"

    def test_name_arm_r_preserved(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="arm_r")
        assert result[0].name == "arm_r"
        assert result[1].name == "arm_r_1"

    def test_name_leg_r_preserved(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="leg_r")
        assert result[0].name == "leg_r"
        assert result[1].name == "leg_r_1"


# ---------------------------------------------------------------------------
# LJEC-1-AC4 / LJEC-1-AC5: Parent chain
# ---------------------------------------------------------------------------

class TestLimbChainParents:
    """LJEC-1-AC4 (parent of first segment) and LJEC-1-AC5 (internal parent chain)."""

    def test_n1_parent_name_is_none_when_not_provided(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=1)
        assert result[0].parent_name is None

    def test_n1_parent_name_carries_caller_value(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=1, parent_name="spine")
        assert result[0].parent_name == "spine"

    def test_n2_first_bone_parent_equals_caller_supplied(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="arm_l", parent_name="spine")
        assert result[0].parent_name == "spine"

    def test_n2_second_bone_parent_equals_first_bone_name(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="arm_l", parent_name="spine")
        assert result[1].parent_name == "arm_l"

    def test_n3_parent_chain_is_sequential(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=3, name="arm_l", parent_name="spine")
        assert result[0].parent_name == "spine"
        assert result[1].parent_name == "arm_l"
        assert result[2].parent_name == "arm_l_1"

    def test_n3_leg_parent_chain_is_sequential(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=3, name="leg_l", parent_name="root")
        assert result[0].parent_name == "root"
        assert result[1].parent_name == "leg_l"
        assert result[2].parent_name == "leg_l_1"

    def test_parent_name_none_passes_through_to_first_bone(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2, name="arm_l", parent_name=None)
        assert result[0].parent_name is None

    def test_n4_parent_chain_complete(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=4, name="arm_l", parent_name="spine")
        assert result[0].parent_name == "spine"
        assert result[1].parent_name == "arm_l"
        assert result[2].parent_name == "arm_l_1"
        assert result[3].parent_name == "arm_l_2"


# ---------------------------------------------------------------------------
# LJEC-1-AC6: Position interpolation
# ---------------------------------------------------------------------------

class TestLimbChainInterpolation:
    """LJEC-1-AC6: positions interpolate linearly between head and tail."""

    def _lerp(self, a, b, t):
        """Reference lerp using known-good float arithmetic on tuple components."""
        ax, ay, az = a._t
        bx, by, bz = b._t
        return Vector(((ax + (bx - ax) * t), (ay + (by - ay) * t), (az + (bz - az) * t)))

    def test_n1_head_equals_chain_head(self):
        head = _v(0, 0, 0)
        tail = _v(0, 1, 0)
        result = _make_arm_chain(head, tail, n=1)
        assert result[0].head == head

    def test_n1_tail_equals_chain_tail(self):
        head = _v(0, 0, 0)
        tail = _v(0, 1, 0)
        result = _make_arm_chain(head, tail, n=1)
        assert result[0].tail == tail

    def test_n2_segment0_head_equals_chain_head(self):
        head = _v(0, 0, 0)
        tail = _v(0, 2, 0)
        result = _make_arm_chain(head, tail, n=2)
        assert result[0].head == head

    def test_n2_segment0_tail_is_midpoint(self):
        head = _v(0, 0, 0)
        tail = _v(0, 2, 0)
        result = _make_arm_chain(head, tail, n=2)
        expected_mid = _v(0, 1, 0)
        assert result[0].tail == expected_mid

    def test_n2_segment1_head_equals_segment0_tail(self):
        head = _v(0, 0, 0)
        tail = _v(0, 2, 0)
        result = _make_arm_chain(head, tail, n=2)
        assert result[1].head == result[0].tail

    def test_n2_segment1_tail_equals_chain_tail(self):
        head = _v(0, 0, 0)
        tail = _v(0, 2, 0)
        result = _make_arm_chain(head, tail, n=2)
        assert result[1].tail == tail

    def test_n3_contiguous_segments(self):
        head = _v(0, 0, 0)
        tail = _v(0, 3, 0)
        result = _make_arm_chain(head, tail, n=3)
        # Each segment tail == next segment head
        assert result[0].tail == result[1].head
        assert result[1].tail == result[2].head

    def test_n3_first_segment_head_is_chain_head(self):
        head = _v(0, 0, 0)
        tail = _v(0, 3, 0)
        result = _make_arm_chain(head, tail, n=3)
        assert result[0].head == head

    def test_n3_last_segment_tail_is_chain_tail(self):
        head = _v(0, 0, 0)
        tail = _v(0, 3, 0)
        result = _make_arm_chain(head, tail, n=3)
        assert result[2].tail == tail

    def test_n2_non_axis_aligned_interpolation(self):
        """Interpolation works for non-axis-aligned vectors."""
        head = _v(1.0, 2.0, 3.0)
        tail = _v(4.0, 8.0, 6.0)
        result = _make_arm_chain(head, tail, n=2)
        # Segment 0: head=(1,2,3) tail=(2.5, 5, 4.5)
        # Segment 1: head=(2.5, 5, 4.5) tail=(4, 8, 6)
        assert result[0].head == _v(1.0, 2.0, 3.0)
        assert result[0].tail == _v(2.5, 5.0, 4.5)
        assert result[1].head == _v(2.5, 5.0, 4.5)
        assert result[1].tail == _v(4.0, 8.0, 6.0)

    def test_n4_all_segments_contiguous(self):
        head = _v(0, 0, 0)
        tail = _v(0, 0, 4)
        result = _make_arm_chain(head, tail, n=4)
        for i in range(3):
            assert result[i].tail == result[i + 1].head, (
                f"segment {i}.tail != segment {i+1}.head"
            )
        assert result[0].head == head
        assert result[3].tail == tail


# ---------------------------------------------------------------------------
# LJEC-1-AC9: n=1 identity
# ---------------------------------------------------------------------------

class TestLimbChainN1Identity:
    """LJEC-1-AC9: n=1 produces single-bone output semantically equal to legacy."""

    def test_n1_single_element_list(self):
        head = _v(0, 0.2, 0.6)
        tail = _v(0, 0.5, 0.3)
        result = _make_arm_chain(head, tail, n=1, name="arm_l", parent_name="spine")
        assert len(result) == 1

    def test_n1_matches_expected_bonespec(self):
        head = _v(0, 0.2, 0.6)
        tail = _v(0, 0.5, 0.3)
        result = _make_arm_chain(head, tail, n=1, name="arm_l", parent_name="spine")
        bone = result[0]
        assert bone.name == "arm_l"
        assert bone.head == head
        assert bone.tail == tail
        assert bone.parent_name == "spine"

    def test_n1_leg_l_identity(self):
        head = _v(0, 0.1, 0.2)
        tail = _v(0, 0.1, 0.0)
        result = _make_arm_chain(head, tail, n=1, name="leg_l", parent_name="root")
        bone = result[0]
        assert bone.name == "leg_l"
        assert bone.head == head
        assert bone.tail == tail
        assert bone.parent_name == "root"


# ---------------------------------------------------------------------------
# LJEC-1-AC10: Return type
# ---------------------------------------------------------------------------

class TestLimbChainReturnType:
    """LJEC-1-AC10: returns a list, not a tuple or generator."""

    def test_returns_list(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=2)
        assert isinstance(result, list)

    def test_elements_are_bonespec(self):
        result = _make_arm_chain(_v(0, 0, 0), _v(0, 1, 0), n=3)
        for bone in result:
            assert isinstance(bone, BoneSpec)


# ---------------------------------------------------------------------------
# LJEC-2-AC1: Function signature
# ---------------------------------------------------------------------------

class TestLimbChainSignature:
    """LJEC-2-AC1: function signature is exactly as specified."""

    def test_callable_with_positional_args(self):
        """All parameters are positional-or-keyword per LJEC-2-AC1."""
        result = limb_chain(_v(0, 0, 0), _v(0, 1, 0), 2, "arm_l")
        assert len(result) == 2

    def test_callable_with_keyword_args(self):
        result = limb_chain(
            head=_v(0, 0, 0),
            tail=_v(0, 1, 0),
            n=2,
            name="arm_l",
            parent_name="spine",
        )
        assert len(result) == 2

    def test_parent_name_defaults_to_none(self):
        """parent_name has a default of None per LJEC-2-AC1."""
        result = limb_chain(_v(0, 0, 0), _v(0, 1, 0), 1, "arm_l")
        assert result[0].parent_name is None


# ---------------------------------------------------------------------------
# LJEC-2-AC2: ALLOWED_END_SHAPES constant
# ---------------------------------------------------------------------------

class TestAllowedEndShapes:
    """LJEC-2-AC2: module exports ALLOWED_END_SHAPES with correct tokens."""

    def test_allowed_end_shapes_is_tuple(self):
        assert isinstance(ALLOWED_END_SHAPES, tuple)

    def test_allowed_end_shapes_contains_none(self):
        assert "none" in ALLOWED_END_SHAPES

    def test_allowed_end_shapes_contains_sphere(self):
        assert "sphere" in ALLOWED_END_SHAPES

    def test_allowed_end_shapes_contains_box(self):
        assert "box" in ALLOWED_END_SHAPES

    def test_allowed_end_shapes_has_exactly_three_tokens(self):
        assert len(ALLOWED_END_SHAPES) == 3

    def test_allowed_end_shapes_tokens_are_lowercase_strings(self):
        for token in ALLOWED_END_SHAPES:
            assert isinstance(token, str)
            assert token == token.lower()


# ---------------------------------------------------------------------------
# LJEC-2-AC3: Module importable without bpy
# ---------------------------------------------------------------------------

class TestLimbChainImportability:
    """LJEC-2-AC3: limb_chain module is importable without real bpy."""

    def test_module_importable_without_bpy(self):
        """The module must already be imported (bpy is stubbed) — just verify."""
        import src.core.rig_models.limb_chain as lc
        assert hasattr(lc, "limb_chain")
        assert hasattr(lc, "ALLOWED_END_SHAPES")
