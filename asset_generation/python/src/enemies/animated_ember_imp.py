"""Animated ember imp enemy builder."""

import math

from mathutils import Euler

from .base_enemy import BaseEnemy
from ..animations.armature_builders import create_humanoid_armature
from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes


class AnimatedEmberImp(BaseEnemy):
    """Humanoid fire creature"""

    def create_body(self):
        """Create cylindrical body"""
        body_height = random_variance(1.2, 0.2, self.rng)
        body_width = random_variance(0.4, 0.1, self.rng)
        body = create_cylinder(
            location=(0, 0, body_height * 0.5),
            scale=(body_width, body_width, body_height), vertices=8
        )
        self.parts.append(body)

        # Store dimensions
        self.body_height = body_height
        self.body_width = body_width

    def create_head(self):
        """Create spherical head"""
        head_scale = self.body_width * 1.1
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * 0.7),
            scale=(head_scale, head_scale, head_scale)
        )
        self.parts.append(head)

    def create_limbs(self):
        """Create arms and legs"""
        # Arms
        arm_length = random_variance(0.8, 0.2, self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + arm_length * 0.5), 0, self.body_height * 0.7),
                scale=(0.12, 0.12, arm_length), vertices=6
            )
            arm.rotation_euler = Euler((0, 0, math.pi/2))
            self.parts.append(arm)

            hand = create_sphere(
                location=(side * (self.body_width + arm_length), 0, self.body_height * 0.7),
                scale=(0.15, 0.15, 0.15)
            )
            self.parts.append(hand)

        # Legs
        leg_length = random_variance(0.7, 0.1, self.rng)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.3, 0, leg_length * 0.5),
                scale=(0.12, 0.12, leg_length), vertices=6
            )
            self.parts.append(leg)

    def apply_materials(self):
        """Apply fire-themed materials"""
        enemy_mats = get_enemy_materials('ember_imp', self.materials, self.rng)

        # Apply materials to individual parts for variation
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body - fire orange
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head - ember red

        # Apply materials to limbs
        limb_material = enemy_mats['limbs']    # Arms/legs - bone white
        hand_material = enemy_mats['extra']    # Hands - random theme color

        part_index = 2  # Start after body and head
        # Arms
        for i in range(2):  # 2 arms
            apply_material_to_object(self.parts[part_index], limb_material)     # Arm
            apply_material_to_object(self.parts[part_index + 1], hand_material) # Hand
            part_index += 2

        # Legs
        for i in range(2):  # 2 legs
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

    def create_armature(self):
        """Create humanoid armature for ember imp"""
        return create_humanoid_armature("ember_imp", self.body_height)

    def get_body_type(self):
        """Return body type for animation system"""
        return EnemyBodyTypes.HUMANOID
