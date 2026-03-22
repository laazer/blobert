"""Animation system for procedural enemies"""

from .animation_system import create_all_animations, create_simple_armature
from .armature_builders import create_quadruped_armature, create_blob_armature, create_humanoid_armature
from .keyframe_system import set_bone_keyframe
from .body_types import (
    BaseBodyType, BlobBodyType, 
    QuadrupedBodyType, HumanoidBodyType,
    BodyTypeFactory
)

__all__ = [
    'create_all_animations',
    'create_simple_armature', 
    'create_quadruped_armature',
    'create_blob_armature',
    'create_humanoid_armature',
    'set_bone_keyframe',
    'BaseBodyType',
    'BlobBodyType', 
    'QuadrupedBodyType',
    'HumanoidBodyType',
    'BodyTypeFactory'
]