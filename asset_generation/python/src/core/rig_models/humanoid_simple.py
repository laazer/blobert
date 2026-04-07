"""7-bone humanoid rig (imp, carapace husk, examples)."""

from __future__ import annotations

from mathutils import Vector

from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel


class HumanoidSimpleRig(SimpleRigModel):
    """7-bone humanoid layout (imp, carapace husk, examples)."""

    def rig_definition(self) -> RigDefinition:
        h = self.body_height
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, h * 0.2)), None),
                "spine": (Vector((0, 0, h * 0.2)), Vector((0, 0, h * 0.7)), "root"),
                "head": (Vector((0, 0, h * 0.7)), Vector((0, 0, h * 1.0)), "spine"),
                "arm_l": (Vector((0, h * 0.2, h * 0.6)), Vector((0, h * 0.5, h * 0.3)), "spine"),
                "arm_r": (Vector((0, -h * 0.2, h * 0.6)), Vector((0, -h * 0.5, h * 0.3)), "spine"),
                "leg_l": (Vector((0, h * 0.1, h * 0.2)), Vector((0, h * 0.1, 0)), "root"),
                "leg_r": (Vector((0, -h * 0.1, h * 0.2)), Vector((0, -h * 0.1, 0)), "root"),
            }
        )
