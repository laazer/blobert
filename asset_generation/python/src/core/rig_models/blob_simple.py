"""Minimal 3-bone blob rig (slug-style root / body / head)."""

from __future__ import annotations

from mathutils import Vector

from ...utils.procedural_constants import BlobRigLayout
from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel


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
