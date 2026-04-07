"""Animated carapace husk enemy builder."""

import math

from mathutils import Euler

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models import HumanoidSimpleRig
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedCarapaceHusk(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Heavy wide humanoid with thick arms and short legs"""

    body_height = 1.0

    def build_mesh_parts(self):
        body_height = random_variance(1.0, 0.15, self.rng)
        body_width = random_variance(0.7, 0.1, self.rng)
        body = create_cylinder(
            location=(0, 0, body_height * 0.5),
            scale=(body_width, body_width, body_height),
            vertices=8,
        )
        self.parts.append(body)
        self.body_height = body_height
        self.body_width = body_width

        head_scale = self.body_width * random_variance(1.2, 0.1, self.rng)
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * 0.6),
            scale=(head_scale, head_scale, head_scale * 0.85),
        )
        self.parts.append(head)

        arm_length = random_variance(0.5, 0.1, self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + arm_length * 0.5), 0, self.body_height * 0.75),
                scale=(0.18, 0.18, arm_length),
                vertices=6,
            )
            arm.rotation_euler = Euler((0, 0, math.pi / 2))
            self.parts.append(arm)

        leg_length = random_variance(0.5, 0.1, self.rng)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.35, 0, leg_length * 0.5),
                scale=(0.18, 0.18, leg_length),
                vertices=6,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("carapace_husk", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        limb_material = enemy_mats["limbs"]
        for part in self.parts[2:]:
            apply_material_to_object(part, limb_material)

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID
