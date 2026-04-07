"""Abstract animated enemy: typed rig + default armature creation."""

from __future__ import annotations

from abc import abstractmethod

from ..animations.keyframe_system import create_simple_armature
from ..core.rig_types import RigDefinition
from .base_enemy import BaseEnemy


class AnimatedEnemy(BaseEnemy):
    """Enemy with a RigDefinition-driven simple armature."""

    @abstractmethod
    def get_rig_definition(self) -> RigDefinition:
        """Bone layout for this enemy."""

    def create_armature(self):
        return create_simple_armature(self.name, self.get_rig_definition())
