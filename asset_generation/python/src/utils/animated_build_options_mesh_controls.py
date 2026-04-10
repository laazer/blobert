"""Introspected mesh / rig float sliders for animated enemy build options."""

from __future__ import annotations

import re
from typing import Any

from .blender_stubs import ensure_blender_stubs

_MESH_ATTR_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Int ClassVars already covered by static build controls — do not duplicate as mesh sliders.
_MESH_INT_KEYS_EXCLUDED: frozenset[str] = frozenset({"DEFAULT_EYE_COUNT", "PERIPHERAL_EYES_MAX"})


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
