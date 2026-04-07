"""Minimal 3-bone blob rig (slug-style root / body / head)."""

from __future__ import annotations

from typing import ClassVar, Final

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

    RIG_ROOT_TAIL_Z: ClassVar[float] = BlobRigLayout.ROOT_TAIL_Z
    RIG_BODY_END_Z: ClassVar[float] = BlobRigLayout.BODY_END_Z
    RIG_HEAD_END_Z: ClassVar[float] = BlobRigLayout.HEAD_END_Z

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        b = self._rig_ratio
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * b("RIG_ROOT_TAIL_Z"))), None),
                "body": (Vector((0, 0, h * b("RIG_ROOT_TAIL_Z"))), Vector((0, 0, h * b("RIG_BODY_END_Z"))), "root"),
                "head": (Vector((0, 0, h * b("RIG_BODY_END_Z"))), Vector((0, 0, h * b("RIG_HEAD_END_Z"))), "body"),
            }
        )
