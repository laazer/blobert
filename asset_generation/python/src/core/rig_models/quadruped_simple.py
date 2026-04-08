"""9-bone quadruped rig (spider, claw crawler, example spider)."""

from __future__ import annotations

import math
from typing import ClassVar, Final

from mathutils import Vector

from ..rig_types import BoneSpec, RigDefinition, rig_from_bone_map
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
    SPIDER_LEG_COUNT: ClassVar[int] = 0
    SPIDER_LEG_SEGMENTS: ClassVar[int] = 1

    def rig_definition(self) -> RigDefinition:
        s = self.body_height
        q = self._rig_ratio
        spider_legs = int(getattr(type(self), "SPIDER_LEG_COUNT", 0))
        spider_segments = max(1, min(3, int(getattr(type(self), "SPIDER_LEG_SEGMENTS", 1))))
        if spider_legs >= 8:
            torso: list[BoneSpec] = [
                BoneSpec("root", Vector((0, 0, 0)), Vector((0, 0, s * q("RIG_ROOT_TAIL_Z"))), None),
                BoneSpec(
                    "spine",
                    Vector((0, 0, s * q("RIG_ROOT_TAIL_Z"))),
                    Vector((s * q("RIG_SPINE_FORWARD_X"), 0, s * q("RIG_SPINE_UPPER_Z"))),
                    "root",
                ),
                BoneSpec(
                    "head",
                    Vector((s * q("RIG_SPINE_FORWARD_X"), 0, s * q("RIG_SPINE_UPPER_Z"))),
                    Vector((s * q("RIG_HEAD_FORWARD_X"), 0, s * q("RIG_HEAD_UPPER_Z"))),
                    "spine",
                ),
            ]
            bones = list(torso)
            radius = s * q("RIG_LEG_CORNER_XY")
            z_top = s * q("RIG_LEG_CORNER_XY")
            z_mid = z_top * 0.45
            for i in range(8):
                angle = (2.0 * 3.141592653589793 * i) / 8.0
                cx = radius * float(math.cos(angle))
                cy = radius * float(math.sin(angle))
                base = f"leg_{i}"
                parent = "spine" if i < 4 else "root"
                points = [Vector((cx, cy, z_top))]
                if spider_segments >= 2:
                    points.append(Vector((cx * 1.35, cy * 1.35, z_mid)))
                if spider_segments >= 3:
                    points.append(Vector((cx * 1.75, cy * 1.75, 0)))
                for seg in range(spider_segments):
                    name = base if seg == 0 else f"{base}_{seg}"
                    p0 = points[seg]
                    p1 = points[min(seg + 1, len(points) - 1)]
                    seg_parent = parent if seg == 0 else (base if seg == 1 else f"{base}_{seg-1}")
                    bones.append(BoneSpec(name=name, head=p0, tail=p1, parent_name=seg_parent))
            return RigDefinition(bones=tuple(bones))
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
