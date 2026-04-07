"""9-bone quadruped rig (spider, claw crawler, example spider)."""

from __future__ import annotations

from typing import Final

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

    def rig_definition(self) -> RigDefinition:
        s = self.body_height
        q = QuadrupedRigLayout
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, s * q.ROOT_TAIL_Z)), None),
                "spine": (
                    Vector((0, 0, s * q.ROOT_TAIL_Z)),
                    Vector((s * q.SPINE_FORWARD_X, 0, s * q.SPINE_UPPER_Z)),
                    "root",
                ),
                "head": (
                    Vector((s * q.SPINE_FORWARD_X, 0, s * q.SPINE_UPPER_Z)),
                    Vector((s * q.HEAD_FORWARD_X, 0, s * q.HEAD_UPPER_Z)),
                    "spine",
                ),
                "leg_fl": (
                    Vector((s * q.LEG_CORNER_XY, s * q.LEG_CORNER_XY, s * q.LEG_CORNER_XY)),
                    Vector((s * q.LEG_CORNER_XY, s * q.LEG_CORNER_XY, 0)),
                    "spine",
                ),
                "leg_fr": (
                    Vector((s * q.LEG_CORNER_XY, -s * q.LEG_CORNER_XY, s * q.LEG_CORNER_XY)),
                    Vector((s * q.LEG_CORNER_XY, -s * q.LEG_CORNER_XY, 0)),
                    "spine",
                ),
                "leg_ml": (Vector((0, s * q.LEG_MID_Y, s * q.LEG_CORNER_XY)), Vector((0, s * q.LEG_MID_Y, 0)), "spine"),
                "leg_mr": (Vector((0, -s * q.LEG_MID_Y, s * q.LEG_CORNER_XY)), Vector((0, -s * q.LEG_MID_Y, 0)), "spine"),
                "leg_bl": (
                    Vector((-s * q.LEG_REAR_X, s * q.LEG_CORNER_XY, s * q.LEG_CORNER_XY)),
                    Vector((-s * q.LEG_REAR_X, s * q.LEG_CORNER_XY, 0)),
                    "root",
                ),
                "leg_br": (
                    Vector((-s * q.LEG_REAR_X, -s * q.LEG_CORNER_XY, s * q.LEG_CORNER_XY)),
                    Vector((-s * q.LEG_REAR_X, -s * q.LEG_CORNER_XY, 0)),
                    "root",
                ),
            }
        )
