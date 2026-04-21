"""Abstract base for procedural body-family motion (enemy keyframe animation)."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

try:
    from animations.keyframe_system import set_bone_keyframe
except ImportError:
    from src.animations.keyframe_system import set_bone_keyframe
try:
    from utils.config import AnimationConfig, AnimationTypes
except ImportError:
    from src.utils.config import AnimationConfig, AnimationTypes

from .bones import BoneNames


class BaseBodyType(ABC):
    """Base class for body types that know how to animate themselves."""

    def __init__(self, armature, rng):
        self.armature = armature
        self.rng = rng

    def create_all_animations(self):
        animations = AnimationTypes.get_all()
        for anim_name in animations:
            length = AnimationConfig.get_length(anim_name)
            if anim_name == AnimationTypes.IDLE:
                self.create_idle_animation(length)
            elif anim_name == AnimationTypes.MOVE:
                self.create_move_animation(length)
            elif anim_name == AnimationTypes.ATTACK:
                self.create_attack_animation(length)
            elif anim_name == AnimationTypes.DAMAGE:
                self.create_damage_animation(length)
            elif anim_name == AnimationTypes.DEATH:
                self.create_death_animation(length)

    @abstractmethod
    def create_idle_animation(self, length: int):
        pass

    @abstractmethod
    def create_move_animation(self, length: int):
        pass

    @abstractmethod
    def create_attack_animation(self, length: int):
        pass

    @abstractmethod
    def create_damage_animation(self, length: int):
        pass

    @abstractmethod
    def create_death_animation(self, length: int):
        pass

    def create_spawn_animation(self, length: int):
        for frame in [0, length // 3, length]:
            if frame == 0:
                scale = (0.01, 0.01, 0.01)
            elif frame == length // 3:
                scale = (1.2, 1.2, 1.2)
            else:
                scale = (1.0, 1.0, 1.0)
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, scale=scale)
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, -0.5))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length // 2, location=(0, 0, 0.2))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))

    def create_special_attack_animation(self, length: int):
        windup_end = length // 3
        strike_start = windup_end
        _strike_end = (length * 2) // 3
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, windup_end, rotation=(-0.8, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.SPINE, strike_start, rotation=(1.0, 0, -0.3))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))

    def create_damage_heavy_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 8, location=(-2.0, 0, 0.5))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, 6, rotation=(-1.2, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))

    def create_damage_fire_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, 4, location=(-0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(0, 0, 0))
        for frame in range(4, length, 3):
            shake_x = 0.1 * self.rng.uniform(-1, 1)
            shake_z = 0.1 * self.rng.uniform(-1, 1)
            set_bone_keyframe(self.armature, BoneNames.BODY, frame, location=(shake_x, 0, shake_z))

    def create_damage_ice_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.ROOT, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length // 3, location=(-1.0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.ROOT, length, location=(-0.8, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1.0, 1.0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, length // 2, scale=(0.9, 0.9, 1.1))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(0.85, 0.85, 1.15))

    def create_stunned_animation(self, length: int):
        for frame in range(0, length + 1, 6):
            sway_amount = 0.4 * math.sin(frame * 0.2)
            wobble_z = 0.2 * math.sin(frame * 0.15)
            set_bone_keyframe(self.armature, BoneNames.SPINE, frame, rotation=(sway_amount, 0, wobble_z))
        for frame in range(0, length + 1, 8):
            head_rotation = 0.3 * math.sin(frame * 0.1)
            set_bone_keyframe(self.armature, BoneNames.HEAD, frame, rotation=(0, 0, head_rotation))

    def create_celebrate_animation(self, length: int):
        for frame in range(0, length + 1, 6):
            bounce_height = 0.3 * abs(math.sin(frame * 0.3))
            set_bone_keyframe(self.armature, BoneNames.ROOT, frame, location=(0, 0, bounce_height))
        set_bone_keyframe(self.armature, BoneNames.BODY, 0, scale=(1.0, 1.0, 1.0))
        set_bone_keyframe(self.armature, BoneNames.BODY, length // 2, scale=(1.1, 1.1, 0.9))
        set_bone_keyframe(self.armature, BoneNames.BODY, length, scale=(1.0, 1.0, 1.0))

    def create_taunt_animation(self, length: int):
        set_bone_keyframe(self.armature, BoneNames.SPINE, 0, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length // 3, rotation=(0.5, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.SPINE, length, rotation=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, 0, location=(0, 0, 0))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length // 2, location=(0.2, 0, 0.1))
        set_bone_keyframe(self.armature, BoneNames.HEAD, length, location=(0, 0, 0))
