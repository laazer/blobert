"""7-bone humanoid rig (imp, carapace husk, examples)."""

from __future__ import annotations

from mathutils import Vector

from ...utils.procedural_constants import HumanoidRigLayout
from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel


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
