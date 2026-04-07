"""Animated claw crawler enemy builder."""

import math

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_types import RigDefinition, quadruped_simple_rig_definition
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy


class AnimatedClawCrawler(AnimatedEnemy):
    """Flat disc body with large front claws and quadruped movement"""

    def build_mesh_parts(self):
        body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(
            location=(0, 0, 0.2),
            scale=(body_scale, body_scale * random_variance(0.9, 0.1, self.rng), body_scale * 0.35),
        )
        self.parts.append(body)
        self.body_scale = body_scale

        head_scale = self.body_scale * random_variance(0.4, 0.1, self.rng)
        head = create_sphere(
            location=(self.body_scale * 1.1, 0, 0.25),
            scale=(head_scale, head_scale, head_scale * 0.7),
        )
        self.parts.append(head)
        self.head_scale = head_scale

        pe = int(self.build_options.get("peripheral_eyes", 0))
        self._peripheral_eyes = max(0, min(3, pe))
        eye_scale = self.head_scale * 0.12
        for i in range(self._peripheral_eyes):
            if self._peripheral_eyes == 1:
                dy, dz = 0.0, 0.18
            elif self._peripheral_eyes == 2:
                dy = self.body_scale * 0.38 * (1 if i == 0 else -1)
                dz = 0.12
            else:
                ang = (i / 3.0) * math.pi - math.pi / 2
                dy = self.body_scale * 0.42 * math.cos(ang)
                dz = 0.08 + 0.12 * math.sin(ang + 0.4)
            eye = create_sphere(
                location=(-self.body_scale * 0.48, dy, 0.22 + dz),
                scale=(eye_scale, eye_scale, eye_scale),
            )
            self.parts.append(eye)

        for side in [-1, 1]:
            claw_length = random_variance(0.35, 0.08, self.rng)
            claw = create_cylinder(
                location=(self.body_scale * 0.6, side * self.body_scale * 0.5, 0.1),
                scale=(0.15, 0.15, claw_length),
                vertices=6,
            )
            self.parts.append(claw)

        leg_positions = [
            (0, self.body_scale * 0.5, 0),
            (0, -self.body_scale * 0.5, 0),
            (-self.body_scale * 0.4, self.body_scale * 0.4, 0),
            (-self.body_scale * 0.4, -self.body_scale * 0.4, 0),
        ]
        for leg_x, leg_y, leg_z in leg_positions:
            leg_length = random_variance(0.3, 0.08, self.rng)
            leg = create_cylinder(
                location=(leg_x, leg_y, leg_z),
                scale=(0.08, 0.08, leg_length),
                vertices=6,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        enemy_mats = get_enemy_materials("claw_crawler", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        eye_mat = enemy_mats["extra"]
        claw_material = enemy_mats["extra"]
        limb_material = enemy_mats["limbs"]
        part_index = 2
        for _ in range(self._peripheral_eyes):
            apply_material_to_object(self.parts[part_index], eye_mat)
            part_index += 1
        for _ in range(2):
            apply_material_to_object(self.parts[part_index], claw_material)
            part_index += 1
        for _ in range(4):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1

    def get_rig_definition(self) -> RigDefinition:
        return quadruped_simple_rig_definition(self.body_scale)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
