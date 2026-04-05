"""Multi-segment insectoid body archetype."""

from ...core.blender_utils import create_cylinder, create_sphere, random_variance
from ...materials.material_system import apply_material_to_object, get_enemy_materials
from .base_model_type import BaseModelType


class InsectoidModel(BaseModelType):
    """Multi-segment insectoid with legs and eyes"""

    def create_geometry(self):
        """Create segmented insect body with legs"""
        self.body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(
            location=(0, 0, 0.3),
            scale=(self.body_scale, self.body_scale * 0.8, self.body_scale * 0.9),
        )
        self.parts.append(body)

        head_scale = self.body_scale * random_variance(0.6, 0.1, self.rng)
        head_offset = self.body_scale + head_scale * 0.5
        head = create_sphere(
            location=(head_offset, 0, 0.3),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)

        eye_count = self.rng.choice([2, 4])
        eye_scale = head_scale * 0.15
        for i in range(eye_count):
            side = 1 if i % 2 == 0 else -1
            eye_x = head_offset + head_scale * 0.7
            eye_y = side * head_scale * 0.4
            eye_z = 0.4
            eye = create_sphere(
                location=(eye_x, eye_y, eye_z),
                scale=(eye_scale, eye_scale, eye_scale),
            )
            self.parts.append(eye)

        leg_positions = [
            (self.body_scale * 0.3, self.body_scale * 0.3, 0),
            (self.body_scale * 0.3, -self.body_scale * 0.3, 0),
            (0, self.body_scale * 0.4, 0),
            (0, -self.body_scale * 0.4, 0),
            (-self.body_scale * 0.2, self.body_scale * 0.3, 0),
            (-self.body_scale * 0.2, -self.body_scale * 0.3, 0),
        ]

        for leg_x, leg_y, leg_z in leg_positions:
            leg_length = random_variance(0.3, 0.1, self.rng)
            leg = create_cylinder(
                location=(leg_x, leg_y, leg_z),
                scale=(0.08, 0.08, leg_length),
                vertices=6,
            )
            self.parts.append(leg)

    def apply_themed_materials(self):
        """Custom material application for insects"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)

        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])

        leg_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]

        for i, part in enumerate(self.parts[2:]):
            if i < 6:
                apply_material_to_object(part, leg_material)
            else:
                apply_material_to_object(part, eye_material)
