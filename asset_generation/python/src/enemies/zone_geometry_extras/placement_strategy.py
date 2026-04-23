"""Placement and facing policy helpers for zone-geometry extras."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from mathutils import Vector

from ...utils.placement_clustering import clamp01

# World axes (Blender Z-up): extras spawn only where the surface normal aligns with enabled facings.
PLACE_KEYS: tuple[str, ...] = (
    "place_top",
    "place_bottom",
    "place_front",
    "place_back",
    "place_left",
    "place_right",
)
PLACE_WORLD: dict[str, Vector] = {
    "place_top": Vector((0.0, 0.0, 1.0)),
    "place_bottom": Vector((0.0, 0.0, -1.0)),
    "place_front": Vector((1.0, 0.0, 0.0)),
    "place_back": Vector((-1.0, 0.0, 0.0)),
    "place_right": Vector((0.0, 1.0, 0.0)),
    "place_left": Vector((0.0, -1.0, 0.0)),
}
FACING_DOT_MIN = 0.45


def zone_extra_clustering(spec: Mapping[str, Any]) -> float:
    """Read clustering scalar with [0, 1] clamp semantics."""
    return clamp01(spec.get("clustering"), 0.5)


def zone_distribution(spec: Mapping[str, Any]) -> str:
    """Resolve placement distribution mode with uniform fallback."""
    v = str(spec.get("distribution", "uniform")).strip().lower()
    return v if v in ("random", "uniform") else "uniform"


def zone_uniform_shape(spec: Mapping[str, Any]) -> str:
    """Resolve uniform placement shape with arc fallback."""
    v = str(spec.get("uniform_shape", "arc")).strip().lower()
    return v if v in ("arc", "ring") else "arc"


def place_flags(spec: Mapping[str, Any]) -> list[bool]:
    """Extract ordered place_* booleans."""
    return [bool(spec.get(k, True)) for k in PLACE_KEYS]


def facing_allows_normal(spec: Mapping[str, Any], nrm: Vector | tuple[float, float, float]) -> bool:
    """Return whether facing toggles allow an outward normal candidate."""
    flags = place_flags(spec)
    if not any(flags):
        return True
    if all(flags):
        return True
    normal = nrm if isinstance(nrm, Vector) else Vector(nrm)
    ol = normal.length
    if ol < 1e-12:
        return False
    for key, on in zip(PLACE_KEYS, flags):
        if not on:
            continue
        if normal.dot(PLACE_WORLD[key]) >= FACING_DOT_MIN:
            return True
    return False
