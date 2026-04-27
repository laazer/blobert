"""Blender-side attachment handlers for zone-geometry extras."""

from __future__ import annotations

import math
from typing import Any

import bpy
from mathutils import Vector

from ...core.blender_utils import create_cone, create_sphere
from ...materials.material_system import (
    apply_feature_slot_overrides,
    apply_material_to_object,
    apply_zone_texture_pattern_overrides,
    get_enemy_materials,
    material_for_zone_geometry_extra,
)
from ...utils.build_options import OFFSET_XYZ_MAX, OFFSET_XYZ_MIN
from ...utils.placement_clustering import (
    clustered_ellipsoid_angles_bounded,
    placement_prng,
    uniform_arc_angles,
    uniform_ring_angles,
)

try:
    from ...player.player_materials import create_slime_body_material
except ImportError:  # pragma: no cover - fallback for direct src package imports in tests/tools
    from src.player.player_materials import create_slime_body_material
from .geometry_math import (
    body_ref_size,
    ellipsoid_normal,
    ellipsoid_point_at,
    head_ref_size,
    vec_xyz,
    zone_extra_scale,
)
from .placement_strategy import (
    FACING_DOT_MIN,
    PLACE_KEYS,
    PLACE_WORLD,
    zone_distribution,
    zone_extra_clustering,
    zone_uniform_shape,
)


def _orient_cone_outward(obj: bpy.types.Object, outward: Vector) -> None:
    z_axis = Vector((0.0, 0.0, 1.0))
    ol = outward.length
    out = Vector((0.0, 0.0, 1.0)) if ol < 1e-9 else outward * (1.0 / ol)
    rot = z_axis.rotation_difference(out)
    to_euler = getattr(rot, "to_euler", None)
    obj.rotation_euler = to_euler() if callable(to_euler) else (0.0, 0.0, 0.0)


def _legacy_zone_extra_offset(spec: dict[str, Any], axis: str) -> float:
    try:
        v = float(spec.get(axis, 0.0))
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(v):
        return 0.0
    return max(OFFSET_XYZ_MIN, min(OFFSET_XYZ_MAX, v))


def _legacy_facing_allows_normal(spec: dict[str, Any], nrm: Vector) -> bool:
    flags = [bool(spec.get(k, True)) for k in PLACE_KEYS]
    if not any(flags):
        return True
    if all(flags):
        return True
    ol = nrm.length
    if ol < 1e-12:
        return False
    nn = nrm * (1.0 / ol)
    for key, on in zip(PLACE_KEYS, flags):
        if not on:
            continue
        if nn.dot(PLACE_WORLD[key]) >= FACING_DOT_MIN:
            return True
    return False


def append_animated_enemy_zone_extras(model: Any) -> None:
    """Attach zone extras for animated enemy models."""
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
    slot_mats = apply_feature_slot_overrides(enemy_mats, feat_dict, model.build_options)
    slot_mats = apply_zone_texture_pattern_overrides(slot_mats, model.build_options)

    body_spec = raw.get("body")
    if bc is not None and br is not None and isinstance(body_spec, dict):
        append_body_ellipsoid_extras(
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
            append_head_ellipsoid_extras(
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


def append_body_ellipsoid_extras(
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
    ref = body_ref_size(a, b, h)
    cx += _legacy_zone_extra_offset(spec, "offset_x")
    cy += _legacy_zone_extra_offset(spec, "offset_y")
    cz += _legacy_zone_extra_offset(spec, "offset_z")

    if kind == "spikes":
        n = max(1, int(spec.get("spike_count", 8)))
        spike_sz = zone_extra_scale(spec, "spike_size")
        cl = zone_extra_clustering(spec)
        dist_m = zone_distribution(spec)
        u_shape = zone_uniform_shape(spec)
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
                    p = ellipsoid_point_at(cx, cy, cz, a, b, h, t1, t2)
                    nrm = Vector(ellipsoid_normal(cx, cy, cz, a, b, h, p))
                    if not _legacy_facing_allows_normal(spec, nrm):
                        continue
                    tip = Vector(p) + nrm * depth
                    cone = create_cone(
                        location=vec_xyz(tip),
                        scale=(rad, rad, depth),
                        vertices=verts,
                        depth=1.0,
                        radius1=0.4,
                        radius2=0.0,
                    )
                    _orient_cone_outward(cone, nrm)
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
                p = ellipsoid_point_at(cx, cy, cz, a, b, h, t1, t2)
                nrm = Vector(ellipsoid_normal(cx, cy, cz, a, b, h, p))
                if not _legacy_facing_allows_normal(spec, nrm):
                    continue
                tip = Vector(p) + nrm * depth
                cone = create_cone(
                    location=vec_xyz(tip),
                    scale=(rad, rad, depth),
                    vertices=verts,
                    depth=1.0,
                    radius1=0.4,
                    radius2=0.0,
                )
                _orient_cone_outward(cone, nrm)
                apply_material_to_object(cone, mat)
                model.parts.append(cone)
                placed += 1
    elif kind == "shell":
        shell_s = zone_extra_scale(spec, "shell_scale", default=1.08, lo=1.01, hi=1.5)
        shell_obj = create_sphere(location=(cx, cy, cz), scale=(a * shell_s, b * shell_s, h * shell_s))
        apply_material_to_object(shell_obj, mat)
        model.parts.append(shell_obj)
    elif kind == "bulbs":
        nb = max(1, int(spec.get("bulb_count", 4)))
        bulb_sz = zone_extra_scale(spec, "bulb_size")
        cl = zone_extra_clustering(spec)
        dist_m = zone_distribution(spec)
        u_shape = zone_uniform_shape(spec)
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
                    p = ellipsoid_point_at(cx, cy, cz, aa, bb, hh, t1, t2)
                    nrm = Vector(ellipsoid_normal(cx, cy, cz, a, b, h, p))
                    if not _legacy_facing_allows_normal(spec, nrm):
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
                p = ellipsoid_point_at(cx, cy, cz, aa, bb, hh, t1, t2)
                nrm = Vector(ellipsoid_normal(cx, cy, cz, a, b, h, p))
                if not _legacy_facing_allows_normal(spec, nrm):
                    continue
                bulb = create_sphere(location=p, scale=(br, br, br))
                apply_material_to_object(bulb, mat)
                model.parts.append(bulb)
                placed += 1


def append_head_ellipsoid_extras(
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
    ref = head_ref_size(ax, ay, az)
    hx += _legacy_zone_extra_offset(spec, "offset_x")
    hy += _legacy_zone_extra_offset(spec, "offset_y")
    hz += _legacy_zone_extra_offset(spec, "offset_z")

    if kind == "horns":
        spike_sz = zone_extra_scale(spec, "spike_size")
        cl = zone_extra_clustering(spec)
        horn_spread = 1.0 - cl * 0.88
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        rad = ref * 0.18 * spike_sz
        depth = ref * 0.42 * spike_sz
        for side in (-1, 1):
            p = (
                hx + ax * 0.3,
                hy + float(side) * ay * 0.35 * horn_spread,
                hz + az * 0.5,
            )
            nrm = Vector(ellipsoid_normal(hx, hy, hz, ax, ay, az, p))
            if not _legacy_facing_allows_normal(spec, nrm):
                continue
            tip = Vector(p) + nrm * depth
            cone = create_cone(
                location=vec_xyz(tip),
                scale=(rad, rad, depth),
                vertices=verts,
                depth=1.0,
                radius1=0.35,
                radius2=0.0,
            )
            _orient_cone_outward(cone, nrm)
            apply_material_to_object(cone, mat)
            model.parts.append(cone)
    elif kind == "spikes":
        spike_sz = zone_extra_scale(spec, "spike_size")
        cl = zone_extra_clustering(spec)
        dist_m = zone_distribution(spec)
        u_shape = zone_uniform_shape(spec)
        shape = str(spec.get("spike_shape", "cone"))
        verts = 4 if shape == "pyramid" else 10
        count = max(1, int(spec.get("spike_count", 4)))
        rad = ref * 0.18 * spike_sz
        depth = ref * 0.4 * spike_sz
        prng = placement_prng(model)
        phi_lo, phi_hi = 0.15 * math.pi, 0.7 * math.pi
        placed = 0

        def _head_point(t1: float, t2: float) -> tuple[tuple[float, float, float], Vector]:
            p = (
                hx + ax * math.sin(t2) * math.cos(t1),
                hy + ay * math.sin(t2) * math.sin(t1),
                hz + az * math.cos(t2),
            )
            nrm = Vector(ellipsoid_normal(hx, hy, hz, ax, ay, az, p))
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
                    if not _legacy_facing_allows_normal(spec, nrm):
                        continue
                    tip = Vector(p) + nrm * depth
                    cone = create_cone(
                        location=vec_xyz(tip),
                        scale=(rad, rad, depth),
                        vertices=verts,
                        depth=1.0,
                        radius1=0.35,
                        radius2=0.0,
                    )
                    _orient_cone_outward(cone, nrm)
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
                if not _legacy_facing_allows_normal(spec, nrm):
                    continue
                tip = Vector(p) + nrm * depth
                cone = create_cone(
                    location=vec_xyz(tip),
                    scale=(rad, rad, depth),
                    vertices=verts,
                    depth=1.0,
                    radius1=0.35,
                    radius2=0.0,
                )
                _orient_cone_outward(cone, nrm)
                apply_material_to_object(cone, mat)
                model.parts.append(cone)
                placed += 1
    elif kind == "shell":
        shell_s = zone_extra_scale(spec, "shell_scale", default=1.08, lo=1.01, hi=1.5)
        shell_obj = create_sphere(location=(hx, hy, hz), scale=(ax * shell_s, ay * shell_s, az * shell_s))
        apply_material_to_object(shell_obj, mat)
        model.parts.append(shell_obj)
    elif kind == "bulbs":
        nb = max(1, int(spec.get("bulb_count", 3)))
        bulb_sz = zone_extra_scale(spec, "bulb_size")
        cl = zone_extra_clustering(spec)
        dist_m = zone_distribution(spec)
        u_shape = zone_uniform_shape(spec)
        br = ref * 0.17 * bulb_sz
        prng = placement_prng(model)
        phi_lo, phi_hi = 0.2 * math.pi, 0.8 * math.pi
        placed = 0

        def _head_bulb_point(t1: float, t2: float) -> tuple[tuple[float, float, float], Vector]:
            p = (
                hx + ax * 0.45 * math.sin(t2) * math.cos(t1),
                hy + ay * 0.45 * math.sin(t2) * math.sin(t1),
                hz + az * 0.45 * math.cos(t2),
            )
            nrm = Vector(ellipsoid_normal(hx, hy, hz, ax, ay, az, p))
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
                    if not _legacy_facing_allows_normal(spec, nrm):
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
                if not _legacy_facing_allows_normal(spec, nrm):
                    continue
                bulb = create_sphere(location=p, scale=(br, br, br))
                apply_material_to_object(bulb, mat)
                model.parts.append(bulb)
                placed += 1


def append_player_slime_zone_extras(builder: Any) -> None:
    """Attach body/head zone extras for procedural player slime before mesh join."""
    opts = getattr(builder, "build_options", None)
    if not isinstance(opts, dict):
        return
    raw = opts.get("zone_geometry_extras")
    if not isinstance(raw, dict):
        return

    color = getattr(builder, "color", "blue")
    finish = getattr(builder, "_resolved_body_finish", getattr(builder, "finish", "glossy"))
    custom_hex = str(getattr(builder, "_resolved_body_custom_hex", getattr(builder, "custom_color_hex", "") or ""))
    body_mat = create_slime_body_material(color, finish=finish, custom_color_hex=custom_hex)
    slot_mats: dict[str, bpy.types.Material | None] = {
        "body": body_mat,
        "head": body_mat,
        "limbs": body_mat,
        "joints": body_mat,
        "extra": body_mat,
    }
    features = opts.get("features")
    feat_dict = features if isinstance(features, dict) else None

    extras = getattr(builder, "_zone_extra_parts", None)
    if not isinstance(extras, list):
        return

    brx = float(getattr(builder, "BODY_RADIUS_XY", 1.0))
    brz = float(getattr(builder, "BODY_RADIUS_Z", 0.8))
    bcx, bcy, bcz = 0.0, 0.0, brz

    ey = float(getattr(builder, "EYE_OFFSET_Y", 0.84))
    ez = float(getattr(builder, "EYE_OFFSET_Z", 1.05))
    sx, sy, sz = getattr(builder, "SCLERA_SCALE", (0.22, 0.12, 0.22))
    hx, hy, hz = 0.0, ey, ez
    ax = float(sx) * 1.25
    ay = float(sy) * 1.25
    az = float(sz) * 1.25

    class _PlayerSlimeZoneExtrasModel:
        __slots__ = ("parts", "build_options", "rng")

        def __init__(self, parts: list[Any], build_options: dict[str, Any], rng: Any) -> None:
            self.parts = parts
            self.build_options = build_options
            self.rng = rng

    model = _PlayerSlimeZoneExtrasModel(extras, opts, getattr(builder, "rng", None))

    body_spec = raw.get("body")
    if isinstance(body_spec, dict):
        append_body_ellipsoid_extras(
            model,
            body_spec,
            slot_mats,
            feat_dict,
            bcx,
            bcy,
            bcz,
            brx,
            brx,
            brz,
        )

    head_spec = raw.get("head")
    if isinstance(head_spec, dict) and max(ax, ay, az) > 1e-8:
        append_head_ellipsoid_extras(model, head_spec, slot_mats, feat_dict, hx, hy, hz, ax, ay, az)
