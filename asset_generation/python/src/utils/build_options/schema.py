"""Consolidated animated build option schema/composition logic.

This module provides typed contracts for build options, control definitions,
and validation utilities for animated enemy generation.
"""


from __future__ import annotations

import json
import math
import re
from typing import Any, TypedDict

from src.utils.config import ANIMATED_SLUGS

from ..blender_stubs import ensure_blender_stubs
from ..body_type_presets import body_type_control_def

_ANIMATED_ENEMY_SLUGS: frozenset[str] = frozenset(ANIMATED_SLUGS)


# Typed contracts for build options (framework-agnostic)
class EyeConfigTypedDict(TypedDict):
    """Typed contract for eye configuration options."""

    count: int
    direction: str  # 'uniform', 'random', 'separate'
    scale_ratio: float
    x_along: float
    y_side: float
    z_offset: float


class MouthConfigTypedDict(TypedDict):
    """Typed contract for mouth configuration options."""

    enabled: bool
    shape: str  # 'simple', 'detailed', 'teeth'
    scale_ratio: float


class TailConfigTypedDict(TypedDict):
    """Typed contract for tail configuration options."""

    enabled: bool
    segments: int
    curve_intensity: float
    tip_shape: str  # 'pointed', 'rounded', 'spiked'


class MaterialConfigTypedDict(TypedDict):
    """Typed contract for material configuration options."""

    base_color: str  # hex color
    metallic_factor: float
    roughness: float
    emissive_enabled: bool
    emissive_color: str | None


class BuildOptionsCoreTypedDict(TypedDict, total=False):
    """Core typed contract for build options (framework-agnostic)."""

    eye_count: int
    eye_direction: str
    eye_scale_ratio: float
    mouth_shape: str
    tail_enabled: bool
    tail_segments: int
    material_base_color: str
    material_metallic: float
    material_roughness: float


__all__ = [
    "EyeConfigTypedDict",
    "MouthConfigTypedDict",
    "TailConfigTypedDict",
    "MaterialConfigTypedDict",
    "BuildOptionsCoreTypedDict",
] + list(globals().keys())  # Preserve existing exports

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
    "imp": [
        {
            "key": "RIG_HEAD_SCALE",
            "label": "Rig head scale",
            "type": "float",
            "min": 0.1,
            "max": 3.0,
            "step": 0.05,
            "default": 1.0,
            "unit": "× body width",
            "hint": "Multiplier applied to the head mesh scale relative to the body width ratio.",
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

_FEAT_ZONE_FLAT_KEY = re.compile(r"^feat_(body|head|limbs|joints|extra)_(finish|hex|color_mode|color_image_id|color_image_preview)$")
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
    return placement_seed_def(_PLACEMENT_SEED_MAX)


def _spider_eye_control_defs() -> list[dict[str, Any]]:
    return spider_eye_control_defs(
        placement_clustering_min=_PLACEMENT_CLUSTERING_MIN,
        placement_clustering_max=_PLACEMENT_CLUSTERING_MAX,
        default_placement_clustering=_DEFAULT_PLACEMENT_CLUSTERING,
        distribution_modes=_DISTRIBUTION_MODES,
        default_distribution=_DEFAULT_DISTRIBUTION,
    )


def _feature_zones(slug: str) -> tuple[str, ...]:
    return _FEATURE_ZONES_BY_SLUG.get(slug, ("body",))


def feature_zones(slug: str) -> tuple[str, ...]:
    """Public wrapper for per-slug feature zones."""
    return _feature_zones(slug)


def _zone_texture_control_defs(slug: str) -> list[dict[str, Any]]:
    return _zone_texture_control_defs_for_zones(_feature_zones(slug))


def _default_features_dict(slug: str) -> dict[str, dict[str, Any]]:
    return {
        z: {
            "finish": "default",
            "hex": "",
            "color_image": {"mode": "single", "id": None, "preview": None},
        }
        for z in _feature_zones(slug)
    }


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
        color_image = inner.get("color_image")
        if isinstance(color_image, dict):
            zd["color_image"] = {
                "mode": str(color_image.get("mode", "single")),
                "id": color_image.get("id"),
                "preview": color_image.get("preview"),
            }
        else:
            zd["color_image"] = {"mode": "single", "id": None, "preview": None}
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
            color_img = b.get("color_image")
            if isinstance(color_img, dict):
                out[z]["color_image"] = {
                    "mode": str(color_img.get("mode", "single")),
                    "id": color_img.get("id"),
                    "preview": color_img.get("preview"),
                }
            else:
                out[z]["color_image"] = {"mode": "single", "id": None, "preview": None}
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
            out[z] = {
                "finish": "default",
                "hex": "",
                "color_image": {"mode": "single", "id": None, "preview": None},
            }
    nested = src.get("features")
    if isinstance(nested, dict):
        for zone, data in nested.items():
            if zone not in out or not isinstance(data, dict):
                continue
            if "finish" in data:
                out[zone]["finish"] = str(data["finish"])
            if "hex" in data:
                out[zone]["hex"] = str(data["hex"])
            color_img = data.get("color_image")
            if isinstance(color_img, dict):
                out[zone]["color_image"] = {
                    "mode": str(color_img.get("mode", "single")),
                    "id": color_img.get("id"),
                    "preview": color_img.get("preview"),
                }
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
                if field == "color_mode":
                    out[zone]["color_image"]["mode"] = str(v)
                elif field == "color_image_id":
                    out[zone]["color_image"]["id"] = v if v is not None else None
                elif field == "color_image_preview":
                    out[zone]["color_image"]["preview"] = v if v is not None else None
                else:
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


def merge_zone_geometry_extras(
    slug: str, src: dict[str, Any], base: dict[str, Any]
) -> dict[str, Any]:
    """Public wrapper for zone-geometry-extra merge behavior."""
    return _merge_zone_geometry_extras(slug, src, base)


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
                "key": f"feat_{zone}_color_mode",
                "label": f"{label} color mode",
                "type": "select_str",
                "options": list(_COLOR_MODE_OPTIONS),
                "default": "single",
            }
        )
        defs.append(
            {
                "key": f"feat_{zone}_color_image_id",
                "label": f"{label} image texture ID",
                "type": "str",
                "default": "",
            }
        )
        defs.append(
            {
                "key": f"feat_{zone}_color_image_preview",
                "label": f"{label} image preview",
                "type": "str",
                "default": "",
            }
        )
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
        rig_rot_defs = (
            _rig_rotation_control_defs()
            if slug in _ANIMATED_ENEMY_SLUGS
            else []
        )
        body_row = (
            [body_type_control_def()] if slug in _ANIMATED_ENEMY_SLUGS else []
        )
        merged = (
            static_non_float
            + body_row
            + _eye_shape_pupil_control_defs()
            + _mouth_control_defs()
            + tail_defs[:2]  # tail_enabled, tail_shape (non-float)
            + [tail_defs[2]]  # tail_length (float) — before static_float and mesh floats
            + static_float
            + rig_rot_defs
            + _mesh_float_control_defs(slug)
            + _feature_control_defs(slug)
            + _part_feature_control_defs(slug)
            + _zone_extra_control_defs(slug)
            + _zone_texture_control_defs(slug)
            + [_placement_seed_def()]
        )
        out[slug] = merged
    return out


def _defaults_for_slug(slug: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    if slug in _ANIMATED_ENEMY_SLUGS:
        out["body_type"] = "default"
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
    if slug in _ANIMATED_ENEMY_SLUGS:
        for c in _rig_rotation_control_defs():
            out[c["key"]] = c.get("default")
    for c in _zone_texture_control_defs(slug):
        out[c["key"]] = c.get("default")
    mesh = _mesh_numeric_defaults(slug)
    out["mesh"] = dict(mesh)
    out["features"] = _default_features_dict(slug)
    out["zone_geometry_extras"] = _default_zone_geometry_extras(slug)
    out["placement_seed"] = 0
    return out


def defaults_for_slug(slug: str) -> dict[str, Any]:
    """Public wrapper for per-slug default build options."""
    return _defaults_for_slug(slug)


def _migrate_legacy_stripe_rotation_keys(src: dict[str, Any]) -> None:
    """Map ``feat_*_texture_stripe_rot_{x,y,z}`` to yaw/pitch (x→pitch, y→yaw; z dropped)."""
    for k in list(src.keys()):
        if not isinstance(k, str) or not k.endswith("_texture_stripe_rot_x"):
            continue
        base = k[: -len("texture_stripe_rot_x")]
        xk = f"{base}texture_stripe_rot_x"
        yk = f"{base}texture_stripe_rot_y"
        zk = f"{base}texture_stripe_rot_z"
        pitch_k = f"{base}texture_stripe_rot_pitch"
        yaw_k = f"{base}texture_stripe_rot_yaw"
        if pitch_k not in src and xk in src:
            src[pitch_k] = src[xk]
        if yaw_k not in src and yk in src:
            src[yaw_k] = src[yk]
        for old in (xk, yk, zk):
            src.pop(old, None)


def options_for_enemy(enemy_type: str, raw: dict[str, Any] | None) -> dict[str, Any]:
    """Merge defaults with user JSON; mesh overrides live under ``mesh``."""
    base = _defaults_for_slug(enemy_type)
    mesh_keys = set(_mesh_numeric_defaults(enemy_type).keys())
    if not raw:
        return _coerce_and_validate(enemy_type, base)

    nested = raw.get(enemy_type)
    src: dict[str, Any] = nested if isinstance(nested, dict) else dict(raw)
    _migrate_legacy_stripe_rotation_keys(src)

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
    if enemy_type in _ANIMATED_ENEMY_SLUGS:
        allowed_non_mesh |= {c["key"] for c in _rig_rotation_control_defs()}
        allowed_non_mesh.add("body_type")
    allowed_non_mesh |= {c["key"] for c in _zone_texture_control_defs(enemy_type)}
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
    from .validate import coerce_validate_enemy_build_options

    return coerce_validate_enemy_build_options(enemy_type, merged)


def parse_build_options_json(raw: str | None) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


_NOT_REEXPORT = frozenset(
    {
        "Any",
        "annotations",
        "body_type_control_def",
        "ensure_blender_stubs",
        "json",
        "math",
        "re",
    }
)
__all__ = sorted(
    k
    for k in globals()
    if not k.startswith("__") and k not in _NOT_REEXPORT
)


# Consolidated helper definitions from retired animated_build_options_* modules.

"""Mouth, tail, eye/pupil, and rig rotation control defs (extracted for module size limits)."""


# Per-part rotation controls (M25-04).
_RIG_ROT_MIN = -180.0
_RIG_ROT_MAX = 180.0
_RIG_ROT_STEP = 1.0

RIG_ROT_MIN = _RIG_ROT_MIN
RIG_ROT_MAX = _RIG_ROT_MAX
RIG_ROT_STEP = _RIG_ROT_STEP


def _rig_rotation_control_defs() -> list[dict[str, Any]]:
    """Return 6 per-part rotation float controls (head X/Y/Z, body X/Y/Z) in degrees."""
    _parts = (
        ("HEAD", "Head"),
        ("BODY", "Body"),
    )
    _axes = ("X", "Y", "Z")
    return [
        {
            "key": f"RIG_{part}_ROT_{axis}",
            "label": f"Rig {part_label.lower()} rotation {axis}",
            "type": "float",
            "min": _RIG_ROT_MIN,
            "max": _RIG_ROT_MAX,
            "step": _RIG_ROT_STEP,
            "default": 0.0,
            "unit": "deg",
            "hint": f"Cosmetic rotation of the {part_label.lower()} mesh around the {axis}-axis (degrees).",
        }
        for part, part_label in _parts
        for axis in _axes
    ]


def rig_rotation_control_defs() -> list[dict[str, Any]]:
    """Public wrapper for rig rotation control definitions."""
    return _rig_rotation_control_defs()


# Eye / pupil shape options.
_EYE_SHAPE_OPTIONS: tuple[str, ...] = ("circle", "oval", "slit", "square")
_PUPIL_SHAPE_OPTIONS: tuple[str, ...] = ("dot", "slit", "diamond")
_DEFAULT_EYE_SHAPE = "circle"
_DEFAULT_PUPIL_SHAPE = "dot"

# Mouth shape options (MTE-1)
_MOUTH_SHAPE_OPTIONS: tuple[str, ...] = ("smile", "grimace", "flat", "fang", "beak")
_DEFAULT_MOUTH_SHAPE = "smile"

# Tail shape options (MTE-1)
_TAIL_SHAPE_OPTIONS: tuple[str, ...] = ("spike", "whip", "club", "segmented", "curled")
_DEFAULT_TAIL_SHAPE = "spike"

# Tail length bounds and step (MTE-1)
_TAIL_LENGTH_MIN = 0.5
_TAIL_LENGTH_MAX = 3.0
_TAIL_LENGTH_STEP = 0.05
_TAIL_LENGTH_DEFAULT = 1.0

# NOTE: "custom" is intentionally excluded from _TEXTURE_MODE_OPTIONS. It is a
# client-side-only upload mode (blob URL via URL.createObjectURL) and is NOT a
# valid Blender build option. The frontend injects "custom" into the texture_mode
# selector without modifying this tuple. See ticket M25-03.
_TEXTURE_MODE_OPTIONS: tuple[str, ...] = (
    "none",
    "gradient",
    "spots",
    "checkerboard",
    "stripes",
    "assets",
)
_COLOR_MODE_OPTIONS: tuple[str, ...] = ("single", "gradient", "image")
_GRAD_DIRECTION_OPTIONS: tuple[str, ...] = ("horizontal", "vertical", "radial")

_TEXTURE_SPOT_DENSITY_MIN = 0.1
_TEXTURE_SPOT_DENSITY_MAX = 5.0
_TEXTURE_SPOT_DENSITY_STEP = 0.05
_TEXTURE_SPOT_DENSITY_DEFAULT = 1.0

_TEXTURE_SPOT_PATTERN_OPTIONS: tuple[str, ...] = ("grid", "hex")
_DEFAULT_TEXTURE_SPOT_PATTERN = "grid"

# Visual presets for stripe phase axis (orthogonal + diagonal); names are UX labels.
_TEXTURE_STRIPE_PRESET_OPTIONS: tuple[str, ...] = ("beachball", "doplar", "swirl")
_DEFAULT_TEXTURE_STRIPE_PRESET = "beachball"

_TEXTURE_STRIPE_ROT_DEG_MIN = -360.0
_TEXTURE_STRIPE_ROT_DEG_MAX = 360.0
_TEXTURE_STRIPE_ROT_DEG_STEP = 1.0
_DEFAULT_TEXTURE_STRIPE_ROT_DEG = 0.0

_TEXTURE_STRIPE_WIDTH_MIN = 0.05
_TEXTURE_STRIPE_WIDTH_MAX = 1.0
_TEXTURE_STRIPE_WIDTH_STEP = 0.01
_TEXTURE_STRIPE_WIDTH_DEFAULT = 0.2

_TEXTURE_ASSET_TILE_REPEAT_MIN = 0.5
_TEXTURE_ASSET_TILE_REPEAT_MAX = 8.0
_TEXTURE_ASSET_TILE_REPEAT_STEP = 0.5
_TEXTURE_ASSET_TILE_REPEAT_DEFAULT = 1.0


def _eye_shape_pupil_control_defs() -> list[dict[str, Any]]:
    """Return the three eye-shape + pupil control defs shared by every animated slug."""
    return [
        {
            "key": "eye_shape",
            "label": "Eye shape",
            "type": "select_str",
            "options": list(_EYE_SHAPE_OPTIONS),
            "default": _DEFAULT_EYE_SHAPE,
            "segmented": True,
        },
        {
            "key": "pupil_enabled",
            "label": "Pupil",
            "type": "bool",
            "default": False,
        },
        {
            "key": "pupil_shape",
            "label": "Pupil shape",
            "type": "select_str",
            "options": list(_PUPIL_SHAPE_OPTIONS),
            "default": _DEFAULT_PUPIL_SHAPE,
            "segmented": True,
        },
    ]


def eye_shape_pupil_control_defs() -> list[dict[str, Any]]:
    """Public wrapper for shared eye/pupil control definitions."""
    return _eye_shape_pupil_control_defs()


def _texture_control_defs() -> list[dict[str, Any]]:
    """Return the texture control defs shared by every animated slug."""
    return [
        {
            "key": "texture_mode",
            "label": "Texture mode",
            "type": "select_str",
            "options": list(_TEXTURE_MODE_OPTIONS),
            "default": "none",
        },
        {
            "key": "texture_grad_color_a",
            "label": "Gradient color A",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_grad_color_b",
            "label": "Gradient color B",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_grad_direction",
            "label": "Gradient direction",
            "type": "select_str",
            "options": list(_GRAD_DIRECTION_OPTIONS),
            "default": "horizontal",
        },
        {
            "key": "texture_spot_color",
            "label": "Spot color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_spot_bg_color",
            "label": "Spot background color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_spot_pattern",
            "label": "Spot layout",
            "type": "select_str",
            "options": list(_TEXTURE_SPOT_PATTERN_OPTIONS),
            "default": _DEFAULT_TEXTURE_SPOT_PATTERN,
            "segmented": True,
        },
        {
            "key": "texture_spot_density",
            "label": "Spot density",
            "type": "float",
            "min": _TEXTURE_SPOT_DENSITY_MIN,
            "max": _TEXTURE_SPOT_DENSITY_MAX,
            "step": _TEXTURE_SPOT_DENSITY_STEP,
            "default": _TEXTURE_SPOT_DENSITY_DEFAULT,
        },
        {
            "key": "texture_stripe_color",
            "label": "Stripe color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_stripe_bg_color",
            "label": "Stripe background color",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_stripe_width",
            "label": "Stripe width",
            "type": "float",
            "min": _TEXTURE_STRIPE_WIDTH_MIN,
            "max": _TEXTURE_STRIPE_WIDTH_MAX,
            "step": _TEXTURE_STRIPE_WIDTH_STEP,
            "default": _TEXTURE_STRIPE_WIDTH_DEFAULT,
        },
        {
            "key": "texture_stripe_direction",
            "label": "Stripe preset",
            "type": "select_str",
            "options": list(_TEXTURE_STRIPE_PRESET_OPTIONS),
            "default": _DEFAULT_TEXTURE_STRIPE_PRESET,
            "segmented": True,
        },
        {
            "key": "texture_stripe_rot_yaw",
            "label": "Stripe yaw",
            "type": "float",
            "min": _TEXTURE_STRIPE_ROT_DEG_MIN,
            "max": _TEXTURE_STRIPE_ROT_DEG_MAX,
            "step": _TEXTURE_STRIPE_ROT_DEG_STEP,
            "default": _DEFAULT_TEXTURE_STRIPE_ROT_DEG,
            "unit": "deg",
        },
        {
            "key": "texture_stripe_rot_pitch",
            "label": "Stripe pitch",
            "type": "float",
            "min": _TEXTURE_STRIPE_ROT_DEG_MIN,
            "max": _TEXTURE_STRIPE_ROT_DEG_MAX,
            "step": _TEXTURE_STRIPE_ROT_DEG_STEP,
            "default": _DEFAULT_TEXTURE_STRIPE_ROT_DEG,
            "unit": "deg",
        },
        {
            "key": "texture_asset_id",
            "label": "Asset texture",
            "type": "str",
            "default": "",
        },
        {
            "key": "texture_asset_tile_repeat",
            "label": "Tile repeat",
            "type": "float",
            "min": _TEXTURE_ASSET_TILE_REPEAT_MIN,
            "max": _TEXTURE_ASSET_TILE_REPEAT_MAX,
            "step": _TEXTURE_ASSET_TILE_REPEAT_STEP,
            "default": _TEXTURE_ASSET_TILE_REPEAT_DEFAULT,
        },
    ]


def texture_control_defs() -> list[dict[str, Any]]:
    """Public wrapper for shared texture control definitions."""
    return _texture_control_defs()


def _mouth_control_defs() -> list[dict[str, Any]]:
    """Return the mouth control defs (MTE-1)."""
    return [
        {
            "key": "mouth_enabled",
            "label": "Mouth",
            "type": "bool",
            "default": False,
        },
        {
            "key": "mouth_shape",
            "label": "Mouth shape",
            "type": "select_str",
            "options": list(_MOUTH_SHAPE_OPTIONS),
            "default": _DEFAULT_MOUTH_SHAPE,
        },
    ]


def mouth_control_defs() -> list[dict[str, Any]]:
    """Public wrapper for mouth control definitions."""
    return _mouth_control_defs()


def _tail_control_defs() -> list[dict[str, Any]]:
    """Return the tail control defs (MTE-1)."""
    return [
        {
            "key": "tail_enabled",
            "label": "Tail",
            "type": "bool",
            "default": False,
        },
        {
            "key": "tail_shape",
            "label": "Tail shape",
            "type": "select_str",
            "options": list(_TAIL_SHAPE_OPTIONS),
            "default": _DEFAULT_TAIL_SHAPE,
        },
        {
            "key": "tail_length",
            "label": "Tail length",
            "type": "float",
            "min": _TAIL_LENGTH_MIN,
            "max": _TAIL_LENGTH_MAX,
            "step": _TAIL_LENGTH_STEP,
            "default": _TAIL_LENGTH_DEFAULT,
        },
    ]


def tail_control_defs() -> list[dict[str, Any]]:
    """Public wrapper for tail control definitions."""
    return _tail_control_defs()

"""Introspected mesh / rig float sliders for animated enemy build options."""

import re

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

"""Per-zone ``texture_*`` control defs expanded to ``feat_{zone}_texture_*`` for the asset editor."""



_ZONE_LABEL = {
    "body": "Body",
    "head": "Head",
    "limbs": "Limbs",
    "joints": "Joints",
    "extra": "Extra",
}


def _zone_texture_control_defs_for_zones(zones: tuple[str, ...]) -> list[dict[str, Any]]:
    """Per-zone surface texture controls; keys ``feat_{zone}_texture_*`` (aligned with material zones)."""
    base = _texture_control_defs()
    out: list[dict[str, Any]] = []
    for z in zones:
        zlab = _ZONE_LABEL.get(z, z.replace("_", " ").title())
        for c in base:
            old_key = str(c["key"])
            if not old_key.startswith("texture_"):
                continue
            suffix = old_key.removeprefix("texture_")
            new_key = f"feat_{z}_texture_{suffix}"
            label = f"{zlab} — {c['label']}"
            out.append({**c, "key": new_key, "label": label})
    return out


def zone_texture_control_defs(slug: str) -> list[dict[str, Any]]:
    """Public wrapper returning per-zone texture controls for an enemy slug."""
    return _zone_texture_control_defs(slug)

"""Spider eye_count / placement controls for GET /api/meta (single source: ``AnimatedSpider``)."""




def placement_seed_def(placement_seed_max: int) -> dict[str, Any]:
    return {
        "key": "placement_seed",
        "label": "Placement seed (random distribution)",
        "type": "int",
        "min": 0,
        "max": placement_seed_max,
        "default": 0,
    }


def spider_eye_control_defs(
    *,
    placement_clustering_min: float,
    placement_clustering_max: float,
    default_placement_clustering: float,
    distribution_modes: tuple[str, ...],
    default_distribution: str,
) -> list[dict[str, Any]]:
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
            "options": list(distribution_modes),
            "default": default_distribution,
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
            "min": placement_clustering_min,
            "max": placement_clustering_max,
            "step": 0.05,
            "default": default_placement_clustering,
            "unit": "0–1",
            "hint": "How tightly grouped vs spread eyes are when placement is random (multi-eye only).",
        },
    ]

"""Per-limb / per-joint feature control defs (extracted for module size limits)."""




def _part_feature_control_defs(slug: str) -> list[dict[str, Any]]:
    """Optional per-limb / per-joint material keys (flat API); merged into ``features[*].parts``."""
    ensure_blender_stubs()
    try:
        from enemies.animated.registry import AnimatedEnemyBuilder
    except ImportError:
        from src.enemies.animated.registry import AnimatedEnemyBuilder

    cls = AnimatedEnemyBuilder.ENEMY_CLASSES.get(slug)
    if cls is None:
        return []
    defs: list[dict[str, Any]] = []
    if slug in ("imp", "carapace_husk"):
        n_arm = max(1, min(8, int(getattr(cls, "ARM_SEGMENTS", 1))))
        n_leg = max(1, min(8, int(getattr(cls, "LEG_SEGMENTS", 1))))
        jvis = bool(getattr(cls, "LIMB_JOINT_VISUAL", False))
        for label_base, idx_prefix, n_seg in (
            ("Arm", "arm", n_arm),
            ("Leg", "leg", n_leg),
        ):
            for side in range(2):
                pid = f"{idx_prefix}_{side}"
                defs.append(
                    {
                        "key": f"feat_limb_{pid}_finish",
                        "label": f"{label_base} {side} (limb) finish",
                        "type": "select_str",
                        "options": list(_FINISH_OPTIONS_ORDER),
                        "default": "default",
                    }
                )
                defs.append(
                    {
                        "key": f"feat_limb_{pid}_hex",
                        "label": f"{label_base} {side} (limb) hex",
                        "type": "str",
                        "default": "",
                    }
                )
                if jvis:
                    for ji in range(max(0, n_seg - 1)):
                        jpid = f"{idx_prefix}_{side}_j{ji}"
                        defs.append(
                            {
                                "key": f"feat_joint_{jpid}_finish",
                                "label": f"{label_base} {side} joint {ji} finish",
                                "type": "select_str",
                                "options": list(_FINISH_OPTIONS_ORDER),
                                "default": "default",
                            }
                        )
                        defs.append(
                            {
                                "key": f"feat_joint_{jpid}_hex",
                                "label": f"{label_base} {side} joint {ji} hex",
                                "type": "str",
                                "default": "",
                            }
                        )
    if slug == "spider":
        for leg in range(8):
            pid = f"leg_{leg}"
            defs.append(
                {
                    "key": f"feat_limb_{pid}_finish",
                    "label": f"Leg {leg} cylinders finish",
                    "type": "select_str",
                    "options": list(_FINISH_OPTIONS_ORDER),
                    "default": "default",
                }
            )
            defs.append(
                {
                    "key": f"feat_limb_{pid}_hex",
                    "label": f"Leg {leg} cylinders hex",
                    "type": "str",
                    "default": "",
                }
            )
            for jn in ("root", "knee", "ankle", "foot"):
                jpid = f"leg_{leg}_{jn}"
                defs.append(
                    {
                        "key": f"feat_joint_{jpid}_finish",
                        "label": f"Leg {leg} joint ({jn}) finish",
                        "type": "select_str",
                        "options": list(_FINISH_OPTIONS_ORDER),
                        "default": "default",
                    }
                )
                defs.append(
                    {
                        "key": f"feat_joint_{jpid}_hex",
                        "label": f"Leg {leg} joint ({jn}) hex",
                        "type": "str",
                        "default": "",
                    }
                )
    return defs
