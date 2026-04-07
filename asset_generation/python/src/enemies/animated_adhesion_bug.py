"""Animated adhesion bug enemy builder."""

from mathutils import Vector

from ..core.blender_utils import create_cylinder, create_sphere, random_variance
from ..core.rig_types import RigDefinition, rig_from_bone_map
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy


class AnimatedAdhesionBug(AnimatedEnemy):
    """Multi-segment bug with quadruped movement"""

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

        eye_count = self.rng.choice([2, 4])
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
        enemy_mats = get_enemy_materials("adhesion_bug", self.materials, self.rng)
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        leg_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        for i, part in enumerate(self.parts[2:]):
            if i < 6:
                apply_material_to_object(part, leg_material)
            else:
                apply_material_to_object(part, eye_material)

    def get_rig_definition(self) -> RigDefinition:
        s = self.body_scale
        return rig_from_bone_map(
            {
                "root": (Vector((0, 0, 0)), Vector((0, 0, s * 0.2)), None),
                "spine": (Vector((0, 0, s * 0.2)), Vector((s * 0.5, 0, s * 0.4)), "root"),
                "head": (Vector((s * 0.5, 0, s * 0.4)), Vector((s * 0.8, 0, s * 0.6)), "spine"),
                "leg_fl": (Vector((s * 0.3, s * 0.3, s * 0.3)), Vector((s * 0.3, s * 0.3, 0)), "spine"),
                "leg_fr": (Vector((s * 0.3, -s * 0.3, s * 0.3)), Vector((s * 0.3, -s * 0.3, 0)), "spine"),
                "leg_ml": (Vector((0, s * 0.4, s * 0.3)), Vector((0, s * 0.4, 0)), "spine"),
                "leg_mr": (Vector((0, -s * 0.4, s * 0.3)), Vector((0, -s * 0.4, 0)), "spine"),
                "leg_bl": (Vector((-s * 0.2, s * 0.3, s * 0.3)), Vector((-s * 0.2, s * 0.3, 0)), "root"),
                "leg_br": (Vector((-s * 0.2, -s * 0.3, s * 0.3)), Vector((-s * 0.2, -s * 0.3, 0)), "root"),
            }
        )

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
