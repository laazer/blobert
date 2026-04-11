"""Attach procedural zone geometry extras (spikes, bulbs, horns) for supported enemies."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Vector

from ..core.blender_utils import create_cone, create_sphere
from ..materials.material_system import (
    apply_feature_slot_overrides,
    apply_material_to_object,
    get_enemy_materials,
    material_for_zone_geometry_extra,
)
from ..utils.animated_build_options import _OFFSET_XYZ_MAX, _OFFSET_XYZ_MIN
from ..utils.placement_clustering import (
    clamp01,
    clustered_ellipsoid_angles_bounded,
    placement_prng,
    uniform_arc_angles,
    uniform_ring_angles,
)


def _vec_xyz(v: Vector) -> tuple[float, float, float]:
    if hasattr(v, "x"):
        return (float(v.x), float(v.y), float(v.z))
    inner = getattr(v, "_t", None)
    if inner is not None and len(inner) >= 3:
        return (float(inner[0]), float(inner[1]), float(inner[2]))
    return (0.0, 0.0, 0.0)


def _ellipsoid_point_at(
    cx: float, cy: float, cz: float, a: float, b: float, h: float, theta: float, phi: float
) -> tuple[float, float, float]:
    x = cx + a * math.sin(phi) * math.cos(theta)
    y = cy + b * math.sin(phi) * math.sin(theta)
    z = cz + h * math.cos(phi)
    return (x, y, z)


def _ellipsoid_normal(cx: float, cy: float, cz: float, a: float, b: float, h: float, p: tuple[float, float, float]) -> Vector:
    vx, vy, vz = p[0] - cx, p[1] - cy, p[2] - cz
    nx, ny, nz = vx / (a * a), vy / (b * b), vz / (h * h)
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    if ln < 1e-9:
        return Vector((0.0, 0.0, 1.0))
    return Vector((nx / ln, ny / ln, nz / ln))


def _zone_extra_clustering(spec: dict[str, Any]) -> float:
    return clamp01(spec.get("clustering"), 0.5)


def _zone_distribution(spec: dict[str, Any]) -> str:
    v = str(spec.get("distribution", "uniform")).strip().lower()
    return v if v in ("random", "uniform") else "uniform"


def _zone_uniform_shape(spec: dict[str, Any]) -> str:
    v = str(spec.get("uniform_shape", "arc")).strip().lower()
    return v if v in ("arc", "ring") else "arc"


def _zone_extra_scale(spec: dict[str, Any], key: str, default: float = 1.0, lo: float = 0.25, hi: float = 3.0) -> float:
    try:
        s = float(spec.get(key, default))
    except (TypeError, ValueError):
        s = default
    if math.isnan(s):
        s = default
    elif math.isinf(s):
        s = lo if s < 0 else hi
    return max(lo, min(hi, s))


def _zone_extra_offset(spec: dict[str, Any], axis: str) -> float:
    try:
        v = float(spec.get(axis, 0.0))
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    return max(_OFFSET_XYZ_MIN, min(_OFFSET_XYZ_MAX, v))


# World axes (Blender Z-up): extras spawn only where the surface normal aligns with enabled facings.
_PLACE_KEYS: tuple[str, ...] = (
    "place_top",
    "place_bottom",
    "place_front",
    "place_back",
    "place_left",
    "place_right",
)
_PLACE_WORLD: dict[str, Vector] = {
    "place_top": Vector((0.0, 0.0, 1.0)),
    "place_bottom": Vector((0.0, 0.0, -1.0)),
    "place_front": Vector((1.0, 0.0, 0.0)),
    "place_back": Vector((-1.0, 0.0, 0.0)),
    "place_right": Vector((0.0, 1.0, 0.0)),
    "place_left": Vector((0.0, -1.0, 0.0)),
}
_FACING_DOT_MIN = 0.45


def _place_flags(spec: dict[str, Any]) -> list[bool]:
    return [bool(spec.get(k, True)) for k in _PLACE_KEYS]


def _facing_allows_normal(spec: dict[str, Any], nrm: Vector) -> bool:
    flags = _place_flags(spec)
    if not any(flags):
        return True
    if all(flags):
        return True
    ol = nrm.length
    if ol < 1e-12:
        return False
    nn = nrm * (1.0 / ol)
    for k, on in zip(_PLACE_KEYS, flags):
        if not on:
            continue
        if nn.dot(_PLACE_WORLD[k]) >= _FACING_DOT_MIN:
            return True
    return False


def _body_ref_scale(a: float, b: float, h: float) -> float:
    """Characteristic length from body semi-axes (scales spike/bulb mesh with creature size)."""
    ax = max(1e-6, abs(a))
    ay = max(1e-6, abs(b))
    az = max(1e-6, abs(h))
    return float((ax * ay * az) ** (1.0 / 3.0))


def _head_ref_scale(ax: float, ay: float, az: float) -> float:
    u = max(1e-6, abs(ax), abs(ay), abs(az))
    return float(u)


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


def append_animated_enemy_zone_extras(model: Any) -> None:
    """Attach ``zone_geometry_extras`` body/head geometry for any animated enemy that set ``_zone_geom_*`` in ``build_mesh_parts``."""
    raw = model.build_options.get("zone_geometry_extras")
    if not isinstance(raw, dict):
        return

    theme = getattr(model, "name", None)
    if not isinstance(theme, str) or not theme:
        return

    bc = getattr(model, "_zone_geom_body_center", None)
    br = getattr(model, "_zone_geom_body_radii", None)
    hc = getattr(model, "_zone_geom_head_center", None)
    hr = getattr(model, "_zone_geom_head_radii", None)

    features = model.build_options.get("features")
    feat_dict = features if isinstance(features, dict) else None
    enemy_mats = get_enemy_materials(theme, model.materials, model.rng)
    slot_mats = apply_feature_slot_overrides(enemy_mats, feat_dict)

    body_spec = raw.get("body")
    if bc is not None and br is not None and isinstance(body_spec, dict):
        _append_body_ellipsoid_extras(
            model,
            body_spec,
            slot_mats,
            feat_dict,
            float(bc.x),
            float(bc.y),
            float(bc.z),
            float(br.x),
            float(br.y),
            float(br.z),
        )

    head_spec = raw.get("head")
    if hc is not None and hr is not None and isinstance(head_spec, dict):
        ax, ay, az = float(hr.x), float(hr.y), float(hr.z)
        if max(ax, ay, az) > 1e-8:
            _append_head_ellipsoid_extras(
                model,
                head_spec,
                slot_mats,
                feat_dict,
                float(hc.x),
                float(hc.y),
                float(hc.z),
                ax,
                ay,
                az,
            )


def append_slug_zone_extras(model: Any) -> None:
    """Backward-compatible entry: slug instances only."""
    from .animated_slug import AnimatedSlug

    if isinstance(model, AnimatedSlug):
        append_animated_enemy_zone_extras(model)


def append_spider_zone_extras(model: Any) -> None:
    """Backward-compatible entry: spider instances only."""
    from .animated_spider import AnimatedSpider

    if isinstance(model, AnimatedSpider):
        append_animated_enemy_zone_extras(model)


def _append_body_ellipsoid_extras(
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
    ref = _body_ref_scale(a, b, h)
    cx += _zone_extra_offset(spec, "offset_x")
    cy += _zone_extra_offset(spec, "offset_y")
    cz += _zone_extra_offset(spec, "offset_z")
    if kind == "spikes":
        n = max(1, int(spec.get("spike_count", 8)))
        spike_sz = _zone_extra_scale(spec, "spike_size")
        cl = _zone_extra_clustering(spec)
        dist_m = _zone_distribution(spec)
        u_shape = _zone_uniform_shape(spec)
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        rad = ref * 0.22 * spike_sz
        depth = ref * 0.48 * spike_sz
        prng = placement_prng(model)
        placed = 0
        if dist_m == "uniform":
            for i in range(n):
                for attempt in range(48):
                    phase = attempt * 0.21
                    if u_shape == "ring":
                        t1, t2 = uniform_ring_angles(
                            i,
                            n,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_a=0.22 * math.pi,
                            phi_b=0.78 * math.pi,
                            clustering=cl,
                        )
                    else:
                        t1, t2 = uniform_arc_angles(
                            i,
                            n,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_lo=0.0,
                            phi_hi=math.pi,
                            clustering=cl,
                        )
                    t1 = (t1 + phase) % (2.0 * math.pi)
                    p = _ellipsoid_point_at(cx, cy, cz, a, b, h, t1, t2)
                    nrm = _ellipsoid_normal(cx, cy, cz, a, b, h, p)
                    if not _facing_allows_normal(spec, nrm):
                        continue
                    tip = Vector(p) + nrm * depth
                    cone = create_cone(
                        location=_vec_xyz(tip),
                        scale=(rad, rad, depth),
                        vertices=verts,
                        depth=1.0,
                        radius1=0.4,
                        radius2=0.0,
                    )
                    _orient_cone_outward(cone, (cx, cy, cz), nrm)
                    apply_material_to_object(cone, mat)
                    model.parts.append(cone)
                    placed += 1
                    break
        else:
            max_attempts = max(300, n * 60)
            attempts = 0
            while placed < n and attempts < max_attempts:
                attempts += 1
                t1, t2 = clustered_ellipsoid_angles_bounded(
                    prng,
                    cl,
                    theta_lo=0.0,
                    theta_hi=2.0 * math.pi,
                    phi_lo=0.0,
                    phi_hi=math.pi,
                )
                p = _ellipsoid_point_at(cx, cy, cz, a, b, h, t1, t2)
                nrm = _ellipsoid_normal(cx, cy, cz, a, b, h, p)
                if not _facing_allows_normal(spec, nrm):
                    continue
                tip = Vector(p) + nrm * depth
                cone = create_cone(
                    location=_vec_xyz(tip),
                    scale=(rad, rad, depth),
                    vertices=verts,
                    depth=1.0,
                    radius1=0.4,
                    radius2=0.0,
                )
                _orient_cone_outward(cone, (cx, cy, cz), nrm)
                apply_material_to_object(cone, mat)
                model.parts.append(cone)
                placed += 1
    elif kind == "shell":
        shell_s = _zone_extra_scale(spec, "shell_scale", default=1.08, lo=1.01, hi=1.5)
        shell_obj = create_sphere(
            location=(cx, cy, cz),
            scale=(a * shell_s, b * shell_s, h * shell_s),
        )
        apply_material_to_object(shell_obj, mat)
        model.parts.append(shell_obj)
    elif kind == "bulbs":
        nb = max(1, int(spec.get("bulb_count", 4)))
        bulb_sz = _zone_extra_scale(spec, "bulb_size")
        cl = _zone_extra_clustering(spec)
        dist_m = _zone_distribution(spec)
        u_shape = _zone_uniform_shape(spec)
        br = ref * 0.2 * bulb_sz
        prng = placement_prng(model)
        aa, bb, hh = a * 0.92, b * 0.92, h * 0.92
        placed = 0
        if dist_m == "uniform":
            for i in range(nb):
                for attempt in range(48):
                    phase = attempt * 0.19
                    if u_shape == "ring":
                        t1, t2 = uniform_ring_angles(
                            i,
                            nb,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_a=0.28 * math.pi,
                            phi_b=0.72 * math.pi,
                            clustering=cl,
                        )
                    else:
                        t1, t2 = uniform_arc_angles(
                            i,
                            nb,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_lo=0.0,
                            phi_hi=math.pi,
                            clustering=cl,
                        )
                    t1 = (t1 + phase) % (2.0 * math.pi)
                    p = _ellipsoid_point_at(cx, cy, cz, aa, bb, hh, t1, t2)
                    nrm = _ellipsoid_normal(cx, cy, cz, a, b, h, p)
                    if not _facing_allows_normal(spec, nrm):
                        continue
                    bulb = create_sphere(location=p, scale=(br, br, br))
                    apply_material_to_object(bulb, mat)
                    model.parts.append(bulb)
                    placed += 1
                    break
        else:
            max_attempts = max(400, nb * 80)
            attempts = 0
            while placed < nb and attempts < max_attempts:
                attempts += 1
                t1, t2 = clustered_ellipsoid_angles_bounded(
                    prng,
                    cl,
                    theta_lo=0.0,
                    theta_hi=2.0 * math.pi,
                    phi_lo=0.0,
                    phi_hi=math.pi,
                )
                p = _ellipsoid_point_at(cx, cy, cz, aa, bb, hh, t1, t2)
                nrm = _ellipsoid_normal(cx, cy, cz, a, b, h, p)
                if not _facing_allows_normal(spec, nrm):
                    continue
                bulb = create_sphere(location=p, scale=(br, br, br))
                apply_material_to_object(bulb, mat)
                model.parts.append(bulb)
                placed += 1


def _append_head_ellipsoid_extras(
    model: Any,
    spec: dict[str, Any],
    slot_mats: dict[str, bpy.types.Material | None],
    features: dict[str, Any] | None,
    hx: float,
    hy: float,
    hz: float,
    ax: float,
    ay: float,
    az: float,
) -> None:
    kind = str(spec.get("kind", "none"))
    mat = material_for_zone_geometry_extra(
        "head",
        slot_mats,
        features,
        str(spec.get("finish", "default")),
        str(spec.get("hex", "")),
    )
    ref = _head_ref_scale(ax, ay, az)
    hx += _zone_extra_offset(spec, "offset_x")
    hy += _zone_extra_offset(spec, "offset_y")
    hz += _zone_extra_offset(spec, "offset_z")
    hc = (hx, hy, hz)

    if kind == "horns":
        spike_sz = _zone_extra_scale(spec, "spike_size")
        cl = _zone_extra_clustering(spec)
        horn_spread = 1.0 - cl * 0.88
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        rad = ref * 0.18 * spike_sz
        depth = ref * 0.42 * spike_sz
        for side in (-1, 1):
            px = hx + ax * 0.3
            py = hy + float(side) * ay * 0.35 * horn_spread
            pz = hz + az * 0.5
            p = (px, py, pz)
            nrm = _ellipsoid_normal(hx, hy, hz, ax, ay, az, p)
            if not _facing_allows_normal(spec, nrm):
                continue
            tip = Vector(p) + nrm * depth
            cone = create_cone(
                location=_vec_xyz(tip),
                scale=(rad, rad, depth),
                vertices=verts,
                depth=1.0,
                radius1=0.35,
                radius2=0.0,
            )
            _orient_cone_outward(cone, hc, nrm)
            apply_material_to_object(cone, mat)
            model.parts.append(cone)
    elif kind == "spikes":
        spike_sz = _zone_extra_scale(spec, "spike_size")
        cl = _zone_extra_clustering(spec)
        dist_m = _zone_distribution(spec)
        u_shape = _zone_uniform_shape(spec)
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        count = max(1, int(spec.get("spike_count", 4)))
        rad = ref * 0.18 * spike_sz
        depth = ref * 0.4 * spike_sz
        prng = placement_prng(model)
        phi_lo, phi_hi = 0.15 * math.pi, 0.7 * math.pi
        placed = 0

        def _head_point(t1: float, t2: float) -> tuple[tuple[float, float, float], Vector]:
            px = hx + ax * math.sin(t2) * math.cos(t1)
            py = hy + ay * math.sin(t2) * math.sin(t1)
            pz = hz + az * math.cos(t2)
            p = (px, py, pz)
            nrm = _ellipsoid_normal(hx, hy, hz, ax, ay, az, p)
            return p, nrm

        if dist_m == "uniform":
            for i in range(count):
                for attempt in range(48):
                    phase = attempt * 0.18
                    if u_shape == "ring":
                        t1, t2 = uniform_ring_angles(
                            i,
                            count,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_a=phi_lo + 0.06 * math.pi,
                            phi_b=phi_hi - 0.06 * math.pi,
                            clustering=cl,
                        )
                    else:
                        t1, t2 = uniform_arc_angles(
                            i,
                            count,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_lo=phi_lo,
                            phi_hi=phi_hi,
                            clustering=cl,
                        )
                    t1 = (t1 + phase) % (2.0 * math.pi)
                    p, nrm = _head_point(t1, t2)
                    if not _facing_allows_normal(spec, nrm):
                        continue
                    tip = Vector(p) + nrm * depth
                    cone = create_cone(
                        location=_vec_xyz(tip),
                        scale=(rad, rad, depth),
                        vertices=verts,
                        depth=1.0,
                        radius1=0.35,
                        radius2=0.0,
                    )
                    _orient_cone_outward(cone, hc, nrm)
                    apply_material_to_object(cone, mat)
                    model.parts.append(cone)
                    placed += 1
                    break
        else:
            max_attempts = max(300, count * 60)
            attempts = 0
            while placed < count and attempts < max_attempts:
                attempts += 1
                t1, t2 = clustered_ellipsoid_angles_bounded(
                    prng,
                    cl,
                    theta_lo=0.0,
                    theta_hi=2.0 * math.pi,
                    phi_lo=phi_lo,
                    phi_hi=phi_hi,
                )
                p, nrm = _head_point(t1, t2)
                if not _facing_allows_normal(spec, nrm):
                    continue
                tip = Vector(p) + nrm * depth
                cone = create_cone(
                    location=_vec_xyz(tip),
                    scale=(rad, rad, depth),
                    vertices=verts,
                    depth=1.0,
                    radius1=0.35,
                    radius2=0.0,
                )
                _orient_cone_outward(cone, hc, nrm)
                apply_material_to_object(cone, mat)
                model.parts.append(cone)
                placed += 1
    elif kind == "shell":
        shell_s = _zone_extra_scale(spec, "shell_scale", default=1.08, lo=1.01, hi=1.5)
        shell_obj = create_sphere(
            location=(hx, hy, hz),
            scale=(ax * shell_s, ay * shell_s, az * shell_s),
        )
        apply_material_to_object(shell_obj, mat)
        model.parts.append(shell_obj)
    elif kind == "bulbs":
        nb = max(1, int(spec.get("bulb_count", 3)))
        bulb_sz = _zone_extra_scale(spec, "bulb_size")
        cl = _zone_extra_clustering(spec)
        dist_m = _zone_distribution(spec)
        u_shape = _zone_uniform_shape(spec)
        br = ref * 0.17 * bulb_sz
        prng = placement_prng(model)
        phi_lo, phi_hi = 0.2 * math.pi, 0.8 * math.pi
        placed = 0

        def _head_bulb_point(t1: float, t2: float) -> tuple[tuple[float, float, float], Vector]:
            px = hx + ax * 0.45 * math.sin(t2) * math.cos(t1)
            py = hy + ay * 0.45 * math.sin(t2) * math.sin(t1)
            pz = hz + az * 0.45 * math.cos(t2)
            p = (px, py, pz)
            nrm = _ellipsoid_normal(hx, hy, hz, ax, ay, az, p)
            return p, nrm

        if dist_m == "uniform":
            for i in range(nb):
                for attempt in range(48):
                    phase = attempt * 0.17
                    if u_shape == "ring":
                        t1, t2 = uniform_ring_angles(
                            i,
                            nb,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_a=phi_lo + 0.05 * math.pi,
                            phi_b=phi_hi - 0.05 * math.pi,
                            clustering=cl,
                        )
                    else:
                        t1, t2 = uniform_arc_angles(
                            i,
                            nb,
                            theta_lo=0.0,
                            theta_hi=2.0 * math.pi,
                            phi_lo=phi_lo,
                            phi_hi=phi_hi,
                            clustering=cl,
                        )
                    t1 = (t1 + phase) % (2.0 * math.pi)
                    p, nrm = _head_bulb_point(t1, t2)
                    if not _facing_allows_normal(spec, nrm):
                        continue
                    bulb = create_sphere(location=p, scale=(br, br, br))
                    apply_material_to_object(bulb, mat)
                    model.parts.append(bulb)
                    placed += 1
                    break
        else:
            max_attempts = max(400, nb * 80)
            attempts = 0
            while placed < nb and attempts < max_attempts:
                attempts += 1
                t1, t2 = clustered_ellipsoid_angles_bounded(
                    prng,
                    cl,
                    theta_lo=0.0,
                    theta_hi=2.0 * math.pi,
                    phi_lo=phi_lo,
                    phi_hi=phi_hi,
                )
                p, nrm = _head_bulb_point(t1, t2)
                if not _facing_allows_normal(spec, nrm):
                    continue
                bulb = create_sphere(location=p, scale=(br, br, br))
                apply_material_to_object(bulb, mat)
                model.parts.append(bulb)
                placed += 1
