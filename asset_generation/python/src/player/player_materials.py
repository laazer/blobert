"""
Materials for the player slime character.

The slime uses a high-gloss Principled BSDF with low roughness to achieve
the characteristic shiny, wet-candy look. Eye highlights use near-zero
roughness for a mirror-like reflection.
"""

from typing import Tuple

import bpy

Color = Tuple[float, float, float, float]  # RGBA 0.0–1.0
FinishSettings = Tuple[float, float, float]  # roughness, metallic, transmission

# ------------------------------------------------------------------
# Slime body palette — eight color variants
# ------------------------------------------------------------------

SLIME_COLORS = {
    "blue":   (0.12, 0.72, 0.95, 1.0),
    "green":  (0.18, 0.85, 0.38, 1.0),
    "pink":   (0.98, 0.40, 0.65, 1.0),
    "purple": (0.62, 0.28, 0.92, 1.0),
    "yellow": (0.98, 0.88, 0.15, 1.0),
    "orange": (0.98, 0.55, 0.12, 1.0),
    "red":    (0.95, 0.20, 0.22, 1.0),
    "white":  (0.92, 0.95, 0.98, 1.0),
}

SLIME_FINISHES: dict[str, FinishSettings] = {
    "glossy": (0.05, 0.0, 0.0),
    "matte": (0.55, 0.0, 0.0),
    "metallic": (0.25, 0.65, 0.0),
    "gel": (0.08, 0.0, 0.35),
}

# Eye and accessory colors — consistent regardless of body color
SCLERA_WHITE: Color = (0.98, 0.98, 0.98, 1.0)
PUPIL_DARK: Color = (0.05, 0.05, 0.12, 1.0)
HIGHLIGHT_WHITE: Color = (1.00, 1.00, 1.00, 1.0)
CHEEK_PINK: Color = (0.97, 0.60, 0.72, 1.0)


def _apply_principled_inputs(principled, **kwargs):
    """Set Principled BSDF inputs by name; silently skip unknown names.

    Handles the Blender 3.x / 4.x rename differences gracefully.
    """
    for name, value in kwargs.items():
        if name in principled.inputs:
            principled.inputs[name].default_value = value


def _parse_hex_color(hex_value: str) -> Color:
    """Convert '#RRGGBB' (or 'RRGGBB') to RGBA in [0,1]."""
    raw = (hex_value or "").strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError("hex color must be 6 characters (RRGGBB)")
    try:
        r = int(raw[0:2], 16) / 255.0
        g = int(raw[2:4], 16) / 255.0
        b = int(raw[4:6], 16) / 255.0
    except ValueError as error:
        raise ValueError("hex color must be valid hexadecimal") from error
    return (r, g, b, 1.0)


def create_slime_body_material(
    color_name: str = "blue",
    finish: str = "glossy",
    custom_color_hex: str = "",
) -> bpy.types.Material:
    """Create the main slime body material — glossy, candy-like."""
    base_color = _parse_hex_color(custom_color_hex) if custom_color_hex else SLIME_COLORS.get(color_name, SLIME_COLORS["blue"])
    roughness, metallic, transmission = SLIME_FINISHES.get(finish, SLIME_FINISHES["glossy"])

    material_name = f"slime_body_{color_name}_{finish}"
    if custom_color_hex:
        material_name = f"slime_body_custom_{custom_color_hex.strip().lstrip('#')}_{finish}"
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True

    nodes = material.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    _apply_principled_inputs(
        principled,
        **{
            "Base Color": base_color,
            "Roughness": roughness,
            "Metallic": metallic,
            "Transmission Weight": transmission,
            "Transmission": transmission,
        },
    )

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    return material


def create_sclera_material() -> bpy.types.Material:
    """Slightly glossy white for eye whites."""
    material = bpy.data.materials.new(name="slime_eye_sclera")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    _apply_principled_inputs(
        principled,
        **{"Base Color": SCLERA_WHITE, "Roughness": 0.15},
    )

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return material


def create_pupil_material() -> bpy.types.Material:
    """Dark blue-black for eye pupils."""
    material = bpy.data.materials.new(name="slime_eye_pupil")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    _apply_principled_inputs(
        principled,
        **{"Base Color": PUPIL_DARK, "Roughness": 0.35},
    )

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return material


def create_highlight_material() -> bpy.types.Material:
    """Pure-white near-mirror material for the bright eye glint."""
    material = bpy.data.materials.new(name="slime_eye_highlight")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    _apply_principled_inputs(
        principled,
        **{"Base Color": HIGHLIGHT_WHITE, "Roughness": 0.0},
    )

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return material


def create_cheek_material() -> bpy.types.Material:
    """Soft, matte rose-pink for the blush marks."""
    material = bpy.data.materials.new(name="slime_cheek")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    _apply_principled_inputs(
        principled,
        **{"Base Color": CHEEK_PINK, "Roughness": 0.55},
    )

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    return material
