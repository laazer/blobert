"""Preset RigDefinitions for imported meshes and shared body archetypes."""

from __future__ import annotations

from mathutils import Vector

from .rig_types import RigDefinition, rig_from_bone_map


def imported_blob_rig(scale: float) -> RigDefinition:
    s = scale
    return rig_from_bone_map(
        {
            "root": (Vector((0, 0, 0)), Vector((0, 0, s * 0.3)), None),
            "body": (Vector((0, 0, s * 0.3)), Vector((0, 0, s * 0.8)), "root"),
            "head": (Vector((0, 0, s * 0.8)), Vector((0, 0, s * 1.2)), "body"),
        }
    )


def imported_humanoid_rig(body_height: float) -> RigDefinition:
    h = body_height
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


def imported_quadruped_rig(body_scale: float) -> RigDefinition:
    s = body_scale
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
