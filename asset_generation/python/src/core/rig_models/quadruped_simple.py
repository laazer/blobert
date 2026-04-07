"""9-bone quadruped rig (spider, claw crawler, example spider)."""

from __future__ import annotations

from typing import ClassVar, Final

from mathutils import Vector

from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel

# --- Mesh helpers (quadruped family) ---
CYLINDER_VERTICES_HEX: Final[int] = 6
QUADRUPED_LEG_THICKNESS: Final[float] = 0.08


class QuadrupedRigLayout:
    """Bone positions as fractions of ``body_height``."""

    ROOT_TAIL_Z: Final[float] = 0.2
    SPINE_FORWARD_X: Final[float] = 0.5
    SPINE_UPPER_Z: Final[float] = 0.4
    HEAD_FORWARD_X: Final[float] = 0.8
    HEAD_UPPER_Z: Final[float] = 0.6
    LEG_CORNER_XY: Final[float] = 0.3
    LEG_MID_Y: Final[float] = 0.4
    LEG_REAR_X: Final[float] = 0.2


class QuadrupedSimpleRig(SimpleRigModel):
    """9-bone quadruped layout (spider, claw crawler, example spider)."""

    RIG_ROOT_TAIL_Z: ClassVar[float] = QuadrupedRigLayout.ROOT_TAIL_Z
    RIG_SPINE_FORWARD_X: ClassVar[float] = QuadrupedRigLayout.SPINE_FORWARD_X
    RIG_SPINE_UPPER_Z: ClassVar[float] = QuadrupedRigLayout.SPINE_UPPER_Z
    RIG_HEAD_FORWARD_X: ClassVar[float] = QuadrupedRigLayout.HEAD_FORWARD_X
    RIG_HEAD_UPPER_Z: ClassVar[float] = QuadrupedRigLayout.HEAD_UPPER_Z
    RIG_LEG_CORNER_XY: ClassVar[float] = QuadrupedRigLayout.LEG_CORNER_XY
    RIG_LEG_MID_Y: ClassVar[float] = QuadrupedRigLayout.LEG_MID_Y
    RIG_LEG_REAR_X: ClassVar[float] = QuadrupedRigLayout.LEG_REAR_X

    def rig_definition(self) -> RigDefinition:
        s = self.body_height
        q = self._rig_ratio
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, s * q("RIG_ROOT_TAIL_Z"))), None),
                "spine": (
                    Vector((0, 0, s * q("RIG_ROOT_TAIL_Z"))),
                    Vector((s * q("RIG_SPINE_FORWARD_X"), 0, s * q("RIG_SPINE_UPPER_Z"))),
                    "root",
                ),
                "head": (
                    Vector((s * q("RIG_SPINE_FORWARD_X"), 0, s * q("RIG_SPINE_UPPER_Z"))),
                    Vector((s * q("RIG_HEAD_FORWARD_X"), 0, s * q("RIG_HEAD_UPPER_Z"))),
                    "spine",
                ),
                "leg_fl": (
                    Vector((s * q("RIG_LEG_CORNER_XY"), s * q("RIG_LEG_CORNER_XY"), s * q("RIG_LEG_CORNER_XY"))),
                    Vector((s * q("RIG_LEG_CORNER_XY"), s * q("RIG_LEG_CORNER_XY"), 0)),
                    "spine",
                ),
                "leg_fr": (
                    Vector((s * q("RIG_LEG_CORNER_XY"), -s * q("RIG_LEG_CORNER_XY"), s * q("RIG_LEG_CORNER_XY"))),
                    Vector((s * q("RIG_LEG_CORNER_XY"), -s * q("RIG_LEG_CORNER_XY"), 0)),
                    "spine",
                ),
                "leg_ml": (
                    Vector((0, s * q("RIG_LEG_MID_Y"), s * q("RIG_LEG_CORNER_XY"))),
                    Vector((0, s * q("RIG_LEG_MID_Y"), 0)),
                    "spine",
                ),
                "leg_mr": (
                    Vector((0, -s * q("RIG_LEG_MID_Y"), s * q("RIG_LEG_CORNER_XY"))),
                    Vector((0, -s * q("RIG_LEG_MID_Y"), 0)),
                    "spine",
                ),
                "leg_bl": (
                    Vector((-s * q("RIG_LEG_REAR_X"), s * q("RIG_LEG_CORNER_XY"), s * q("RIG_LEG_CORNER_XY"))),
                    Vector((-s * q("RIG_LEG_REAR_X"), s * q("RIG_LEG_CORNER_XY"), 0)),
                    "root",
                ),
                "leg_br": (
                    Vector((-s * q("RIG_LEG_REAR_X"), -s * q("RIG_LEG_CORNER_XY"), s * q("RIG_LEG_CORNER_XY"))),
                    Vector((-s * q("RIG_LEG_REAR_X"), -s * q("RIG_LEG_CORNER_XY"), 0)),
                    "root",
                ),
            }
        )
