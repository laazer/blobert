"""Blob / slime body-family motion."""

from __future__ import annotations

import math

try:
    from animations.keyframe_system import set_bone_keyframe
except ImportError:
    from src.animations.keyframe_system import set_bone_keyframe
from .bones import BoneNames
from .motion_base import BaseBodyType


class BlobBodyType(BaseBodyType):
    """Blob body type - squashing, stretching, pulsing creatures"""

    def create_idle_animation(self, length: int):
        for frame in range(0, length + 1, 5):
            scale_factor = 1.0 + 0.3 * math.sin(frame * 0.2)
            set_bone_keyframe(self.armature, BoneNames.BODY, frame, scale=(1, 1, scale_factor))
            head_z = 0.5 * math.sin(frame * 0.15)
            set_bone_keyframe(self.armature, BoneNames.HEAD, frame, location=(0, 0, head_z))

    def create_move_animation(self, length: int):
        for frame in range(0, length + 1, 2):
            progress = frame / length
            x_pos = 2.0 * math.sin(progress * math.pi * 2)
            stretch_y = 1.0 + 1.0 * math.sin(progress * math.pi * 4)
            squash_z = 1.0 - 0.5 * math.sin(progress * math.pi * 4)
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_pos, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.BODY, frame, scale=(1, stretch_y, squash_z))

    def create_attack_animation(self, length: int):
        windup_end = length // 3
        strike_end = (length * 2) // 3
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, windup_end, scale=(2.0, 2.0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.BODY, strike_end, scale=(4.0, 4.0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, windup_end, location=(2.0, 0, -0.5))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))

    def create_damage_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 5, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, 3, scale=(0.3, 0.3, 2.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1, 1, 1))

    def create_death_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, length // 2, scale=(1.5, 1.5, 0.2))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(2.0, 2.0, 0.05))
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length // 3, scale=(0.5, 0.5, 0.5))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, scale=(0.01, 0.01, 0.01))

    def create_spawn_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, -1.0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length // 2, location=(0, 0, 0.2))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(2.0, 2.0, 0.1))
        set_bone_keyframe(self.armature, BoneNames.BODY, length // 3, scale=(1.5, 1.5, 0.5))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1.0, 1.0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, scale=(0.01, 0.01, 0.01))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length // 2, scale=(0.01, 0.01, 0.01))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, scale=(1.0, 1.0, 1.0))

    def create_special_attack_animation(self, length: int):
        windup_end = length // 4
        expansion_peak = length // 2
        slam_end = (length * 3) // 4
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.BODY, windup_end, scale=(0.5, 0.5, 2.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, expansion_peak, scale=(6.0, 6.0, 0.2))
        set_bone_keyframe(self.armature, BoneNames.BODY, slam_end, scale=(4.0, 4.0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1, 1, 1))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, windup_end, location=(0, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.ROOT, expansion_peak, location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
