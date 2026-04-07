"""Animation system for procedural enemies.

Import ``create_all_animations`` from ``animations.animation_system``;
body-type motion lives in ``body_families``.
"""

from .keyframe_system import set_bone_keyframe

__all__ = ["set_bone_keyframe"]
