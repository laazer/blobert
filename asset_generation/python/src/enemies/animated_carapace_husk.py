"""Animated carapace husk enemy builder."""

from typing import ClassVar

from mathutils import Vector

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models.humanoid_simple import (
    CYLINDER_VERTICES_HEX,
    CYLINDER_VERTICES_OCT,
    MESH_BODY_CENTER_Z_FACTOR,
    HumanoidSimpleRig,
)
from ..core.rig_models.limb_mesh import append_segmented_limb_mesh
from ..materials.material_system import apply_material_to_object, material_for_zone_part
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


def _humanoid_limb_part_kinds(
    n_seg: int,
    joint_vis: bool,
    end_shape: str,
) -> list[tuple[str, int | None]]:
    out: list[tuple[str, int | None]] = []
    n = max(1, min(8, int(n_seg)))
    for i in range(n):
        out.append(("cyl", i))
        if joint_vis and i < n - 1:
            out.append(("joint", i))
    if end_shape != "none":
        out.append(("end", None))
    return out


class AnimatedCarapaceHusk(HumanoidSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Heavy wide humanoid with thick arms and short legs"""

    body_height = 1.0

    BODY_HEIGHT_BASE: ClassVar[float] = 1.0
    BODY_HEIGHT_VARIANCE: ClassVar[float] = 0.15
    BODY_WIDTH_BASE: ClassVar[float] = 0.7
    BODY_WIDTH_VARIANCE: ClassVar[float] = 0.1
    HEAD_SCALE_BASE: ClassVar[float] = 1.2
    HEAD_SCALE_VARIANCE: ClassVar[float] = 0.1
    HEAD_ABOVE_BODY_SCALE: ClassVar[float] = 0.6
    HEAD_FLATTEN_Z: ClassVar[float] = 0.85
    ARM_LENGTH_BASE: ClassVar[float] = 0.5
    ARM_LENGTH_VARIANCE: ClassVar[float] = 0.1
    ARM_OUTWARD_HALF_LENGTH: ClassVar[float] = 0.5
    ARM_RADIUS: ClassVar[float] = 0.18
    ARM_HEIGHT_RATIO: ClassVar[float] = 0.75
    LEG_LENGTH_BASE: ClassVar[float] = 0.5
    LEG_LENGTH_VARIANCE: ClassVar[float] = 0.1
    LEG_X_SPREAD_RATIO: ClassVar[float] = 0.35
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

        head_scale = self.body_width * random_variance(
            self._mesh("HEAD_SCALE_BASE"), self._mesh("HEAD_SCALE_VARIANCE"), self.rng
        )
        head = create_sphere(
            location=(0, 0, self.body_height + head_scale * self._mesh("HEAD_ABOVE_BODY_SCALE")),
            scale=(head_scale, head_scale, head_scale * self._mesh("HEAD_FLATTEN_Z")),
        )
        self.parts.append(head)

        arm_length = random_variance(self._mesh("ARM_LENGTH_BASE"), self._mesh("ARM_LENGTH_VARIANCE"), self.rng)
        n_arm = max(1, min(8, int(self._mesh("ARM_SEGMENTS"))))
        n_leg = max(1, min(8, int(self._mesh("LEG_SEGMENTS"))))
        joint_vis = bool(self._mesh("LIMB_JOINT_VISUAL"))
        ball_scale = float(self._mesh("LIMB_JOINT_BALL_SCALE"))
        arm_end = self._mesh_str("ARM_END_SHAPE")
        leg_end = self._mesh_str("LEG_END_SHAPE")
        arm_r = float(self._mesh("ARM_RADIUS"))
        z_arm = self.body_height * self._mesh("ARM_HEIGHT_RATIO")
        end_r = arm_r

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
                end_scale=(end_r, end_r, end_r),
            )

        leg_length = random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng)
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

    def apply_themed_materials(self):
        enemy_mats = self._themed_slot_materials_for("carapace_husk")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        limb_material = enemy_mats["limbs"]
        features = self.build_options.get("features")

        n_arm = max(1, min(8, int(self._mesh("ARM_SEGMENTS"))))
        n_leg = max(1, min(8, int(self._mesh("LEG_SEGMENTS"))))
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
                    mat = limb_material
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

    def get_body_type(self):
        return EnemyBodyTypes.HUMANOID
