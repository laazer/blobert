"""Minimal 3-bone blob rig (slug-style root / body / head)."""

from __future__ import annotations

from mathutils import Vector

from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel


class BlobSimpleRig(SimpleRigModel):
    """Minimal 3-bone blob (slug-style root / body / head)."""

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * 0.3)), None),
                "body": (Vector((0, 0, h * 0.3)), Vector((0, 0, h * 0.8)), "root"),
                "head": (Vector((0, 0, h * 0.8)), Vector((0, 0, h * 1.2)), "body"),
            }
        )
