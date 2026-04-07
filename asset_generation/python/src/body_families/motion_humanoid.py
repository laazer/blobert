"""Humanoid body-family motion."""

from __future__ import annotations

import math

try:
    from animations.keyframe_system import set_bone_keyframe
except ImportError:
    from src.animations.keyframe_system import set_bone_keyframe
from .bones import BoneNames
from .motion_base import BaseBodyType


class HumanoidBodyType(BaseBodyType):
    """Humanoid body type - bipedal creatures with arms"""

    def create_idle_animation(self, length: int):
        for frame in range(0, length + 1, 6):
            chest_rise = 0.3 * math.sin(frame * 0.12)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, location=(0, 0, chest_rise))
            arm_sway = 0.3 * math.sin(frame * 0.1)
            set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, frame, rotation=(arm_sway, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, frame, rotation=(-arm_sway, 0, 0))

    def create_move_animation(self, length: int):
        for frame in range(0, length + 1, 2):
            progress = frame / length
            x_pos = 1.0 * progress
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_pos, 0, 0))
            leg_swing = 1.0 * math.sin(progress * math.pi * 4)
            set_bone_keyframe(self.armature, BoneNames.LEG_LEFT, frame, rotation=(leg_swing, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_RIGHT, frame, rotation=(-leg_swing, 0, 0))
            arm_swing = 0.6 * math.sin(progress * math.pi * 4 + math.pi)
            set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, frame, rotation=(arm_swing, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, frame, rotation=(-arm_swing, 0, 0))

    def create_attack_animation(self, length: int):
        windup_frame = length // 3
        strike_frame = length // 2
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, windup_frame, rotation=(0.2, 0, -0.4))
        set_bone_keyframe(self.armature, BoneNames.SPINE, strike_frame, rotation=(0.4, 0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, windup_frame, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, strike_frame, rotation=(1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, length, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, windup_frame, rotation=(0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, strike_frame, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, length, rotation=(0, 0, 0))

    def create_special_attack_animation(self, length: int):
        raise_frame = length // 3
        slam_frame = (length * 2) // 3
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, raise_frame, rotation=(-0.6, 0, 0), location=(0, 0, 0.2)
        )
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, slam_frame, rotation=(0.8, 0, 0), location=(0, 0, -0.2)
        )
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))
        for arm_name in [BoneNames.ARM_LEFT, BoneNames.ARM_RIGHT]:
            set_bone_keyframe(self.armature, arm_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, arm_name, raise_frame, rotation=(-1.8, 0, 0))
            set_bone_keyframe(self.armature, arm_name, slam_frame, rotation=(1.2, 0, 0))
            set_bone_keyframe(self.armature, arm_name, length, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, slam_frame, location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))

    def create_damage_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 5, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 3, rotation=(-0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))

    def create_death_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length // 3, rotation=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, (length * 2) // 3, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(-1.6, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, -0.8))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, length // 2, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, length // 2, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_LEFT, length, rotation=(1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ARM_RIGHT, length, rotation=(1.2, 0, 0))
