"""
Shared procedural mesh pipeline for animated creatures (geometry + materials + join).
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

from ..core.blender_utils import (
    apply_smooth_shading,
    detect_body_scale_from_mesh,
    join_objects,
)
from ..materials.material_system import (
    apply_feature_slot_overrides,
    apply_material_to_object,
    get_enemy_materials,
)


def _validate_scale(scale: float) -> float:
    s = float(scale)
    if not math.isfinite(s) or s <= 0:
        raise ValueError(f"scale must be finite and strictly positive, got {scale!r}")
    return s


class BaseAnimatedModel(ABC):
    """Procedural mesh: parts list, optional uniform scale, themed materials, finalize."""

    def __init__(self, name, materials, rng, scale: float = 1.0, build_options: dict | None = None):
        self.name = name
        self.materials = materials
        self.rng = rng
        self.scale = _validate_scale(scale)
        self.build_options: dict = dict(build_options or {})
        self.parts: list = []

    def _mesh(self, name: str):
        """Resolve a numeric ClassVar, with optional UI override from ``build_options['mesh']``."""
        cls = type(self)
        base = getattr(cls, name)
        raw = self.build_options.get("mesh", {}).get(name)
        if raw is None:
            return base
        if isinstance(base, tuple):
            return base
        if isinstance(base, bool):
            if isinstance(raw, bool):
                return raw
            if isinstance(raw, (int, float)):
                return bool(int(raw))
            if isinstance(raw, str):
                v = raw.strip().lower()
                if v in ("1", "true", "yes", "on"):
                    return True
                if v in ("0", "false", "no", "off", ""):
                    return False
            raise ValueError(f"invalid bool mesh override for {name!r}: {raw!r}")
        if isinstance(base, int) and type(base) is not bool:
            return int(round(float(raw)))
        return float(raw)

    def _mesh_str(self, name: str, allowed: tuple[str, ...] | None = None) -> str:
        """Resolve a string ClassVar with optional ``build_options['mesh']`` override."""
        from ..core.rig_models.limb_chain import ALLOWED_END_SHAPES

        allowed_set = allowed if allowed is not None else ALLOWED_END_SHAPES
        base = getattr(type(self), name)
        raw = self.build_options.get("mesh", {}).get(name)
        token = base if raw is None else raw
        if not isinstance(token, str):
            token = str(token)
        if token not in allowed_set:
            raise ValueError(f"invalid mesh string for {name!r}: {token!r} (allowed: {allowed_set})")
        return token

    def _scaled_location(self, xyz: tuple) -> tuple:
        if self.scale == 1.0:
            return xyz
        s = self.scale
        return (xyz[0] * s, xyz[1] * s, xyz[2] * s)

    def _scaled_primitive_extent(self, xyz: tuple) -> tuple:
        if self.scale == 1.0:
            return xyz
        s = self.scale
        return (xyz[0] * s, xyz[1] * s, xyz[2] * s)

    @abstractmethod
    def build_mesh_parts(self) -> None:
        """Populate ``self.parts`` with Blender mesh objects."""

    def _themed_slot_materials_for(self, theme_name: str) -> dict:
        """Theme palette slots with optional per-slot finish/color from ``build_options['features']``."""
        raw = get_enemy_materials(theme_name, self.materials, self.rng)
        return apply_feature_slot_overrides(raw, self.build_options.get("features"))

    def apply_themed_materials(self) -> None:
        enemy_mats = self._themed_slot_materials_for(self.name)
        if len(self.parts) >= 1:
            apply_material_to_object(self.parts[0], enemy_mats["body"])
        if len(self.parts) >= 2:
            apply_material_to_object(self.parts[1], enemy_mats["head"])
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats["limbs"])

    def finalize(self):
        if not self.parts:
            return None
        mesh = join_objects(self.parts)
        apply_smooth_shading(mesh)
        return mesh

    def _estimate_dimensions_from_prefab(self, prefab_mesh) -> None:
        scale = detect_body_scale_from_mesh(prefab_mesh)
        self.body_scale = scale
        self.body_height = scale * 2.0
        self.height = scale * 2.0
        self.length = scale * 2.0
        self.width = scale
        self.head_scale = scale * 0.6
        self.body_width = scale * 0.4
