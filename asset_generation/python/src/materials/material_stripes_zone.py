"""Blender material factory for projection-based object-space stripe patterns."""

from __future__ import annotations

import math
import re

import bpy

from .gradient_generator import create_stripes_png_and_load
from .presets import (
    ENEMY_FINISH_PRESETS,
    MaterialColors,
    parse_hex_color,
    rgba_from_hex_or_fallback,
    sanitize_hex_input,
)
from .texture_handlers import create_material


def _sanitize_image_label_local(label: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9_]+", "_", str(label or "stripe").strip())
    return (raw[:48] or "stripe").lstrip("_") or "stripe"


def _canonical_stripe_rotation_key(
    *,
    rot_yaw_deg: float,
    rot_pitch_deg: float,
    rot_roll_deg: float = 0.0,
) -> tuple[str, str, str]:
    """Canonical rotation key based on the texture generator's effective transform.

    The stripe generator applies:
    - yaw directly as an angle in direction projection (mod 360 equivalent)
    - pitch via cos(radians(pitch)) vertical scaling (periodic + even)
    - roll as phase offset (mod 360 equivalent)
    """
    yaw_key = f"{(float(rot_yaw_deg) % 360.0):06.2f}"
    roll_key = f"{(float(rot_roll_deg) % 360.0):06.2f}"
    pitch_scale = math.cos(math.radians(float(rot_pitch_deg)))
    pitch_key = f"{pitch_scale:+.4f}"
    return pitch_key, yaw_key, roll_key


def _base_angle_deg_for_preset(preset: str) -> float:
    p = str(preset or "beachball").strip().lower()
    if p in ("y", "doplar", "horizontal"):
        return 90.0
    if p in ("z", "swirl"):
        return 60.0
    return 0.0


def _stripe_direction_vector(
    *,
    stripe_preset: str,
    rot_yaw_deg: float,
    rot_pitch_deg: float,
) -> tuple[float, float, float]:
    """Build normalized object-space stripe direction from preset+yaw+pitch."""
    final_yaw = math.radians(_base_angle_deg_for_preset(stripe_preset) + float(rot_yaw_deg))
    pitch = math.radians(float(rot_pitch_deg))
    x = math.cos(final_yaw) * math.cos(pitch)
    y = math.sin(pitch)
    z = math.sin(final_yaw) * math.cos(pitch)
    length = math.sqrt((x * x) + (y * y) + (z * z))
    if length <= 1e-8:
        return (1.0, 0.0, 0.0)
    return (x / length, y / length, z / length)


def _find_principled_bsdf(nodes: object) -> object | None:
    for node in nodes:
        if getattr(node, "type", None) == "BSDF_PRINCIPLED":
            return node
        if getattr(node, "bl_idname", "") == "ShaderNodeBsdfPrincipled":
            return node
    return None


def _principled_base_color_socket(bsdf: object) -> object | None:
    socket = bsdf.inputs.get("Base Color")
    if socket is None:
        socket = bsdf.inputs.get("Color")
    return socket


def _rgba_to_rrggbb(rgba: tuple[float, ...]) -> str:
    """Pack RGBA float tuple into 6-char hex for PNG texture generation."""
    r = int(max(0, min(255, round(float(rgba[0]) * 255.0))))
    g = int(max(0, min(255, round(float(rgba[1]) * 255.0))))
    b = int(max(0, min(255, round(float(rgba[2]) * 255.0))))
    return f"{r:02x}{g:02x}{b:02x}"


def _add_object_space_stripes_to_principled(
    *,
    mat: bpy.types.Material,
    stripe_rgba: tuple[float, float, float, float],
    bg_rgba: tuple[float, float, float, float],
    stripe_width: float,
    stripe_preset: str,
    rot_yaw_deg: float,
    rot_pitch_deg: float,
    rot_roll_deg: float,
) -> None:
    """Drive Principled base color with object-space projected hard stripes."""
    nt = mat.node_tree
    if nt is None:
        return
    nodes = nt.nodes
    links = nt.links
    bsdf = _find_principled_bsdf(nodes)
    if bsdf is None:
        return
    bc_in = _principled_base_color_socket(bsdf)
    if bc_in is None:
        return
    for lk in list(bc_in.links):
        links.remove(lk)

    dir_x, dir_y, dir_z = _stripe_direction_vector(
        stripe_preset=stripe_preset,
        rot_yaw_deg=rot_yaw_deg,
        rot_pitch_deg=rot_pitch_deg,
    )
    period = max(0.05, min(1.0, float(stripe_width)))
    frequency = 1.0 / period
    phase_offset = float(rot_roll_deg) / 360.0

    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-1200, 200)
    separate_xyz = nodes.new(type="ShaderNodeSeparateXYZ")
    separate_xyz.location = (-1000, 200)
    object_out = tex_coord.outputs.get("Object")
    if object_out is None:
        object_out = tex_coord.outputs.get("Generated")
    if object_out is None:
        # Keep existing base color if coordinate source is unavailable.
        return
    links.new(object_out, separate_xyz.inputs["Vector"])

    mul_x = nodes.new(type="ShaderNodeMath")
    mul_x.location = (-800, 300)
    mul_x.operation = "MULTIPLY"
    mul_x.inputs[1].default_value = dir_x
    links.new(separate_xyz.outputs["X"], mul_x.inputs[0])

    mul_y = nodes.new(type="ShaderNodeMath")
    mul_y.location = (-800, 200)
    mul_y.operation = "MULTIPLY"
    mul_y.inputs[1].default_value = dir_y
    links.new(separate_xyz.outputs["Y"], mul_y.inputs[0])

    mul_z = nodes.new(type="ShaderNodeMath")
    mul_z.location = (-800, 100)
    mul_z.operation = "MULTIPLY"
    mul_z.inputs[1].default_value = dir_z
    links.new(separate_xyz.outputs["Z"], mul_z.inputs[0])

    add_xy = nodes.new(type="ShaderNodeMath")
    add_xy.location = (-620, 240)
    add_xy.operation = "ADD"
    links.new(mul_x.outputs["Value"], add_xy.inputs[0])
    links.new(mul_y.outputs["Value"], add_xy.inputs[1])

    add_xyz = nodes.new(type="ShaderNodeMath")
    add_xyz.location = (-460, 220)
    add_xyz.operation = "ADD"
    links.new(add_xy.outputs["Value"], add_xyz.inputs[0])
    links.new(mul_z.outputs["Value"], add_xyz.inputs[1])

    add_phase = nodes.new(type="ShaderNodeMath")
    add_phase.location = (-300, 220)
    add_phase.operation = "ADD"
    add_phase.inputs[1].default_value = phase_offset
    links.new(add_xyz.outputs["Value"], add_phase.inputs[0])

    mul_freq = nodes.new(type="ShaderNodeMath")
    mul_freq.location = (-140, 220)
    mul_freq.operation = "MULTIPLY"
    mul_freq.inputs[1].default_value = frequency
    links.new(add_phase.outputs["Value"], mul_freq.inputs[0])

    frac = nodes.new(type="ShaderNodeMath")
    frac.location = (20, 220)
    frac.operation = "FRACT"
    links.new(mul_freq.outputs["Value"], frac.inputs[0])

    less_than = nodes.new(type="ShaderNodeMath")
    less_than.location = (180, 220)
    less_than.operation = "LESS_THAN"
    less_than.inputs[1].default_value = 0.5
    links.new(frac.outputs["Value"], less_than.inputs[0])

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (380, 220)
    mix.blend_type = "MIX"
    fac_in = mix.inputs.get("Fac") or mix.inputs.get("Factor")
    color1_in = mix.inputs.get("Color1") or mix.inputs.get("A")
    color2_in = mix.inputs.get("Color2") or mix.inputs.get("B")
    if fac_in is None or color1_in is None or color2_in is None:
        return
    color1_in.default_value = bg_rgba
    color2_in.default_value = stripe_rgba
    links.new(less_than.outputs["Value"], fac_in)

    color_out = mix.outputs.get("Color")
    if color_out is None:
        return
    links.new(color_out, bc_in)


def material_for_stripes_zone(
    *,
    base_palette_name: str,
    finish: str,
    stripe_hex: str,
    bg_hex: str,
    stripe_width: float,
    stripe_preset: str,
    rot_yaw_deg: float,
    rot_pitch_deg: float,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Stripe material with mixed strategy: doplar=object-space, others=baked texture."""
    all_colors = MaterialColors.get_all()
    palette_base = all_colors.get(base_palette_name)
    if palette_base is None:
        palette_base = (0.6, 0.5, 0.5, 1.0)
    h_zone = sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(h_zone) if len(h_zone) == 6 else palette_base

    stripe_color = rgba_from_hex_or_fallback(stripe_hex, zone_rgba)
    bg_rgba = rgba_from_hex_or_fallback(bg_hex, (1.0, 1.0, 1.0, 1.0))

    finish_roughness, _finish_metallic, finish_transmission = ENEMY_FINISH_PRESETS.get(
        finish,
        ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = finish != "default"
    metallic = 0.0
    roughness = 0.75
    if finish_roughness is not None:
        roughness = finish_roughness
    transmission = finish_transmission if finish_transmission is not None else 0.0
    alpha = stripe_color[3] if len(stripe_color) > 3 else 1.0

    sw = max(0.05, min(1.0, float(stripe_width)))
    # Use canonicalized rotation keys so equivalent transforms map to one material key.
    rot_x_key, rot_y_key, rot_z_key = _canonical_stripe_rotation_key(
        rot_yaw_deg=rot_yaw_deg,
        rot_pitch_deg=rot_pitch_deg,
        rot_roll_deg=0.0,
    )
    new_name = (
        f"{base_palette_name}__feat_{instance_suffix}"
        f"_p{rot_x_key}_y{rot_y_key}_z{rot_z_key}"
    )
    mat = create_material(
        name=new_name,
        color=stripe_color,
        metallic=metallic,
        roughness=roughness,
        alpha=alpha,
        transmission=transmission,
        add_texture=False,
        force_surface=force_surface,
        force_base_color=False,
    )
    preset = str(stripe_preset or "beachball").strip().lower()
    use_object_space_projection = preset == "doplar"

    if use_object_space_projection:
        # Mark for export-time bake so GLTF viewers can match Blender procedural look.
        mat["blobert_stripe_procedural"] = True
        _add_object_space_stripes_to_principled(
            mat=mat,
            stripe_rgba=(
                float(stripe_color[0]),
                float(stripe_color[1]),
                float(stripe_color[2]),
                float(stripe_color[3]),
            ),
            bg_rgba=(
                float(bg_rgba[0]),
                float(bg_rgba[1]),
                float(bg_rgba[2]),
                float(bg_rgba[3]),
            ),
            stripe_width=sw,
            stripe_preset=preset,
            rot_yaw_deg=float(rot_yaw_deg),
            rot_pitch_deg=float(rot_pitch_deg),
            rot_roll_deg=0.0,
        )
    else:
        # Preserve legacy baked-texture behavior for beachball/swirl patterns.
        safe = _sanitize_image_label_local(instance_suffix)
        img_name = (
            f"BlobertTexStripe_{safe}"
            f"_p{rot_x_key}_y{rot_y_key}_z{rot_z_key}_{preset}"
        )
        img = create_stripes_png_and_load(
            width=256,
            height=256,
            stripe_color_hex=_rgba_to_rrggbb(stripe_color),
            bg_color_hex=_rgba_to_rrggbb(bg_rgba),
            stripe_width=sw,
            img_name=img_name,
            stripe_preset=preset,
            rot_x_deg=float(rot_pitch_deg),
            rot_y_deg=float(rot_yaw_deg),
            rot_z_deg=0.0,
        )
        nt = mat.node_tree
        if nt is not None:
            nodes = nt.nodes
            links = nt.links
            bsdf = _find_principled_bsdf(nodes)
            if bsdf is not None:
                bc_in = _principled_base_color_socket(bsdf)
                if bc_in is not None:
                    for lk in list(bc_in.links):
                        links.remove(lk)
                    tex = nodes.new(type="ShaderNodeTexImage")
                    tex.location = (-450, 200)
                    tex.image = img
                    tex.interpolation = "Linear"
                    tex.extension = "REPEAT"
                    uv = nodes.new(type="ShaderNodeUVMap")
                    uv.location = (-700, 200)
                    links.new(uv.outputs["UV"], tex.inputs["Vector"])
                    links.new(tex.outputs["Color"], bc_in)

    return mat
