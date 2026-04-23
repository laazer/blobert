"""Animated ember imp enemy builder."""
from __future__ import annotations

import math
from typing import ClassVar

from mathutils import Euler, Vector

from ..core.blender_utils import (
    create_cylinder,
    create_mouth_mesh,
    create_sphere,
    create_tail_mesh,
    random_variance,
)
from ..core.rig_models.humanoid_simple import (
    CYLINDER_VERTICES_HEX,
    CYLINDER_VERTICES_OCT,
    MESH_BODY_CENTER_Z_FACTOR,
    HumanoidSimpleRig,
)
from ..core.rig_models.limb_mesh import append_segmented_limb_mesh
from ..materials.material_system import apply_material_to_object, material_for_zone_part
from ..utils.body_type_presets import humanoid_torso_leg_multipliers
from ..utils.config import EnemyBodyTypes
from .animated_enemy import UsesSimpleRigMixin
from .builder_template import AnimatedEnemyBuilderBase
from .zone_geometry_extras_attach import append_animated_enemy_zone_extras


def _humanoid_limb_part_kinds(
    n_seg: int,
    joint_vis: bool,
    end_shape: str,
) -> list[tuple[str, int | None]]:
    """Order matches ``append_segmented_limb_mesh`` + end cap (same length as ``_limb_part_count``)."""
    out: list[tuple[str, int | None]] = []
    n = max(1, min(8, int(n_seg)))
    for i in range(n):
        out.append(("cyl", i))
        if joint_vis and i < n - 1:
            out.append(("joint", i))
    if end_shape != "none":
        out.append(("end", None))
    return out


class AnimatedImp(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemyBuilderBase):
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

    ARM_END_SHAPE: ClassVar[str] = "sphere"

    def _build_body_mesh(self) -> None:
        hm, wm, _ = humanoid_torso_leg_multipliers(self.build_options)
        body_height = random_variance(self._mesh("BODY_HEIGHT_BASE"), self._mesh("BODY_HEIGHT_VARIANCE"), self.rng) * hm
        body_width = random_variance(self._mesh("BODY_WIDTH_BASE"), self._mesh("BODY_WIDTH_VARIANCE"), self.rng) * wm
        body = create_cylinder(
            location=(0, 0, body_height * MESH_BODY_CENTER_Z_FACTOR),
            scale=(body_width, body_width, body_height),
            vertices=CYLINDER_VERTICES_OCT,
        )
        _brx = math.radians(float(self.build_options.get("RIG_BODY_ROT_X") or 0.0))
        _bry = math.radians(float(self.build_options.get("RIG_BODY_ROT_Y") or 0.0))
        _brz = math.radians(float(self.build_options.get("RIG_BODY_ROT_Z") or 0.0))
        body.rotation_euler = Euler((_brx, _bry, _brz), "XYZ")
        self.parts.append(body)
        self.body_height = body_height
        self.body_width = body_width

        bz = float(body_height * MESH_BODY_CENTER_Z_FACTOR)
        self._zone_geom_body_center = Vector((0.0, 0.0, bz))
        self._zone_geom_body_radii = Vector((body_width, body_width, body_height))

        head_scale = self.body_width * self._mesh("HEAD_SCALE_WIDTH_RATIO")
        hz = float(self.body_height + head_scale * self._mesh("HEAD_ABOVE_BODY_SCALE"))
        self._zone_geom_head_center = Vector((0.0, 0.0, hz))
        self._zone_geom_head_radii = Vector((head_scale, head_scale, head_scale))

        head = create_sphere(
            location=(0, 0, hz),
            scale=(head_scale, head_scale, head_scale),
        )
        _hrx = math.radians(float(self.build_options.get("RIG_HEAD_ROT_X") or 0.0))
        _hry = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Y") or 0.0))
        _hrz = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Z") or 0.0))
        head.rotation_euler = Euler((_hrx, _hry, _hrz), "XYZ")
        self.parts.append(head)

    def _build_limbs(self) -> None:
        hm, wm, lm = humanoid_torso_leg_multipliers(self.build_options)
        arm_length = random_variance(self._mesh("ARM_LENGTH_BASE"), self._mesh("ARM_LENGTH_VARIANCE"), self.rng)
        n_arm = max(1, min(8, int(self._mesh("ARM_SEGMENTS"))))
        n_leg = self._segment_count("LEG_SEGMENTS")
        joint_vis = bool(self._mesh("LIMB_JOINT_VISUAL"))
        ball_scale = float(self._mesh("LIMB_JOINT_BALL_SCALE"))
        arm_end = self._mesh_str("ARM_END_SHAPE")
        leg_end = self._mesh_str("LEG_END_SHAPE")
        arm_r = float(self._mesh("ARM_RADIUS"))
        z_arm = self.body_height * self._mesh("ARM_HEIGHT_RATIO")
        hr = float(self._mesh("HAND_RADIUS"))

        for side in [-1, 1]:
            inner = Vector((side * self.body_width, 0.0, z_arm))
            outer = Vector((side * (self.body_width + arm_length), 0.0, z_arm))
            append_segmented_limb_mesh(
                self.parts,
                inner,
                outer,
                n_arm,
                arm_r,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=joint_vis,
                joint_ball_scale=ball_scale,
                end_shape=arm_end,
                end_scale=(hr, hr, hr),
            )

        leg_length = (
            random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng) * lm
        )
        for side in [-1, 1]:
            lx = side * self.body_width * self._mesh("LEG_X_SPREAD_RATIO")
            leg_top = Vector((lx, 0.0, leg_length))
            leg_foot = Vector((lx, 0.0, 0.0))
            append_segmented_limb_mesh(
                self.parts,
                leg_top,
                leg_foot,
                n_leg,
                arm_r,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=joint_vis,
                joint_ball_scale=ball_scale,
                end_shape=leg_end,
                end_scale=(arm_r, arm_r, arm_r),
            )

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

    def _apply_materials(self) -> None:
        enemy_mats = self._themed_slot_materials_for("imp")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        limb_material = enemy_mats["limbs"]
        hand_material = enemy_mats["extra"]
        features = self.build_options.get("features")

        n_arm = max(1, min(8, int(self._mesh("ARM_SEGMENTS"))))
        n_leg = self._segment_count("LEG_SEGMENTS")
        joint_vis = bool(self._mesh("LIMB_JOINT_VISUAL"))
        arm_end = self._mesh_str("ARM_END_SHAPE")
        leg_end = self._mesh_str("LEG_END_SHAPE")

        def _limb_part_count(n: int, end_shape: str) -> int:
            cyl = n
            joints = (n - 1) if joint_vis else 0
            end = 0 if end_shape == "none" else 1
            return cyl + joints + end

        i = 2
        lp = int(self._mesh("LIMB_PAIRS"))
        arm_kinds = _humanoid_limb_part_kinds(n_arm, joint_vis, arm_end)
        leg_kinds = _humanoid_limb_part_kinds(n_leg, joint_vis, leg_end)
        for arm_idx in range(lp):
            cnt = _limb_part_count(n_arm, arm_end)
            for j in range(cnt):
                kind, seg_i = arm_kinds[j]
                if kind == "cyl":
                    mat = material_for_zone_part("limbs", f"arm_{arm_idx}", enemy_mats, features)
                elif kind == "joint" and seg_i is not None:
                    mat = material_for_zone_part("joints", f"arm_{arm_idx}_j{seg_i}", enemy_mats, features)
                else:
                    mat = hand_material if (j == cnt - 1 and arm_end != "none") else limb_material
                apply_material_to_object(self.parts[i + j], mat)
            i += cnt
        for leg_idx in range(lp):
            cnt = _limb_part_count(n_leg, leg_end)
            for j in range(cnt):
                kind, seg_i = leg_kinds[j]
                if kind == "cyl":
                    mat = material_for_zone_part("limbs", f"leg_{leg_idx}", enemy_mats, features)
                elif kind == "joint" and seg_i is not None:
                    mat = material_for_zone_part("joints", f"leg_{leg_idx}_j{seg_i}", enemy_mats, features)
                else:
                    mat = limb_material
                apply_material_to_object(self.parts[i + j], mat)
            i += cnt

    def _add_zone_extras(self) -> None:
        append_animated_enemy_zone_extras(self)

    def build_mesh_parts(self) -> None:
        super().build_mesh_parts()

    def apply_themed_materials(self) -> None:
        super().apply_themed_materials()

    def get_body_type(self) -> EnemyBodyTypes:
        return EnemyBodyTypes.HUMANOID
