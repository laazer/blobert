"""7-bone humanoid rig (imp, carapace husk, examples)."""

from __future__ import annotations

import math
from typing import Final

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

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        r = HumanoidRigLayout
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * r.ROOT_TAIL_Z)), None),
                "spine": (Vector((0, 0, h * r.ROOT_TAIL_Z)), Vector((0, 0, h * r.SPINE_TOP_Z)), "root"),
                "head": (Vector((0, 0, h * r.SPINE_TOP_Z)), Vector((0, 0, h * r.HEAD_TOP_Z)), "spine"),
                "arm_l": (
                    Vector((0, h * r.ARM_SHOULDER_Y, h * r.ARM_UPPER_Z)),
                    Vector((0, h * r.ARM_OUTER_Y, h * r.ARM_LOWER_Z)),
                    "spine",
                ),
                "arm_r": (
                    Vector((0, -h * r.ARM_SHOULDER_Y, h * r.ARM_UPPER_Z)),
                    Vector((0, -h * r.ARM_OUTER_Y, h * r.ARM_LOWER_Z)),
                    "spine",
                ),
                "leg_l": (Vector((0, h * r.LEG_INNER_Y, h * r.LEG_UPPER_Z)), Vector((0, h * r.LEG_INNER_Y, 0)), "root"),
                "leg_r": (Vector((0, -h * r.LEG_INNER_Y, h * r.LEG_UPPER_Z)), Vector((0, -h * r.LEG_INNER_Y, 0)), "root"),
            }
        )
