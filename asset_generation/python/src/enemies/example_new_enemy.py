"""
Examples of adding enemies with BaseAnimatedModel / AnimatedEnemy.
"""

import math

from mathutils import Vector

from ..core.blender_utils import create_cylinder, create_sphere
from ..core.rig_types import rig_from_bone_map
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy


class ExampleSpider(AnimatedEnemy):
    """8-legged spider — quadruped-style rig."""

    def build_mesh_parts(self):
        self.body_scale = 0.8
        body = create_sphere(
            location=(0, 0, 0.2),
            scale=(self.body_scale, self.body_scale, self.body_scale * 0.7),
        )
        self.parts.append(body)

        leg_angles = [i * 45 for i in range(8)]
        for angle in leg_angles:
            x_offset = math.cos(math.radians(angle)) * self.body_scale * 0.4
            y_offset = math.sin(math.radians(angle)) * self.body_scale * 0.4
            leg = create_cylinder(
                location=(x_offset, y_offset, 0.1),
                scale=(0.05, 0.05, 0.4),
                vertices=6,
            )
            self.parts.append(leg)

    def get_rig_definition(self):
        s = self.body_scale
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, s * 0.2)), None),
                "spine": (Vector((0, 0, s * 0.2)), Vector((s * 0.5, 0, s * 0.4)), "root"),
                "head": (Vector((s * 0.5, 0, s * 0.4)), Vector((s * 0.8, 0, s * 0.6)), "spine"),
                "leg_fl": (Vector((s * 0.3, s * 0.3, s * 0.3)), Vector((s * 0.3, s * 0.3, 0)), "spine"),
                "leg_fr": (Vector((s * 0.3, -s * 0.3, s * 0.3)), Vector((s * 0.3, -s * 0.3, 0)), "spine"),
                "leg_ml": (Vector((0, s * 0.4, s * 0.3)), Vector((0, s * 0.4, 0)), "spine"),
                "leg_mr": (Vector((0, -s * 0.4, s * 0.3)), Vector((0, -s * 0.4, 0)), "spine"),
                "leg_bl": (Vector((-s * 0.2, s * 0.3, s * 0.3)), Vector((-s * 0.2, s * 0.3, 0)), "root"),
                "leg_br": (Vector((-s * 0.2, -s * 0.3, s * 0.3)), Vector((-s * 0.2, -s * 0.3, 0)), "root"),
            }
        )

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("claw_crawler", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        for part in self.parts[1:]:
            apply_material_to_object(part, enemy_mats["limbs"])


class ExampleGhost(AnimatedEnemy):
    """Floating ghost — blob rig."""

    def build_mesh_parts(self):
        body = create_sphere(location=(0, 0, 1.0), scale=(1.2, 1.2, 1.5))
        self.parts.append(body)
        self.body_scale = 1.2
        for i in range(3):
            x_offset = (i - 1) * 0.3
            tendril = create_cylinder(
                location=(x_offset, 0, 0.3),
                scale=(0.1, 0.1, 0.8),
                vertices=6,
            )
            self.parts.append(tendril)

    def get_rig_definition(self):
        s = self.body_scale
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, s * 0.3)), None),
                "body": (Vector((0, 0, s * 0.3)), Vector((0, 0, s * 0.8)), "root"),
                "head": (Vector((0, 0, s * 0.8)), Vector((0, 0, s * 1.2)), "body"),
            }
        )

    def get_body_type(self):
        return EnemyBodyTypes.BLOB

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("tar_slug", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        for part in self.parts[1:]:
            apply_material_to_object(part, enemy_mats["limbs"])


class ExampleMech(AnimatedEnemy):
    """Robot mech — humanoid rig."""

    def build_mesh_parts(self):
        self.body_height = 2.0
        self.body_width = 0.8
        body = create_cylinder(
            location=(0, 0, self.body_height * 0.5),
            scale=(self.body_width, self.body_width, self.body_height),
            vertices=8,
        )
        self.parts.append(body)
        head = create_cylinder(
            location=(0, 0, self.body_height + 0.3),
            scale=(0.4, 0.4, 0.3),
            vertices=4,
        )
        self.parts.append(head)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + 0.4), 0, self.body_height * 0.7),
                scale=(0.15, 0.15, 0.8),
                vertices=6,
            )
            self.parts.append(arm)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.3, 0, 0.6),
                scale=(0.15, 0.15, 1.2),
                vertices=6,
            )
            self.parts.append(leg)

    def get_rig_definition(self):
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

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("ember_imp", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats["limbs"])