"""Animated adhesion bug enemy builder."""

from .base_enemy import BaseEnemy
from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..animations.armature_builders import create_quadruped_armature
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes


class AnimatedAdhesionBug(BaseEnemy):
    """Multi-segment bug with quadruped movement"""

    def create_body(self):
        """Create main body sphere"""
        body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(location=(0, 0, 0.3), scale=(body_scale, body_scale * 0.8, body_scale * 0.9))
        self.parts.append(body)
        self.body_scale = body_scale  # Store for other parts

    def create_head(self):
        """Create head sphere"""
        head_scale = self.body_scale * random_variance(0.6, 0.1, self.rng)
        head_offset = self.body_scale + head_scale * 0.5
        head = create_sphere(location=(head_offset, 0, 0.3), scale=(head_scale, head_scale, head_scale))
        self.parts.append(head)
        self.head_scale = head_scale

    def create_limbs(self):
        """Create 6 legs and eyes"""
        # Eyes (tiny spheres on head)
        eye_count = self.rng.choice([2, 4])
        eye_scale = self.head_scale * 0.15
        for i in range(eye_count):
            side = 1 if i % 2 == 0 else -1
            eye_x = self.body_scale + self.head_scale * 1.2
            eye_y = side * self.head_scale * 0.4
            eye_z = 0.4
            eye = create_sphere(location=(eye_x, eye_y, eye_z), scale=(eye_scale, eye_scale, eye_scale))
            self.parts.append(eye)

        # Legs (short cylinders) — 6 legs total
        leg_positions = [
            (self.body_scale * 0.3, self.body_scale * 0.3, 0),   # front left
            (self.body_scale * 0.3, -self.body_scale * 0.3, 0),  # front right
            (0, self.body_scale * 0.4, 0),                        # middle left
            (0, -self.body_scale * 0.4, 0),                       # middle right
            (-self.body_scale * 0.2, self.body_scale * 0.3, 0),  # back left
            (-self.body_scale * 0.2, -self.body_scale * 0.3, 0), # back right
        ]

        for i, (leg_x, leg_y, leg_z) in enumerate(leg_positions):
            leg_length = random_variance(0.3, 0.1, self.rng)
            leg = create_cylinder(
                location=(leg_x, leg_y, leg_z),
                scale=(0.08, 0.08, leg_length),
                vertices=6
            )
            self.parts.append(leg)

    def apply_materials(self):
        """Apply themed materials with specific body part assignments"""
        enemy_mats = get_enemy_materials('adhesion_bug', self.materials, self.rng)

        # Apply materials to individual parts for variation
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body - toxic green
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head - organic brown

        # Apply material to legs and eyes
        leg_material = enemy_mats['limbs']    # Legs - bone white
        eye_material = enemy_mats['extra']    # Eyes - random theme color

        for i, part in enumerate(self.parts[2:]):  # Skip body and head
            if i < 6:  # First 6 are legs
                apply_material_to_object(part, leg_material)
            else:  # Eyes get special material
                apply_material_to_object(part, eye_material)

    def create_armature(self):
        """Create quadruped armature for adhesion bug"""
        return create_quadruped_armature("adhesion_bug", self.body_scale)

    def get_body_type(self):
        """Return body type for animation system"""
        return EnemyBodyTypes.QUADRUPED
