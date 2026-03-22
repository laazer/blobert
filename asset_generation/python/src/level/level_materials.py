"""
Material helpers for level objects.

All level objects are static meshes — they need simple, readable materials
rather than the procedural biological/elemental system used for enemies.
"""

import bpy
from typing import Tuple

Color = Tuple[float, float, float, float]  # RGBA, 0.0–1.0

# ------------------------------------------------------------------
# Named material colors
# ------------------------------------------------------------------

STONE_GREY: Color = (0.50, 0.50, 0.50, 1.0)
MOVING_BLUE: Color = (0.30, 0.40, 0.70, 1.0)
CRUMBLE_BROWN: Color = (0.45, 0.35, 0.28, 1.0)
WALL_DARK: Color = (0.38, 0.38, 0.38, 1.0)
METAL_GREY: Color = (0.55, 0.55, 0.58, 1.0)
IRON_DARK: Color = (0.18, 0.18, 0.20, 1.0)
FIRE_ORANGE: Color = (0.90, 0.42, 0.08, 1.0)
CHECKPOINT_STONE: Color = (0.42, 0.42, 0.48, 1.0)
CHECKPOINT_BEAM: Color = (1.00, 0.85, 0.20, 1.0)


def create_solid_material(name: str, base_color: Color) -> bpy.types.Material:
    """Create a Principled BSDF material with a solid base color."""
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True

    nodes = material.node_tree.nodes
    nodes.clear()

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.inputs['Base Color'].default_value = base_color

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(
        principled.outputs['BSDF'], output.inputs['Surface']
    )

    return material


def create_emissive_material(
    name: str,
    base_color: Color,
    emission_strength: float = 2.0,
) -> bpy.types.Material:
    """Create a glowing emissive material (checkpoint beams, active trap glow)."""
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True

    nodes = material.node_tree.nodes
    nodes.clear()

    emission = nodes.new(type='ShaderNodeEmission')
    emission.inputs['Color'].default_value = base_color
    emission.inputs['Strength'].default_value = emission_strength

    output = nodes.new(type='ShaderNodeOutputMaterial')
    material.node_tree.links.new(
        emission.outputs['Emission'], output.inputs['Surface']
    )

    return material
