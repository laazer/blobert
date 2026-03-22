"""
Wall level objects: solid and crenellated (battlemented) variants
"""

from ..core.blender_utils import create_box, random_variance
from .base_level_object import BaseLevelObject
from .level_materials import create_solid_material, STONE_GREY, WALL_DARK


def _apply_single_material(parts, material_name: str, color):
    from ..materials.material_system import apply_material_to_object
    material = create_solid_material(material_name, color)
    for part in parts:
        apply_material_to_object(part, material)


class SolidWall(BaseLevelObject):
    """A plain rectangular stone wall segment."""

    NOMINAL_WIDTH = 4.0
    HEIGHT = 3.0
    THICKNESS = 0.4
    SIZE_VARIANCE = 0.2

    def create_structure(self):
        width = random_variance(self.NOMINAL_WIDTH, self.SIZE_VARIANCE, self.rng)

        wall = create_box(location=(0, 0, 0), scale=(width, self.THICKNESS, self.HEIGHT))
        self.parts.append(wall)

        self.width = width

    def apply_materials(self):
        _apply_single_material(self.parts, "solid_wall", STONE_GREY)

    def get_object_metadata(self):
        return {"width": round(self.width, 3), "height": self.HEIGHT}


class CrenellatedWall(BaseLevelObject):
    """A wall with battlements (merlons) along the top edge.

    The wall body is one box. Merlons are evenly spaced smaller boxes
    placed on top, with gaps between them. Every other position is a
    gap (crenel) — the open space that defenders shoot through.
    """

    NOMINAL_WIDTH = 5.0
    WALL_HEIGHT = 2.5
    THICKNESS = 0.5
    MERLON_HEIGHT = 0.6
    MERLON_DEPTH_RATIO = 0.9  # merlons fill this fraction of the wall thickness
    MERLON_COUNT = 4           # number of solid merlons (gaps = merlons - 1)
    SIZE_VARIANCE = 0.15

    def create_structure(self):
        width = random_variance(self.NOMINAL_WIDTH, self.SIZE_VARIANCE, self.rng)

        # Wall body — centered at origin
        wall_body = create_box(
            location=(0, 0, 0),
            scale=(width, self.THICKNESS, self.WALL_HEIGHT),
        )
        self.parts.append(wall_body)

        self._build_merlons(width)
        self.width = width

    def _build_merlons(self, wall_width: float):
        """Place evenly-spaced merlon boxes along the top of the wall."""
        merlon_width = wall_width / (2 * self.MERLON_COUNT - 1)
        merlon_thickness = self.THICKNESS * self.MERLON_DEPTH_RATIO
        merlon_z = self.WALL_HEIGHT / 2 + self.MERLON_HEIGHT / 2

        for index in range(self.MERLON_COUNT):
            # Alternate merlon / gap — merlons are at even indices
            x = -wall_width / 2 + merlon_width / 2 + index * 2 * merlon_width
            merlon = create_box(
                location=(x, 0, merlon_z),
                scale=(merlon_width, merlon_thickness, self.MERLON_HEIGHT),
            )
            self.parts.append(merlon)

    def apply_materials(self):
        _apply_single_material(self.parts, "crenellated_wall", WALL_DARK)

    def get_object_metadata(self):
        return {
            "width": round(self.width, 3),
            "wall_height": self.WALL_HEIGHT,
            "merlon_count": self.MERLON_COUNT,
        }
