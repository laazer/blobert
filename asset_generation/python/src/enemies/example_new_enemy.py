"""
Examples of adding enemies with BaseAnimatedModel / AnimatedEnemy.
"""

import math

from mathutils import Vector

from ..core.blender_utils import create_cylinder, create_sphere
from ..core.rig_models.blob_simple import CYLINDER_VERTICES_HEX as BLOB_CYL_HEX
from ..core.rig_models.blob_simple import BlobSimpleRig
from ..core.rig_models.humanoid_simple import (
    CYLINDER_VERTICES_HEX,
    CYLINDER_VERTICES_OCT,
    CYLINDER_VERTICES_SQUARE,
    MESH_BODY_CENTER_Z_FACTOR,
    HumanoidSimpleRig,
)
from ..core.rig_models.quadruped_simple import CYLINDER_VERTICES_HEX as QUAD_CYL_HEX
from ..core.rig_models.quadruped_simple import QuadrupedSimpleRig
from ..core.rig_types import rig_from_bone_map
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class ExampleSpider(QuadrupedSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """8-legged spider — quadruped-style rig."""

    body_height = 0.8

    def build_mesh_parts(self):
        body = create_sphere(
            location=(0, 0, 0.2),
            scale=(self.body_height, self.body_height, self.body_height * 0.7),
        )
        self.parts.append(body)

        leg_angles = [i * 45 for i in range(8)]
        for angle in leg_angles:
            x_offset = math.cos(math.radians(angle)) * self.body_height * 0.4
            y_offset = math.sin(math.radians(angle)) * self.body_height * 0.4
            leg = create_cylinder(
                location=(x_offset, y_offset, 0.1),
                scale=(0.05, 0.05, 0.4),
                vertices=QUAD_CYL_HEX,
            )
            self.parts.append(leg)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("spider", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        for part in self.parts[1:]:
            apply_material_to_object(part, enemy_mats["limbs"])


class ExampleGhost(BlobSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Floating ghost — blob rig."""

    body_height = 1.2

    def build_mesh_parts(self):
        body = create_sphere(location=(0, 0, 1.0), scale=(1.2, 1.2, 1.5))
        self.parts.append(body)
        for i in range(3):
            x_offset = (i - 1) * 0.3
            tendril = create_cylinder(
                location=(x_offset, 0, 0.3),
                scale=(0.1, 0.1, 0.8),
                vertices=BLOB_CYL_HEX,
            )
            self.parts.append(tendril)

    def get_body_type(self):
        return EnemyBodyTypes.BLOB

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("slug", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        for part in self.parts[1:]:
            apply_material_to_object(part, enemy_mats["limbs"])


class ExampleMech(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Robot mech — humanoid rig."""

    body_height = 2.0

    def build_mesh_parts(self):
        self.body_width = 0.8
        body = create_cylinder(
            location=(0, 0, self.body_height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(self.body_width, self.body_width, self.body_height),
            vertices=CYLINDER_VERTICES_OCT,
        )
        self.parts.append(body)
        head = create_cylinder(
            location=(0, 0, self.body_height + 0.3),
            scale=(0.4, 0.4, 0.3),
            vertices=CYLINDER_VERTICES_SQUARE,
        )
        self.parts.append(head)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(side * (self.body_width + 0.4), 0, self.body_height * 0.7),
                scale=(0.15, 0.15, 0.8),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(arm)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(side * self.body_width * 0.3, 0, 0.6),
                scale=(0.15, 0.15, 1.2),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(leg)

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("imp", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats["limbs"])


class ExampleCustomRigEnemy(AnimatedEnemy):
    """Enemy with a one-off bone layout (not one of the shared SimpleRigModel presets)."""

    def build_mesh_parts(self):
        self.parts.append(create_sphere(location=(0, 0, 0.5), scale=(0.5, 0.5, 0.5)))

    def get_rig_definition(self):
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, 0.5)), None),
                "head": (Vector((0, 0, 0.5)), Vector((0, 0, 1.0)), "root"),
            }
        )

    def get_body_type(self):
        return EnemyBodyTypes.BLOB

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("slug", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
