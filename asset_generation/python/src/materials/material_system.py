"""
Material creation system with procedural textures
"""

import bpy
from ..utils.materials import MaterialColors, MaterialNames, MaterialThemes, MaterialCategories


# Map texture type → handler function (populated after handler definitions below)
_TEXTURE_HANDLERS: dict = {}


def create_material(name, color, metallic=0.0, roughness=0.5, alpha=1.0, add_texture=True):
    """Create an enhanced material with optional procedural textures"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    output = nodes.new(type='ShaderNodeOutputMaterial')
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    bsdf.location = (0, 0)
    output.location = (300, 0)

    bsdf.inputs["Base Color"].default_value = color
    if "Metallic" in bsdf.inputs:
        bsdf.inputs["Metallic"].default_value = metallic
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness

    if alpha < 1.0:
        mat.blend_method = 'BLEND'
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha

    if add_texture:
        texture_type = MaterialCategories.get_texture_type(name)
        handler = _TEXTURE_HANDLERS.get(texture_type)
        if handler:
            handler(mat, nodes, links, bsdf, color)

    return mat


def add_organic_texture(mat, nodes, links, bsdf, base_color):
    """Add organic/biological texture details"""
    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-600, 200)
    noise.inputs["Scale"].default_value = 15.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6

    ramp = nodes.new(type='ShaderNodeValToRGB')
    ramp.location = (-400, 200)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7

    mix = nodes.new(type='ShaderNodeMixRGB')
    mix.location = (-200, 0)
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = 0.3
    mix.inputs["Color1"].default_value = base_color

    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"], bsdf.inputs["Roughness"])


def add_metallic_texture(mat, nodes, links, bsdf, base_color):
    """Add metallic surface details"""
    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-400, 0)
    noise.inputs["Scale"].default_value = 50.0
    noise.inputs["Detail"].default_value = 15.0

    links.new(noise.outputs["Fac"], bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.9


def add_emissive_texture(mat, nodes, links, bsdf, base_color):
    """Add glowing/emissive texture"""
    emission = nodes.new(type='ShaderNodeEmission')
    emission.location = (0, -200)
    dim_color = (base_color[0] * 0.5, base_color[1] * 0.5, base_color[2] * 0.5, 1.0)
    emission.inputs["Color"].default_value = dim_color
    emission.inputs["Strength"].default_value = 1.5

    try:
        mix_shader = nodes.new(type='ShaderNodeMixShader')
        mix_shader.location = (200, 0)

        factor_input = mix_shader.inputs.get("Fac") or mix_shader.inputs.get("Factor")
        if factor_input:
            factor_input.default_value = 0.3

        output = nodes.get("Material Output")
        links.new(bsdf.outputs["BSDF"], mix_shader.inputs[1])
        links.new(emission.outputs["Emission"], mix_shader.inputs[2])
        links.new(mix_shader.outputs["Shader"], output.inputs["Surface"])
    except Exception:
        emission.inputs["Strength"].default_value = 0.5
        output = nodes.get("Material Output")
        links.new(emission.outputs["Emission"], output.inputs["Surface"])

    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-400, -200)
    noise.inputs["Scale"].default_value = 25.0

    math_node = nodes.new(type='ShaderNodeMath')
    math_node.location = (-200, -200)
    math_node.operation = 'MULTIPLY'
    math_node.inputs[1].default_value = 0.5

    links.new(noise.outputs["Fac"], math_node.inputs[0])
    links.new(math_node.outputs["Value"], bsdf.inputs["Emission Strength"])


def add_rocky_texture(mat, nodes, links, bsdf, base_color):
    """Add rocky/stone texture"""
    noise_large = nodes.new(type='ShaderNodeTexNoise')
    noise_large.location = (-600, 100)
    noise_large.inputs["Scale"].default_value = 8.0
    noise_large.inputs["Detail"].default_value = 6.0

    noise_detail = nodes.new(type='ShaderNodeTexNoise')
    noise_detail.location = (-600, -100)
    noise_detail.inputs["Scale"].default_value = 30.0
    noise_detail.inputs["Detail"].default_value = 12.0

    mix = nodes.new(type='ShaderNodeMixRGB')
    mix.location = (-400, 0)
    mix.blend_type = 'MULTIPLY'
    mix.inputs["Fac"].default_value = 0.5

    color_mix = nodes.new(type='ShaderNodeMixRGB')
    color_mix.location = (-200, 0)
    color_mix.blend_type = 'MULTIPLY'
    color_mix.inputs["Fac"].default_value = 0.4
    color_mix.inputs["Color1"].default_value = base_color

    links.new(noise_large.outputs["Fac"], mix.inputs["Color1"])
    links.new(noise_detail.outputs["Fac"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], color_mix.inputs["Color2"])
    links.new(color_mix.outputs["Color"], bsdf.inputs["Base Color"])

    bsdf.inputs["Roughness"].default_value = 0.9


def add_crystalline_texture(mat, nodes, links, bsdf, base_color):
    """Add ice/crystal texture"""
    bsdf.inputs["Roughness"].default_value = 0.1
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.8
        bsdf.inputs["IOR"].default_value = 1.31
    elif "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.7
        mat.blend_method = 'BLEND'

    noise = nodes.new(type='ShaderNodeTexNoise')
    noise.location = (-400, 0)
    noise.inputs["Scale"].default_value = 20.0
    noise.inputs["Detail"].default_value = 4.0

    mix = nodes.new(type='ShaderNodeMixRGB')
    mix.location = (-200, 0)
    mix.blend_type = 'MIX'
    mix.inputs["Fac"].default_value = 0.1
    mix.inputs["Color1"].default_value = base_color

    links.new(noise.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


# Register handlers after all functions are defined
_TEXTURE_HANDLERS = {
    'organic': add_organic_texture,
    'metallic': add_metallic_texture,
    'emissive': add_emissive_texture,
    'rocky': add_rocky_texture,
    'crystalline': add_crystalline_texture,
}


def setup_materials() -> dict:
    """Create all materials from the shared color palette"""
    materials = {}
    for name, color in MaterialColors.get_all().items():
        is_metallic = name in MaterialCategories.METALLIC_SHADER
        metallic = 0.8 if is_metallic else 0.0
        roughness = 0.3 if is_metallic else 0.7
        alpha = color[3] if len(color) > 3 else 1.0
        materials[name] = create_material(name, color, metallic, roughness, alpha, add_texture=True)
    return materials


def apply_material_to_object(obj, material) -> None:
    """Apply material to a mesh object"""
    if obj and obj.type == 'MESH' and material:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material


def _build_body_part_material_map(available_mats: list, rng) -> dict:
    """Map body part names to materials given a list of available theme materials"""
    count = len(available_mats)
    if count >= 3:
        return {
            'body': available_mats[0],
            'head': available_mats[1],
            'limbs': available_mats[2],
            'extra': rng.choice(available_mats),
        }
    if count == 2:
        return {
            'body': available_mats[0],
            'head': available_mats[1],
            'limbs': available_mats[0],
            'extra': available_mats[1],
        }
    fallback = available_mats[0]
    return {'body': fallback, 'head': fallback, 'limbs': fallback, 'extra': fallback}


def get_enemy_materials(enemy_name: str, materials: dict, rng) -> dict:
    """Return a body-part → material mapping for the given enemy type"""
    default_fallback = {
        'body': materials.get(MaterialNames.ORGANIC_BROWN),
        'head': materials.get(MaterialNames.FLESH_PINK),
        'limbs': materials.get(MaterialNames.BONE_WHITE),
        'extra': materials.get(MaterialNames.ORGANIC_BROWN),
    }

    if not MaterialThemes.has_theme(enemy_name):
        return default_fallback

    theme_material_names = MaterialThemes.get_theme(enemy_name)
    available_mats = [materials[n] for n in theme_material_names if n in materials]

    if not available_mats:
        return default_fallback

    return _build_body_part_material_map(available_mats, rng)
