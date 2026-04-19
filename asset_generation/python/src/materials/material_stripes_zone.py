"""Blender material factory for baked horizontal-stripes textures."""

from __future__ import annotations

import bpy

from ..utils.materials import MaterialColors
from .gradient_generator import _sanitize_image_label, create_stripes_png_and_load


def _material_for_stripes_zone(
    *,
    base_palette_name: str,
    finish: str,
    stripe_hex: str,
    bg_hex: str,
    stripe_width: float,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Solid base material with baked horizontal stripes texture."""
    from . import material_system as ms

    all_colors = MaterialColors.get_all()
    palette_base = all_colors.get(base_palette_name)
    if palette_base is None:
        palette_base = (0.6, 0.5, 0.5, 1.0)
    h_zone = ms._sanitize_hex_input(zone_hex_fallback)
    zone_rgba = ms._parse_hex_color(h_zone) if len(h_zone) == 6 else palette_base

    stripe_color = ms._rgba_from_hex_or_fallback(stripe_hex, zone_rgba)

    finish_roughness, _finish_metallic, finish_transmission = ms.ENEMY_FINISH_PRESETS.get(
        finish,
        ms.ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = finish != "default"
    metallic = 0.0
    roughness = 0.75
    if finish_roughness is not None:
        roughness = finish_roughness
    transmission = finish_transmission if finish_transmission is not None else 0.0
    alpha = stripe_color[3] if len(stripe_color) > 3 else 1.0

    new_name = f"{base_palette_name}__feat_{instance_suffix}"
    mat = ms.create_material(
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

    safe = _sanitize_image_label(instance_suffix)
    img_name = f"BlobertTexStripe_{safe}"
    img = create_stripes_png_and_load(
        width=128,
        height=128,
        stripe_color_hex=ms._sanitize_hex_input(stripe_hex),
        bg_color_hex=ms._sanitize_hex_input(bg_hex),
        stripe_width=stripe_width,
        img_name=img_name,
    )

    nt = mat.node_tree
    if nt is not None:
        nodes = nt.nodes
        links = nt.links
        bsdf = ms._find_principled_bsdf(nodes)
        if bsdf is not None:
            bc_in = ms._principled_base_color_socket(bsdf)
            if bc_in is not None:
                tex = nodes.new(type="ShaderNodeTexImage")
                tex.location = (-450, 200)
                tex.image = img
                tex.interpolation = "Linear"
                tex.extension = "REPEAT"

                uv = nodes.new(type="ShaderNodeUVMap")
                uv.location = (-800, 200)
                links.new(uv.outputs["UV"], tex.inputs["Vector"])
                links.new(tex.outputs["Color"], bc_in)

    return mat
