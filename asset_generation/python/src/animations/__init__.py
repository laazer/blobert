"""Animation system for procedural enemies"""

from .animation_system import create_all_animations, create_simple_armature
from .body_types import (
    BaseBodyType,
    BlobBodyType,
    BodyTypeFactory,
    HumanoidBodyType,
    QuadrupedBodyType,
)
from .keyframe_system import set_bone_keyframe

__all__ = [
    'create_all_animations',
    'create_simple_armature',
    'set_bone_keyframe',
    'BaseBodyType',
    'BlobBodyType', 
    'QuadrupedBodyType',
    'HumanoidBodyType',
    'BodyTypeFactory'
]