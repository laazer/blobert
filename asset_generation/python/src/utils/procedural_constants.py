"""Shared numeric literals for procedural rig layouts and animated enemy meshes."""

from __future__ import annotations

import math
from typing import Final

# --- Import pipeline (no concrete enemy class) ---
IMPORT_DEFAULT_BODY_HEIGHT: Final[float] = 1.0

# --- Mesh primitives (cylinders) ---
CYLINDER_VERTICES_HEX: Final[int] = 6
CYLINDER_VERTICES_OCT: Final[int] = 8
CYLINDER_VERTICES_SQUARE: Final[int] = 4

# --- Placement / rotation reused across builders ---
EULER_Z_90: Final[float] = math.pi / 2
MESH_BODY_CENTER_Z_FACTOR: Final[float] = 0.5  # e.g. cylinder at z = height * this

# --- Quadruped-style legs (spider + claw crawler thin legs) ---
QUADRUPED_LEG_THICKNESS: Final[float] = 0.08


class BlobRigLayout:
    """Bone Z extents as fractions of ``body_height`` (blob / spitter family)."""

    ROOT_TAIL_Z: Final[float] = 0.3
    BODY_END_Z: Final[float] = 0.8
    HEAD_END_Z: Final[float] = 1.2


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
