"""Coercion and validation for merged animated enemy build options (extracted for module size)."""

from __future__ import annotations

import math
from typing import Any


def coerce_validate_enemy_build_options(enemy_type: str, merged: dict[str, Any]) -> dict[str, Any]:
    """Apply control defs and mesh/zone sanitization. Lazy-imports parent to avoid import cycles."""
    from . import animated_build_options as m
    from .body_type_presets import body_type_control_def

    out = dict(merged)
    static_defs: list[dict[str, Any]] = (
        list(m._spider_eye_control_defs())
        if enemy_type == "spider"
        else list(m._ANIMATED_BUILD_CONTROLS.get(enemy_type, []))
    )
    if enemy_type in m._ANIMATED_ENEMY_SLUGS:
        static_defs.insert(0, body_type_control_def())
    static_defs.extend(m._eye_shape_pupil_control_defs())
    static_defs.extend(m._mouth_control_defs())
    static_defs.extend(m._tail_control_defs())
    static_defs.extend(m._rig_rotation_control_defs())
    static_defs.extend(m._zone_texture_control_defs(enemy_type))
    static_defs.append(m._placement_seed_def())
    for c in static_defs:
        key = c["key"]
        if key not in out:
            continue
        t = c["type"]
        if t == "int":
            lo = int(c["min"])
            hi = int(c["max"])
            try:
                v = int(out[key])
            except (TypeError, ValueError):
                dv = c.get("default", lo)
                try:
                    v = int(dv)
                except (TypeError, ValueError):
                    v = lo
            out[key] = max(lo, min(hi, v))
        elif t == "float":
            lo = float(c["min"])
            hi = float(c["max"])
            try:
                v = float(out[key])
            except (TypeError, ValueError):
                dv = c.get("default", lo)
                try:
                    v = float(dv)
                except (TypeError, ValueError):
                    v = lo
            if math.isnan(v):
                dv = c.get("default", lo)
                try:
                    v = float(dv)
                except (TypeError, ValueError):
                    v = lo
            out[key] = max(lo, min(hi, v))
        elif t == "select":
            opts = c["options"]
            if out[key] not in opts:
                out[key] = c.get("default", opts[0])
        elif t == "select_str":
            opts = tuple(c.get("options", ()))
            raw_s = str(out[key]).strip().lower()
            if raw_s not in opts:
                d = c.get("default")
                out[key] = d if isinstance(d, str) and d in opts else (opts[0] if opts else raw_s)
            else:
                out[key] = raw_s
        elif t == "bool":
            out[key] = m._coerce_boolish(out[key], default=bool(c.get("default", False)))

    mesh_in = dict(out.get("mesh") or {})
    mesh_out: dict[str, Any] = {}
    defaults = m._mesh_numeric_defaults(enemy_type)
    for c in m._mesh_float_control_defs(enemy_type):
        key = c["key"]
        base_v = defaults[key]
        raw_v = mesh_in.get(key, base_v)
        try:
            v = float(raw_v)
        except (TypeError, ValueError):
            v = float(base_v)
        lo = float(c["min"])
        hi = float(c["max"])
        v = max(lo, min(hi, v))
        if isinstance(base_v, int) and type(base_v) is not bool:
            mesh_out[key] = int(round(v))
        else:
            mesh_out[key] = v

    out["mesh"] = mesh_out
    zg = out.get("zone_geometry_extras")
    if not isinstance(zg, dict):
        zg = m._default_zone_geometry_extras(enemy_type)
    out["zone_geometry_extras"] = m._sanitize_zone_geometry_extras(enemy_type, zg)
    return out
