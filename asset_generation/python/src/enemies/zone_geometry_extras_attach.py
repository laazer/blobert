"""Compatibility dispatcher for zone-geometry extras attachment entrypoints."""

from __future__ import annotations

import math
from typing import Any

from mathutils import Vector

from ..core.blender_utils import create_cone, create_sphere
from ..materials.material_system import (
    apply_feature_slot_overrides,
    apply_material_to_object,
    apply_zone_texture_pattern_overrides,
    get_enemy_materials,
    material_for_zone_geometry_extra,
)
from ..utils.build_options import OFFSET_XYZ_MAX, OFFSET_XYZ_MIN
from ..utils.placement_clustering import (
    clustered_ellipsoid_angles_bounded,
    placement_prng,
    uniform_arc_angles,
    uniform_ring_angles,
)
from .zone_geometry_extras import attachment as _attachment_module
from .zone_geometry_extras.attachment import (
    _orient_cone_outward as _orient_cone_outward_core,
)
from .zone_geometry_extras.geometry_math import (
    ellipsoid_normal as _ellipsoid_normal_core,
)
from .zone_geometry_extras.placement_strategy import (
    FACING_DOT_MIN as _FACING_DOT_MIN,
)
from .zone_geometry_extras.placement_strategy import (
    PLACE_KEYS as _PLACE_KEYS,
)
from .zone_geometry_extras.placement_strategy import (
    PLACE_WORLD as _PLACE_WORLD,
)
from .zone_geometry_extras.placement_strategy import (
    place_flags as _place_flags,
)
from .zone_geometry_extras.placement_strategy import (
    zone_distribution as _zone_distribution,
)
from .zone_geometry_extras.placement_strategy import (
    zone_extra_clustering as _zone_extra_clustering,
)
from .zone_geometry_extras.placement_strategy import (
    zone_uniform_shape as _zone_uniform_shape,
)


def _ellipsoid_normal(
    cx: float, cy: float, cz: float, a: float, b: float, h: float, point: tuple[float, float, float]
) -> Vector:
    return Vector(_ellipsoid_normal_core(cx, cy, cz, a, b, h, point))


def _sync_attachment_dependencies() -> None:
    _attachment_module.create_cone = create_cone
    _attachment_module.create_sphere = create_sphere
    _attachment_module.apply_feature_slot_overrides = apply_feature_slot_overrides
    _attachment_module.apply_material_to_object = apply_material_to_object
    _attachment_module.apply_zone_texture_pattern_overrides = apply_zone_texture_pattern_overrides
    _attachment_module.get_enemy_materials = get_enemy_materials
    _attachment_module.material_for_zone_geometry_extra = material_for_zone_geometry_extra
    _attachment_module.clustered_ellipsoid_angles_bounded = clustered_ellipsoid_angles_bounded
    _attachment_module.placement_prng = placement_prng
    _attachment_module.uniform_arc_angles = uniform_arc_angles
    _attachment_module.uniform_ring_angles = uniform_ring_angles
    _attachment_module.zone_extra_clustering = _zone_extra_clustering
    _attachment_module.zone_distribution = _zone_distribution
    _attachment_module.zone_uniform_shape = _zone_uniform_shape


def _zone_extra_offset(spec: dict[str, Any], axis: str) -> float:
    try:
        v = float(spec.get(axis, 0.0))
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    return max(OFFSET_XYZ_MIN, min(OFFSET_XYZ_MAX, v))


def _facing_allows_normal(spec: dict[str, Any], nrm: Vector) -> bool:
    flags = _place_flags(spec)
    if not any(flags):
        return True
    if all(flags):
        return True
    ol = nrm.length
    if ol < 1e-12:
        return False
    nn = nrm * (1.0 / ol)
    for key, on in zip(_PLACE_KEYS, flags):
        if not on:
            continue
        if nn.dot(_PLACE_WORLD[key]) >= _FACING_DOT_MIN:
            return True
    return False


def _orient_cone_outward(obj: Any, _base_center: tuple[float, float, float], outward: Vector) -> None:
    _orient_cone_outward_core(obj, outward)


def append_slug_zone_extras(model: Any) -> None:
    """Backward-compatible entry: slug instances only."""
    from .animated_slug import AnimatedSlug

    if isinstance(model, AnimatedSlug):
        append_animated_enemy_zone_extras(model)


def append_spider_zone_extras(model: Any) -> None:
    """Backward-compatible entry: spider instances only."""
    from .animated_spider import AnimatedSpider

    if isinstance(model, AnimatedSpider):
        append_animated_enemy_zone_extras(model)


def append_animated_enemy_zone_extras(model: Any) -> None:
    _sync_attachment_dependencies()
    _attachment_module.append_animated_enemy_zone_extras(model)


def _append_body_ellipsoid_extras(
    model: Any,
    spec: dict[str, Any],
    slot_mats: dict[str, Any],
    features: dict[str, Any] | None,
    cx: float,
    cy: float,
    cz: float,
    a: float,
    b: float,
    h: float,
) -> None:
    _sync_attachment_dependencies()
    _attachment_module.append_body_ellipsoid_extras(model, spec, slot_mats, features, cx, cy, cz, a, b, h)


def _append_head_ellipsoid_extras(
    model: Any,
    spec: dict[str, Any],
    slot_mats: dict[str, Any],
    features: dict[str, Any] | None,
    hx: float,
    hy: float,
    hz: float,
    ax: float,
    ay: float,
    az: float,
) -> None:
    _sync_attachment_dependencies()
    _attachment_module.append_head_ellipsoid_extras(model, spec, slot_mats, features, hx, hy, hz, ax, ay, az)


def append_player_slime_zone_extras(builder: Any) -> None:
    _sync_attachment_dependencies()
    _attachment_module.append_player_slime_zone_extras(builder)


__all__ = [
    "append_animated_enemy_zone_extras",
    "append_slug_zone_extras",
    "append_spider_zone_extras",
    "append_player_slime_zone_extras",
]
