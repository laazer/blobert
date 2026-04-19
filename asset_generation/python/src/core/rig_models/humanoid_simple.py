"""Humanoid rig (imp, carapace husk, examples): torso + multi-segment arms and legs."""

from __future__ import annotations

import math
from typing import ClassVar, Final

from mathutils import Vector

from ..rig_types import BoneSpec, RigDefinition
from .base import SimpleRigModel
from .limb_chain import limb_chain

# --- Mesh helpers (humanoid family) ---
CYLINDER_VERTICES_HEX: Final[int] = 6
CYLINDER_VERTICES_OCT: Final[int] = 8
CYLINDER_VERTICES_SQUARE: Final[int] = 4
EULER_Z_90: Final[float] = math.pi / 2
MESH_BODY_CENTER_Z_FACTOR: Final[float] = 0.5  # e.g. torso cylinder at z = height * this


class HumanoidRigLayout:
    """Bone positions as fractions of ``body_height``."""

    ROOT_TAIL_Z: Final[float] = 0.2
    SPINE_TOP_Z: Final[float] = 0.7
    HEAD_TOP_Z: Final[float] = 1.0
    ARM_SHOULDER_Y: Final[float] = 0.2
    ARM_OUTER_Y: Final[float] = 0.5
    ARM_UPPER_Z: Final[float] = 0.6
    ARM_LOWER_Z: Final[float] = 0.3
    LEG_INNER_Y: Final[float] = 0.1
    LEG_UPPER_Z: Final[float] = 0.2


class HumanoidSimpleRig(SimpleRigModel):
    """Humanoid layout: root, spine, head, optional multi-segment arms and legs."""

    RIG_ROOT_TAIL_Z: ClassVar[float] = HumanoidRigLayout.ROOT_TAIL_Z
    RIG_SPINE_TOP_Z: ClassVar[float] = HumanoidRigLayout.SPINE_TOP_Z
    RIG_HEAD_TOP_Z: ClassVar[float] = HumanoidRigLayout.HEAD_TOP_Z
    RIG_ARM_SHOULDER_Y: ClassVar[float] = HumanoidRigLayout.ARM_SHOULDER_Y
    RIG_ARM_OUTER_Y: ClassVar[float] = HumanoidRigLayout.ARM_OUTER_Y
    RIG_ARM_UPPER_Z: ClassVar[float] = HumanoidRigLayout.ARM_UPPER_Z
    RIG_ARM_LOWER_Z: ClassVar[float] = HumanoidRigLayout.ARM_LOWER_Z
    RIG_LEG_INNER_Y: ClassVar[float] = HumanoidRigLayout.LEG_INNER_Y
    RIG_LEG_UPPER_Z: ClassVar[float] = HumanoidRigLayout.LEG_UPPER_Z

    ARM_SEGMENTS: ClassVar[int] = 1
    LEG_SEGMENTS: ClassVar[int] = 1
    ARM_END_SHAPE: ClassVar[str] = "none"
    LEG_END_SHAPE: ClassVar[str] = "none"
    LIMB_JOINT_BALL_SCALE: ClassVar[float] = 1.4
    LIMB_JOINT_VISUAL: ClassVar[bool] = True

    def _segment_count(self, key: str) -> int:
        mesh_fn = getattr(self, "_mesh", None)
        if callable(mesh_fn):
            v = int(round(float(mesh_fn(key))))
        else:
            v = int(getattr(type(self), key, 1))
        v = max(1, min(8, v))
        if key == "LEG_SEGMENTS":
            from ...utils.body_type_presets import humanoid_leg_segment_count

            raw_opts = getattr(self, "build_options", None)
            opts = raw_opts if isinstance(raw_opts, dict) else None
            return humanoid_leg_segment_count(v, opts)
        return v

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        r = self._rig_ratio
        n_arm = self._segment_count("ARM_SEGMENTS")
        n_leg = self._segment_count("LEG_SEGMENTS")

        torso: list[BoneSpec] = [
            BoneSpec("root", Vector((0, 0, 0)), Vector((0, 0, h * r("RIG_ROOT_TAIL_Z"))), None),
            BoneSpec(
                "spine",
                Vector((0, 0, h * r("RIG_ROOT_TAIL_Z"))),
                Vector((0, 0, h * r("RIG_SPINE_TOP_Z"))),
                "root",
            ),
            BoneSpec(
                "head",
                Vector((0, 0, h * r("RIG_SPINE_TOP_Z"))),
                Vector((0, 0, h * r("RIG_HEAD_TOP_Z"))),
                "spine",
            ),
        ]
        arm_l = limb_chain(
            Vector((0, h * r("RIG_ARM_SHOULDER_Y"), h * r("RIG_ARM_UPPER_Z"))),
            Vector((0, h * r("RIG_ARM_OUTER_Y"), h * r("RIG_ARM_LOWER_Z"))),
            n_arm,
            "arm_l",
            "spine",
        )
        arm_r = limb_chain(
            Vector((0, -h * r("RIG_ARM_SHOULDER_Y"), h * r("RIG_ARM_UPPER_Z"))),
            Vector((0, -h * r("RIG_ARM_OUTER_Y"), h * r("RIG_ARM_LOWER_Z"))),
            n_arm,
            "arm_r",
            "spine",
        )
        leg_l = limb_chain(
            Vector((0, h * r("RIG_LEG_INNER_Y"), h * r("RIG_LEG_UPPER_Z"))),
            Vector((0, h * r("RIG_LEG_INNER_Y"), 0)),
            n_leg,
            "leg_l",
            "root",
        )
        leg_r = limb_chain(
            Vector((0, -h * r("RIG_LEG_INNER_Y"), h * r("RIG_LEG_UPPER_Z"))),
            Vector((0, -h * r("RIG_LEG_INNER_Y"), 0)),
            n_leg,
            "leg_r",
            "root",
        )
        all_bones = torso + arm_l + arm_r + leg_l + leg_r
        return RigDefinition(bones=tuple(all_bones))
