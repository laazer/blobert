"""
Abstract base for procedural enemy body archetypes.
"""

from abc import ABC, abstractmethod

from ...materials.material_system import apply_material_to_object, get_enemy_materials


class BaseModelType(ABC):
    """Base class for enemy model types"""

    def __init__(self, name, materials, rng):
        self.name = name
        self.materials = materials
        self.rng = rng
        self.parts = []

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
