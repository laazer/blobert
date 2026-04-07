"""Animated tar slug enemy builder."""

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models import BlobSimpleRig
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedSlug(BlobSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Elongated slug with blob movement"""

    body_height = 1.0

    def build_mesh_parts(self):
        length = random_variance(2.0, 0.3, self.rng)
        width = random_variance(0.8, 0.2, self.rng)
        height = random_variance(0.6, 0.1, self.rng)

        body = create_sphere(location=(0, 0, height * 0.5), scale=(length, width, height))
        self.parts.append(body)

        self.length = length
        self.width = width
        self.height = height

        head_scale = self.width * 0.4
        head = create_sphere(
            location=(self.length * 0.7, 0, self.height * 0.8),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)

        for side in [-1, 1]:
            stalk = create_cylinder(
                location=(self.length * 0.6, side * self.width * 0.3, self.height + 0.3),
                scale=(0.05, 0.05, 0.3),
                vertices=6,
            )
            self.parts.append(stalk)

            eye = create_sphere(
                location=(self.length * 0.6, side * self.width * 0.3, self.height + 0.6),
                scale=(0.1, 0.1, 0.1),
            )
            self.parts.append(eye)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("slug", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        stalk_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        for i, part in enumerate(self.parts[2:]):
            if i % 2 == 0:
                apply_material_to_object(part, stalk_material)
            else:
                apply_material_to_object(part, eye_material)

    def get_body_type(self):
        return EnemyBodyTypes.BLOB
