"""Blender material factory: UV-mapped baked stripes (glTF / Three.js preview compatible)."""

from __future__ import annotations

import bpy

from .gradient_generator import _sanitize_image_label, create_stripes_png_and_load
from .presets import (
    ENEMY_FINISH_PRESETS,
    MaterialColors,
    parse_hex_color,
    rgba_from_hex_or_fallback,
    sanitize_hex_input,
)
from .texture_handlers import create_material


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
    """Pack linear-ish RGBA into 6-char hex for the PNG generator."""
    r = int(max(0, min(255, round(float(rgba[0]) * 255.0))))
    g = int(max(0, min(255, round(float(rgba[1]) * 255.0))))
    b = int(max(0, min(255, round(float(rgba[2]) * 255.0))))
    return f"{r:02x}{g:02x}{b:02x}"


def _material_for_stripes_zone(
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
    """Solid base material with baked stripes texture (same pattern as spots → glTF export)."""
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
    safe = _sanitize_image_label(instance_suffix)
    # Include rotation angles and preset in names to avoid material/texture cache collisions.
    rot_y_int = int(round(rot_yaw_deg)) % 360
    rot_x_int = int(round(rot_pitch_deg)) % 360
    new_name = f"{base_palette_name}__feat_{instance_suffix}_p{rot_x_int}_y{rot_y_int}"
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

    img_name = f"BlobertTexStripe_{safe}_p{rot_x_int}_y{rot_y_int}_{stripe_preset}"
    # Rotation mapping: pitch (x-axis rotation) + yaw (y-axis rotation); z always 0.
    img = create_stripes_png_and_load(
        width=256,
        height=256,
        stripe_color_hex=_rgba_to_rrggbb(stripe_color),
        bg_color_hex=_rgba_to_rrggbb(bg_rgba),
        stripe_width=sw,
        img_name=img_name,
        stripe_preset=stripe_preset,
        rot_x_deg=float(rot_pitch_deg),  # Pitch rotates around X axis
        rot_y_deg=float(rot_yaw_deg),    # Yaw rotates around Y axis
        rot_z_deg=0.0,                    # Z rotation not exposed in UI
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
                uv.location = (-800, 200)

                # Rotation is applied during texture generation, not in shader
                # Just apply UV coordinates directly to texture
                links.new(uv.outputs["UV"], tex.inputs["Vector"])

                links.new(tex.outputs["Color"], bc_in)

    return mat
