"""Minimal 3-bone blob rig (slug-style root / body / head)."""

from __future__ import annotations

from typing import Final

from mathutils import Vector

from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel

# --- Mesh helpers (blob / slug / spitter family) ---
CYLINDER_VERTICES_HEX: Final[int] = 6
MESH_BODY_CENTER_Z_FACTOR: Final[float] = 0.5  # e.g. body primitive centered on vertical extent


class BlobRigLayout:
    """Bone Z extents as fractions of ``body_height`` (blob / spitter family)."""

    ROOT_TAIL_Z: Final[float] = 0.3
    BODY_END_Z: Final[float] = 0.8
    HEAD_END_Z: Final[float] = 1.2


class BlobSimpleRig(SimpleRigModel):
    """Minimal 3-bone blob (slug-style root / body / head)."""

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        b = BlobRigLayout
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * b.ROOT_TAIL_Z)), None),
                "body": (Vector((0, 0, h * b.ROOT_TAIL_Z)), Vector((0, 0, h * b.BODY_END_Z)), "root"),
                "head": (Vector((0, 0, h * b.BODY_END_Z)), Vector((0, 0, h * b.HEAD_END_Z)), "body"),
            }
        )
