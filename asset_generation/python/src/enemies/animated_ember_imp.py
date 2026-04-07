"""Animated ember imp enemy builder."""

import math

from mathutils import Euler, Vector

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_types import RigDefinition, rig_from_bone_map
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy


class AnimatedEmberImp(AnimatedEnemy):
    """Humanoid fire creature"""

    def build_mesh_parts(self):
        body_height = random_variance(1.2, 0.2, self.rng)
        body_width = random_variance(0.4, 0.1, self.rng)
        body = create_cylinder(
            location=(0, 0, body_height * 0.5),
            scale=(body_width, body_width, body_height),
            vertices=8,
        )
        self.parts.append(body)
        self.body_height = body_height
        self.body_width = body_width

        head_scale = self.body_width * 1.1
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * 0.7),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)

        arm_length = random_variance(0.8, 0.2, self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + arm_length * 0.5), 0, self.body_height * 0.7),
                scale=(0.12, 0.12, arm_length),
                vertices=6,
            )
            arm.rotation_euler = Euler((0, 0, math.pi / 2))
            self.parts.append(arm)

            hand = create_sphere(
                location=(side * (self.body_width + arm_length), 0, self.body_height * 0.7),
                scale=(0.15, 0.15, 0.15),
            )
            self.parts.append(hand)

        leg_length = random_variance(0.7, 0.1, self.rng)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.3, 0, leg_length * 0.5),
                scale=(0.12, 0.12, leg_length),
                vertices=6,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("ember_imp", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        limb_material = enemy_mats["limbs"]
        hand_material = enemy_mats["extra"]
        part_index = 2
        for _i in range(2):
            apply_material_to_object(self.parts[part_index], limb_material)
            apply_material_to_object(self.parts[part_index + 1], hand_material)
            part_index += 2
        for _i in range(2):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

    def get_rig_definition(self) -> RigDefinition:
        h = self.body_height
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * 0.2)), None),
                "spine": (Vector((0, 0, h * 0.2)), Vector((0, 0, h * 0.7)), "root"),
                "head": (Vector((0, 0, h * 0.7)), Vector((0, 0, h * 1.0)), "spine"),
                "arm_l": (Vector((0, h * 0.2, h * 0.6)), Vector((0, h * 0.5, h * 0.3)), "spine"),
                "arm_r": (Vector((0, -h * 0.2, h * 0.6)), Vector((0, -h * 0.5, h * 0.3)), "spine"),
                "leg_l": (Vector((0, h * 0.1, h * 0.2)), Vector((0, h * 0.1, 0)), "root"),
                "leg_r": (Vector((0, -h * 0.1, h * 0.2)), Vector((0, -h * 0.1, 0)), "root"),
            }
        )

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID
