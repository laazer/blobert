"""Animated ember imp enemy builder."""

from typing import ClassVar

from mathutils import Euler

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models.humanoid_simple import (
    CYLINDER_VERTICES_HEX,
    CYLINDER_VERTICES_OCT,
    EULER_Z_90,
    MESH_BODY_CENTER_Z_FACTOR,
    HumanoidSimpleRig,
)
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedImp(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Humanoid fire creature"""

    body_height = 1.0

    BODY_HEIGHT_BASE: ClassVar[float] = 1.2
    BODY_HEIGHT_VARIANCE: ClassVar[float] = 0.2
    BODY_WIDTH_BASE: ClassVar[float] = 0.4
    BODY_WIDTH_VARIANCE: ClassVar[float] = 0.1
    HEAD_SCALE_WIDTH_RATIO: ClassVar[float] = 1.1
    HEAD_ABOVE_BODY_SCALE: ClassVar[float] = 0.7
    ARM_LENGTH_BASE: ClassVar[float] = 0.8
    ARM_LENGTH_VARIANCE: ClassVar[float] = 0.2
    ARM_OUTWARD_HALF_LENGTH: ClassVar[float] = 0.5
    ARM_RADIUS: ClassVar[float] = 0.12
    ARM_HEIGHT_RATIO: ClassVar[float] = 0.7
    HAND_RADIUS: ClassVar[float] = 0.15
    LEG_LENGTH_BASE: ClassVar[float] = 0.7
    LEG_LENGTH_VARIANCE: ClassVar[float] = 0.1
    LEG_X_SPREAD_RATIO: ClassVar[float] = 0.3
    LEG_Z_HALF_LENGTH: ClassVar[float] = 0.5
    LIMB_PAIRS: ClassVar[int] = 2

    def build_mesh_parts(self):
        body_height = random_variance(self._mesh("BODY_HEIGHT_BASE"), self._mesh("BODY_HEIGHT_VARIANCE"), self.rng)
        body_width = random_variance(self._mesh("BODY_WIDTH_BASE"), self._mesh("BODY_WIDTH_VARIANCE"), self.rng)
        body = create_cylinder(
            location=(0, 0, body_height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(body_width, body_width, body_height),
            vertices=CYLINDER_VERTICES_OCT,
        )
        self.parts.append(body)
        self.body_height = body_height
        self.body_width = body_width

        head_scale = self.body_width * self._mesh("HEAD_SCALE_WIDTH_RATIO")
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * self._mesh("HEAD_ABOVE_BODY_SCALE")),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)

        arm_length = random_variance(self._mesh("ARM_LENGTH_BASE"), self._mesh("ARM_LENGTH_VARIANCE"), self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=(
                    side * (self.body_width + arm_length * self._mesh("ARM_OUTWARD_HALF_LENGTH")),
                    0,
                    self.body_height * self._mesh("ARM_HEIGHT_RATIO"),
                ),
                scale=(self._mesh("ARM_RADIUS"), self._mesh("ARM_RADIUS"), arm_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            arm.rotation_euler = Euler((0, 0, EULER_Z_90))
            self.parts.append(arm)

            hand = create_sphere(
                location=(
                    side * (self.body_width + arm_length),
                    0,
                    self.body_height * self._mesh("ARM_HEIGHT_RATIO"),
                ),
                scale=(self._mesh("HAND_RADIUS"), self._mesh("HAND_RADIUS"), self._mesh("HAND_RADIUS")),
            )
            self.parts.append(hand)

        leg_length = random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=(
                    side * self.body_width * self._mesh("LEG_X_SPREAD_RATIO"),
                    0,
                    leg_length * self._mesh("LEG_Z_HALF_LENGTH"),
                ),
                scale=(self._mesh("ARM_RADIUS"), self._mesh("ARM_RADIUS"), leg_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("imp", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        limb_material = enemy_mats["limbs"]
        hand_material = enemy_mats["extra"]
        part_index = 2
        lp = int(self._mesh("LIMB_PAIRS"))
        for _i in range(lp):
            apply_material_to_object(self.parts[part_index], limb_material)
            apply_material_to_object(self.parts[part_index + 1], hand_material)
            part_index += 2
        for _i in range(lp):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID
