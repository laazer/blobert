"""
Per-slug procedural build controls for animated enemies (UI + generator).

JSON from the asset editor / CLI is either:
  - flat: {"eye_count": 4} (keys must match the current enemy slug's controls), or
  - nested: {"spider": {"eye_count": 4, "mesh": {"BODY_BASE": 1.2}}}

Numeric ClassVars on each enemy class (``BODY_*`` mesh tuning and ``RIG_*`` rig layout ratios) can be overridden under the ``mesh`` object.
"""

from __future__ import annotations

import json
import math
import re
from typing import Any

from .animated_build_options_appendage_defs import (
    _eye_shape_pupil_control_defs,
    _mouth_control_defs,
    _tail_control_defs,
    _texture_control_defs,
)
from .animated_build_options_mesh_controls import (
    _mesh_float_control_defs,
    _mesh_numeric_defaults,
)
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

# Material finish keys (keep aligned with materials.material_system.ENEMY_FINISH_PRESETS).
_VALID_FINISHES: frozenset[str] = frozenset(
    {"default", "glossy", "matte", "metallic", "gel"}
)
_FINISH_OPTIONS_ORDER: tuple[str, ...] = (
    "default",
    "glossy",
    "matte",
    "metallic",
    "gel",
)

# Per-slug material feature slots merged into build_options["features"].
# ``joints`` is used for hinge / ball meshes when the rig exposes them (humanoid joint balls, spider leg spheres).
_FEATURE_ZONES_BY_SLUG: dict[str, tuple[str, ...]] = {
    "imp": ("body", "head", "limbs", "joints", "extra"),
    "carapace_husk": ("body", "head", "limbs", "joints", "extra"),
    "spider": ("body", "head", "limbs", "joints", "extra"),
    "claw_crawler": ("body", "head", "limbs", "extra"),
    "spitter": ("body", "head", "limbs"),
    "slug": ("body", "head", "extra"),
    # Procedural player slime: body blob + face region (same attach path as animated enemies: body/head only).
    "player_slime": ("body", "head"),
}

_FEAT_ZONE_FLAT_KEY = re.compile(r"^feat_(body|head|limbs|joints|extra)_(finish|hex)$")
_FEAT_LIMB_PART_FLAT_KEY = re.compile(r"^feat_limb_([a-z0-9_]+)_(finish|hex)$")
_FEAT_JOINT_PART_FLAT_KEY = re.compile(r"^feat_joint_([a-z0-9_]+)_(finish|hex)$")

_EXTRA_KINDS_ORDER: tuple[str, ...] = ("none", "shell", "spikes", "horns", "bulbs")
_SPIKE_COUNT_MIN = 1
_SPIKE_COUNT_MAX = 24
_BULB_COUNT_MIN = 1
_BULB_COUNT_MAX = 16
_SPIKE_SIZE_MIN = 0.25
_SPIKE_SIZE_MAX = 3.0
_BULB_SIZE_MIN = 0.25
_BULB_SIZE_MAX = 3.0
_SHELL_SCALE_MIN = 1.01
_SHELL_SCALE_MAX = 1.5
_DEFAULT_SHELL_SCALE = 1.08
_PLACEMENT_CLUSTERING_MIN = 0.0
_PLACEMENT_CLUSTERING_MAX = 1.0
_DEFAULT_PLACEMENT_CLUSTERING = 0.5
_DISTRIBUTION_MODES: tuple[str, ...] = ("uniform", "random")
_UNIFORM_SHAPES: tuple[str, ...] = ("arc", "ring")
_DEFAULT_DISTRIBUTION = "uniform"
_DEFAULT_UNIFORM_SHAPE = "arc"
_PLACEMENT_SEED_MAX = 2_147_483_647
_OFFSET_XYZ_MIN = -2.0
_OFFSET_XYZ_MAX = 2.0
OFFSET_XYZ_MIN = _OFFSET_XYZ_MIN
OFFSET_XYZ_MAX = _OFFSET_XYZ_MAX
_OFFSET_XYZ_STEP = 0.05
_EXTRA_ZONE_FLAT_KEY = re.compile(
    r"^extra_zone_(body|head|limbs|joints|extra)_"
    r"(kind|spike_shape|spike_count|spike_size|bulb_count|bulb_size|shell_scale|clustering|distribution|uniform_shape|"
    r"finish|hex|offset_x|offset_y|offset_z|"
    r"place_top|place_bottom|place_front|place_back|place_left|place_right)$"
)
_ZONE_GEOM_EXTRA_PLACE_KEYS: tuple[str, ...] = (
    "place_top",
    "place_bottom",
    "place_front",
    "place_back",
    "place_left",
    "place_right",
)
_ZONE_GEOM_EXTRA_FIELDS: frozenset[str] = frozenset(
    {
        "kind",
        "spike_shape",
        "spike_count",
        "spike_size",
        "bulb_count",
        "bulb_size",
        "shell_scale",
        "clustering",
        "distribution",
        "uniform_shape",
        "finish",
        "hex",
        "offset_x",
        "offset_y",
        "offset_z",
        *_ZONE_GEOM_EXTRA_PLACE_KEYS,
    }
)


def _placement_seed_def() -> dict[str, Any]:
    return {
        "key": "placement_seed",
        "label": "Placement seed (random distribution)",
        "type": "int",
        "min": 0,
        "max": _PLACEMENT_SEED_MAX,
        "default": 0,
    }


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
        {
            "key": "eye_distribution",
            "label": "Eye placement",
            "type": "select_str",
            "options": list(_DISTRIBUTION_MODES),
            "default": _DEFAULT_DISTRIBUTION,
            "segmented": True,
        },
        {
            "key": "eye_uniform_shape",
            "label": "Eye uniform pattern",
            "type": "select_str",
            "options": ["arc"],
            "default": "arc",
        },
        {
            "key": "eye_clustering",
            "label": "Eye clustering (multi-eye)",
            "type": "float",
            "min": _PLACEMENT_CLUSTERING_MIN,
            "max": _PLACEMENT_CLUSTERING_MAX,
            "step": 0.05,
            "default": _DEFAULT_PLACEMENT_CLUSTERING,
            "unit": "0–1",
            "hint": "How tightly grouped vs spread eyes are when placement is random (multi-eye only).",
        },
    ]


def _feature_zones(slug: str) -> tuple[str, ...]:
    return _FEATURE_ZONES_BY_SLUG.get(slug, ("body",))


def _default_features_dict(slug: str) -> dict[str, dict[str, str]]:
    return {z: {"finish": "default", "hex": ""} for z in _feature_zones(slug)}


def _default_zone_geometry_extras_payload() -> dict[str, Any]:
    return {
        "kind": "none",
        "spike_shape": "cone",
        "spike_count": 8,
        "spike_size": 1.0,
        "bulb_count": 4,
        "bulb_size": 1.0,
        "clustering": _DEFAULT_PLACEMENT_CLUSTERING,
        "distribution": _DEFAULT_DISTRIBUTION,
        "uniform_shape": _DEFAULT_UNIFORM_SHAPE,
        "finish": "default",
        "hex": "",
        "place_top": True,
        "place_bottom": True,
        "place_front": True,
        "place_back": True,
        "place_left": True,
        "place_right": True,
        "offset_x": 0.0,
        "offset_y": 0.0,
        "offset_z": 0.0,
        "shell_scale": _DEFAULT_SHELL_SCALE,
    }


def _default_zone_geometry_extras(slug: str) -> dict[str, Any]:
    return {
        z: dict(_default_zone_geometry_extras_payload()) for z in _feature_zones(slug)
    }


def _coerce_boolish(v: Any, default: bool = True) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(int(v))
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "yes", "on"):
            return True
        if s in ("0", "false", "no", "off", ""):
            return False
        return default
    return default


def _sanitize_hex(raw: str) -> str:
    s = "".join(c for c in str(raw).strip().lower() if c in "0123456789abcdef")
    return s[:6]


def _validate_features_map(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for zone, inner in d.items():
        if not isinstance(inner, dict):
            inner = {}
        fin = str(inner.get("finish", "default"))
        if fin not in _VALID_FINISHES:
            fin = "default"
        hx = _sanitize_hex(inner.get("hex", ""))
        parts_out: dict[str, dict[str, str]] = {}
        pr = inner.get("parts")
        if isinstance(pr, dict):
            for pid, pinner in pr.items():
                if not isinstance(pinner, dict):
                    continue
                pfin = str(pinner.get("finish", "default"))
                if pfin not in _VALID_FINISHES:
                    pfin = "default"
                parts_out[str(pid)] = {
                    "finish": pfin,
                    "hex": _sanitize_hex(pinner.get("hex", "")),
                }
        zd: dict[str, Any] = {"finish": fin, "hex": hx}
        if parts_out:
            zd["parts"] = parts_out
        out[str(zone)] = zd
    return out


def _ensure_zone_parts(out: dict[str, Any], zone: str) -> dict[str, Any]:
    z = out.setdefault(zone, {"finish": "default", "hex": ""})
    if not isinstance(z, dict):
        z = {"finish": "default", "hex": ""}
        out[zone] = z
    parts = z.setdefault("parts", {})
    if not isinstance(parts, dict):
        parts = {}
        z["parts"] = parts
    return parts


def _merge_features_for_slug(
    slug: str, src: dict[str, Any], feat_base: dict[str, Any]
) -> dict[str, Any]:
    zones = _feature_zones(slug)
    out: dict[str, Any] = {}
    for z in zones:
        b = feat_base.get(z)
        if isinstance(b, dict):
            out[z] = {
                "finish": str(b.get("finish", "default")),
                "hex": str(b.get("hex", "")),
            }
            bp = b.get("parts")
            if isinstance(bp, dict):
                parts: dict[str, dict[str, str]] = {}
                for pid, pdata in bp.items():
                    if not isinstance(pdata, dict):
                        continue
                    parts[str(pid)] = {
                        "finish": str(pdata.get("finish", "default")),
                        "hex": str(pdata.get("hex", "")),
                    }
                if parts:
                    out[z]["parts"] = parts
        else:
            out[z] = {"finish": "default", "hex": ""}
    nested = src.get("features")
    if isinstance(nested, dict):
        for zone, data in nested.items():
            if zone not in out or not isinstance(data, dict):
                continue
            if "finish" in data:
                out[zone]["finish"] = str(data["finish"])
            if "hex" in data:
                out[zone]["hex"] = str(data["hex"])
            subp = data.get("parts")
            if isinstance(subp, dict):
                parts = _ensure_zone_parts(out, zone)
                for pid, pdata in subp.items():
                    if not isinstance(pdata, dict):
                        continue
                    entry = parts.setdefault(str(pid), {"finish": "default", "hex": ""})
                    if "finish" in pdata:
                        entry["finish"] = str(pdata["finish"])
                    if "hex" in pdata:
                        entry["hex"] = str(pdata["hex"])
    for k, v in src.items():
        m = _FEAT_ZONE_FLAT_KEY.match(k)
        if m:
            zone, field = m.group(1), m.group(2)
            if zone in out:
                out[zone][field] = str(v)
            continue
        m = _FEAT_LIMB_PART_FLAT_KEY.match(k)
        if m:
            pid, field = m.group(1), m.group(2)
            if "limbs" in out:
                parts = _ensure_zone_parts(out, "limbs")
                entry = parts.setdefault(pid, {"finish": "default", "hex": ""})
                entry[field] = str(v)
            continue
        m = _FEAT_JOINT_PART_FLAT_KEY.match(k)
        if m:
            pid, field = m.group(1), m.group(2)
            if "joints" in out:
                parts = _ensure_zone_parts(out, "joints")
                entry = parts.setdefault(pid, {"finish": "default", "hex": ""})
                entry[field] = str(v)
            continue
    return _validate_features_map(out)


def _merge_zone_geometry_extras(
    slug: str, src: dict[str, Any], base: dict[str, Any]
) -> dict[str, Any]:
    zones = _feature_zones(slug)
    out: dict[str, Any] = {}
    for z in zones:
        b = base.get(z)
        if isinstance(b, dict):
            entry = dict(_default_zone_geometry_extras_payload())
            for fk in _ZONE_GEOM_EXTRA_FIELDS:
                if fk in b:
                    val = b[fk]
                    if fk in _ZONE_GEOM_EXTRA_PLACE_KEYS:
                        entry[fk] = _coerce_boolish(val, True)
                    elif fk in ("offset_x", "offset_y", "offset_z", "shell_scale"):
                        try:
                            entry[fk] = float(val)
                        except (TypeError, ValueError):
                            pass
                    else:
                        entry[fk] = val
            out[z] = entry
        else:
            out[z] = dict(_default_zone_geometry_extras_payload())

    nested = src.get("zone_geometry_extras")
    if isinstance(nested, dict):
        for zone, data in nested.items():
            if zone not in out or not isinstance(data, dict):
                continue
            for fk in _ZONE_GEOM_EXTRA_FIELDS:
                if fk in data:
                    val = data[fk]
                    if fk in _ZONE_GEOM_EXTRA_PLACE_KEYS:
                        out[zone][fk] = _coerce_boolish(val, True)
                    elif fk in ("offset_x", "offset_y", "offset_z", "shell_scale"):
                        try:
                            out[zone][fk] = float(val)
                        except (TypeError, ValueError):
                            pass
                    else:
                        out[zone][fk] = val

    for k, v in src.items():
        m = _EXTRA_ZONE_FLAT_KEY.match(k)
        if not m:
            continue
        zone, field = m.group(1), m.group(2)
        if zone not in out:
            continue
        if field in ("spike_count", "bulb_count"):
            try:
                out[zone][field] = int(v)
            except (TypeError, ValueError):
                pass
        elif field in (
            "spike_size",
            "bulb_size",
            "clustering",
            "offset_x",
            "offset_y",
            "offset_z",
            "shell_scale",
        ):
            try:
                out[zone][field] = float(v)
            except (TypeError, ValueError):
                pass
        elif field in _ZONE_GEOM_EXTRA_PLACE_KEYS:
            out[zone][field] = _coerce_boolish(v, True)
        else:
            out[zone][field] = v
    return out


def _sanitize_zone_geometry_extras(slug: str, d: dict[str, Any]) -> dict[str, Any]:
    zones = _feature_zones(slug)
    valid_kinds = frozenset(_EXTRA_KINDS_ORDER)
    out: dict[str, Any] = {}
    for z in zones:
        raw = d.get(z)
        if not isinstance(raw, dict):
            raw = {}
        entry = dict(_default_zone_geometry_extras_payload())
        kind = str(raw.get("kind", "none")).strip().lower()
        if kind not in valid_kinds:
            kind = "none"
        if kind == "horns" and z != "head":
            kind = "none"
        entry["kind"] = kind
        shape = str(raw.get("spike_shape", "cone")).strip().lower()
        entry["spike_shape"] = shape if shape in ("cone", "pyramid") else "cone"
        try:
            sc = int(raw.get("spike_count", entry["spike_count"]))
        except (TypeError, ValueError):
            sc = 8
        entry["spike_count"] = max(_SPIKE_COUNT_MIN, min(_SPIKE_COUNT_MAX, sc))
        try:
            ss = float(raw.get("spike_size", entry["spike_size"]))
        except (TypeError, ValueError):
            ss = 1.0
        entry["spike_size"] = max(_SPIKE_SIZE_MIN, min(_SPIKE_SIZE_MAX, ss))
        try:
            bc = int(raw.get("bulb_count", entry["bulb_count"]))
        except (TypeError, ValueError):
            bc = 4
        entry["bulb_count"] = max(_BULB_COUNT_MIN, min(_BULB_COUNT_MAX, bc))
        try:
            bs = float(raw.get("bulb_size", entry["bulb_size"]))
        except (TypeError, ValueError):
            bs = 1.0
        entry["bulb_size"] = max(_BULB_SIZE_MIN, min(_BULB_SIZE_MAX, bs))
        try:
            cl = float(raw.get("clustering", entry["clustering"]))
        except (TypeError, ValueError):
            cl = _DEFAULT_PLACEMENT_CLUSTERING
        entry["clustering"] = max(
            _PLACEMENT_CLUSTERING_MIN, min(_PLACEMENT_CLUSTERING_MAX, cl)
        )
        dist = str(raw.get("distribution", entry["distribution"])).strip().lower()
        entry["distribution"] = (
            dist if dist in _DISTRIBUTION_MODES else _DEFAULT_DISTRIBUTION
        )
        us = str(raw.get("uniform_shape", entry["uniform_shape"])).strip().lower()
        entry["uniform_shape"] = us if us in _UNIFORM_SHAPES else _DEFAULT_UNIFORM_SHAPE
        if kind == "horns":
            entry["uniform_shape"] = "arc"
        for pk in _ZONE_GEOM_EXTRA_PLACE_KEYS:
            entry[pk] = _coerce_boolish(raw.get(pk, entry[pk]), True)
        fin = str(raw.get("finish", "default"))
        if fin not in _VALID_FINISHES:
            fin = "default"
        entry["finish"] = fin
        entry["hex"] = _sanitize_hex(raw.get("hex", ""))
        for axis in ("offset_x", "offset_y", "offset_z"):
            try:
                ov = float(raw.get(axis, 0.0))
            except (TypeError, ValueError):
                ov = 0.0
            if math.isnan(ov):
                ov = 0.0
            entry[axis] = max(_OFFSET_XYZ_MIN, min(_OFFSET_XYZ_MAX, ov))
        try:
            sh = float(raw.get("shell_scale", entry["shell_scale"]))
        except (TypeError, ValueError):
            sh = _DEFAULT_SHELL_SCALE
        if math.isnan(sh):
            sh = _DEFAULT_SHELL_SCALE
        elif math.isinf(sh):
            sh = _SHELL_SCALE_MIN if sh < 0 else _SHELL_SCALE_MAX
        else:
            sh = max(_SHELL_SCALE_MIN, min(_SHELL_SCALE_MAX, sh))
        entry["shell_scale"] = sh
        out[z] = entry
    return out


def _zone_extra_control_defs(slug: str) -> list[dict[str, Any]]:
    defs: list[dict[str, Any]] = []
    for zone in _feature_zones(slug):
        zlabel = zone.replace("_", " ").title()
        defs.append(
            {
                "key": f"extra_zone_{zone}_kind",
                "label": f"{zlabel} geometry extra",
                "type": "select_str",
                "options": list(_EXTRA_KINDS_ORDER),
                "default": "none",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_spike_shape",
                "label": f"{zlabel} spike shape",
                "type": "select_str",
                "options": ["cone", "pyramid"],
                "default": "cone",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_spike_count",
                "label": f"{zlabel} spike count",
                "type": "int",
                "min": _SPIKE_COUNT_MIN,
                "max": _SPIKE_COUNT_MAX,
                "default": 8,
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_spike_size",
                "label": f"{zlabel} spike / horn size",
                "type": "float",
                "min": _SPIKE_SIZE_MIN,
                "max": _SPIKE_SIZE_MAX,
                "step": 0.05,
                "default": 1.0,
                "unit": "× zone",
                "hint": "Scales spike or horn geometry relative to the zone mesh size.",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_bulb_count",
                "label": f"{zlabel} bulb count",
                "type": "int",
                "min": _BULB_COUNT_MIN,
                "max": _BULB_COUNT_MAX,
                "default": 4,
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_bulb_size",
                "label": f"{zlabel} bulb size",
                "type": "float",
                "min": _BULB_SIZE_MIN,
                "max": _BULB_SIZE_MAX,
                "step": 0.05,
                "default": 1.0,
                "unit": "× zone",
                "hint": "Scales bulb geometry relative to the zone mesh size.",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_shell_scale",
                "label": f"{zlabel} shell scale",
                "type": "float",
                "min": _SHELL_SCALE_MIN,
                "max": _SHELL_SCALE_MAX,
                "step": 0.01,
                "default": _DEFAULT_SHELL_SCALE,
                "unit": "× volume",
                "hint": "Expands the shell slightly beyond the enclosed body (must stay > 1).",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_clustering",
                "label": f"{zlabel} extra clustering",
                "type": "float",
                "min": _PLACEMENT_CLUSTERING_MIN,
                "max": _PLACEMENT_CLUSTERING_MAX,
                "step": 0.05,
                "default": _DEFAULT_PLACEMENT_CLUSTERING,
                "unit": "0–1",
                "hint": "For uniform placement, how tightly extras cluster on the zone surface.",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_distribution",
                "label": f"{zlabel} extra distribution",
                "type": "select_str",
                "options": list(_DISTRIBUTION_MODES),
                "default": _DEFAULT_DISTRIBUTION,
                "segmented": True,
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_uniform_shape",
                "label": f"{zlabel} uniform pattern",
                "type": "select_str",
                "options": list(_UNIFORM_SHAPES),
                "default": _DEFAULT_UNIFORM_SHAPE,
            }
        )
        for pk, plab in (
            ("place_top", "Top (+Z)"),
            ("place_bottom", "Bottom (−Z)"),
            ("place_front", "Front (+X)"),
            ("place_back", "Back (−X)"),
            ("place_right", "Right side (+Y)"),
            ("place_left", "Left side (−Y)"),
        ):
            defs.append(
                {
                    "key": f"extra_zone_{zone}_{pk}",
                    "label": f"{zlabel} extra on {plab}",
                    "type": "bool",
                    "default": True,
                }
            )
        defs.append(
            {
                "key": f"extra_zone_{zone}_finish",
                "label": f"{zlabel} extra finish",
                "type": "select_str",
                "options": list(_FINISH_OPTIONS_ORDER),
                "default": "default",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_hex",
                "label": f"{zlabel} extra hex",
                "type": "str",
                "default": "",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_offset_x",
                "label": f"{zlabel} offset X (Blender world +X = front)",
                "type": "float",
                "min": _OFFSET_XYZ_MIN,
                "max": _OFFSET_XYZ_MAX,
                "step": _OFFSET_XYZ_STEP,
                "default": 0.0,
                "unit": "Blender units",
                "hint": "World-space shift along +X (front) after the extra is attached.",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_offset_y",
                "label": f"{zlabel} offset Y (Blender world +Y = right)",
                "type": "float",
                "min": _OFFSET_XYZ_MIN,
                "max": _OFFSET_XYZ_MAX,
                "step": _OFFSET_XYZ_STEP,
                "default": 0.0,
                "unit": "Blender units",
                "hint": "World-space shift along +Y (right) after the extra is attached.",
            }
        )
        defs.append(
            {
                "key": f"extra_zone_{zone}_offset_z",
                "label": f"{zlabel} offset Z (Blender world +Z = up)",
                "type": "float",
                "min": _OFFSET_XYZ_MIN,
                "max": _OFFSET_XYZ_MAX,
                "step": _OFFSET_XYZ_STEP,
                "default": 0.0,
                "unit": "Blender units",
                "hint": "World-space shift along +Z (up) after the extra is attached.",
            }
        )
    return defs


def _feature_control_defs(slug: str) -> list[dict[str, Any]]:
    defs: list[dict[str, Any]] = []
    for zone in _feature_zones(slug):
        label = zone.replace("_", " ").title()
        defs.append(
            {
                "key": f"feat_{zone}_finish",
                "label": f"{label} finish",
                "type": "select_str",
                "options": list(_FINISH_OPTIONS_ORDER),
                "default": "default",
            }
        )
        defs.append(
            {
                "key": f"feat_{zone}_hex",
                "label": f"{label} hex",
                "type": "str",
                "default": "",
            }
        )
    return defs


# Import after constants to avoid an import cycle:
# animated_build_options_part_feature_defs imports _FINISH_OPTIONS_ORDER from this module.
from .animated_build_options_part_feature_defs import _part_feature_control_defs


def animated_build_controls_for_api() -> dict[str, list[dict[str, Any]]]:
    """Slug -> control definitions for the web client (static + introspected mesh floats)."""
    ensure_blender_stubs()
    try:
        from enemies.animated.registry import AnimatedEnemyBuilder
    except ImportError:
        from src.enemies.animated.registry import AnimatedEnemyBuilder

    slugs = (
        set(AnimatedEnemyBuilder.ENEMY_CLASSES.keys())
        | set(_ANIMATED_BUILD_CONTROLS.keys())
        | {"spider", "player_slime"}
    )
    out: dict[str, list[dict[str, Any]]] = {}
    for slug in sorted(slugs):
        static = list(_ANIMATED_BUILD_CONTROLS.get(slug, []))
        if slug == "spider":
            static = _spider_eye_control_defs()
        # eye_shape / pupil_enabled / pupil_shape are non-float controls that must
        # appear before any float-type entry (ESPS-1-AC-6).  Split static into its
        # non-float prefix and float suffix so the new controls slot in correctly.
        static_non_float = [c for c in static if c.get("type") != "float"]
        static_float = [c for c in static if c.get("type") == "float"]
        tail_defs = _tail_control_defs()
        merged = (
            static_non_float
            + _eye_shape_pupil_control_defs()
            + _mouth_control_defs()
            + tail_defs[:2]  # tail_enabled, tail_shape (non-float)
            + [tail_defs[2]]  # tail_length (float) — before static_float and mesh floats
            + static_float
            + _mesh_float_control_defs(slug)
            + _feature_control_defs(slug)
            + _part_feature_control_defs(slug)
            + _zone_extra_control_defs(slug)
            + _texture_control_defs()
            + [_placement_seed_def()]
        )
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
    for c in _eye_shape_pupil_control_defs():
        out[c["key"]] = c.get("default")
    for c in _mouth_control_defs():
        out[c["key"]] = c.get("default")
    for c in _tail_control_defs():
        out[c["key"]] = c.get("default")
    for c in _texture_control_defs():
        out[c["key"]] = c.get("default")
    mesh = _mesh_numeric_defaults(slug)
    out["mesh"] = dict(mesh)
    out["features"] = _default_features_dict(slug)
    out["zone_geometry_extras"] = _default_zone_geometry_extras(slug)
    out["placement_seed"] = 0
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
        allowed_non_mesh = {
            c["key"] for c in _ANIMATED_BUILD_CONTROLS.get(enemy_type, [])
        }
    allowed_non_mesh |= {c["key"] for c in _eye_shape_pupil_control_defs()}
    allowed_non_mesh |= {c["key"] for c in _mouth_control_defs()}
    allowed_non_mesh |= {c["key"] for c in _tail_control_defs()}
    allowed_non_mesh |= {c["key"] for c in _texture_control_defs()}
    allowed_non_mesh |= {"placement_seed"}

    if isinstance(src.get("mesh"), dict):
        for k, v in src["mesh"].items():
            if k in mesh_keys:
                mesh[k] = v

    for k, v in src.items():
        if k in ("mesh", "features", "zone_geometry_extras"):
            continue
        if (
            _FEAT_ZONE_FLAT_KEY.match(k)
            or _FEAT_LIMB_PART_FLAT_KEY.match(k)
            or _FEAT_JOINT_PART_FLAT_KEY.match(k)
            or _EXTRA_ZONE_FLAT_KEY.match(k)
        ):
            continue
        if k in mesh_keys:
            mesh[k] = v
        elif k in allowed_non_mesh:
            merged[k] = v

    merged["mesh"] = mesh
    feat_base = merged.get("features")
    if not isinstance(feat_base, dict):
        feat_base = _default_features_dict(enemy_type)
    merged["features"] = _merge_features_for_slug(enemy_type, src, feat_base)
    zg_base = merged.get("zone_geometry_extras")
    if not isinstance(zg_base, dict):
        zg_base = _default_zone_geometry_extras(enemy_type)
    merged["zone_geometry_extras"] = _merge_zone_geometry_extras(
        enemy_type, src, zg_base
    )
    if raw:
        root_flat = {
            str(k): v
            for k, v in raw.items()
            if k != enemy_type and _EXTRA_ZONE_FLAT_KEY.match(str(k))
        }
        if root_flat:
            merged["zone_geometry_extras"] = _merge_zone_geometry_extras(
                enemy_type,
                root_flat,
                merged["zone_geometry_extras"],
            )
    return _coerce_and_validate(enemy_type, merged)


def _coerce_and_validate(enemy_type: str, merged: dict[str, Any]) -> dict[str, Any]:
    # Import here to avoid an import cycle: animated_build_options_validate imports this module.
    from .animated_build_options_validate import coerce_validate_enemy_build_options

    return coerce_validate_enemy_build_options(enemy_type, merged)


def parse_build_options_json(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
