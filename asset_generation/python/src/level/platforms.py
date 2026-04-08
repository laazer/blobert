"""
Platform level objects: flat, moving, and crumbling variants
"""

from ..core.blender_utils import create_box, random_variance
from .base_level_object import BaseLevelObject
from .level_materials import (
    CRUMBLE_BROWN,
    MOVING_BLUE,
    STONE_GREY,
    create_solid_material,
)


def _apply_single_material(parts, material_name: str, color):
    """Apply one material to every part in the list."""
    from ..materials.material_system import apply_material_to_object
    material = create_solid_material(material_name, color)
    for part in parts:
        apply_material_to_object(part, material)


class FlatPlatform(BaseLevelObject):
    """A simple rectangular stone platform."""

    NOMINAL_WIDTH = 4.0
    NOMINAL_DEPTH = 2.0
    HEIGHT = 0.3
    SIZE_VARIANCE = 0.25

    def create_structure(self):
        width = random_variance(self.NOMINAL_WIDTH, self.SIZE_VARIANCE, self.rng)
        depth = random_variance(self.NOMINAL_DEPTH, self.SIZE_VARIANCE, self.rng)

        platform = create_box(location=(0, 0, 0), scale=(width, depth, self.HEIGHT))
        self.parts.append(platform)

        self.width = width
        self.depth = depth

    def apply_materials(self):
        _apply_single_material(self.parts, "platform_stone", STONE_GREY)

    def get_object_metadata(self):
        return {"width": round(self.width, 3), "depth": round(self.depth, 3)}


class MovingPlatform(BaseLevelObject):
    """A platform that moves back and forth along an axis in the game engine.

    The mesh is the same shape as FlatPlatform but uses a distinct blue material
    so level designers can identify it at a glance. Movement parameters are stored
    in the companion .object.json for the game engine to read.
    """

    NOMINAL_WIDTH = 3.0
    NOMINAL_DEPTH = 1.5
    HEIGHT = 0.3
    SIZE_VARIANCE = 0.2
    MOVEMENT_SPEED = 2.0
    MOVEMENT_RANGE = 4.0

    def create_structure(self):
        width = random_variance(self.NOMINAL_WIDTH, self.SIZE_VARIANCE, self.rng)
        depth = random_variance(self.NOMINAL_DEPTH, self.SIZE_VARIANCE, self.rng)

        platform = create_box(location=(0, 0, 0), scale=(width, depth, self.HEIGHT))
        self.parts.append(platform)

        self.width = width
        self.depth = depth

    def apply_materials(self):
        _apply_single_material(self.parts, "moving_platform", MOVING_BLUE)

    def get_object_metadata(self):
        return {
            "width": round(self.width, 3),
            "depth": round(self.depth, 3),
            "movement_speed": self.MOVEMENT_SPEED,
            "movement_range": self.MOVEMENT_RANGE,
            "movement_axis": "x",
        }


class CrumblingPlatform(BaseLevelObject):
    """A platform that breaks apart after the player stands on it.

    Uses a weathered brown material to telegraph fragility. The crumble_delay
    is exported to the companion JSON so the game engine can drive the timer.
    """

    NOMINAL_WIDTH = 3.0
    NOMINAL_DEPTH = 1.8
    HEIGHT = 0.25
    SIZE_VARIANCE = 0.2
    CRUMBLE_DELAY_SECONDS = 1.5

    def create_structure(self):
        width = random_variance(self.NOMINAL_WIDTH, self.SIZE_VARIANCE, self.rng)
        depth = random_variance(self.NOMINAL_DEPTH, self.SIZE_VARIANCE, self.rng)

        platform = create_box(location=(0, 0, 0), scale=(width, depth, self.HEIGHT))
        self.parts.append(platform)

        self.width = width
        self.depth = depth

    def apply_materials(self):
        _apply_single_material(self.parts, "crumbling_platform", CRUMBLE_BROWN)

    def get_object_metadata(self):
        return {
            "width": round(self.width, 3),
            "depth": round(self.depth, 3),
            "crumble_delay_seconds": self.CRUMBLE_DELAY_SECONDS,
        }
