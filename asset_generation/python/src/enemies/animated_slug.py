"""Animated tar slug enemy builder."""

from typing import ClassVar

from mathutils import Vector

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models.blob_simple import (
    CYLINDER_VERTICES_HEX,
    MESH_BODY_CENTER_Z_FACTOR,
    BlobSimpleRig,
)
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin
from .zone_geometry_extras_attach import append_animated_enemy_zone_extras


class AnimatedSlug(BlobSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Elongated slug with blob movement"""

    body_height = 1.0

    LENGTH_BASE: ClassVar[float] = 2.0
    LENGTH_VARIANCE: ClassVar[float] = 0.3
    WIDTH_BASE: ClassVar[float] = 0.8
    WIDTH_VARIANCE: ClassVar[float] = 0.2
    HEIGHT_BASE: ClassVar[float] = 0.6
    HEIGHT_VARIANCE: ClassVar[float] = 0.1
    HEAD_WIDTH_RATIO: ClassVar[float] = 0.4
    HEAD_X_RATIO: ClassVar[float] = 0.7
    HEAD_Z_RATIO: ClassVar[float] = 0.8
    STALK_X_RATIO: ClassVar[float] = 0.6
    STALK_Y_SPREAD: ClassVar[float] = 0.3
    STALK_Z_BASE: ClassVar[float] = 0.3
    STALK_RADIUS: ClassVar[float] = 0.05
    STALK_LENGTH: ClassVar[float] = 0.3
    EYE_Z_OFFSET: ClassVar[float] = 0.6
    EYE_RADIUS: ClassVar[float] = 0.1

    def build_mesh_parts(self):
        length = random_variance(self._mesh("LENGTH_BASE"), self._mesh("LENGTH_VARIANCE"), self.rng)
        width = random_variance(self._mesh("WIDTH_BASE"), self._mesh("WIDTH_VARIANCE"), self.rng)
        height = random_variance(self._mesh("HEIGHT_BASE"), self._mesh("HEIGHT_VARIANCE"), self.rng)

        body = create_sphere(
            location=(0, 0, height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(length, width, height),
        )
        self.parts.append(body)

        self.length = length
        self.width = width
        self.height = height

        cz = float(height * MESH_BODY_CENTER_Z_FACTOR)
        self._zone_geom_body_center = Vector((0.0, 0.0, cz))
        self._zone_geom_body_radii = Vector((length, width, height))

        head_scale = self.width * self._mesh("HEAD_WIDTH_RATIO")
        hx = float(self.length * self._mesh("HEAD_X_RATIO"))
        hz = float(self.height * self._mesh("HEAD_Z_RATIO"))
        self._zone_geom_head_center = Vector((hx, 0.0, hz))
        self._zone_geom_head_radii = Vector((head_scale, head_scale, head_scale))

        head = create_sphere(
            location=(hx, 0, hz),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)

        for side in [-1, 1]:
            stalk = create_cylinder(
                location=(
                    self.length * self._mesh("STALK_X_RATIO"),
                    side * self.width * self._mesh("STALK_Y_SPREAD"),
                    self.height + self._mesh("STALK_Z_BASE"),
                ),
                scale=(self._mesh("STALK_RADIUS"), self._mesh("STALK_RADIUS"), self._mesh("STALK_LENGTH")),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(stalk)

            eye = create_sphere(
                location=(
                    self.length * self._mesh("STALK_X_RATIO"),
                    side * self.width * self._mesh("STALK_Y_SPREAD"),
                    self.height + self._mesh("EYE_Z_OFFSET"),
                ),
                scale=(self._mesh("EYE_RADIUS"), self._mesh("EYE_RADIUS"), self._mesh("EYE_RADIUS")),
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

        append_animated_enemy_zone_extras(self)

    def get_body_type(self):
        return EnemyBodyTypes.BLOB
