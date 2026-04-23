"""Animated tar slug enemy builder."""

import math
from typing import ClassVar

from mathutils import Euler, Vector

from ..core.blender_utils import (
    create_cylinder,
    create_eye_mesh,
    create_mouth_mesh,
    create_pupil_mesh,
    create_sphere,
    create_tail_mesh,
    random_variance,
)
from ..core.rig_models.blob_simple import (
    CYLINDER_VERTICES_HEX,
    MESH_BODY_CENTER_Z_FACTOR,
    BlobSimpleRig,
)
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.body_type_presets import blob_body_type_scales
from ..utils.config import EnemyBodyTypes
from .animated_enemy import UsesSimpleRigMixin
from .builder_template import AnimatedEnemyBuilderBase
from .zone_geometry_extras_attach import append_animated_enemy_zone_extras


class AnimatedSlug(BlobSimpleRig, UsesSimpleRigMixin, AnimatedEnemyBuilderBase):
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

    def _build_body_mesh(self) -> None:
        length = random_variance(
            self._mesh("LENGTH_BASE"), self._mesh("LENGTH_VARIANCE"), self.rng
        )
        width = random_variance(
            self._mesh("WIDTH_BASE"), self._mesh("WIDTH_VARIANCE"), self.rng
        )
        height = random_variance(
            self._mesh("HEIGHT_BASE"), self._mesh("HEIGHT_VARIANCE"), self.rng
        )
        sx, sy, sz = blob_body_type_scales(self.build_options)
        length *= sx
        width *= sy
        height *= sz

        body = create_sphere(
            location=(0, 0, height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(length, width, height),
        )
        _brx = math.radians(float(self.build_options.get("RIG_BODY_ROT_X") or 0.0))
        _bry = math.radians(float(self.build_options.get("RIG_BODY_ROT_Y") or 0.0))
        _brz = math.radians(float(self.build_options.get("RIG_BODY_ROT_Z") or 0.0))
        body.rotation_euler = Euler((_brx, _bry, _brz), "XYZ")
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
        _hrx = math.radians(float(self.build_options.get("RIG_HEAD_ROT_X") or 0.0))
        _hry = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Y") or 0.0))
        _hrz = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Z") or 0.0))
        head.rotation_euler = Euler((_hrx, _hry, _hrz), "XYZ")
        self.parts.append(head)

    def _build_limbs(self) -> None:
        eye_shape = str(self.build_options.get("eye_shape", "circle"))
        pupil_enabled = bool(self.build_options.get("pupil_enabled", False))
        pupil_shape = str(self.build_options.get("pupil_shape", "dot"))
        eye_radius = float(self._mesh("EYE_RADIUS"))
        pupil_scale = eye_radius * 0.35
        for side in [-1, 1]:
            stalk_x = self.length * self._mesh("STALK_X_RATIO")
            stalk_y = side * self.width * self._mesh("STALK_Y_SPREAD")
            stalk = create_cylinder(
                location=(
                    stalk_x,
                    stalk_y,
                    self.height + self._mesh("STALK_Z_BASE"),
                ),
                scale=(
                    self._mesh("STALK_RADIUS"),
                    self._mesh("STALK_RADIUS"),
                    self._mesh("STALK_LENGTH"),
                ),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(stalk)

            eye_z = self.height + float(self._mesh("EYE_Z_OFFSET"))
            eye_loc = (stalk_x, stalk_y, eye_z)
            eye = create_eye_mesh(eye_shape, eye_loc, eye_radius)
            self.parts.append(eye)

            if pupil_enabled:
                pupil_center = (
                    stalk_x,
                    stalk_y,
                    eye_z + eye_radius + eye_radius * 0.05,
                )
                self.parts.append(
                    create_pupil_mesh(pupil_shape, pupil_center, pupil_scale)
                )

        self._pupil_enabled = pupil_enabled

        # Mouth extra (MTE-7)
        mouth_enabled = bool(self.build_options.get("mouth_enabled", False))
        if mouth_enabled:
            mouth_shape = str(self.build_options.get("mouth_shape") or "smile")
            mouth_location = self._zone_geom_head_center + Vector(
                (self._zone_geom_head_radii.x, 0.0, 0.0)
            )
            self.parts.append(
                create_mouth_mesh(
                    mouth_shape, tuple(mouth_location), self._zone_geom_head_radii.x
                )
            )

        # Tail extra (MTE-7)
        tail_enabled = bool(self.build_options.get("tail_enabled", False))
        if tail_enabled:
            tail_shape = str(self.build_options.get("tail_shape") or "spike")
            tail_length = float(self.build_options.get("tail_length", 1.0))
            tail_location = self._zone_geom_body_center + Vector(
                (-self._zone_geom_body_radii.x, 0.0, 0.0)
            )
            self.parts.append(
                create_tail_mesh(tail_shape, tail_length, tuple(tail_location))
            )

    def _apply_materials(self) -> None:
        enemy_mats = get_enemy_materials("slug", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        stalk_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        head_material = enemy_mats["head"]
        pupil_enabled = getattr(self, "_pupil_enabled", False)
        if pupil_enabled:
            # Part pattern per side: stalk (0), eye (1), pupil (2) → repeat every 3.
            for i, part in enumerate(self.parts[2:]):
                r = i % 3
                if r == 0:
                    apply_material_to_object(part, stalk_material)
                elif r == 1:
                    apply_material_to_object(part, eye_material)
                else:
                    apply_material_to_object(part, head_material)
        else:
            # Original pattern: stalk (even), eye (odd).
            for i, part in enumerate(self.parts[2:]):
                if i % 2 == 0:
                    apply_material_to_object(part, stalk_material)
                else:
                    apply_material_to_object(part, eye_material)

    def _add_zone_extras(self) -> None:
        append_animated_enemy_zone_extras(self)

    def build_mesh_parts(self) -> None:
        super().build_mesh_parts()

    def apply_themed_materials(self) -> None:
        super().apply_themed_materials()

    def get_body_type(self) -> EnemyBodyTypes:
        return EnemyBodyTypes.BLOB
