"""Animated claw crawler enemy builder."""

from .base_enemy import BaseEnemy
from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..animations.armature_builders import create_quadruped_armature
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes


class AnimatedClawCrawler(BaseEnemy):
    """Flat disc body with large front claws and quadruped movement"""

    def create_body(self):
        """Create flat disc body"""
        body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(
            location=(0, 0, 0.2),
            scale=(body_scale, body_scale * random_variance(0.9, 0.1, self.rng), body_scale * 0.35)
        )
        self.parts.append(body)
        self.body_scale = body_scale

    def create_head(self):
        """Create flat head disc at front of body"""
        head_scale = self.body_scale * random_variance(0.4, 0.1, self.rng)
        head = create_sphere(
            location=(self.body_scale * 1.1, 0, 0.25),
            scale=(head_scale, head_scale, head_scale * 0.7)
        )
        self.parts.append(head)
        self.head_scale = head_scale

    def create_limbs(self):
        """Create 2 large front claws and 4 regular legs"""
        # Front claws (wide short cylinders)
        for side in [-1, 1]:
            claw_length = random_variance(0.35, 0.08, self.rng)
            claw = create_cylinder(
                location=(self.body_scale * 0.6, side * self.body_scale * 0.5, 0.1),
                scale=(0.15, 0.15, claw_length),
                vertices=6
            )
            self.parts.append(claw)

        # Regular legs (4 total)
        leg_positions = [
            (0, self.body_scale * 0.5, 0),                          # middle left
            (0, -self.body_scale * 0.5, 0),                         # middle right
            (-self.body_scale * 0.4, self.body_scale * 0.4, 0),    # back left
            (-self.body_scale * 0.4, -self.body_scale * 0.4, 0),   # back right
        ]
        for leg_x, leg_y, leg_z in leg_positions:
            leg_length = random_variance(0.3, 0.08, self.rng)
            leg = create_cylinder(
                location=(leg_x, leg_y, leg_z),
                scale=(0.08, 0.08, leg_length),
                vertices=6
            )
            self.parts.append(leg)

    def apply_materials(self):
        """Apply stone/earth themed materials"""
        enemy_mats = get_enemy_materials('claw_crawler', self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body - stone gray
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head - dirt brown
        claw_material = enemy_mats['extra']    # Claws - bone white
        limb_material = enemy_mats['limbs']    # Legs - bone white
        part_index = 2
        # Claws
        for _ in range(2):
            apply_material_to_object(self.parts[part_index], claw_material)
            part_index += 1
        # Legs
        for _ in range(4):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

    def create_armature(self):
        """Create quadruped armature for claw crawler"""
        return create_quadruped_armature("claw_crawler", self.body_scale)

    def get_body_type(self):
        """Return body type for animation system"""
        return EnemyBodyTypes.QUADRUPED
