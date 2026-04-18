"""Animated claw crawler enemy builder."""
from __future__ import annotations

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
from ..core.rig_models.quadruped_simple import (
    CYLINDER_VERTICES_HEX,
    QUADRUPED_LEG_THICKNESS,
    QuadrupedSimpleRig,
)
from ..materials.material_system import apply_material_to_object
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin
from .zone_geometry_extras_attach import append_animated_enemy_zone_extras


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
        body_scale = random_variance(self._mesh("BODY_BASE"), self._mesh("BODY_VARIANCE"), self.rng)
        flatten_y = random_variance(self._mesh("BODY_FLATTEN_Y_BASE"), self._mesh("BODY_FLATTEN_Y_VARIANCE"), self.rng)
        bz = float(self._mesh("BODY_CENTER_Z"))
        self._zone_geom_body_center = Vector((0.0, 0.0, bz))
        self._zone_geom_body_radii = Vector(
            (body_scale, body_scale * flatten_y, body_scale * float(self._mesh("BODY_FLATTEN_Z")))
        )

        body = create_sphere(
            location=(0, 0, bz),
            scale=(
                body_scale,
                body_scale * flatten_y,
                body_scale * self._mesh("BODY_FLATTEN_Z"),
            ),
        )
        _brx = math.radians(float(self.build_options.get("RIG_BODY_ROT_X") or 0.0))
        _bry = math.radians(float(self.build_options.get("RIG_BODY_ROT_Y") or 0.0))
        _brz = math.radians(float(self.build_options.get("RIG_BODY_ROT_Z") or 0.0))
        body.rotation_euler = Euler((_brx, _bry, _brz), "XYZ")
        self.parts.append(body)
        self.body_scale = body_scale

        head_scale = self.body_scale * random_variance(
            self._mesh("HEAD_SCALE_REL"), self._mesh("HEAD_SCALE_VARIANCE"), self.rng
        )
        hx = float(self.body_scale * self._mesh("HEAD_X_ALONG"))
        hz = float(self._mesh("HEAD_CENTER_Z"))
        rz = float(head_scale * self._mesh("HEAD_FLATTEN_Z"))
        self._zone_geom_head_center = Vector((hx, 0.0, hz))
        self._zone_geom_head_radii = Vector((head_scale, head_scale, rz))

        head = create_sphere(
            location=(hx, 0, hz),
            scale=(head_scale, head_scale, rz),
        )
        _hrx = math.radians(float(self.build_options.get("RIG_HEAD_ROT_X") or 0.0))
        _hry = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Y") or 0.0))
        _hrz = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Z") or 0.0))
        head.rotation_euler = Euler((_hrx, _hry, _hrz), "XYZ")
        self.parts.append(head)
        self.head_scale = head_scale

        pe = int(self.build_options.get("peripheral_eyes", 0))
        self._peripheral_eyes = max(0, min(int(self._mesh("PERIPHERAL_EYES_MAX")), pe))
        eye_scale = self.head_scale * self._mesh("EYE_SCALE_HEAD_RATIO")
        eye_shape = str(self.build_options.get("eye_shape", "circle"))
        pupil_enabled = bool(self.build_options.get("pupil_enabled", False))
        pupil_shape = str(self.build_options.get("pupil_shape", "dot"))
        pupil_scale = eye_scale * 0.35
        for i in range(self._peripheral_eyes):
            if self._peripheral_eyes == 1:
                dy, dz = self._mesh("EYE_ONE_DY"), self._mesh("EYE_ONE_DZ")
            elif self._peripheral_eyes == 2:
                dy = self.body_scale * self._mesh("EYE_TWO_DY_SCALE") * (1 if i == 0 else -1)
                dz = self._mesh("EYE_TWO_DZ")
            else:
                ang = (i / self._mesh("PERIPHERAL_EYE_ANGLE_DIVISOR")) * math.pi - float(self._mesh("EYE_RING_PHASE"))
                dy = self.body_scale * self._mesh("EYE_RING_DY_SCALE") * math.cos(ang)
                dz = self._mesh("EYE_RING_DZ_BASE") + self._mesh("EYE_RING_DZ_SIN_SCALE") * math.sin(
                    ang + self._mesh("EYE_RING_ANGLE_OFFSET")
                )
            eye_loc_x = float(-self.body_scale * self._mesh("EYE_BACK_X"))
            eye_loc_y = float(dy)
            eye_loc_z = float(self._mesh("EYE_BASE_Z") + dz)
            eye_location = (eye_loc_x, eye_loc_y, eye_loc_z)
            eye = create_eye_mesh(eye_shape, eye_location, eye_scale)
            self.parts.append(eye)
            if pupil_enabled:
                pupil_center = (eye_loc_x + eye_scale + eye_scale * 0.05, eye_loc_y, eye_loc_z)
                self.parts.append(create_pupil_mesh(pupil_shape, pupil_center, pupil_scale))

        self._pupil_enabled = pupil_enabled

        for side in [-1, 1]:
            claw_length = random_variance(self._mesh("CLAW_LENGTH_BASE"), self._mesh("CLAW_LENGTH_VARIANCE"), self.rng)
            claw = create_cylinder(
                location=(
                    self.body_scale * self._mesh("CLAW_X"),
                    side * self.body_scale * self._mesh("CLAW_Y_SPREAD"),
                    self._mesh("CLAW_Z"),
                ),
                scale=(self._mesh("CLAW_RADIUS"), self._mesh("CLAW_RADIUS"), claw_length),
                vertices=CYLINDER_VERTICES_HEX,
            )
            self.parts.append(claw)

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

        # Mouth extra (MTE-7)
        mouth_enabled = bool(self.build_options.get("mouth_enabled", False))
        if mouth_enabled:
            mouth_shape = str(self.build_options.get("mouth_shape") or "smile")
            mouth_location = self._zone_geom_head_center + Vector(
                (self._zone_geom_head_radii.x, 0.0, 0.0)
            )
            self.parts.append(
                create_mouth_mesh(mouth_shape, tuple(mouth_location), self._zone_geom_head_radii.x)
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

    def apply_themed_materials(self):
        enemy_mats = self._themed_slot_materials_for("claw_crawler")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        eye_mat = enemy_mats["extra"]
        claw_material = enemy_mats["extra"]
        limb_material = enemy_mats["limbs"]
        pupil_enabled = getattr(self, "_pupil_enabled", False)
        part_index = 2
        for _ in range(self._peripheral_eyes):
            apply_material_to_object(self.parts[part_index], eye_mat)
            part_index += 1
            if pupil_enabled:
                apply_material_to_object(self.parts[part_index], enemy_mats["head"])
                part_index += 1
        for _ in range(int(self._mesh("CLAW_COUNT"))):
            apply_material_to_object(self.parts[part_index], claw_material)
            part_index += 1
        for _ in range(int(self._mesh("LEG_COUNT"))):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

        append_animated_enemy_zone_extras(self)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
