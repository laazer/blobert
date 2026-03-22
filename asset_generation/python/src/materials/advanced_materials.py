"""
Advanced Material System - Enhanced procedural textures and effects
"""

import bpy
import random
from typing import Dict, List, Tuple, Optional
from .material_system import MATERIAL_COLORS


def create_layered_material(name: str, layers: List[Dict]) -> bpy.types.Material:
    """Create complex multi-layered materials
    
    Args:
        name: Material name
        layers: List of layer definitions with type, strength, scale, etc.
    """
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Clear existing nodes
    nodes.clear()
    
    # Create main nodes
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # Position main nodes
    bsdf.location = (0, 0)
    output.location = (400, 0)
    
    # Process layers from bottom to top
    current_color_input = None
    current_roughness_input = None
    y_offset = 0
    
    for i, layer in enumerate(layers):
        layer_type = layer.get('type', 'base')
        strength = layer.get('strength', 1.0)
        
        if layer_type == 'base':
            _add_base_layer(nodes, links, bsdf, layer, y_offset)
        elif layer_type == 'wear':
            current_color_input = _add_wear_layer(nodes, links, current_color_input or bsdf.inputs["Base Color"], layer, y_offset)
        elif layer_type == 'detail':
            current_roughness_input = _add_detail_layer(nodes, links, current_roughness_input or bsdf.inputs["Roughness"], layer, y_offset)
        elif layer_type == 'glow':
            _add_glow_layer(nodes, links, bsdf, layer, y_offset)
        elif layer_type == 'animated':
            _add_animated_layer(nodes, links, bsdf, layer, y_offset)
        
        y_offset -= 200
    
    return mat


def _add_base_layer(nodes, links, bsdf, layer, y_offset):
    """Add base material layer"""
    color = layer.get('color', (0.5, 0.5, 0.5, 1.0))
    metallic = layer.get('metallic', 0.0)
    roughness = layer.get('roughness', 0.5)
    
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness


def _add_wear_layer(nodes, links, base_input, layer, y_offset):
    """Add wear/aging effects to material"""
    # Create wear mask using noise
    wear_noise = nodes.new(type='ShaderNodeTexNoise')
    wear_noise.location = (-800, y_offset)
    wear_noise.inputs["Scale"].default_value = layer.get('scale', 15.0)
    wear_noise.inputs["Detail"].default_value = layer.get('detail', 8.0)
    
    # Create worn color (darker, different hue)
    worn_color = layer.get('worn_color', (0.3, 0.2, 0.1, 1.0))
    
    # Mix original and worn colors
    color_mix = nodes.new(type='ShaderNodeMixRGB')
    color_mix.location = (-400, y_offset)
    color_mix.blend_type = 'MIX'
    color_mix.inputs["Color2"].default_value = worn_color
    
    # Use noise to control mixing
    links.new(wear_noise.outputs["Fac"], color_mix.inputs["Fac"])
    links.new(base_input, color_mix.inputs["Color1"])
    
    return color_mix.outputs["Color"]


def _add_detail_layer(nodes, links, base_input, layer, y_offset):
    """Add fine surface details"""
    detail_noise = nodes.new(type='ShaderNodeTexNoise')
    detail_noise.location = (-600, y_offset)
    detail_noise.inputs["Scale"].default_value = layer.get('scale', 50.0)
    detail_noise.inputs["Detail"].default_value = layer.get('detail', 15.0)
    
    # Math node to adjust intensity
    math_node = nodes.new(type='ShaderNodeMath')
    math_node.location = (-400, y_offset)
    math_node.operation = 'MULTIPLY'
    math_node.inputs[1].default_value = layer.get('strength', 0.3)
    
    # Add to existing roughness
    add_node = nodes.new(type='ShaderNodeMath')
    add_node.location = (-200, y_offset)
    add_node.operation = 'ADD'
    
    links.new(detail_noise.outputs["Fac"], math_node.inputs[0])
    links.new(math_node.outputs["Value"], add_node.inputs[0])
    links.new(base_input, add_node.inputs[1])
    
    return add_node.outputs["Value"]


def _add_glow_layer(nodes, links, bsdf, layer, y_offset):
    """Add emissive glow effects"""
    glow_color = layer.get('glow_color', (1.0, 0.3, 0.1, 1.0))
    glow_strength = layer.get('strength', 2.0)
    
    # Set emission properties
    bsdf.inputs["Emission Color"].default_value = glow_color
    bsdf.inputs["Emission Strength"].default_value = glow_strength
    
    # Optional: Add noise modulation for flickering
    if layer.get('flicker', False):
        flicker_noise = nodes.new(type='ShaderNodeTexNoise')
        flicker_noise.location = (-600, y_offset)
        flicker_noise.inputs["Scale"].default_value = 2.0
        
        # Math to create flicker effect
        math_flicker = nodes.new(type='ShaderNodeMath')
        math_flicker.location = (-400, y_offset)
        math_flicker.operation = 'MULTIPLY'
        math_flicker.inputs[1].default_value = glow_strength
        
        links.new(flicker_noise.outputs["Fac"], math_flicker.inputs[0])
        links.new(math_flicker.outputs["Value"], bsdf.inputs["Emission Strength"])


def _add_animated_layer(nodes, links, bsdf, layer, y_offset):
    """Add time-based animation to materials"""
    # Use object info or geometry nodes for animation drivers
    # This is a placeholder - actual implementation would use drivers
    pass


def create_damage_variant(base_material_name: str, damage_level: float) -> bpy.types.Material:
    """Create damaged version of existing material
    
    Args:
        base_material_name: Name of base material to damage
        damage_level: 0.0 (pristine) to 1.0 (heavily damaged)
    """
    damaged_name = f"{base_material_name}_damaged_{int(damage_level * 100)}"
    
    # Define damage effects based on damage level
    damage_layers = [
        {'type': 'base', 'color': MATERIAL_COLORS.get(base_material_name, (0.5, 0.5, 0.5, 1.0))},
        {'type': 'wear', 'strength': damage_level, 'worn_color': (0.2, 0.15, 0.1, 1.0)},
        {'type': 'detail', 'strength': damage_level * 0.5, 'scale': 80.0}
    ]
    
    return create_layered_material(damaged_name, damage_layers)


def create_environmental_variant(base_material_name: str, environment: str) -> bpy.types.Material:
    """Create environment-adapted material variant
    
    Args:
        base_material_name: Base material to adapt
        environment: 'swamp', 'desert', 'arctic', 'volcanic', 'toxic'
    """
    env_name = f"{base_material_name}_{environment}"
    base_color = MATERIAL_COLORS.get(base_material_name, (0.5, 0.5, 0.5, 1.0))
    
    env_layers = [{'type': 'base', 'color': base_color}]
    
    if environment == 'swamp':
        # Add mud and moisture effects
        env_layers.extend([
            {'type': 'wear', 'strength': 0.6, 'worn_color': (0.3, 0.25, 0.1, 1.0)},  # Mud
            {'type': 'glow', 'glow_color': (0.2, 0.4, 0.1, 1.0), 'strength': 0.3}     # Slime glow
        ])
    
    elif environment == 'volcanic':
        # Add heat effects and ember glow
        env_layers.extend([
            {'type': 'wear', 'strength': 0.4, 'worn_color': (0.4, 0.2, 0.1, 1.0)},    # Heat damage
            {'type': 'glow', 'glow_color': (1.0, 0.3, 0.0, 1.0), 'strength': 1.5, 'flicker': True}  # Ember glow
        ])
    
    elif environment == 'arctic':
        # Add ice and frost effects
        env_layers.extend([
            {'type': 'wear', 'strength': 0.3, 'worn_color': (0.7, 0.8, 0.9, 1.0)},    # Frost coating
            {'type': 'detail', 'strength': 0.2, 'scale': 30.0}                         # Ice crystals
        ])
    
    elif environment == 'toxic':
        # Add corrosion and toxic glow
        env_layers.extend([
            {'type': 'wear', 'strength': 0.7, 'worn_color': (0.4, 0.6, 0.2, 1.0)},    # Corrosion
            {'type': 'glow', 'glow_color': (0.3, 0.8, 0.2, 1.0), 'strength': 0.8}     # Toxic glow
        ])
    
    return create_layered_material(env_name, env_layers)


def create_magical_material(base_name: str, magic_type: str) -> bpy.types.Material:
    """Create magical variant with special effects
    
    Args:
        base_name: Base material name
        magic_type: 'fire', 'ice', 'lightning', 'shadow', 'holy'
    """
    magic_name = f"{base_name}_magical_{magic_type}"
    base_color = MATERIAL_COLORS.get(base_name, (0.5, 0.5, 0.5, 1.0))
    
    magic_effects = {
        'fire': {
            'glow_color': (1.0, 0.4, 0.0, 1.0),
            'strength': 2.0,
            'flicker': True
        },
        'ice': {
            'glow_color': (0.3, 0.7, 1.0, 1.0),
            'strength': 0.8,
            'flicker': False
        },
        'lightning': {
            'glow_color': (0.8, 0.9, 1.0, 1.0),
            'strength': 3.0,
            'flicker': True
        },
        'shadow': {
            'worn_color': (0.1, 0.1, 0.15, 1.0),
            'glow_color': (0.2, 0.1, 0.3, 1.0),
            'strength': 0.5
        },
        'holy': {
            'glow_color': (1.0, 1.0, 0.8, 1.0),
            'strength': 1.5,
            'flicker': False
        }
    }
    
    effect = magic_effects.get(magic_type, magic_effects['fire'])
    
    magic_layers = [
        {'type': 'base', 'color': base_color},
        {'type': 'glow', **effect}
    ]
    
    if 'worn_color' in effect:
        magic_layers.insert(1, {'type': 'wear', 'strength': 0.3, 'worn_color': effect['worn_color']})
    
    return create_layered_material(magic_name, magic_layers)


def add_subsurface_scattering(material: bpy.types.Material, sss_amount: float = 0.3):
    """Add realistic subsurface scattering for organic materials"""
    if not material or not material.use_nodes:
        return
    
    nodes = material.node_tree.nodes
    bsdf = nodes.get('Principled BSDF')
    
    if bsdf and 'Subsurface' in bsdf.inputs:
        bsdf.inputs['Subsurface'].default_value = sss_amount
        # Typical skin/flesh SSS radii (RGB)
        if 'Subsurface Radius' in bsdf.inputs:
            bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.2, 0.1)
        if 'Subsurface Color' in bsdf.inputs:
            # Slightly reddish for organic materials
            bsdf.inputs['Subsurface Color'].default_value = (0.8, 0.4, 0.3, 1.0)


def create_advanced_material_set(enemy_type: str, environment: str = None, damage: float = 0.0, magic_type: str = None) -> Dict[str, bpy.types.Material]:
    """Create complete advanced material set for an enemy
    
    Args:
        enemy_type: Type of enemy (adhesion_bug, ember_imp, etc.)
        environment: Optional environment adaptation
        damage: Damage level 0.0-1.0
        magic_type: Optional magical effects
    
    Returns:
        Dictionary of materials for different body parts
    """
    from .material_system import ENEMY_MATERIAL_THEMES
    
    # Get base materials for this enemy type
    base_materials = ENEMY_MATERIAL_THEMES.get(enemy_type, ['organic_brown', 'flesh_pink', 'bone_white'])
    
    advanced_materials = {}
    
    for i, base_mat_name in enumerate(base_materials):
        part_name = ['body', 'head', 'limbs'][i] if i < 3 else 'extra'
        
        # Start with base material
        current_material = base_mat_name
        
        # Apply environmental effects
        if environment:
            current_material = create_environmental_variant(current_material, environment)
        else:
            # Create basic layered version
            base_color = MATERIAL_COLORS.get(base_mat_name, (0.5, 0.5, 0.5, 1.0))
            layers = [{'type': 'base', 'color': base_color}]
            
            # Add appropriate texture type
            if 'organic' in base_mat_name or 'flesh' in base_mat_name:
                layers.append({'type': 'detail', 'strength': 0.2, 'scale': 25.0})
                current_material = create_layered_material(f"{base_mat_name}_enhanced", layers)
                add_subsurface_scattering(current_material, 0.2)
            elif 'metal' in base_mat_name:
                layers.extend([
                    {'type': 'wear', 'strength': 0.3, 'worn_color': (0.4, 0.25, 0.15, 1.0)},
                    {'type': 'detail', 'strength': 0.4, 'scale': 60.0}
                ])
                current_material = create_layered_material(f"{base_mat_name}_enhanced", layers)
            else:
                current_material = create_layered_material(f"{base_mat_name}_enhanced", layers)
        
        # Apply damage if specified
        if damage > 0.0:
            if hasattr(current_material, 'name'):
                current_material = create_damage_variant(current_material.name, damage)
            else:
                current_material = create_damage_variant(base_mat_name, damage)
        
        # Apply magical effects if specified
        if magic_type:
            if hasattr(current_material, 'name'):
                current_material = create_magical_material(current_material.name, magic_type)
            else:
                current_material = create_magical_material(base_mat_name, magic_type)
        
        advanced_materials[part_name] = current_material
    
    return advanced_materials


# Preset configurations for easy use
MATERIAL_PRESETS = {
    'battle_worn': lambda enemy: create_advanced_material_set(enemy, damage=0.6),
    'swamp_corrupted': lambda enemy: create_advanced_material_set(enemy, environment='swamp', damage=0.3),
    'volcanic_forged': lambda enemy: create_advanced_material_set(enemy, environment='volcanic'),
    'ice_cursed': lambda enemy: create_advanced_material_set(enemy, environment='arctic', magic_type='ice'),
    'fire_blessed': lambda enemy: create_advanced_material_set(enemy, magic_type='fire'),
    'shadow_touched': lambda enemy: create_advanced_material_set(enemy, magic_type='shadow'),
    'toxic_mutated': lambda enemy: create_advanced_material_set(enemy, environment='toxic', damage=0.4),
}