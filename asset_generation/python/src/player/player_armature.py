"""
Armature builder for the player slime character
"""

from mathutils import Vector

from ..animations.keyframe_system import create_simple_armature
from ..core.rig_types import rig_from_bone_map
from ..utils.config import PlayerBoneNames


def create_player_slime_armature(name: str = "player_slime") -> object:
    """Create the player slime armature.

    Bone layout (all positions are in world space at rest):
      root  — control bone at the base; driven by game engine movement
      body  — main deformer; squash/stretch keyframes live here
      eye_l — left eye, driven for blinks and look-direction squints
      eye_r — right eye (mirror of eye_l)
      arm_l — left arm nub, wiggles during idle and celebrate
      arm_r — right arm nub
    """
    bone_positions = {
        PlayerBoneNames.ROOT: (
            Vector((0.0, 0.0, 0.00)),
            Vector((0.0, 0.0, 0.15)),
            None,
        ),
        PlayerBoneNames.BODY: (
            Vector((0.0, 0.0, 0.15)),
            Vector((0.0, 0.0, 1.60)),
            PlayerBoneNames.ROOT,
        ),
        PlayerBoneNames.EYE_LEFT: (
            Vector((-0.34, 0.84, 1.05)),
            Vector((-0.34, 0.84, 1.28)),
            PlayerBoneNames.BODY,
        ),
        PlayerBoneNames.EYE_RIGHT: (
            Vector((0.34, 0.84, 1.05)),
            Vector((0.34, 0.84, 1.28)),
            PlayerBoneNames.BODY,
        ),
        PlayerBoneNames.ARM_LEFT: (
            Vector((-0.90, 0.0, 0.85)),
            Vector((-1.20, 0.0, 0.85)),
            PlayerBoneNames.BODY,
        ),
        PlayerBoneNames.ARM_RIGHT: (
            Vector((0.90, 0.0, 0.85)),
            Vector((1.20, 0.0, 0.85)),
            PlayerBoneNames.BODY,
        ),
    }

    return create_simple_armature(name, rig_from_bone_map(bone_positions))
