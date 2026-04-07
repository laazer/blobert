"""
Per-slug procedural build controls for animated enemies (UI + generator).

JSON from the asset editor / CLI is either:
  - flat: {"eye_count": 4} (keys must match the current enemy slug's controls), or
  - nested: {"spider": {"eye_count": 4}}
"""

from __future__ import annotations

import json
from typing import Any

# Declarative controls for GET /api/meta (and validation). Keys are ANIMATED_SLUGS subsets.
_ANIMATED_BUILD_CONTROLS: dict[str, list[dict[str, Any]]] = {
    "spider": [
        {
            "key": "eye_count",
            "label": "Eyes",
            "type": "select",
            "options": [2, 4],
            "default": 2,
        },
    ],
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


def animated_build_controls_for_api() -> dict[str, list[dict[str, Any]]]:
    """Slug -> control definitions for the web client."""
    return {k: list(v) for k, v in _ANIMATED_BUILD_CONTROLS.items()}


def _defaults_for_slug(slug: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for c in _ANIMATED_BUILD_CONTROLS.get(slug, []):
        out[c["key"]] = c.get("default")
    return out


def options_for_enemy(enemy_type: str, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge defaults with user JSON; only keys registered for this slug."""
    base = _defaults_for_slug(enemy_type)
    if not raw:
        return base
    nested = raw.get(enemy_type)
    if isinstance(nested, dict):
        src = nested
    else:
        allowed = {c["key"] for c in _ANIMATED_BUILD_CONTROLS.get(enemy_type, [])}
        src = {k: v for k, v in raw.items() if k in allowed}
    merged = {**base, **src}
    return _coerce_and_validate(enemy_type, merged)


def _coerce_and_validate(enemy_type: str, merged: dict[str, Any]) -> dict[str, Any]:
    out = dict(merged)
    for c in _ANIMATED_BUILD_CONTROLS.get(enemy_type, []):
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
    return out


def parse_build_options_json(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
