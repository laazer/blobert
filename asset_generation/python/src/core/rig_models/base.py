"""Shared base for preset rig layouts (class-level scale, no per-call size args)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..rig_types import RigDefinition


class SimpleRigModel(ABC):
    """Bone layout template. Each concrete enemy class sets ``body_height``; ``rig_definition`` reads ``self.body_height``."""

    @abstractmethod
    def rig_definition(self) -> RigDefinition:
        """Bone layout for this rig preset at ``self.body_height`` (from the concrete enemy class)."""
