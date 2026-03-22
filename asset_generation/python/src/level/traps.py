"""
Trap level objects: spike and fire variants, with companion TrapData
"""

from ..core.blender_utils import create_box, create_cylinder, random_variance
from ..materials.material_system import apply_material_to_object
from .base_level_object import BaseLevelObject
from .level_object_data import TrapData, TrapType
from .level_materials import (
    create_solid_material,
    create_emissive_material,
    METAL_GREY,
    IRON_DARK,
    FIRE_ORANGE,
)


class SpikeTrap(BaseLevelObject):
    """A floor trap with a metal base plate and a grid of upward-pointing spikes.

    The base plate is flush with z=0. Spikes extend above it. In the game engine,
    spikes retract and extend on a timer driven by cooldown_seconds.
    """

    BASE_WIDTH = 2.0
    BASE_DEPTH = 2.0
    BASE_HEIGHT = 0.15
    SPIKE_RADIUS = 0.05
    SPIKE_HEIGHT = 0.7
    SPIKE_GRID_DIMENSION = 3   # NxN grid of spikes
    SPIKE_GRID_SPACING = 0.55  # distance between spike centres

    TRAP_DAMAGE = 25.0
    TRAP_TRIGGER_RADIUS = 1.2
    TRAP_COOLDOWN = 2.0

    def create_structure(self):
        base = create_box(
            location=(0, 0, 0),
            scale=(self.BASE_WIDTH, self.BASE_DEPTH, self.BASE_HEIGHT),
        )
        self.parts.append(base)
        self._base_parts_count = 1

        self._build_spike_grid()

    def _build_spike_grid(self):
        """Create an NxN grid of spike cylinders above the base plate."""
        base_top_z = self.BASE_HEIGHT / 2
        spike_center_z = base_top_z + self.SPIKE_HEIGHT / 2
        grid_n = self.SPIKE_GRID_DIMENSION
        half_span = (grid_n - 1) / 2 * self.SPIKE_GRID_SPACING

        for row in range(grid_n):
            for col in range(grid_n):
                x = -half_span + col * self.SPIKE_GRID_SPACING
                y = -half_span + row * self.SPIKE_GRID_SPACING
                spike = create_cylinder(
                    location=(x, y, spike_center_z),
                    scale=(self.SPIKE_RADIUS, self.SPIKE_RADIUS, self.SPIKE_HEIGHT / 2),
                    vertices=6,
                    depth=2.0,
                )
                self.parts.append(spike)

    def apply_materials(self):
        base_material = create_solid_material("spike_base", IRON_DARK)
        spike_material = create_solid_material("spike_metal", METAL_GREY)

        apply_material_to_object(self.parts[0], base_material)
        for spike_part in self.parts[1:]:
            apply_material_to_object(spike_part, spike_material)

    def get_trap_data(self):
        return [
            TrapData(
                name="spike_strike",
                trap_type=TrapType.SPIKE,
                damage_per_hit=self.TRAP_DAMAGE,
                trigger_radius=self.TRAP_TRIGGER_RADIUS,
                cooldown_seconds=self.TRAP_COOLDOWN,
                activation_delay_seconds=0.0,
                is_visible_when_inactive=True,
            )
        ]

    def get_object_metadata(self):
        return {
            "base_width": self.BASE_WIDTH,
            "base_depth": self.BASE_DEPTH,
            "spike_count": self.SPIKE_GRID_DIMENSION ** 2,
        }


class FireTrap(BaseLevelObject):
    """A wall-mounted fire trap with four directional nozzles.

    The body is a dark iron box. Each nozzle is a short cylinder extending
    outward from each face of the body, with an emissive orange tip to
    indicate active state. Fire shoots from the nozzles on a cooldown.
    """

    BODY_SIZE = 0.5
    NOZZLE_RADIUS = 0.08
    NOZZLE_LENGTH = 0.25
    NOZZLE_TIP_LENGTH = 0.1

    TRAP_DAMAGE = 15.0
    TRAP_TRIGGER_RADIUS = 1.8
    TRAP_COOLDOWN = 3.0
    TRAP_ACTIVATION_DELAY = 0.5

    # (x_offset, y_offset, rotation_euler_z) for each of the 4 side nozzles
    _NOZZLE_DIRECTIONS = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
    ]

    def create_structure(self):
        half = self.BODY_SIZE / 2
        body = create_box(
            location=(0, 0, 0),
            scale=(self.BODY_SIZE, self.BODY_SIZE, self.BODY_SIZE),
        )
        self.parts.append(body)
        self._nozzle_start_index = 1

        nozzle_origin = half + self.NOZZLE_LENGTH / 2
        tip_origin = half + self.NOZZLE_LENGTH + self.NOZZLE_TIP_LENGTH / 2

        for dx, dy in self._NOZZLE_DIRECTIONS:
            nozzle = create_cylinder(
                location=(dx * nozzle_origin, dy * nozzle_origin, 0),
                scale=(self.NOZZLE_RADIUS, self.NOZZLE_RADIUS, self.NOZZLE_LENGTH / 2),
                vertices=8,
                depth=2.0,
            )
            self.parts.append(nozzle)

            tip = create_cylinder(
                location=(dx * tip_origin, dy * tip_origin, 0),
                scale=(self.NOZZLE_RADIUS * 1.4, self.NOZZLE_RADIUS * 1.4, self.NOZZLE_TIP_LENGTH / 2),
                vertices=8,
                depth=2.0,
            )
            self.parts.append(tip)

    def apply_materials(self):
        body_material = create_solid_material("fire_trap_body", IRON_DARK)
        nozzle_material = create_solid_material("fire_trap_nozzle", METAL_GREY)
        tip_material = create_emissive_material("fire_trap_tip", FIRE_ORANGE, emission_strength=3.0)

        apply_material_to_object(self.parts[0], body_material)

        for index, part in enumerate(self.parts[1:]):
            if index % 2 == 0:
                apply_material_to_object(part, nozzle_material)
            else:
                apply_material_to_object(part, tip_material)

    def get_trap_data(self):
        return [
            TrapData(
                name="fire_burst",
                trap_type=TrapType.FIRE,
                damage_per_hit=self.TRAP_DAMAGE,
                trigger_radius=self.TRAP_TRIGGER_RADIUS,
                cooldown_seconds=self.TRAP_COOLDOWN,
                activation_delay_seconds=self.TRAP_ACTIVATION_DELAY,
                is_visible_when_inactive=True,
            )
        ]

    def get_object_metadata(self):
        return {
            "body_size": self.BODY_SIZE,
            "nozzle_count": len(self._NOZZLE_DIRECTIONS),
        }
