"""9-bone quadruped rig (spider, claw crawler, example spider)."""

from __future__ import annotations

from mathutils import Vector

from ..rig_types import RigDefinition, rig_from_bone_map
from .base import SimpleRigModel


class QuadrupedSimpleRig(SimpleRigModel):
    """9-bone quadruped layout (spider, claw crawler, example spider)."""

    def rig_definition(self) -> RigDefinition:
        s = self.body_height
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, s * 0.2)), None),
                "spine": (Vector((0, 0, s * 0.2)), Vector((s * 0.5, 0, s * 0.4)), "root"),
                "head": (Vector((s * 0.5, 0, s * 0.4)), Vector((s * 0.8, 0, s * 0.6)), "spine"),
                "leg_fl": (Vector((s * 0.3, s * 0.3, s * 0.3)), Vector((s * 0.3, s * 0.3, 0)), "spine"),
                "leg_fr": (Vector((s * 0.3, -s * 0.3, s * 0.3)), Vector((s * 0.3, -s * 0.3, 0)), "spine"),
                "leg_ml": (Vector((0, s * 0.4, s * 0.3)), Vector((0, s * 0.4, 0)), "spine"),
                "leg_mr": (Vector((0, -s * 0.4, s * 0.3)), Vector((0, -s * 0.4, 0)), "spine"),
                "leg_bl": (Vector((-s * 0.2, s * 0.3, s * 0.3)), Vector((-s * 0.2, s * 0.3, 0)), "root"),
                "leg_br": (Vector((-s * 0.2, -s * 0.3, s * 0.3)), Vector((-s * 0.2, -s * 0.3, 0)), "root"),
            }
        )
