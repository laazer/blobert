"""Bipedal humanoid body archetype."""

from ...core.blender_utils import create_cylinder, create_sphere, random_variance
from ...materials.material_system import apply_material_to_object, get_enemy_materials
from .base_model_type import BaseModelType


class HumanoidModel(BaseModelType):
    """Bipedal humanoid creature with arms and legs"""

    def create_geometry(self):
        """Create humanoid body with limbs"""
        self.body_height = random_variance(1.2, 0.2, self.rng)
        self.body_width = random_variance(0.4, 0.1, self.rng)
        body = create_cylinder(
            location=self._scaled_location((0, 0, self.body_height * 0.5)),
            scale=self._scaled_primitive_extent((self.body_width, self.body_width, self.body_height)),
            vertices=8,
        )
        self.parts.append(body)

        head_scale = self.body_width * 1.1
        head = create_sphere(
            location=self._scaled_location((0, 0, self.body_height + head_scale * 0.7)),
            scale=self._scaled_primitive_extent((head_scale, head_scale, head_scale)),
        )
        self.parts.append(head)

        arm_length = random_variance(0.8, 0.2, self.rng)
        for side in [-1, 1]:
            arm = create_cylinder(
                location=self._scaled_location(
                    (side * (self.body_width + arm_length * 0.5), 0, self.body_height * 0.7)
                ),
                scale=self._scaled_primitive_extent((0.12, 0.12, arm_length)),
                vertices=6,
            )
            arm.rotation_euler = (0, 0, 1.57 * side)
            self.parts.append(arm)

            hand = create_sphere(
                location=self._scaled_location(
                    (side * (self.body_width + arm_length), 0, self.body_height * 0.7)
                ),
                scale=self._scaled_primitive_extent((0.15, 0.15, 0.15)),
            )
            self.parts.append(hand)

        leg_length = random_variance(0.7, 0.1, self.rng)
        for side in [-1, 1]:
            leg = create_cylinder(
                location=self._scaled_location((side * self.body_width * 0.3, 0, leg_length * 0.5)),
                scale=self._scaled_primitive_extent((0.12, 0.12, leg_length)),
                vertices=6,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        """Custom material application for humanoids"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)

        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])

        limb_material = enemy_mats["limbs"]
        hand_material = enemy_mats["extra"]

        part_index = 2
        for _i in range(2):
            apply_material_to_object(self.parts[part_index], limb_material)
            apply_material_to_object(self.parts[part_index + 1], hand_material)
            part_index += 2

        for _i in range(2):
            apply_material_to_object(self.parts[part_index], limb_material)
            part_index += 1
