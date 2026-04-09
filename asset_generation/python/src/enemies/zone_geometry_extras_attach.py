"""Attach procedural zone geometry extras (spikes, bulbs, horns) for supported enemies."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Vector

from ..core.blender_utils import create_cone, create_sphere


def _vec_xyz(v: Vector) -> tuple[float, float, float]:
    if hasattr(v, "x"):
        return (float(v.x), float(v.y), float(v.z))
    inner = getattr(v, "_t", None)
    if inner is not None and len(inner) >= 3:
        return (float(inner[0]), float(inner[1]), float(inner[2]))
    return (0.0, 0.0, 0.0)
from ..core.rig_models.blob_simple import MESH_BODY_CENTER_Z_FACTOR
from ..materials.material_system import (
    apply_feature_slot_overrides,
    apply_material_to_object,
    get_enemy_materials,
    material_for_zone_geometry_extra,
)


def _ellipsoid_point(cz: float, a: float, b: float, h: float, theta: float, phi: float) -> tuple[float, float, float]:
    x = a * math.sin(phi) * math.cos(theta)
    y = b * math.sin(phi) * math.sin(theta)
    z = cz + h * math.cos(phi)
    return (x, y, z)


def _ellipsoid_normal(cx: float, cy: float, cz: float, a: float, b: float, h: float, p: tuple[float, float, float]) -> Vector:
    vx, vy, vz = p[0] - cx, p[1] - cy, p[2] - cz
    nx, ny, nz = vx / (a * a), vy / (b * b), vz / (h * h)
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    if ln < 1e-9:
        return Vector((0.0, 0.0, 1.0))
    return Vector((nx / ln, ny / ln, nz / ln))


def _orient_cone_outward(obj: bpy.types.Object, _base_center: tuple[float, float, float], outward: Vector) -> None:
    z_axis = Vector((0.0, 0.0, 1.0))
    ol = outward.length
    if ol < 1e-9:
        out = Vector((0.0, 0.0, 1.0))
    else:
        out = outward * (1.0 / ol)
    rot = z_axis.rotation_difference(out)
    to_euler = getattr(rot, "to_euler", None)
    if callable(to_euler):
        obj.rotation_euler = to_euler()
    else:
        obj.rotation_euler = (0.0, 0.0, 0.0)


def append_slug_zone_extras(model: Any) -> None:
    from .animated_slug import AnimatedSlug

    if not isinstance(model, AnimatedSlug):
        return

    raw = model.build_options.get("zone_geometry_extras")
    if not isinstance(raw, dict):
        return

    features = model.build_options.get("features")
    feat_dict = features if isinstance(features, dict) else None
    enemy_mats = get_enemy_materials("slug", model.materials, model.rng)
    slot_mats = apply_feature_slot_overrides(enemy_mats, feat_dict)

    cz = model.height * MESH_BODY_CENTER_Z_FACTOR
    cx, cy = 0.0, 0.0
    a, b, h = model.length, model.width, model.height

    body_spec = raw.get("body")
    if isinstance(body_spec, dict):
        _append_slug_body_extras(model, body_spec, slot_mats, feat_dict, cx, cy, cz, a, b, h)

    head_spec = raw.get("head")
    if isinstance(head_spec, dict):
        _append_slug_head_extras(model, head_spec, slot_mats, feat_dict)


def _append_slug_body_extras(
    model: Any,
    spec: dict[str, Any],
    slot_mats: dict[str, bpy.types.Material | None],
    features: dict[str, Any] | None,
    cx: float,
    cy: float,
    cz: float,
    a: float,
    b: float,
    h: float,
) -> None:
    kind = str(spec.get("kind", "none"))
    mat = material_for_zone_geometry_extra(
        "body",
        slot_mats,
        features,
        str(spec.get("finish", "default")),
        str(spec.get("hex", "")),
    )
    if kind == "spikes":
        n = max(1, int(spec.get("spike_count", 8)))
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        for i in range(n):
            theta = (2.0 * math.pi * i) / max(1, n)
            phi = math.pi * 0.5
            p = _ellipsoid_point(cz, a, b, h, theta, phi)
            nrm = _ellipsoid_normal(cx, cy, cz, a, b, h, p)
            tip = Vector(p) + nrm * 0.12
            cone = create_cone(
                location=_vec_xyz(tip),
                scale=(0.06, 0.06, 0.12),
                vertices=verts,
                depth=1.0,
                radius1=0.4,
                radius2=0.0,
            )
            _orient_cone_outward(cone, (cx, cy, cz), nrm)
            apply_material_to_object(cone, mat)
            model.parts.append(cone)
    elif kind == "bulbs":
        nb = max(1, int(spec.get("bulb_count", 4)))
        for _ in range(nb):
            t1 = model.rng.random() * 2.0 * math.pi
            t2 = model.rng.random() * math.pi
            p = _ellipsoid_point(cz, a * 0.92, b * 0.92, h * 0.92, t1, t2)
            bulb = create_sphere(location=p, scale=(0.07, 0.07, 0.07))
            apply_material_to_object(bulb, mat)
            model.parts.append(bulb)


def _append_slug_head_extras(
    model: Any,
    spec: dict[str, Any],
    slot_mats: dict[str, bpy.types.Material | None],
    features: dict[str, Any] | None,
) -> None:
    kind = str(spec.get("kind", "none"))
    mat = material_for_zone_geometry_extra(
        "head",
        slot_mats,
        features,
        str(spec.get("finish", "default")),
        str(spec.get("hex", "")),
    )
    head_scale = model.width * float(model._mesh("HEAD_WIDTH_RATIO"))
    hx = model.length * float(model._mesh("HEAD_X_RATIO"))
    hz = model.height * float(model._mesh("HEAD_Z_RATIO"))
    hc = (hx, 0.0, hz)

    if kind == "horns":
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        for side in (-1, 1):
            px = hx + head_scale * 0.3
            py = float(side) * head_scale * 0.35
            pz = hz + head_scale * 0.5
            p = (px, py, pz)
            nrm = _ellipsoid_normal(hx, 0.0, hz, head_scale, head_scale, head_scale, p)
            tip = Vector(p) + nrm * 0.08
            cone = create_cone(
                location=_vec_xyz(tip),
                scale=(0.05, 0.05, 0.14),
                vertices=verts,
                depth=1.0,
                radius1=0.35,
                radius2=0.0,
            )
            _orient_cone_outward(cone, hc, nrm)
            apply_material_to_object(cone, mat)
            model.parts.append(cone)
    elif kind == "spikes":
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        count = max(1, int(spec.get("spike_count", 4)))
        for si in range(count):
            angle = (2.0 * math.pi * si) / max(1, count)
            px = hx + head_scale * 0.4 * math.cos(angle)
            py = head_scale * 0.4 * math.sin(angle)
            pz = hz + head_scale * 0.55
            p = (px, py, pz)
            nrm = _ellipsoid_normal(hx, 0.0, hz, head_scale, head_scale, head_scale, p)
            tip = Vector(p) + nrm * 0.08
            cone = create_cone(
                location=_vec_xyz(tip),
                scale=(0.05, 0.05, 0.12),
                vertices=verts,
                depth=1.0,
                radius1=0.35,
                radius2=0.0,
            )
            _orient_cone_outward(cone, hc, nrm)
            apply_material_to_object(cone, mat)
            model.parts.append(cone)
    elif kind == "bulbs":
        nb = max(1, int(spec.get("bulb_count", 3)))
        for _ in range(nb):
            t1 = model.rng.random() * 2.0 * math.pi
            t2 = model.rng.random() * 0.6 * math.pi + 0.2 * math.pi
            px = hx + head_scale * 0.45 * math.sin(t2) * math.cos(t1)
            py = head_scale * 0.45 * math.sin(t2) * math.sin(t1)
            pz = hz + head_scale * 0.45 * math.cos(t2)
            bulb = create_sphere(location=(px, py, pz), scale=(0.06, 0.06, 0.06))
            apply_material_to_object(bulb, mat)
            model.parts.append(bulb)
