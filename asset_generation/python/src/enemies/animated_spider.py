"""Animated adhesion bug enemy builder."""

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_models import QuadrupedSimpleRig
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedSpider(QuadrupedSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Multi-segment bug with quadruped movement"""

    body_height = 1.0

    def build_mesh_parts(self):
        """Create body, head, eyes, and legs."""
        body_scale = random_variance(1.0, 0.2, self.rng)
        body = create_sphere(location=(0, 0, 0.3), scale=(body_scale, body_scale * 0.8, body_scale * 0.9))
        self.parts.append(body)
        self.body_scale = body_scale

        head_scale = self.body_scale * random_variance(0.6, 0.1, self.rng)
        head_offset = self.body_scale + head_scale * 0.5
        head = create_sphere(location=(head_offset, 0, 0.3), scale=(head_scale, head_scale, head_scale))
        self.parts.append(head)
        self.head_scale = head_scale

        eye_count = int(self.build_options.get("eye_count", 2))
        if eye_count not in (2, 4):
            eye_count = 2
        self._eye_count = eye_count
        eye_scale = self.head_scale * 0.15
        for i in range(eye_count):
            side = 1 if i % 2 == 0 else -1
            eye_x = self.body_scale + self.head_scale * 1.2
            eye_y = side * self.head_scale * 0.4
            eye_z = 0.4
            eye = create_sphere(location=(eye_x, eye_y, eye_z), scale=(eye_scale, eye_scale, eye_scale))
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
        enemy_mats = get_enemy_materials("spider", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        leg_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        ec = getattr(self, "_eye_count", 2)
        for i in range(ec):
            apply_material_to_object(self.parts[2 + i], eye_material)
        for i in range(6):
            apply_material_to_object(self.parts[2 + ec + i], leg_material)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
