"""Animated acid spitter enemy builder."""

from .base_enemy import BaseEnemy
from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..animations.armature_builders import create_blob_armature
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes


class AnimatedAcidSpitter(BaseEnemy):
    """Squat acid sac with blob movement"""

    def create_body(self):
        """Create squat pulsing sac body"""
        body_scale = random_variance(1.0, 0.15, self.rng)
        height = random_variance(0.9, 0.1, self.rng)
        body = create_sphere(location=(0, 0, height * 0.5), scale=(body_scale, body_scale * random_variance(1.0, 0.15, self.rng), height))
        self.parts.append(body)
        self.body_scale = body_scale
        self.height = height

    def create_head(self):
        """Create small forward-facing head nub"""
        head_scale = self.body_scale * random_variance(0.35, 0.08, self.rng)
        head = create_sphere(location=(self.body_scale * 0.8, 0, self.height * 0.9), scale=(head_scale, head_scale, head_scale))
        self.parts.append(head)
        self.head_scale = head_scale

    def create_limbs(self):
        """Create two drip-tendrils below the body"""
        for side in [-1, 1]:
            tendril_length = random_variance(0.4, 0.1, self.rng)
            tendril = create_cylinder(
                location=(side * self.body_scale * 0.3, 0, 0),
                scale=(0.07, 0.07, tendril_length),
                vertices=6
            )
            self.parts.append(tendril)

    def apply_materials(self):
        """Apply acid-themed materials"""
        enemy_mats = get_enemy_materials('acid_spitter', self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats['body'])    # Body - acid yellow
        apply_material_to_object(self.parts[1], enemy_mats['head'])    # Head - toxic green
        for part in self.parts[2:]:  # Tendrils
            apply_material_to_object(part, enemy_mats['limbs'])

    def create_armature(self):
        """Create blob armature for acid spitter"""
        return create_blob_armature("acid_spitter", self.height)

    def get_body_type(self):
        """Return body type for animation system"""
        return EnemyBodyTypes.BLOB
