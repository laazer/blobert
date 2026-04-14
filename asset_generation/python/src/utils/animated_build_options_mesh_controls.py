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
    if slug == "player_slime":
        try:
            from player.player_slime_body import PlayerSlimeBody
        except ImportError:
            from src.player.player_slime_body import PlayerSlimeBody

        cls = PlayerSlimeBody
    else:
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


def _mesh_float_editor_meta(key: str) -> dict[str, str]:
    """Short unit label + one-line hint for the web build UI (optional JSON fields)."""
    if key.startswith("RIG_"):
        return {
            "unit": "× body scale",
            "hint": "Bone endpoint position as a fraction of body height or body scale (see HumanoidSimpleRig / quadruped layout).",
        }
    ku = key.upper()
    kl = key.lower()
    if kl.endswith("_variance"):
        return {
            "unit": "± spread",
            "hint": "Random deviation applied around the paired base value when the mesh is built.",
        }
    if "SEGMENTS" in ku:
        return {
            "unit": "segments",
            "hint": "Cylinder subdivisions along the limb; prefer whole values 1–8 for clean topology.",
        }
    if ku == "LIMB_JOINT_BALL_SCALE":
        return {
            "unit": "× joint",
            "hint": "Scales the visible joint spheres between limb segments.",
        }
    if "RADIUS" in ku or "THICKNESS" in ku:
        return {
            "unit": "Blender units",
            "hint": "Absolute radius or thickness in Blender scene units (same scale as body meshes).",
        }
    if (
        "RATIO" in ku
        or "_REL" in ku
        or "_ALONG_" in ku
        or "_SPREAD_" in ku
        or "_ABOVE_" in ku
        or "_HALF_" in ku
        or "OUTWARD" in ku
    ):
        return {
            "unit": "ratio",
            "hint": "Unitless proportion relative to another mesh dimension (width, height, or limb length).",
        }
    if "_BASE" in ku:
        return {
            "unit": "× nominal",
            "hint": "Central magnitude before variance; drives size along this axis during generation.",
        }
    if (
        "FLATTEN" in ku
        or "CENTER_Z" in ku
        or "SCALE_Y" in ku
        or "SCALE_Z" in ku
        or "OFFSET" in ku
    ):
        return {
            "unit": "blend",
            "hint": "Shape or placement factor blended into procedural dimensions for this part.",
        }
    return {
        "unit": "tuning",
        "hint": "Procedural mesh scalar for this enemy class.",
    }


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
        row: dict[str, Any] = {
            "key": key,
            "label": _humanize_mesh_control_label(key),
            "type": "float",
            "min": lo,
            "max": hi,
            "step": 0.05,
            "default": vf,
        }
        row.update(_mesh_float_editor_meta(key))
        out.append(row)
    return out
