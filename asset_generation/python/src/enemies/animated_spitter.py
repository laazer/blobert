"""Animated acid spitter enemy builder."""

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models import BlobSimpleRig
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from ..utils.procedural_constants import (
    CYLINDER_VERTICES_HEX,
    MESH_BODY_CENTER_Z_FACTOR,
)
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedSpitter(BlobSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Squat acid sac with blob movement"""

    body_height = 1.0

    def build_mesh_parts(self):
        body_scale = random_variance(1.0, 0.15, self.rng)
        height = random_variance(0.9, 0.1, self.rng)
        body = create_sphere(
            location=(0, 0, height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(body_scale, body_scale * random_variance(1.0, 0.15, self.rng), height),
        )
        self.parts.append(body)
        self.body_scale = body_scale
        self.height = height

        head_scale = self.body_scale * random_variance(0.35, 0.08, self.rng)
        head = create_sphere(
            location=(self.body_scale * 0.8, 0, self.height * 0.9),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)
        self.head_scale = head_scale

        for side in [-1, 1]:
            tendril_length = random_variance(0.4, 0.1, self.rng)
            tendril = create_cylinder(
                location=(side * self.body_scale * 0.3, 0, 0),
                scale=(0.07, 0.07, tendril_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(tendril)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("spitter", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats["limbs"])

    def get_body_type(self):
        return EnemyBodyTypes.BLOB
