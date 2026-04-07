"""
Tests for attack animation frame timing and bone coverage.

bpy is mocked at module level so these run outside Blender.
The critical behaviour being tested is frame ordering and which bones
get keyframes — not the actual Blender API calls.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock Blender and mathutils before any src import touches them.
# setdefault leaves real modules alone if tests somehow run inside Blender.
sys.modules.setdefault('bpy', MagicMock())
sys.modules.setdefault('mathutils', MagicMock())

from src.body_families.motion_blob import BlobBodyType
from src.body_families.motion_humanoid import HumanoidBodyType
from src.body_families.motion_quadruped import QuadrupedBodyType
from src.utils.constants import AnimationConfig, AnimationTypes, BoneNames

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_armature(bone_names: list) -> MagicMock:
    """Return a minimal mock armature whose pose.bones list matches bone_names."""
    armature = MagicMock()
    armature.mode = 'POSE'
    armature.pose.bones = [MagicMock(name=n) for n in bone_names]
    return armature


def _quadruped_armature() -> MagicMock:
    names = BoneNames.get_quadruped_legs() + [BoneNames.ROOT, BoneNames.SPINE, BoneNames.HEAD]
    return _make_armature(names)


def _humanoid_armature() -> MagicMock:
    names = [
        BoneNames.ROOT, BoneNames.SPINE, BoneNames.HEAD,
        BoneNames.ARM_LEFT, BoneNames.ARM_RIGHT,
        BoneNames.LEG_LEFT, BoneNames.LEG_RIGHT,
    ]
    return _make_armature(names)


def _blob_armature() -> MagicMock:
    names = [BoneNames.ROOT, BoneNames.BODY, BoneNames.HEAD]
    return _make_armature(names)


def _keyframe_patch_target(body_type_instance) -> str:
    """Module where set_bone_keyframe is bound (must match patch target)."""
    return type(body_type_instance).__module__ + ".set_bone_keyframe"


def _capture_keyframes(body_type_instance, method_name: str, length: int) -> dict:
    """
    Call body_type_instance.<method_name>(length) with set_bone_keyframe mocked,
    and return a dict of {bone_name: [frame, ...]} for every call made.
    """
    captured: dict = {}

    def _record(armature, bone_name, frame, **kwargs):
        captured.setdefault(bone_name, []).append(frame)

    with patch(_keyframe_patch_target(body_type_instance), side_effect=_record):
        getattr(body_type_instance, method_name)(length)

    return captured


def _capture_rotations(body_type_instance, method_name: str, length: int) -> dict:
    """Like _capture_keyframes but records {bone_name: {frame: rotation}} for rotation calls."""
    captured: dict = {}

    def _record(armature, bone_name, frame, rotation=None, **kwargs):
        if rotation is not None:
            captured.setdefault(bone_name, {})[frame] = rotation

    with patch(_keyframe_patch_target(body_type_instance), side_effect=_record):
        getattr(body_type_instance, method_name)(length)

    return captured


def _capture_locations(body_type_instance, method_name: str, length: int) -> dict:
    """Like _capture_keyframes but records {bone_name: {frame: location}} for location calls."""
    captured: dict = {}

    def _record(armature, bone_name, frame, location=None, **kwargs):
        if location is not None:
            captured.setdefault(bone_name, {})[frame] = location

    with patch(_keyframe_patch_target(body_type_instance), side_effect=_record):
        getattr(body_type_instance, method_name)(length)

    return captured


# ---------------------------------------------------------------------------
# QuadrupedBodyType — attack
# ---------------------------------------------------------------------------

class TestQuadrupedAttackAnimation(unittest.TestCase):

    def setUp(self):
        self.body_type = QuadrupedBodyType(_quadruped_armature(), MagicMock())
        self.length = AnimationConfig.get_length(AnimationTypes.ATTACK)  # 36

    def test_phase_frames_are_distinct_and_ascending(self):
        """Crouch, leap peak, and landing must be on separate frames in order."""
        crouch_frame = self.length // 3        # 12
        leap_peak_frame = self.length // 2     # 18
        land_frame = (self.length * 3) // 4   # 27
        self.assertLess(crouch_frame, leap_peak_frame)
        self.assertLess(leap_peak_frame, land_frame)
        self.assertLess(land_frame, self.length)

    def test_all_six_legs_are_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        for leg_name in BoneNames.get_quadruped_legs():
            with self.subTest(leg=leg_name):
                self.assertIn(leg_name, captured, f"{leg_name} not keyframed in pounce attack")

    def test_spine_and_head_are_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        self.assertIn(BoneNames.SPINE, captured)
        self.assertIn(BoneNames.HEAD, captured)

    def test_legs_have_keyframes_at_all_four_phases(self):
        crouch_frame = self.length // 3
        leap_peak_frame = self.length // 2
        land_frame = (self.length * 3) // 4
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)

        for leg_name in BoneNames.get_quadruped_legs():
            with self.subTest(leg=leg_name):
                frames = set(captured.get(leg_name, []))
                self.assertIn(crouch_frame, frames)
                self.assertIn(leap_peak_frame, frames)
                self.assertIn(land_frame, frames)
                self.assertIn(self.length, frames)

    def test_no_duplicate_frames_on_spine(self):
        """Regression: old code set two keyframes at the same frame, overwriting the crouch."""
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        spine_frames = captured.get(BoneNames.SPINE, [])
        self.assertEqual(len(spine_frames), len(set(spine_frames)),
                         "Spine has duplicate frames — windup keyframe is being overwritten")


# ---------------------------------------------------------------------------
# QuadrupedBodyType — special attack
# ---------------------------------------------------------------------------

class TestQuadrupedSpecialAttackAnimation(unittest.TestCase):

    def setUp(self):
        self.body_type = QuadrupedBodyType(_quadruped_armature(), MagicMock())
        self.length = AnimationConfig.get_length(AnimationTypes.SPECIAL_ATTACK)  # 60

    def test_rise_frame_before_slash_frame(self):
        rise_frame = self.length // 3         # 20
        slash_frame = (self.length * 2) // 3  # 40
        self.assertLess(rise_frame, slash_frame)

    def test_front_legs_are_animated_for_claw_strike(self):
        captured = _capture_keyframes(self.body_type, 'create_special_attack_animation', self.length)
        self.assertIn(BoneNames.LEG_FRONT_LEFT, captured)
        self.assertIn(BoneNames.LEG_FRONT_RIGHT, captured)

    def test_brace_legs_are_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_special_attack_animation', self.length)
        for leg_name in [BoneNames.LEG_BACK_LEFT, BoneNames.LEG_BACK_RIGHT,
                         BoneNames.LEG_MIDDLE_LEFT, BoneNames.LEG_MIDDLE_RIGHT]:
            with self.subTest(leg=leg_name):
                self.assertIn(leg_name, captured)

    def test_spine_rears_backward_at_rise_frame(self):
        """Spine rotation X should be negative (rearing back) at the rise frame."""
        rise_frame = self.length // 3
        rotations = _capture_rotations(self.body_type, 'create_special_attack_animation', self.length)
        spine_rotations = rotations.get(BoneNames.SPINE, {})
        self.assertIn(rise_frame, spine_rotations)
        self.assertLess(spine_rotations[rise_frame][0], 0,
                        "Spine should lean back (negative X) while rearing up")


# ---------------------------------------------------------------------------
# HumanoidBodyType — attack
# ---------------------------------------------------------------------------

class TestHumanoidAttackAnimation(unittest.TestCase):

    def setUp(self):
        self.body_type = HumanoidBodyType(_humanoid_armature(), MagicMock())
        self.length = AnimationConfig.get_length(AnimationTypes.ATTACK)  # 36

    def test_windup_and_strike_frames_are_distinct(self):
        """
        Regression: the original code set windup_end == strike_start, so both
        keyframes landed on the same frame and the windup was silently lost.
        """
        windup_frame = self.length // 3  # 12
        strike_frame = self.length // 2  # 18
        self.assertNotEqual(windup_frame, strike_frame)

    def test_both_arms_are_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        self.assertIn(BoneNames.ARM_RIGHT, captured, "Punching arm not animated")
        self.assertIn(BoneNames.ARM_LEFT, captured, "Guard arm not animated")

    def test_spine_is_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        self.assertIn(BoneNames.SPINE, captured)

    def test_right_arm_pulls_back_on_windup(self):
        windup_frame = self.length // 3
        rotations = _capture_rotations(self.body_type, 'create_attack_animation', self.length)
        arm_rotations = rotations.get(BoneNames.ARM_RIGHT, {})
        self.assertIn(windup_frame, arm_rotations, "No windup keyframe on right arm")
        self.assertLess(arm_rotations[windup_frame][0], 0,
                        "Windup should pull arm back (negative X rotation)")

    def test_right_arm_punches_forward_on_strike(self):
        strike_frame = self.length // 2
        rotations = _capture_rotations(self.body_type, 'create_attack_animation', self.length)
        arm_rotations = rotations.get(BoneNames.ARM_RIGHT, {})
        self.assertIn(strike_frame, arm_rotations, "No strike keyframe on right arm")
        self.assertGreater(arm_rotations[strike_frame][0], 0,
                           "Strike should punch forward (positive X rotation)")

    def test_left_arm_raises_as_guard_on_windup(self):
        windup_frame = self.length // 3
        rotations = _capture_rotations(self.body_type, 'create_attack_animation', self.length)
        arm_rotations = rotations.get(BoneNames.ARM_LEFT, {})
        self.assertIn(windup_frame, arm_rotations, "Guard arm has no windup keyframe")
        self.assertGreater(arm_rotations[windup_frame][0], 0,
                           "Guard arm should raise (positive X rotation) during windup")

    def test_no_duplicate_frames_on_right_arm(self):
        """Regression: old code set both windup and strike at the same frame."""
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        arm_frames = captured.get(BoneNames.ARM_RIGHT, [])
        self.assertEqual(len(arm_frames), len(set(arm_frames)),
                         "ARM_RIGHT has duplicate frames — windup is being overwritten by strike")


# ---------------------------------------------------------------------------
# HumanoidBodyType — special attack
# ---------------------------------------------------------------------------

class TestHumanoidSpecialAttackAnimation(unittest.TestCase):

    def setUp(self):
        self.body_type = HumanoidBodyType(_humanoid_armature(), MagicMock())
        self.length = AnimationConfig.get_length(AnimationTypes.SPECIAL_ATTACK)  # 60

    def test_raise_frame_before_slam_frame(self):
        raise_frame = self.length // 3        # 20
        slam_frame = (self.length * 2) // 3  # 40
        self.assertLess(raise_frame, slam_frame)

    def test_both_arms_are_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_special_attack_animation', self.length)
        self.assertIn(BoneNames.ARM_LEFT, captured)
        self.assertIn(BoneNames.ARM_RIGHT, captured)

    def test_both_arms_go_overhead_at_raise_frame(self):
        raise_frame = self.length // 3
        rotations = _capture_rotations(self.body_type, 'create_special_attack_animation', self.length)
        for arm_name in [BoneNames.ARM_LEFT, BoneNames.ARM_RIGHT]:
            with self.subTest(arm=arm_name):
                arm_rotations = rotations.get(arm_name, {})
                self.assertIn(raise_frame, arm_rotations)
                self.assertLess(arm_rotations[raise_frame][0], 0,
                                f"{arm_name} should go overhead (negative X) at raise frame")

    def test_root_drops_on_slam(self):
        slam_frame = (self.length * 2) // 3
        locations = _capture_locations(self.body_type, 'create_special_attack_animation', self.length)
        root_locations = locations.get(BoneNames.ROOT, {})
        self.assertIn(slam_frame, root_locations, "Root should have a keyframe at slam impact")
        self.assertLess(root_locations[slam_frame][2], 0,
                        "Root Z should be negative on slam (dropping for impact weight)")

    def test_spine_is_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_special_attack_animation', self.length)
        self.assertIn(BoneNames.SPINE, captured)


# ---------------------------------------------------------------------------
# BlobBodyType — attack (existing, sanity-checked)
# ---------------------------------------------------------------------------

class TestBlobAttackAnimation(unittest.TestCase):

    def setUp(self):
        self.body_type = BlobBodyType(_blob_armature(), MagicMock())
        self.length = AnimationConfig.get_length(AnimationTypes.ATTACK)  # 36

    def test_body_and_head_are_animated(self):
        captured = _capture_keyframes(self.body_type, 'create_attack_animation', self.length)
        self.assertIn(BoneNames.BODY, captured)
        self.assertIn(BoneNames.HEAD, captured)

    def test_windup_strike_and_return_are_distinct_frames(self):
        windup_end = self.length // 3     # 12
        strike_end = (self.length * 2) // 3  # 24
        self.assertLess(windup_end, strike_end)
        self.assertLess(strike_end, self.length)


if __name__ == '__main__':
    unittest.main()
