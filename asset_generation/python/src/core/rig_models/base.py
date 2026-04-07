"""Shared base for preset rig layouts (class-level scale, no per-call size args)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..rig_types import RigDefinition


class SimpleRigModel(ABC):
    """Bone layout template. Each concrete enemy class sets ``body_height``; ``rig_definition`` reads ``self.body_height``."""

    def _rig_ratio(self, name: str) -> float:
        """Resolve ``RIG_*`` ClassVars; use ``_mesh`` when mixed with ``BaseAnimatedModel`` (``build_options['mesh']``)."""
        mesh_fn = getattr(self, "_mesh", None)
        if callable(mesh_fn):
            return float(mesh_fn(name))
        return float(getattr(type(self), name))

    @abstractmethod
    def rig_definition(self) -> RigDefinition:
        """Bone layout for this rig preset at ``self.body_height`` (from the concrete enemy class)."""
