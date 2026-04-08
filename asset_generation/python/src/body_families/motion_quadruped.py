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

    def _pose_bone_names(self) -> set[str]:
        return {bone.name for bone in self.armature.pose.bones}

    def _is_spider_rig(self) -> bool:
        names = self._pose_bone_names()
        return all(name in names for name in BoneNames.get_spider_leg_roots())

    def _create_spider_move_animation(self, length: int):
        group_a = BoneNames.get_spider_group_a_roots()
        group_b = BoneNames.get_spider_group_b_roots()
        for frame in range(0, length + 1, 2):
            progress = frame / max(1, length)
            cycle = progress * 2.0
            phase_local = cycle % 1.0
            active = group_a if cycle < 1.0 else group_b
            planted = group_b if cycle < 1.0 else group_a

            x_movement = 1.0 * progress
            body_bob = 0.10 * math.sin(progress * math.pi * 4.0)
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(x_movement, 0, body_bob * 0.4))
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, location=(0, 0, body_bob))

            for idx, root in enumerate(active):
                lift = 0.35 * math.sin(phase_local * math.pi)
                swing = 0.55 * math.sin(phase_local * math.pi)
                delay = idx * 0.06
                # Coxa
                set_bone_keyframe(self.armature, root, frame, rotation=(0.30 * swing, 0.0, 0.08 * lift))
                # Femur (delayed spring)
                set_bone_keyframe(
                    self.armature,
                    f"{root}_1",
                    frame,
                    rotation=(0.22 * math.sin((phase_local + delay) * math.pi), 0.0, -0.06 * lift),
                )
                # Tibia (more delayed spring)
                set_bone_keyframe(
                    self.armature,
                    f"{root}_2",
                    frame,
                    rotation=(0.16 * math.sin((phase_local + delay * 1.6) * math.pi), 0.0, 0.03 * lift),
                )

            for idx, root in enumerate(planted):
                settle = 0.08 * math.sin((phase_local + idx * 0.03) * math.pi)
                set_bone_keyframe(self.armature, root, frame, rotation=(-0.05 + settle, 0.0, 0.0))
                set_bone_keyframe(self.armature, f"{root}_1", frame, rotation=(0.03 + settle * 0.5, 0.0, 0.0))
                set_bone_keyframe(self.armature, f"{root}_2", frame, rotation=(-0.03, 0.0, 0.0))

    def _create_spider_idle_animation(self, length: int):
        for frame in range(0, length + 1, 6):
            breathe = 0.06 * math.sin(frame * 0.12)
            sway = 0.05 * math.sin(frame * 0.10)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, rotation=(sway, 0, 0), location=(0, 0, breathe))
            for i, root in enumerate(BoneNames.get_spider_leg_roots()):
                jitter = 0.03 * math.sin(frame * 0.14 + i * 0.35)
                set_bone_keyframe(self.armature, root, frame, rotation=(jitter, 0, 0))

    def _create_spider_attack_animation(self, length: int):
        windup = length // 3
        strike = (length * 2) // 3
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, windup, rotation=(-0.25, 0, 0), location=(0, 0, -0.05))
        set_bone_keyframe(self.armature, BoneNames.SPINE, strike, rotation=(0.35, 0, 0), location=(0, 0, 0.08))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))
        for root in BoneNames.get_spider_group_a_roots():
            set_bone_keyframe(self.armature, root, windup, rotation=(-0.18, 0, 0))
            set_bone_keyframe(self.armature, root, strike, rotation=(0.26, 0, 0))
            set_bone_keyframe(self.armature, root, length, rotation=(0, 0, 0))

    def _create_spider_special_attack_animation(self, length: int):
        rise = length // 3
        slam = (length * 2) // 3
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0), location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, rise, rotation=(-0.30, 0, 0), location=(0, 0, 0.10))
        set_bone_keyframe(self.armature, BoneNames.SPINE, slam, rotation=(0.30, 0, 0), location=(0, 0, -0.02))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0), location=(0, 0, 0))

    def _create_spider_damage_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, max(2, length // 4), location=(-0.25, 0, 0.03))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, max(2, length // 5), rotation=(-0.20, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))

    def _create_spider_death_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length // 2, rotation=(-0.35, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(-0.55, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, -0.15))

    def create_idle_animation(self, length: int):
        if self._is_spider_rig():
            self._create_spider_idle_animation(length)
            return
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
        if self._is_spider_rig():
            self._create_spider_move_animation(length)
            return
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
        if self._is_spider_rig():
            self._create_spider_attack_animation(length)
            return
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
        if self._is_spider_rig():
            self._create_spider_special_attack_animation(length)
            return
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
        if self._is_spider_rig():
            self._create_spider_damage_animation(length)
            return
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 5, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 3, rotation=(-0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))

    def create_death_animation(self, length: int):
        if self._is_spider_rig():
            self._create_spider_death_animation(length)
            return
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length // 3, rotation=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, (length * 2) // 3, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(-1.6, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, -0.8))
