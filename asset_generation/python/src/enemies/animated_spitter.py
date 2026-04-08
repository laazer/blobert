"""Animated acid spitter enemy builder."""
from __future__ import annotations

from typing import ClassVar

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models.blob_simple import (
    CYLINDER_VERTICES_HEX,
    MESH_BODY_CENTER_Z_FACTOR,
    BlobSimpleRig,
)
from ..materials.material_system import apply_material_to_object
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedSpitter(BlobSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Squat acid sac with blob movement"""

    body_height = 1.0

    BODY_BASE: ClassVar[float] = 1.0
    BODY_VARIANCE: ClassVar[float] = 0.15
    HEIGHT_BASE: ClassVar[float] = 0.9
    HEIGHT_VARIANCE: ClassVar[float] = 0.1
    WIDTH_JITTER_VARIANCE: ClassVar[float] = 0.15
    HEAD_SCALE_REL: ClassVar[float] = 0.35
    HEAD_SCALE_VARIANCE: ClassVar[float] = 0.08
    HEAD_X_ALONG: ClassVar[float] = 0.8
    HEAD_Z_HEIGHT_RATIO: ClassVar[float] = 0.9
    TENDRIL_LENGTH_BASE: ClassVar[float] = 0.4
    TENDRIL_LENGTH_VARIANCE: ClassVar[float] = 0.1
    TENDRIL_X_SPREAD: ClassVar[float] = 0.3
    TENDRIL_RADIUS: ClassVar[float] = 0.07

    def build_mesh_parts(self):
        body_scale = random_variance(self._mesh("BODY_BASE"), self._mesh("BODY_VARIANCE"), self.rng)
        height = random_variance(self._mesh("HEIGHT_BASE"), self._mesh("HEIGHT_VARIANCE"), self.rng)
        body = create_sphere(
            location=(0, 0, height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(
                body_scale,
                body_scale * random_variance(1.0, self._mesh("WIDTH_JITTER_VARIANCE"), self.rng),
                height,
            ),
        )
        self.parts.append(body)
        self.body_scale = body_scale
        self.height = height

        head_scale = self.body_scale * random_variance(
            self._mesh("HEAD_SCALE_REL"), self._mesh("HEAD_SCALE_VARIANCE"), self.rng
        )
        head = create_sphere(
            location=(
                self.body_scale * self._mesh("HEAD_X_ALONG"),
                0,
                self.height * self._mesh("HEAD_Z_HEIGHT_RATIO"),
            ),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)
        self.head_scale = head_scale

        for side in [-1, 1]:
            tendril_length = random_variance(
                self._mesh("TENDRIL_LENGTH_BASE"), self._mesh("TENDRIL_LENGTH_VARIANCE"), self.rng
            )
            tendril = create_cylinder(
                location=(side * self.body_scale * self._mesh("TENDRIL_X_SPREAD"), 0, 0),
                scale=(self._mesh("TENDRIL_RADIUS"), self._mesh("TENDRIL_RADIUS"), tendril_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(tendril)

    def apply_themed_materials(self):
        enemy_mats = self._themed_slot_materials_for("spitter")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats["limbs"])

    def get_body_type(self):
        return EnemyBodyTypes.BLOB
