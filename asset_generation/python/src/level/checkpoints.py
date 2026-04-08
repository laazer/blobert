"""
Checkpoint level objects — save points and level transitions
"""

from ..core.blender_utils import create_box, create_cylinder, random_variance
from ..materials.material_system import apply_material_to_object
from .base_level_object import BaseLevelObject
from .level_materials import (
    CHECKPOINT_BEAM,
    CHECKPOINT_STONE,
    create_emissive_material,
    create_solid_material,
)


class Checkpoint(BaseLevelObject):
    """A gateway checkpoint formed by two stone pillars with a glowing energy beam.

    The beam is an emissive gold box spanning the gap between pillar tops.
    In the game engine, the beam activates (brightens or changes color) when
    the player passes through, marking the checkpoint as reached.
    """

    PILLAR_RADIUS = 0.2
    PILLAR_HEIGHT = 3.0
    GATE_WIDTH = 2.0         # gap between pillar centres
    BEAM_HEIGHT = 0.15
    BEAM_DEPTH = 0.15
    HEIGHT_VARIANCE = 0.15

    def create_structure(self):
        pillar_height = random_variance(self.PILLAR_HEIGHT, self.HEIGHT_VARIANCE, self.rng)
        half_gap = self.GATE_WIDTH / 2

        left_pillar = create_cylinder(
            location=(-half_gap, 0, 0),
            scale=(self.PILLAR_RADIUS, self.PILLAR_RADIUS, pillar_height / 2),
            vertices=8,
            depth=2.0,
        )
        self.parts.append(left_pillar)

        right_pillar = create_cylinder(
            location=(half_gap, 0, 0),
            scale=(self.PILLAR_RADIUS, self.PILLAR_RADIUS, pillar_height / 2),
            vertices=8,
            depth=2.0,
        )
        self.parts.append(right_pillar)

        beam_z = pillar_height / 2
        beam = create_box(
            location=(0, 0, beam_z),
            scale=(self.GATE_WIDTH, self.BEAM_DEPTH, self.BEAM_HEIGHT),
        )
        self.parts.append(beam)

        self.pillar_height = pillar_height

    def apply_materials(self):
        pillar_material = create_solid_material("checkpoint_pillar", CHECKPOINT_STONE)
        beam_material = create_emissive_material(
            "checkpoint_beam", CHECKPOINT_BEAM, emission_strength=4.0
        )

        apply_material_to_object(self.parts[0], pillar_material)  # left pillar
        apply_material_to_object(self.parts[1], pillar_material)  # right pillar
        apply_material_to_object(self.parts[2], beam_material)    # beam

    def get_object_metadata(self):
        return {
            "gate_width": self.GATE_WIDTH,
            "pillar_height": round(self.pillar_height, 3),
        }
