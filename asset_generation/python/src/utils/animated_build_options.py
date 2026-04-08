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

# Material finish keys (keep aligned with materials.material_system.ENEMY_FINISH_PRESETS).
_VALID_FINISHES: frozenset[str] = frozenset({"default", "glossy", "matte", "metallic", "gel"})
_FINISH_OPTIONS_ORDER: tuple[str, ...] = ("default", "glossy", "matte", "metallic", "gel")

# Per-slug material feature slots merged into build_options["features"].
# ``joints`` is used for hinge / ball meshes when the rig exposes them (humanoid joint balls, spider leg spheres).
_FEATURE_ZONES_BY_SLUG: dict[str, tuple[str, ...]] = {
    "imp": ("body", "head", "limbs", "joints", "extra"),
    "carapace_husk": ("body", "head", "limbs", "joints", "extra"),
    "spider": ("body", "head", "limbs", "joints", "extra"),
    "slug": ("body", "extra"),
}

_FEAT_ZONE_FLAT_KEY = re.compile(r"^feat_(body|head|limbs|joints|extra)_(finish|hex)$")
_FEAT_LIMB_PART_FLAT_KEY = re.compile(r"^feat_limb_([a-z0-9_]+)_(finish|hex)$")
_FEAT_JOINT_PART_FLAT_KEY = re.compile(r"^feat_joint_([a-z0-9_]+)_(finish|hex)$")


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


def _feature_zones(slug: str) -> tuple[str, ...]:
    return _FEATURE_ZONES_BY_SLUG.get(slug, ("body",))


def _default_features_dict(slug: str) -> dict[str, dict[str, str]]:
    return {z: {"finish": "default", "hex": ""} for z in _feature_zones(slug)}


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


def _merge_features_for_slug(slug: str, src: dict[str, Any], feat_base: dict[str, Any]) -> dict[str, Any]:
    zones = _feature_zones(slug)
    out: dict[str, Any] = {}
    for z in zones:
        b = feat_base.get(z)
        if isinstance(b, dict):
            out[z] = {"finish": str(b.get("finish", "default")), "hex": str(b.get("hex", ""))}
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
        merged = (
            static
            + _mesh_float_control_defs(slug)
            + _feature_control_defs(slug)
            + _part_feature_control_defs(slug)
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
    mesh = _mesh_numeric_defaults(slug)
    out["mesh"] = dict(mesh)
    out["features"] = _default_features_dict(slug)
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
        if k in ("mesh", "features"):
            continue
        if (
            _FEAT_ZONE_FLAT_KEY.match(k)
            or _FEAT_LIMB_PART_FLAT_KEY.match(k)
            or _FEAT_JOINT_PART_FLAT_KEY.match(k)
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
