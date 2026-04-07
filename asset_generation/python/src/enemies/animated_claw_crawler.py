"""Animated claw crawler enemy builder."""

import math
from typing import ClassVar

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models.quadruped_simple import (
    CYLINDER_VERTICES_HEX,
    QUADRUPED_LEG_THICKNESS,
    QuadrupedSimpleRig,
)
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedClawCrawler(QuadrupedSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Flat disc body with large front claws and quadruped movement"""

    body_height = 1.0

    BODY_BASE: ClassVar[float] = 1.0
    BODY_VARIANCE: ClassVar[float] = 0.2
    BODY_CENTER_Z: ClassVar[float] = 0.2
    BODY_FLATTEN_Y_VARIANCE: ClassVar[float] = 0.1
    BODY_FLATTEN_Y_BASE: ClassVar[float] = 0.9
    BODY_FLATTEN_Z: ClassVar[float] = 0.35
    HEAD_SCALE_REL: ClassVar[float] = 0.4
    HEAD_SCALE_VARIANCE: ClassVar[float] = 0.1
    HEAD_X_ALONG: ClassVar[float] = 1.1
    HEAD_CENTER_Z: ClassVar[float] = 0.25
    HEAD_FLATTEN_Z: ClassVar[float] = 0.7
    EYE_SCALE_HEAD_RATIO: ClassVar[float] = 0.12
    PERIPHERAL_EYES_MAX: ClassVar[int] = 3
    EYE_ONE_DY: ClassVar[float] = 0.0
    EYE_ONE_DZ: ClassVar[float] = 0.18
    EYE_TWO_DY_SCALE: ClassVar[float] = 0.38
    EYE_TWO_DZ: ClassVar[float] = 0.12
    PERIPHERAL_EYE_ANGLE_DIVISOR: ClassVar[float] = 3.0
    EYE_RING_PHASE: ClassVar[float] = math.pi / 2
    EYE_RING_DY_SCALE: ClassVar[float] = 0.42
    EYE_RING_DZ_BASE: ClassVar[float] = 0.08
    EYE_RING_DZ_SIN_SCALE: ClassVar[float] = 0.12
    EYE_RING_ANGLE_OFFSET: ClassVar[float] = 0.4
    EYE_BACK_X: ClassVar[float] = 0.48
    EYE_BASE_Z: ClassVar[float] = 0.22
    CLAW_LENGTH_BASE: ClassVar[float] = 0.35
    CLAW_LENGTH_VARIANCE: ClassVar[float] = 0.08
    CLAW_X: ClassVar[float] = 0.6
    CLAW_Y_SPREAD: ClassVar[float] = 0.5
    CLAW_Z: ClassVar[float] = 0.1
    CLAW_RADIUS: ClassVar[float] = 0.15
    LEG_LENGTH_BASE: ClassVar[float] = 0.3
    LEG_LENGTH_VARIANCE: ClassVar[float] = 0.08
    LEG_COUNT: ClassVar[int] = 4
    CLAW_COUNT: ClassVar[int] = 2
    LEG_ANCHOR_RATIOS: ClassVar[tuple[tuple[float, float, float], ...]] = (
        (0, 0.5, 0),
        (0, -0.5, 0),
        (-0.4, 0.4, 0),
        (-0.4, -0.4, 0),
    )

    def build_mesh_parts(self):
        body_scale = random_variance(self.BODY_BASE, self.BODY_VARIANCE, self.rng)
        body = create_sphere(
            location=(0, 0, self.BODY_CENTER_Z),
            scale=(
                body_scale,
                body_scale * random_variance(self.BODY_FLATTEN_Y_BASE, self.BODY_FLATTEN_Y_VARIANCE, self.rng),
                body_scale * self.BODY_FLATTEN_Z,
            ),
        )
        self.parts.append(body)
        self.body_scale = body_scale

        head_scale = self.body_scale * random_variance(self.HEAD_SCALE_REL, self.HEAD_SCALE_VARIANCE, self.rng)
        head = create_sphere(
            location=(self.body_scale * self.HEAD_X_ALONG, 0, self.HEAD_CENTER_Z),
            scale=(head_scale, head_scale, head_scale * self.HEAD_FLATTEN_Z),
        )
        self.parts.append(head)
        self.head_scale = head_scale

        pe = int(self.build_options.get("peripheral_eyes", 0))
        self._peripheral_eyes = max(0, min(self.PERIPHERAL_EYES_MAX, pe))
        eye_scale = self.head_scale * self.EYE_SCALE_HEAD_RATIO
        for i in range(self._peripheral_eyes):
            if self._peripheral_eyes == 1:
                dy, dz = self.EYE_ONE_DY, self.EYE_ONE_DZ
            elif self._peripheral_eyes == 2:
                dy = self.body_scale * self.EYE_TWO_DY_SCALE * (1 if i == 0 else -1)
                dz = self.EYE_TWO_DZ
            else:
                ang = (i / self.PERIPHERAL_EYE_ANGLE_DIVISOR) * math.pi - self.EYE_RING_PHASE
                dy = self.body_scale * self.EYE_RING_DY_SCALE * math.cos(ang)
                dz = self.EYE_RING_DZ_BASE + self.EYE_RING_DZ_SIN_SCALE * math.sin(ang + self.EYE_RING_ANGLE_OFFSET)
            eye = create_sphere(
                location=(-self.body_scale * self.EYE_BACK_X, dy, self.EYE_BASE_Z + dz),
                scale=(eye_scale, eye_scale, eye_scale),
            )
            self.parts.append(eye)

        for side in [-1, 1]:
            claw_length = random_variance(self.CLAW_LENGTH_BASE, self.CLAW_LENGTH_VARIANCE, self.rng)
            claw = create_cylinder(
                location=(self.body_scale * self.CLAW_X, side * self.body_scale * self.CLAW_Y_SPREAD, self.CLAW_Z),
                scale=(self.CLAW_RADIUS, self.CLAW_RADIUS, claw_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(claw)

        for leg_x, leg_y, leg_z in self.LEG_ANCHOR_RATIOS:
            lx = self.body_scale * leg_x
            ly = self.body_scale * leg_y
            lz = leg_z
            leg_length = random_variance(self.LEG_LENGTH_BASE, self.LEG_LENGTH_VARIANCE, self.rng)
            leg = create_cylinder(
                location=(lx, ly, lz),
                scale=(QUADRUPED_LEG_THICKNESS, QUADRUPED_LEG_THICKNESS, leg_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("claw_crawler", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        eye_mat = enemy_mats["extra"]
        claw_material = enemy_mats["extra"]
        limb_material = enemy_mats["limbs"]
        part_index = 2
        for _ in range(self._peripheral_eyes):
            apply_material_to_object(self.parts[part_index], eye_mat)
            part_index += 1
        for _ in range(self.CLAW_COUNT):
            apply_material_to_object(self.parts[part_index], claw_material)
            part_index += 1
        for _ in range(self.LEG_COUNT):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
