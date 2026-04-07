"""Factory mapping body-type id strings to motion classes."""

from __future__ import annotations

from .motion_base import BaseBodyType
from .motion_blob import BlobBodyType
from .motion_humanoid import HumanoidBodyType
from .motion_quadruped import QuadrupedBodyType


class BodyTypeFactory:
    """Factory for creating body type motion handler instances."""

    BODY_TYPES = {
        "blob": BlobBodyType,
        "slime": BlobBodyType,
        "quadruped": QuadrupedBodyType,
        "humanoid": HumanoidBodyType,
    }

    @classmethod
    def create_body_type(cls, body_type_name: str, armature, rng) -> BaseBodyType:
        body_class = cls.BODY_TYPES.get(body_type_name, BlobBodyType)
        return body_class(armature, rng)

    @classmethod
    def get_available_types(cls) -> list:
        return list(cls.BODY_TYPES.keys())
