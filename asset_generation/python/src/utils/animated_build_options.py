"""
Per-slug procedural build controls for animated enemies (UI + generator).

JSON from the asset editor / CLI is either:
  - flat: {"eye_count": 4} (keys must match the current enemy slug's controls), or
  - nested: {"spider": {"eye_count": 4, "mesh": {"BODY_BASE": 1.2}}}

Numeric ClassVars on each enemy class (``BODY_*`` mesh tuning and ``RIG_*`` rig layout ratios) can be overridden under the ``mesh`` object.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .blender_stubs import ensure_blender_stubs

# Declarative controls for GET /api/meta (and validation). Spider eye_count comes from
# ``AnimatedSpider`` (single source of truth) — see ``_spider_eye_control_defs``.
_ANIMATED_BUILD_CONTROLS: dict[str, list[dict[str, Any]]] = {
    "claw_crawler": [
        {
            "key": "peripheral_eyes",
            "label": "Peripheral eyes",
            "type": "int",
            "min": 0,
            "max": 3,
            "default": 0,
        },
    ],
}

_MESH_ATTR_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Int ClassVars already covered by static build controls — do not duplicate as mesh sliders.
_MESH_INT_KEYS_EXCLUDED: frozenset[str] = frozenset({"DEFAULT_EYE_COUNT", "PERIPHERAL_EYES_MAX"})


def _spider_eye_control_defs() -> list[dict[str, Any]]:
    ensure_blender_stubs()
    try:
        from enemies.animated_spider import AnimatedSpider
    except ImportError:
        from src.enemies.animated_spider import AnimatedSpider

    return [
        {
            "key": "eye_count",
            "label": "Eyes",
            "type": "select",
            "options": list(AnimatedSpider.ALLOWED_EYE_COUNTS),
            "default": AnimatedSpider.DEFAULT_EYE_COUNT,
        },
    ]


def _is_mesh_tune_name(name: str) -> bool:
    if not name or name.startswith("_"):
        return False
    return bool(_MESH_ATTR_NAME.match(name))


def _mesh_numeric_defaults(slug: str) -> dict[str, int | float]:
    ensure_blender_stubs()
    try:
        from enemies.animated.registry import AnimatedEnemyBuilder
    except ImportError:
        from src.enemies.animated.registry import AnimatedEnemyBuilder

    cls = AnimatedEnemyBuilder.ENEMY_CLASSES.get(slug)
    if cls is None:
        return {}
    out: dict[str, int | float] = {}
    for name in dir(cls):
        if not _is_mesh_tune_name(name):
            continue
        val = getattr(cls, name, None)
        if type(val) is bool:
            continue
        if isinstance(val, (int, float)):
            if name in _MESH_INT_KEYS_EXCLUDED:
                continue
            out[name] = val
    return out


def _humanize_mesh_control_label(key: str) -> str:
    if key.startswith("RIG_"):
        return "Rig " + key[4:].replace("_", " ").title()
    return key.replace("_", " ").title()


def _mesh_float_control_defs(slug: str) -> list[dict[str, Any]]:
    defaults = _mesh_numeric_defaults(slug)
    out: list[dict[str, Any]] = []
    for key, v in sorted(defaults.items()):
        vf = float(v)
        if vf == 0.0:
            lo, hi = 0.0, 2.0
        else:
            lo = max(0.01, min(vf * 0.05, vf * 0.5))
            hi = max(5.0, vf * 5.0)
        out.append(
            {
                "key": key,
                "label": _humanize_mesh_control_label(key),
                "type": "float",
                "min": lo,
                "max": hi,
                "step": 0.05,
                "default": vf,
            }
        )
    return out


def animated_build_controls_for_api() -> dict[str, list[dict[str, Any]]]:
    """Slug -> control definitions for the web client (static + introspected mesh floats)."""
    ensure_blender_stubs()
    try:
        from enemies.animated.registry import AnimatedEnemyBuilder
    except ImportError:
        from src.enemies.animated.registry import AnimatedEnemyBuilder

    slugs = set(AnimatedEnemyBuilder.ENEMY_CLASSES.keys()) | set(_ANIMATED_BUILD_CONTROLS.keys()) | {"spider"}
    out: dict[str, list[dict[str, Any]]] = {}
    for slug in sorted(slugs):
        static = list(_ANIMATED_BUILD_CONTROLS.get(slug, []))
        if slug == "spider":
            static = _spider_eye_control_defs()
        merged = static + _mesh_float_control_defs(slug)
        out[slug] = merged
    return out


def _defaults_for_slug(slug: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if slug == "spider":
        for c in _spider_eye_control_defs():
            out[c["key"]] = c.get("default")
    else:
        for c in _ANIMATED_BUILD_CONTROLS.get(slug, []):
            out[c["key"]] = c.get("default")
    mesh = _mesh_numeric_defaults(slug)
    out["mesh"] = dict(mesh)
    return out


def options_for_enemy(enemy_type: str, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge defaults with user JSON; mesh overrides live under ``mesh``."""
    base = _defaults_for_slug(enemy_type)
    mesh_keys = set(_mesh_numeric_defaults(enemy_type).keys())
    if not raw:
        return _coerce_and_validate(enemy_type, base)

    nested = raw.get(enemy_type)
    src: dict[str, Any] = nested if isinstance(nested, dict) else dict(raw)

    merged = dict(base)
    mesh = dict(base["mesh"])
    if enemy_type == "spider":
        allowed_non_mesh = {c["key"] for c in _spider_eye_control_defs()}
    else:
        allowed_non_mesh = {c["key"] for c in _ANIMATED_BUILD_CONTROLS.get(enemy_type, [])}

    if isinstance(src.get("mesh"), dict):
        for k, v in src["mesh"].items():
            if k in mesh_keys:
                mesh[k] = v

    for k, v in src.items():
        if k == "mesh":
            continue
        if k in mesh_keys:
            mesh[k] = v
        elif k in allowed_non_mesh:
            merged[k] = v

    merged["mesh"] = mesh
    return _coerce_and_validate(enemy_type, merged)


def _coerce_and_validate(enemy_type: str, merged: dict[str, Any]) -> dict[str, Any]:
    out = dict(merged)
    static_defs = _spider_eye_control_defs() if enemy_type == "spider" else _ANIMATED_BUILD_CONTROLS.get(enemy_type, [])
    for c in static_defs:
        key = c["key"]
        if key not in out:
            continue
        t = c["type"]
        if t == "int":
            v = int(out[key])
            lo = int(c["min"])
            hi = int(c["max"])
            out[key] = max(lo, min(hi, v))
        elif t == "select":
            opts = c["options"]
            if out[key] not in opts:
                out[key] = c.get("default", opts[0])

    mesh_in = dict(out.get("mesh") or {})
    mesh_out: dict[str, Any] = {}
    defaults = _mesh_numeric_defaults(enemy_type)
    for c in _mesh_float_control_defs(enemy_type):
        key = c["key"]
        base_v = defaults[key]
        raw_v = mesh_in.get(key, base_v)
        v = float(raw_v)
        lo = float(c["min"])
        hi = float(c["max"])
        v = max(lo, min(hi, v))
        if isinstance(base_v, int) and type(base_v) is not bool:
            mesh_out[key] = int(round(v))
        else:
            mesh_out[key] = v

    out["mesh"] = mesh_out
    return out


def parse_build_options_json(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
