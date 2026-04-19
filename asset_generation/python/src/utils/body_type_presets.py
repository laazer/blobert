"""Editor `body_type` preset multipliers for animated enemy mesh generation (M25-05)."""

from __future__ import annotations

from typing import Any

BODY_TYPE_OPTIONS: tuple[str, ...] = ("default", "standard_biped", "no_leg_biped")


def normalize_body_type(raw: Any) -> str:
    s = str(raw or "default").strip().lower()
    return s if s in BODY_TYPE_OPTIONS else "default"


def humanoid_leg_segment_count(clamped_mesh_leg_segments: int, build_options: dict[str, Any] | None) -> int:
    """Effective leg segment count after ``body_type`` (humanoid family)."""
    bt = normalize_body_type((build_options or {}).get("body_type"))
    v = max(1, min(8, int(clamped_mesh_leg_segments)))
    if bt == "standard_biped":
        return max(v, 2)
    if bt == "no_leg_biped":
        return 1
    return v


def humanoid_torso_leg_multipliers(build_options: dict[str, Any] | None) -> tuple[float, float, float]:
    """Torso height, torso width, leg length multipliers (humanoid imp / carapace husk)."""
    bt = normalize_body_type((build_options or {}).get("body_type"))
    if bt == "standard_biped":
        return (1.16, 0.92, 1.28)
    if bt == "no_leg_biped":
        return (0.74, 1.2, 0.32)
    return (1.0, 1.0, 1.0)


def blob_body_type_scales(build_options: dict[str, Any] | None) -> tuple[float, float, float]:
    """Ellipsoid (lx, ly, lz) multipliers for slug/spitter body."""
    bt = normalize_body_type((build_options or {}).get("body_type"))
    if bt == "standard_biped":
        return (1.06, 0.92, 1.22)
    if bt == "no_leg_biped":
        return (1.14, 1.18, 0.68)
    return (1.0, 1.0, 1.0)


def spider_body_type_scales(build_options: dict[str, Any] | None) -> tuple[float, float, float, float]:
    """Body radii (x,y,z) multipliers and leg length multiplier."""
    bt = normalize_body_type((build_options or {}).get("body_type"))
    if bt == "standard_biped":
        return (0.94, 0.94, 1.18, 1.22)
    if bt == "no_leg_biped":
        return (1.12, 1.12, 0.72, 0.38)
    return (1.0, 1.0, 1.0, 1.0)


def claw_crawler_body_type_scales(build_options: dict[str, Any] | None) -> tuple[float, float, float]:
    """body_scale mul, flatten_y mul, leg_length mul."""
    bt = normalize_body_type((build_options or {}).get("body_type"))
    if bt == "standard_biped":
        return (1.05, 0.95, 1.25)
    if bt == "no_leg_biped":
        return (1.12, 1.08, 0.4)
    return (1.0, 1.0, 1.0)


def body_type_control_def() -> dict[str, Any]:
    """API + validation control for GET /api/meta animated enemy body presets (M25-05)."""
    return {
        "key": "body_type",
        "label": "Body Type",
        "type": "select_str",
        "options": list(BODY_TYPE_OPTIONS),
        "default": "default",
        "hint": "Preview updates after regeneration",
    }
