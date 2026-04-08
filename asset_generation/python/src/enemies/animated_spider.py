"""Animated spider enemy builder (slug: spider, quadruped body)."""

import math
from typing import ClassVar

from mathutils import Vector

from ..core.blender_utils import create_sphere, random_variance
from ..core.rig_models.limb_mesh import append_segmented_limb_mesh
from ..core.rig_models.quadruped_simple import (
    CYLINDER_VERTICES_HEX,
    QUADRUPED_LEG_THICKNESS,
    QuadrupedSimpleRig,
)
from ..materials.material_system import apply_material_to_object
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin


class AnimatedSpider(QuadrupedSimpleRig, UsesSimpleRigMixin, AnimatedEnemy):
    """Multi-segment bug with quadruped movement"""

    body_height = 1.0

    BODY_BASE: ClassVar[float] = 1.0
    BODY_VARIANCE: ClassVar[float] = 0.2
    BODY_CENTER_Z: ClassVar[float] = 0.3
    BODY_SCALE_Y: ClassVar[float] = 0.8
    BODY_SCALE_Z: ClassVar[float] = 0.9
    HEAD_SCALE_REL: ClassVar[float] = 0.6
    HEAD_SCALE_VARIANCE: ClassVar[float] = 0.1
    HEAD_OFFSET_ALONG_X: ClassVar[float] = 0.5
    EYE_SCALE_HEAD_RATIO: ClassVar[float] = 0.15
    EYE_X_ALONG: ClassVar[float] = 1.2
    EYE_Y_SIDE: ClassVar[float] = 0.4
    EYE_Z: ClassVar[float] = 0.4
    LEG_LENGTH_BASE: ClassVar[float] = 0.9
    LEG_LENGTH_VARIANCE: ClassVar[float] = 0.1
    LEG_COUNT: ClassVar[int] = 8
    LEG_SEGMENTS: ClassVar[int] = 3
    LEG_END_SHAPE: ClassVar[str] = "none"
    LIMB_JOINT_BALL_SCALE: ClassVar[float] = 1.4
    LIMB_JOINT_VISUAL: ClassVar[bool] = True
    SPIDER_LEG_COUNT: ClassVar[int] = 8
    SPIDER_LEG_SEGMENTS: ClassVar[int] = 3
    DEFAULT_EYE_COUNT: ClassVar[int] = 2
    ALLOWED_EYE_COUNTS: ClassVar[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12)
    LEG_ANCHOR_RATIOS: ClassVar[tuple[tuple[float, float, float], ...]] = (
        (0.3, 0.3, 0),
        (0.3, -0.3, 0),
        (0, 0.4, 0),
        (0, -0.4, 0),
        (-0.2, 0.3, 0),
        (-0.2, -0.3, 0),
    )

    @staticmethod
    def _point_on_ellipsoid_surface(center: Vector, radii: Vector, direction: Vector) -> Vector:
        """Project a direction from center to the ellipsoid surface."""
        if direction.length <= 1e-8:
            return Vector((center.x + radii.x, center.y, center.z))
        dx, dy, dz = direction.x, direction.y, direction.z
        rx = max(1e-8, radii.x)
        ry = max(1e-8, radii.y)
        rz = max(1e-8, radii.z)
        denom = ((dx * dx) / (rx * rx)) + ((dy * dy) / (ry * ry)) + ((dz * dz) / (rz * rz))
        if denom <= 1e-12:
            return Vector((center.x + radii.x, center.y, center.z))
        t = 1.0 / math.sqrt(denom)
        return Vector((center.x + dx * t, center.y + dy * t, center.z + dz * t))

    @staticmethod
    def _separate_eye_dirs(eye_dirs: list[Vector], min_distance: float) -> list[Vector]:
        """Push nearby eye directions apart on the head sphere to avoid overlap."""
        if len(eye_dirs) < 2:
            return eye_dirs
        out = [Vector((v.x, v.y, v.z)).normalized() for v in eye_dirs]
        for _ in range(6):
            moved = False
            for i in range(len(out)):
                for j in range(i + 1, len(out)):
                    d = out[i] - out[j]
                    dist = d.length
                    if dist >= min_distance:
                        continue
                    if dist <= 1e-8:
                        d = Vector((0.0, 1.0, 0.0))
                        dist = 1.0
                    push = d.normalized() * ((min_distance - dist) * 0.5)
                    out[i] = (out[i] + push).normalized()
                    out[j] = (out[j] - push).normalized()
                    moved = True
            if not moved:
                break
        return out

    def _resolved_eye_count(self) -> int:
        eye_count = int(self.build_options.get("eye_count", self._mesh("DEFAULT_EYE_COUNT")))
        if eye_count not in self.ALLOWED_EYE_COUNTS:
            return int(self._mesh("DEFAULT_EYE_COUNT"))
        return eye_count

    def _eye_dirs(self, eye_count: int, head_center: Vector, head_scale: float) -> list[Vector]:
        eye_base_z = self._mesh("EYE_Z")
        if eye_count == 1:
            eyes = [Vector((1.0, 0.0, (eye_base_z - head_center.z) / max(1e-8, head_scale)))]
        elif eye_count == 2:
            eye_y = head_scale * self._mesh("EYE_Y_SIDE")
            eyes = [
                Vector((1.0, eye_y / max(1e-8, head_scale), (eye_base_z - head_center.z) / max(1e-8, head_scale))),
                Vector((1.0, -eye_y / max(1e-8, head_scale), (eye_base_z - head_center.z) / max(1e-8, head_scale))),
            ]
        else:
            span = max(1, eye_count - 1)
            eye_arc = self._mesh("EYE_Y_SIDE")
            eyes = []
            for i in range(eye_count):
                t = (i / span) * 2.0 - 1.0
                angle = t * (math.pi * 0.42)
                eye_y = head_scale * eye_arc * math.sin(angle)
                eye_z = eye_base_z + head_scale * 0.30 * math.cos(angle)
                eye_x = head_center.x + head_scale
                eyes.append(
                    Vector(
                        (
                            (eye_x - head_center.x) / max(1e-8, head_scale),
                            eye_y / max(1e-8, head_scale),
                            (eye_z - head_center.z) / max(1e-8, head_scale),
                        )
                    )
                )
        return eyes

    def _leg_chain_points(
        self,
        leg_index: int,
        body_center: Vector,
        body_radii: Vector,
        joint_radius: float,
        leg_length: float,
    ) -> tuple[Vector, Vector, Vector, Vector, Vector]:
        side_x_slots = (0.86, 0.36, -0.36, -0.86)  # front -> back anchors per side
        side_y_slot_scale = (1.00, 1.18, 1.18, 1.00)
        slot_z_bias = (0.02, -0.03, -0.03, 0.02)
        side = 1.0 if leg_index < 4 else -1.0
        slot = leg_index % 4
        x_slot = side_x_slots[slot]
        x_bias = x_slot * body_radii.x
        y_bias = side * body_radii.y * 1.55 * side_y_slot_scale[slot]
        radial_dir = Vector((x_bias, y_bias, 0.0)).normalized()
        tangent_dir = Vector((1.0 if x_slot >= 0 else -1.0, 0.0, 0.0))
        root_dir = Vector(
            (
                radial_dir.x * 1.05 + tangent_dir.x * 0.08,
                radial_dir.y * 1.16,
                -0.08 + slot_z_bias[slot],
            )
        )
        body_socket = self._point_on_ellipsoid_surface(body_center, body_radii, root_dir)
        root = body_socket + radial_dir * (joint_radius * 1.25)

        coxa_deg = 38.0
        femur_down_deg = 30.0
        tibia_down_deg = 55.0
        coxa_len = leg_length * 0.30
        femur_len = leg_length * 0.34
        tibia_len = leg_length * 0.46
        coxa_drop = math.tan(math.radians(max(30.0, min(45.0, coxa_deg)))) * coxa_len * 0.7
        coxa_dir = (radial_dir + tangent_dir * (0.12 * (1.0 if x_slot >= 0 else -1.0))).normalized()
        knee = Vector((root.x + coxa_dir.x * coxa_len, root.y + coxa_dir.y * coxa_len, root.z - coxa_drop))
        femur_h = femur_len * math.cos(math.radians(femur_down_deg))
        femur_v = femur_len * math.sin(math.radians(femur_down_deg))
        femur_dir = (radial_dir + tangent_dir * (0.08 * (1.0 if x_slot >= 0 else -1.0))).normalized()
        ankle = Vector((knee.x + femur_dir.x * femur_h, knee.y + femur_dir.y * femur_h, knee.z - femur_v))
        tibia_h = tibia_len * math.cos(math.radians(tibia_down_deg)) * 1.25
        tibia_dir = (radial_dir + tangent_dir * (0.05 * (1.0 if x_slot >= 0 else -1.0))).normalized()
        foot = Vector((ankle.x + tibia_dir.x * tibia_h, ankle.y + tibia_dir.y * tibia_h, 0.0))
        return body_socket, root, knee, ankle, foot

    def build_mesh_parts(self):
        """Create body, head, eyes, and legs."""
        body_scale = random_variance(self._mesh("BODY_BASE"), self._mesh("BODY_VARIANCE"), self.rng)
        leg_nominal = random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng)
        body_center = Vector((0.0, 0.0, max(float(self._mesh("BODY_CENTER_Z")), leg_nominal * 1.1)))
        body_radii = Vector(
            (
                body_scale,
                body_scale * self._mesh("BODY_SCALE_Y"),
                body_scale * self._mesh("BODY_SCALE_Z"),
            )
        )
        body = create_sphere(
            location=tuple(body_center),
            scale=tuple(body_radii),
        )
        self.parts.append(body)
        self.body_scale = body_scale

        head_scale = self.body_scale * random_variance(
            self._mesh("HEAD_SCALE_REL"), self._mesh("HEAD_SCALE_VARIANCE"), self.rng
        )
        head_offset = self.body_scale + head_scale * self._mesh("HEAD_OFFSET_ALONG_X")
        head_center = Vector((head_offset, 0.0, body_center.z))
        head = create_sphere(
            location=tuple(head_center),
            scale=(head_scale, head_scale, head_scale),
        )
        self.parts.append(head)
        self.head_scale = head_scale

        eye_count = self._resolved_eye_count()
        self._eye_count = eye_count
        eye_scale = self.head_scale * self._mesh("EYE_SCALE_HEAD_RATIO")
        eyes = self._eye_dirs(eye_count, head_center, head_scale)
        # Keep center-to-center spacing >= roughly 2x eye radius on the head sphere.
        min_center_dist = max(0.05, 2.2 * eye_scale / max(1e-8, head_scale))
        eyes = self._separate_eye_dirs(eyes, min_center_dist)
        for eye_dir in eyes:
            eye_dir = eye_dir.normalized()
            eye_center = head_center + eye_dir * head_scale
            eye = create_sphere(location=tuple(eye_center), scale=(eye_scale, eye_scale, eye_scale))
            self.parts.append(eye)

        # Hard requirement: spider always has exactly 8 legs (ignore runtime overrides).
        leg_count = 8
        joint_radius = QUADRUPED_LEG_THICKNESS * float(self._mesh("LIMB_JOINT_BALL_SCALE"))
        for i in range(leg_count):
            leg_length = random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng)
            body_socket, root, knee, ankle, foot = self._leg_chain_points(i, body_center, body_radii, joint_radius, leg_length)

            # Visible attachment from body shell to first leg joint.
            append_segmented_limb_mesh(
                self.parts,
                body_socket,
                root,
                1,
                QUADRUPED_LEG_THICKNESS * 0.9,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=False,
                end_shape="none",
            )

            self.parts.append(create_sphere(location=tuple(root), scale=(joint_radius, joint_radius, joint_radius)))
            append_segmented_limb_mesh(
                self.parts,
                root,
                knee,
                1,
                QUADRUPED_LEG_THICKNESS,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=False,
                end_shape="none",
            )
            self.parts.append(create_sphere(location=tuple(knee), scale=(joint_radius, joint_radius, joint_radius)))
            append_segmented_limb_mesh(
                self.parts,
                knee,
                ankle,
                1,
                QUADRUPED_LEG_THICKNESS,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=False,
                end_shape="none",
            )
            self.parts.append(create_sphere(location=tuple(ankle), scale=(joint_radius, joint_radius, joint_radius)))
            append_segmented_limb_mesh(
                self.parts,
                ankle,
                foot,
                1,
                QUADRUPED_LEG_THICKNESS,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=False,
                end_shape="none",
            )
            self.parts.append(create_sphere(location=tuple(foot), scale=(joint_radius, joint_radius, joint_radius)))

    def apply_themed_materials(self):
        enemy_mats = self._themed_slot_materials_for("spider")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        leg_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        ec = getattr(self, "_eye_count", int(self._mesh("DEFAULT_EYE_COUNT")))
        for i in range(ec):
            apply_material_to_object(self.parts[2 + i], eye_material)
        per_leg = 8  # body->root connector + root/knee/ankle/foot + 3 limb cylinders
        leg_start = 2 + ec
        for i in range(8 * per_leg):
            apply_material_to_object(self.parts[leg_start + i], leg_material)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
