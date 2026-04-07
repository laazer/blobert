"""Backward compatibility: procedural body motion lives in ``body_families``."""

try:
    from body_families.factory import BodyTypeFactory
    from body_families.motion_base import BaseBodyType
    from body_families.motion_blob import BlobBodyType
    from body_families.motion_humanoid import HumanoidBodyType
    from body_families.motion_quadruped import QuadrupedBodyType
except ImportError:
    from src.body_families.factory import BodyTypeFactory
    from src.body_families.motion_base import BaseBodyType
    from src.body_families.motion_blob import BlobBodyType
    from src.body_families.motion_humanoid import HumanoidBodyType
    from src.body_families.motion_quadruped import QuadrupedBodyType

__all__ = [
    "BaseBodyType",
    "BlobBodyType",
    "BodyTypeFactory",
    "HumanoidBodyType",
    "QuadrupedBodyType",
]
