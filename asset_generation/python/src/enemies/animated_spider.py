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
    LEG_LENGTH_BASE: ClassVar[float] = 0.3
    LEG_LENGTH_VARIANCE: ClassVar[float] = 0.1
    LEG_COUNT: ClassVar[int] = 6
    LEG_SEGMENTS: ClassVar[int] = 1
    LEG_END_SHAPE: ClassVar[str] = "none"
    LIMB_JOINT_BALL_SCALE: ClassVar[float] = 1.4
    LIMB_JOINT_VISUAL: ClassVar[bool] = True
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

    def build_mesh_parts(self):
        """Create body, head, eyes, and legs."""
        body_scale = random_variance(self._mesh("BODY_BASE"), self._mesh("BODY_VARIANCE"), self.rng)
        body_center = Vector((0.0, 0.0, float(self._mesh("BODY_CENTER_Z"))))
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

        eye_count = int(self.build_options.get("eye_count", self._mesh("DEFAULT_EYE_COUNT")))
        if eye_count not in self.ALLOWED_EYE_COUNTS:
            eye_count = int(self._mesh("DEFAULT_EYE_COUNT"))
        self._eye_count = eye_count
        eye_scale = self.head_scale * self._mesh("EYE_SCALE_HEAD_RATIO")
        eye_base_z = self._mesh("EYE_Z")
        if eye_count == 1:
            eyes = [Vector((1.0, 0.0, (eye_base_z - head_center.z) / max(1e-8, head_scale)))]
        elif eye_count == 2:
            eye_y = self.head_scale * self._mesh("EYE_Y_SIDE")
            eyes = [
                Vector((1.0, eye_y / max(1e-8, head_scale), (eye_base_z - head_center.z) / max(1e-8, head_scale))),
                Vector((1.0, -eye_y / max(1e-8, head_scale), (eye_base_z - head_center.z) / max(1e-8, head_scale))),
            ]
        else:
            # Distribute eyes across a visible front arc so extra eyes do not overlap.
            span = max(1, eye_count - 1)
            eye_arc = self._mesh("EYE_Y_SIDE")
            eyes = []
            for i in range(eye_count):
                t = (i / span) * 2.0 - 1.0  # [-1, 1]
                angle = t * (math.pi * 0.42)
                eye_y = self.head_scale * eye_arc * math.sin(angle)
                eye_z = eye_base_z + self.head_scale * 0.30 * math.cos(angle)
                # Keep eyes on front hemisphere but centered on the head surface.
                eye_x = head_center.x + self.head_scale
                eyes.append(
                    Vector(
                        (
                            (eye_x - head_center.x) / max(1e-8, head_scale),
                            eye_y / max(1e-8, head_scale),
                            (eye_z - head_center.z) / max(1e-8, head_scale),
                        )
                    )
                )
        # Keep center-to-center spacing >= roughly 2x eye radius on the head sphere.
        min_center_dist = max(0.05, 2.2 * eye_scale / max(1e-8, head_scale))
        eyes = self._separate_eye_dirs(eyes, min_center_dist)
        for eye_dir in eyes:
            eye_dir = eye_dir.normalized()
            eye_center = head_center + eye_dir * head_scale
            eye = create_sphere(location=tuple(eye_center), scale=(eye_scale, eye_scale, eye_scale))
            self.parts.append(eye)

        n_leg_segments = max(1, min(8, int(self._mesh("LEG_SEGMENTS"))))
        joint_visual = bool(self._mesh("LIMB_JOINT_VISUAL"))
        joint_ball_scale = float(self._mesh("LIMB_JOINT_BALL_SCALE"))
        leg_end_shape = self._mesh_str("LEG_END_SHAPE")
        for leg_x, leg_y, leg_z in self.LEG_ANCHOR_RATIOS:
            anchor_dir = Vector(
                (
                    self.body_scale * leg_x,
                    self.body_scale * leg_y,
                    -body_radii.z * 0.15 + leg_z,
                )
            )
            leg_root = self._point_on_ellipsoid_surface(body_center, body_radii, anchor_dir)
            leg_length = random_variance(self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng)
            radial = Vector((leg_root.x - body_center.x, leg_root.y - body_center.y, 0.0))
            radial_dir = radial.normalized() if radial.length > 1e-8 else Vector((1.0, 0.0, 0.0))
            foot = Vector(
                (
                    leg_root.x + radial_dir.x * leg_length * 0.8,
                    leg_root.y + radial_dir.y * leg_length * 0.8,
                    max(0.0, leg_root.z - leg_length * 1.1),
                )
            )
            append_segmented_limb_mesh(
                self.parts,
                leg_root,
                foot,
                n_leg_segments,
                QUADRUPED_LEG_THICKNESS,
                vertices=CYLINDER_VERTICES_HEX,
                joint_visual=joint_visual,
                joint_ball_scale=joint_ball_scale,
                end_shape=leg_end_shape,
                end_scale=(
                    QUADRUPED_LEG_THICKNESS,
                    QUADRUPED_LEG_THICKNESS,
                    QUADRUPED_LEG_THICKNESS,
                ),
            )

    def apply_themed_materials(self):
        enemy_mats = self._themed_slot_materials_for("spider")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        leg_material = enemy_mats["limbs"]
        eye_material = enemy_mats["extra"]
        ec = getattr(self, "_eye_count", int(self._mesh("DEFAULT_EYE_COUNT")))
        for i in range(ec):
            apply_material_to_object(self.parts[2 + i], eye_material)
        n_leg_segments = max(1, min(8, int(self._mesh("LEG_SEGMENTS"))))
        joint_visual = bool(self._mesh("LIMB_JOINT_VISUAL"))
        leg_end_shape = self._mesh_str("LEG_END_SHAPE")
        per_leg = n_leg_segments + ((n_leg_segments - 1) if joint_visual else 0) + (0 if leg_end_shape == "none" else 1)
        leg_start = 2 + ec
        for i in range(int(self._mesh("LEG_COUNT")) * per_leg):
            apply_material_to_object(self.parts[leg_start + i], leg_material)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
