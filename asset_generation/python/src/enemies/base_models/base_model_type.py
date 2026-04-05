"""
Abstract base for procedural enemy body archetypes.
"""

import math
from abc import ABC, abstractmethod

from ...materials.material_system import apply_material_to_object, get_enemy_materials


def _validate_scale(scale: float) -> float:
    s = float(scale)
    if not math.isfinite(s) or s <= 0:
        raise ValueError(f"scale must be finite and strictly positive, got {scale!r}")
    return s


class BaseModelType(ABC):
    """Base class for enemy model types"""

    def __init__(self, name, materials, rng, scale: float = 1.0):
        """Initialize model state.

        ``scale`` is a uniform multiplier for procedural body geometry (locations and
        primitive ``scale`` kwargs). Default ``1.0`` preserves legacy dimensions.
        """
        self.name = name
        self.materials = materials
        self.rng = rng
        self.scale = _validate_scale(scale)
        self.parts = []

    def _scaled_location(self, xyz: tuple) -> tuple:
        """Uniform world scale for primitive ``location``; identity at ``scale == 1.0``."""
        if self.scale == 1.0:
            return xyz
        s = self.scale
        return (xyz[0] * s, xyz[1] * s, xyz[2] * s)

    def _scaled_primitive_extent(self, xyz: tuple) -> tuple:
        """Uniform scale for primitive ``scale=`` kwargs; identity at ``scale == 1.0``."""
        if self.scale == 1.0:
            return xyz
        s = self.scale
        return (xyz[0] * s, xyz[1] * s, xyz[2] * s)

    @abstractmethod
    def create_geometry(self):
        """Create the enemy geometry - implemented by each model type"""
        pass

    def apply_themed_materials(self):
        """Apply materials based on enemy theme"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)

        if len(self.parts) >= 1:
            apply_material_to_object(self.parts[0], enemy_mats["body"])
        if len(self.parts) >= 2:
            apply_material_to_object(self.parts[1], enemy_mats["head"])

        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats["limbs"])
