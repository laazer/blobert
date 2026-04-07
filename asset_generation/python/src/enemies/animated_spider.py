"""Animated spider enemy builder (slug: spider, quadruped body)."""

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


class AnimatedSpider(QuadrupedSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Multi-segment bug with quadruped movement"""

    body_height = 1.0

    BODY_BASE: ClassVar[float] = 1.0
    BODY_VARIANCE: ClassVar[float] = 0.2
    BODY_CENTER_Z: ClassVar[float] = 0.3
    BODY_SCALE_Y: ClassVar[float] = 0.8
    BODY_SCALE_Z: ClassVar[float] = 0.9
    HEAD_SCALE_REL: ClassVar[float] = 0.6
    HEAD_SCALE_VARIANCE: ClassVar[float] = 0.1
    HEAD_OFFSET_ALONG_X: ClassVar[float] = 0.5
    EYE_SCALE_HEAD_RATIO: ClassVar[float] = 0.15
    EYE_X_ALONG: ClassVar[float] = 1.2
    EYE_Y_SIDE: ClassVar[float] = 0.4
    EYE_Z: ClassVar[float] = 0.4
    LEG_LENGTH_BASE: ClassVar[float] = 0.3
    LEG_LENGTH_VARIANCE: ClassVar[float] = 0.1
    LEG_COUNT: ClassVar[int] = 6
    DEFAULT_EYE_COUNT: ClassVar[int] = 2
    ALLOWED_EYE_COUNTS: ClassVar[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12)
    LEG_ANCHOR_RATIOS: ClassVar[tuple[tuple[float, float, float], ...]] = (
        (0.3, 0.3, 0),
        (0.3, -0.3, 0),
        (0, 0.4, 0),
        (0, -0.4, 0),
        (-0.2, 0.3, 0),
        (-0.2, -0.3, 0),
    )

    def build_mesh_parts(self):
        """Create body, head, eyes, and legs."""
        body_scale = random_variance(self._mesh("BODY_BASE"), self._mesh("BODY_VARIANCE"), self.rng)
        body = create_sphere(
            location=(0, 0, self._mesh("BODY_CENTER_Z")),
            scale=(
                body_scale,
                body_scale * self._mesh("BODY_SCALE_Y"),
                body_scale * self._mesh("BODY_SCALE_Z"),
            ),
        )
        self.parts.append(body)
        self.body_scale = body_scale

        head_scale = self.body_scale * random_variance(
            self._mesh("HEAD_SCALE_REL"), self._mesh("HEAD_SCALE_VARIANCE"), self.rng
        )
        head_offset = self.body_scale + head_scale * self._mesh("HEAD_OFFSET_ALONG_X")
        head = create_sphere(
            location=(head_offset, 0, self._mesh("BODY_CENTER_Z")),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)
        self.head_scale = head_scale

        eye_count = int(self.build_options.get("eye_count", self._mesh("DEFAULT_EYE_COUNT")))
        if eye_count not in self.ALLOWED_EYE_COUNTS:
            eye_count = int(self._mesh("DEFAULT_EYE_COUNT"))
        self._eye_count = eye_count
        eye_scale = self.head_scale * self._mesh("EYE_SCALE_HEAD_RATIO")
        for i in range(eye_count):
            side = 1 if i % 2 == 0 else -1
            eye_x = self.body_scale + self.head_scale * self._mesh("EYE_X_ALONG")
            eye_y = side * self.head_scale * self._mesh("EYE_Y_SIDE")
            eye_z = self._mesh("EYE_Z")
            eye = create_sphere(location=(eye_x, eye_y, eye_z), scale=(eye_scale, eye_scale, eye_scale))
            self.parts.append(eye)

        for leg_x, leg_y, leg_z in self.LEG_ANCHOR_RATIOS:
            lx = self.body_scale * leg_x
            ly = self.body_scale * leg_y
            lz = leg_z
            leg_length = random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng)
            leg = create_cylinder(
                location=(lx, ly, lz),
                scale=(QUADRUPED_LEG_THICKNESS, QUADRUPED_LEG_THICKNESS, leg_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("spider", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        leg_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        ec = getattr(self, "_eye_count", int(self._mesh("DEFAULT_EYE_COUNT")))
        for i in range(ec):
            apply_material_to_object(self.parts[2 + i], eye_material)
        for i in range(int(self._mesh("LEG_COUNT"))):
            apply_material_to_object(self.parts[2 + ec + i], leg_material)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
