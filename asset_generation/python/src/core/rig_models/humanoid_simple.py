"""7-bone humanoid rig (imp, carapace husk, examples)."""

from __future__ import annotations

import math
from typing import ClassVar, Final

from mathutils import Vector

from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel

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
    """7-bone humanoid layout (imp, carapace husk, examples)."""

    RIG_ROOT_TAIL_Z: ClassVar[float] = HumanoidRigLayout.ROOT_TAIL_Z
    RIG_SPINE_TOP_Z: ClassVar[float] = HumanoidRigLayout.SPINE_TOP_Z
    RIG_HEAD_TOP_Z: ClassVar[float] = HumanoidRigLayout.HEAD_TOP_Z
    RIG_ARM_SHOULDER_Y: ClassVar[float] = HumanoidRigLayout.ARM_SHOULDER_Y
    RIG_ARM_OUTER_Y: ClassVar[float] = HumanoidRigLayout.ARM_OUTER_Y
    RIG_ARM_UPPER_Z: ClassVar[float] = HumanoidRigLayout.ARM_UPPER_Z
    RIG_ARM_LOWER_Z: ClassVar[float] = HumanoidRigLayout.ARM_LOWER_Z
    RIG_LEG_INNER_Y: ClassVar[float] = HumanoidRigLayout.LEG_INNER_Y
    RIG_LEG_UPPER_Z: ClassVar[float] = HumanoidRigLayout.LEG_UPPER_Z

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        r = self._rig_ratio
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * r("RIG_ROOT_TAIL_Z"))), None),
                "spine": (Vector((0, 0, h * r("RIG_ROOT_TAIL_Z"))), Vector((0, 0, h * r("RIG_SPINE_TOP_Z"))), "root"),
                "head": (Vector((0, 0, h * r("RIG_SPINE_TOP_Z"))), Vector((0, 0, h * r("RIG_HEAD_TOP_Z"))), "spine"),
                "arm_l": (
                    Vector((0, h * r("RIG_ARM_SHOULDER_Y"), h * r("RIG_ARM_UPPER_Z"))),
                    Vector((0, h * r("RIG_ARM_OUTER_Y"), h * r("RIG_ARM_LOWER_Z"))),
                    "spine",
                ),
                "arm_r": (
                    Vector((0, -h * r("RIG_ARM_SHOULDER_Y"), h * r("RIG_ARM_UPPER_Z"))),
                    Vector((0, -h * r("RIG_ARM_OUTER_Y"), h * r("RIG_ARM_LOWER_Z"))),
                    "spine",
                ),
                "leg_l": (
                    Vector((0, h * r("RIG_LEG_INNER_Y"), h * r("RIG_LEG_UPPER_Z"))),
                    Vector((0, h * r("RIG_LEG_INNER_Y"), 0)),
                    "root",
                ),
                "leg_r": (
                    Vector((0, -h * r("RIG_LEG_INNER_Y"), h * r("RIG_LEG_UPPER_Z"))),
                    Vector((0, -h * r("RIG_LEG_INNER_Y"), 0)),
                    "root",
                ),
            }
        )
