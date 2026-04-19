"""Animated spider enemy builder (slug: spider, quadruped body)."""

from __future__ import annotations

import math
from typing import ClassVar

from mathutils import Euler, Vector

from ..core.blender_utils import (
    create_eye_mesh,
    create_mouth_mesh,
    create_pupil_mesh,
    create_sphere,
    create_tail_mesh,
    random_variance,
)
from ..core.rig_models.limb_mesh import append_segmented_limb_mesh
from ..core.rig_models.quadruped_simple import (
    CYLINDER_VERTICES_HEX,
    QUADRUPED_LEG_THICKNESS,
    QuadrupedSimpleRig,
)
from ..materials.material_system import apply_material_to_object, material_for_zone_part
from ..utils.body_type_presets import spider_body_type_scales
from ..utils.constants import EnemyBodyTypes
from .animated_enemy import AnimatedEnemy, UsesSimpleRigMixin
from .animated_spider_eye_helpers import (
    eye_dirs_random,
    eye_dirs_uniform,
    point_on_ellipsoid_surface,
    separate_eye_dirs,
)
from .zone_geometry_extras_attach import append_animated_enemy_zone_extras

_SPIDER_LEG_ANCHOR_RATIOS: tuple[tuple[float, float, float], ...] = (
    (0.3, 0.3, 0),
    (0.3, -0.3, 0),
    (0, 0.4, 0),
    (0, -0.4, 0),
    (-0.2, 0.3, 0),
    (-0.2, -0.3, 0),
)


def _spider_body_radii_and_leg_nominal(
    body_scale: float,
    mesh_scale_y: float,
    mesh_scale_z: float,
    leg_nominal: float,
    build_options: dict,
) -> tuple[Vector, float]:
    rx, ry, rz, leg_m = spider_body_type_scales(build_options)
    leg_nominal *= leg_m
    body_radii = Vector(
        (
            body_scale * rx,
            body_scale * mesh_scale_y * ry,
            body_scale * mesh_scale_z * rz,
        )
    )
    return body_radii, leg_nominal


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
    EYE_Z: ClassVar[float] = 1.0
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
    ALLOWED_EYE_COUNTS: ClassVar[tuple[int, ...]] = (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 99)
    LEG_ANCHOR_RATIOS: ClassVar[tuple[tuple[float, float, float], ...]] = _SPIDER_LEG_ANCHOR_RATIOS

    def _resolved_eye_count(self) -> int:
        raw = self.build_options.get("eye_count", self._mesh("DEFAULT_EYE_COUNT"))
        try:
            eye_count = int(raw)
        except (TypeError, ValueError):
            return int(self._mesh("DEFAULT_EYE_COUNT"))
        # Positive integers are accepted directly from build_options; API coercion
        # enforces ALLOWED_EYE_COUNTS. The builder supports any positive count.
        if eye_count > 0:
            return eye_count
        return int(self._mesh("DEFAULT_EYE_COUNT"))

    def _eye_clustering(self) -> float:
        try:
            c = float(self.build_options.get("eye_clustering", 0.5))
        except (TypeError, ValueError):
            c = 0.5
        return max(0.0, min(1.0, c))

    def _eye_distribution(self) -> str:
        v = str(self.build_options.get("eye_distribution", "uniform")).strip().lower()
        return v if v in ("random", "uniform") else "uniform"

    def _eye_dirs_uniform(self, eye_count: int, head_center: Vector, head_scale: float) -> list[Vector]:
        return eye_dirs_uniform(self, eye_count, head_center, head_scale)

    def _eye_dirs_random(self, eye_count: int, head_center: Vector, head_scale: float) -> list[Vector]:
        return eye_dirs_random(self, eye_count, head_center, head_scale)

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
        body_socket = point_on_ellipsoid_surface(
            body_center, body_radii, root_dir
        )
        root = body_socket + radial_dir * (joint_radius * 1.25)

        coxa_deg = 38.0
        femur_down_deg = 30.0
        tibia_down_deg = 55.0
        coxa_len = leg_length * 0.30
        femur_len = leg_length * 0.34
        tibia_len = leg_length * 0.46
        coxa_drop = (
            math.tan(math.radians(max(30.0, min(45.0, coxa_deg)))) * coxa_len * 0.7
        )
        coxa_dir = (
            radial_dir + tangent_dir * (0.12 * (1.0 if x_slot >= 0 else -1.0))
        ).normalized()
        knee = Vector(
            (
                root.x + coxa_dir.x * coxa_len,
                root.y + coxa_dir.y * coxa_len,
                root.z - coxa_drop,
            )
        )
        femur_h = femur_len * math.cos(math.radians(femur_down_deg))
        femur_v = femur_len * math.sin(math.radians(femur_down_deg))
        femur_dir = (
            radial_dir + tangent_dir * (0.08 * (1.0 if x_slot >= 0 else -1.0))
        ).normalized()
        ankle = Vector(
            (
                knee.x + femur_dir.x * femur_h,
                knee.y + femur_dir.y * femur_h,
                knee.z - femur_v,
            )
        )
        tibia_h = tibia_len * math.cos(math.radians(tibia_down_deg)) * 1.25
        tibia_dir = (
            radial_dir + tangent_dir * (0.05 * (1.0 if x_slot >= 0 else -1.0))
        ).normalized()
        foot = Vector(
            (ankle.x + tibia_dir.x * tibia_h, ankle.y + tibia_dir.y * tibia_h, 0.0)
        )
        return body_socket, root, knee, ankle, foot

    def build_mesh_parts(self):
        """Create body, head, eyes, and legs."""
        body_scale = random_variance(
            self._mesh("BODY_BASE"), self._mesh("BODY_VARIANCE"), self.rng
        )
        leg_nominal = random_variance(
            self._mesh("LEG_LENGTH_BASE"), self._mesh("LEG_LENGTH_VARIANCE"), self.rng
        )
        body_radii, leg_nominal = _spider_body_radii_and_leg_nominal(
            body_scale,
            float(self._mesh("BODY_SCALE_Y")),
            float(self._mesh("BODY_SCALE_Z")),
            leg_nominal,
            self.build_options,
        )
        body_center = Vector(
            (0.0, 0.0, max(float(self._mesh("BODY_CENTER_Z")), leg_nominal * 1.1))
        )
        body = create_sphere(
            location=tuple(body_center),
            scale=tuple(body_radii),
        )
        _brx = math.radians(float(self.build_options.get("RIG_BODY_ROT_X") or 0.0))
        _bry = math.radians(float(self.build_options.get("RIG_BODY_ROT_Y") or 0.0))
        _brz = math.radians(float(self.build_options.get("RIG_BODY_ROT_Z") or 0.0))
        body.rotation_euler = Euler((_brx, _bry, _brz), "XYZ")
        self.parts.append(body)
        self.body_scale = body_scale
        self._zone_geom_body_center = body_center
        self._zone_geom_body_radii = body_radii

        head_scale = self.body_scale * random_variance(
            self._mesh("HEAD_SCALE_REL"), self._mesh("HEAD_SCALE_VARIANCE"), self.rng
        )
        head_offset = self.body_scale + head_scale * self._mesh("HEAD_OFFSET_ALONG_X")
        head_center = Vector((head_offset, 0.0, body_center.z))
        head = create_sphere(
            location=tuple(head_center),
            scale=(head_scale, head_scale, head_scale),
        )
        _hrx = math.radians(float(self.build_options.get("RIG_HEAD_ROT_X") or 0.0))
        _hry = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Y") or 0.0))
        _hrz = math.radians(float(self.build_options.get("RIG_HEAD_ROT_Z") or 0.0))
        head.rotation_euler = Euler((_hrx, _hry, _hrz), "XYZ")
        self.parts.append(head)
        self.head_scale = head_scale
        self._zone_geom_head_center = head_center
        self._zone_geom_head_radii = Vector((head_scale, head_scale, head_scale))

        eye_count = self._resolved_eye_count()
        self._eye_count = eye_count
        eye_scale = self.head_scale * self._mesh("EYE_SCALE_HEAD_RATIO")
        if self._eye_distribution() == "uniform":
            eyes = eye_dirs_uniform(self, eye_count, head_center, head_scale)
        else:
            eyes = eye_dirs_random(self, eye_count, head_center, head_scale)
        # Keep center-to-center spacing >= roughly 2x eye radius on the head sphere.
        min_center_dist = max(0.05, 2.2 * eye_scale / max(1e-8, head_scale))
        eyes = separate_eye_dirs(eyes, min_center_dist)
        eye_shape = str(self.build_options.get("eye_shape", "circle"))
        pupil_enabled = bool(self.build_options.get("pupil_enabled", False))
        pupil_shape = str(self.build_options.get("pupil_shape", "dot"))
        pupil_scale = eye_scale * 0.35
        # Build all eye meshes first, then append all pupil meshes (preserves contiguous eye index range).
        eye_centers: list[Vector] = []
        eye_dirs_resolved: list[Vector] = []
        for eye_dir in eyes:
            eye_dir = eye_dir.normalized()
            eye_center = head_center + eye_dir * head_scale
            eye = create_eye_mesh(eye_shape, tuple(eye_center), eye_scale)
            self.parts.append(eye)
            eye_centers.append(eye_center)
            eye_dirs_resolved.append(eye_dir)
        if pupil_enabled:
            for eye_center, eye_dir in zip(eye_centers, eye_dirs_resolved):
                pupil_center = eye_center + eye_dir * (eye_scale + eye_scale * 0.05)
                self.parts.append(
                    create_pupil_mesh(pupil_shape, tuple(pupil_center), pupil_scale)
                )
        self._pupil_count = eye_count if pupil_enabled else 0

        # Hard requirement: spider always has exactly 8 legs (ignore runtime overrides).
        leg_count = 8
        joint_radius = QUADRUPED_LEG_THICKNESS * float(
            self._mesh("LIMB_JOINT_BALL_SCALE")
        )
        for i in range(leg_count):
            leg_length = random_variance(
                self._mesh("LEG_LENGTH_BASE"),
                self._mesh("LEG_LENGTH_VARIANCE"),
                self.rng,
            )
            body_socket, root, knee, ankle, foot = self._leg_chain_points(
                i, body_center, body_radii, joint_radius, leg_length
            )

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

            self.parts.append(
                create_sphere(
                    location=tuple(root),
                    scale=(joint_radius, joint_radius, joint_radius),
                )
            )
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
            self.parts.append(
                create_sphere(
                    location=tuple(knee),
                    scale=(joint_radius, joint_radius, joint_radius),
                )
            )
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
            self.parts.append(
                create_sphere(
                    location=tuple(ankle),
                    scale=(joint_radius, joint_radius, joint_radius),
                )
            )
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
            self.parts.append(
                create_sphere(
                    location=tuple(foot),
                    scale=(joint_radius, joint_radius, joint_radius),
                )
            )

        # Mouth extra (MTE-7)
        mouth_enabled = bool(self.build_options.get("mouth_enabled", False))
        if mouth_enabled:
            mouth_shape = str(self.build_options.get("mouth_shape") or "smile")
            mouth_location = self._zone_geom_head_center + Vector(
                (self._zone_geom_head_radii.x, 0.0, 0.0)
            )
            self.parts.append(
                create_mouth_mesh(mouth_shape, tuple(mouth_location), self._zone_geom_head_radii.x)
            )

        # Tail extra (MTE-7)
        tail_enabled = bool(self.build_options.get("tail_enabled", False))
        if tail_enabled:
            tail_shape = str(self.build_options.get("tail_shape") or "spike")
            tail_length = float(self.build_options.get("tail_length", 1.0))
            tail_location = self._zone_geom_body_center + Vector(
                (-self._zone_geom_body_radii.x, 0.0, 0.0)
            )
            self.parts.append(
                create_tail_mesh(tail_shape, tail_length, tuple(tail_location))
            )

    def apply_themed_materials(self):
        enemy_mats = self._themed_slot_materials_for("spider")
        apply_material_to_object(self.parts[0], enemy_mats["body"])
        apply_material_to_object(self.parts[1], enemy_mats["head"])
        eye_material = enemy_mats["extra"]
        features = self.build_options.get("features")
        ec = getattr(self, "_eye_count", int(self._mesh("DEFAULT_EYE_COUNT")))
        pc = getattr(self, "_pupil_count", 0)
        for i in range(ec):
            apply_material_to_object(self.parts[2 + i], eye_material)
        for i in range(pc):
            apply_material_to_object(self.parts[2 + ec + i], enemy_mats["head"])
        per_leg = 8  # body->root connector + root/knee/ankle/foot + 3 limb cylinders
        leg_start = 2 + ec + pc
        joint_names = ("root", "knee", "ankle", "foot")
        for leg in range(8):
            for k in range(per_leg):
                idx = leg_start + leg * per_leg + k
                is_joint = k % 2 == 1
                if is_joint:
                    jn = joint_names[(k - 1) // 2]
                    mat = material_for_zone_part(
                        "joints", f"leg_{leg}_{jn}", enemy_mats, features
                    )
                else:
                    mat = material_for_zone_part(
                        "limbs", f"leg_{leg}", enemy_mats, features
                    )
                apply_material_to_object(self.parts[idx], mat)

        append_animated_enemy_zone_extras(self)

    def get_body_type(self):
        return EnemyBodyTypes.QUADRUPED
