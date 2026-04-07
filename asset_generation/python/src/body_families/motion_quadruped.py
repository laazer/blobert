"""Quadruped / multi-leg body-family motion."""

from __future__ import annotations

import math

try:
    from animations.keyframe_system import set_bone_keyframe
except ImportError:
    from src.animations.keyframe_system import set_bone_keyframe
from .bones import BoneNames
from .motion_base import BaseBodyType


class QuadrupedBodyType(BaseBodyType):
    """Quadruped body type - multi-legged creatures with tripod gait"""

    def create_idle_animation(self, length: int):
        for frame in range(0, length + 1, 8):
            body_sway = 0.3 * math.sin(frame * 0.1)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, rotation=(body_sway, 0, 0))
            if frame % 20 == 1:
                leg_names = BoneNames.get_quadruped_legs()
                for i, leg_name in enumerate(leg_names):
                    if leg_name in [bone.name for bone in self.armature.pose.bones]:
                        twitch = 0.3 * math.sin((frame + i * 10) * 0.3)
                        set_bone_keyframe(self.armature, leg_name, frame, rotation=(twitch, 0, 0))

    def create_move_animation(self, length: int):
        for frame in range(0, length + 1, 2):
            progress = frame / length
            x_movement = 1.5 * progress
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_movement, 0, 0))
            body_y = 0.3 * math.sin(progress * math.pi * 6)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, location=(0, 0, body_y))
            leg_cycle_1 = 0.8 * math.sin(progress * math.pi * 4)
            leg_cycle_2 = 0.8 * math.sin(progress * math.pi * 4 + math.pi)
            set_bone_keyframe(self.armature, BoneNames.LEG_FRONT_LEFT, frame, rotation=(leg_cycle_1, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_BACK_RIGHT, frame, rotation=(leg_cycle_1, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_FRONT_RIGHT, frame, rotation=(leg_cycle_2, 0, 0))
            set_bone_keyframe(self.armature, BoneNames.LEG_BACK_LEFT, frame, rotation=(leg_cycle_2, 0, 0))
            if BoneNames.LEG_MIDDLE_LEFT in [bone.name for bone in self.armature.pose.bones]:
                leg_cycle_mid = 0.6 * math.sin(progress * math.pi * 4 + math.pi / 2)
                set_bone_keyframe(self.armature, BoneNames.LEG_MIDDLE_LEFT, frame, rotation=(leg_cycle_mid, 0, 0))
                set_bone_keyframe(self.armature, BoneNames.LEG_MIDDLE_RIGHT, frame, rotation=(leg_cycle_mid, 0, 0))

    def create_attack_animation(self, length: int):
        crouch_frame = length // 3
        leap_peak_frame = length // 2
        land_frame = (length * 3) // 4
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, crouch_frame, rotation=(-0.8, 0, 0), location=(0, 0, -0.3)
        )
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, leap_peak_frame, rotation=(1.2, 0, 0), location=(0, 0, 0.5)
        )
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, land_frame, rotation=(0.3, 0, 0), location=(0, 0, 0.1)
        )
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, crouch_frame, location=(0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.HEAD, leap_peak_frame, location=(0, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))
        for leg_name in BoneNames.get_quadruped_legs():
            set_bone_keyframe(self.armature, leg_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, crouch_frame, rotation=(-0.5, 0, 0))
            set_bone_keyframe(self.armature, leg_name, leap_peak_frame, rotation=(0.8, 0, 0))
            set_bone_keyframe(self.armature, leg_name, land_frame, rotation=(-0.3, 0, 0))
            set_bone_keyframe(self.armature, leg_name, length, rotation=(0, 0, 0))

    def create_special_attack_animation(self, length: int):
        rise_frame = length // 3
        slash_frame = (length * 2) // 3
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, rise_frame, rotation=(-1.5, 0, 0), location=(0, 0, 0.8)
        )
        set_bone_keyframe(
            self.armature, BoneNames.SPINE, slash_frame, rotation=(1.0, 0, 0), location=(0, 0, 0.3)
        )
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, rise_frame, location=(0, 0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, slash_frame, location=(0, 0, 0.3))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))
        for leg_name in [BoneNames.LEG_FRONT_LEFT, BoneNames.LEG_FRONT_RIGHT]:
            set_bone_keyframe(self.armature, leg_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, rise_frame, rotation=(-1.2, 0, 0))
            set_bone_keyframe(self.armature, leg_name, slash_frame, rotation=(1.0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, length, rotation=(0, 0, 0))
        for leg_name in [
            BoneNames.LEG_BACK_LEFT,
            BoneNames.LEG_BACK_RIGHT,
            BoneNames.LEG_MIDDLE_LEFT,
            BoneNames.LEG_MIDDLE_RIGHT,
        ]:
            set_bone_keyframe(self.armature, leg_name, 0, rotation=(0, 0, 0))
            set_bone_keyframe(self.armature, leg_name, rise_frame, rotation=(0.6, 0, 0))
            set_bone_keyframe(self.armature, leg_name, length, rotation=(0, 0, 0))

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
