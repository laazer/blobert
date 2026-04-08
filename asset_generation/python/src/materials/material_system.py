"""
Material creation system with procedural textures
"""
from __future__ import annotations

import bpy

from ..utils.materials import (
    MaterialCategories,
    MaterialColors,
    MaterialNames,
    MaterialThemes,
)

# Map texture type → handler function (populated after handler definitions below)
_TEXTURE_HANDLERS: dict = {}

ENEMY_FINISH_PRESETS = {
    "default": (None, None, None),
    "glossy": (0.12, 0.05, 0.0),
    "matte": (0.8, 0.0, 0.0),
    "metallic": (0.25, 0.75, 0.0),
    "gel": (0.08, 0.0, 0.35),
}


def _sanitize_hex_input(raw: str) -> str:
    s = "".join(c for c in str(raw or "").strip().lower() if c in "0123456789abcdef")
    return s[:6]


def _parse_hex_color(hex_value: str):
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


def _force_principled_value(bsdf, input_name, value):
    """Force a Principled input to a value by removing inbound links."""
    socket = bsdf.inputs.get(input_name)
    if socket is None:
        return
    for link in list(socket.links):
        bsdf.id_data.links.remove(link)
    socket.default_value = value


def create_material(
    name,
    color,
    metallic=0.0,
    roughness=0.5,
    alpha=1.0,
    transmission=0.0,
    add_texture=True,
    force_surface=False,
    force_base_color=False,
):
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
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission

    if alpha < 1.0:
        mat.blend_method = 'BLEND'
        if "Alpha" in bsdf.inputs:
            bsdf.inputs["Alpha"].default_value = alpha

    if add_texture:
        texture_type = MaterialCategories.get_texture_type(name)
        handler = _TEXTURE_HANDLERS.get(texture_type)
        if handler:
            handler(mat, nodes, links, bsdf, color)

    # Explicit overrides should win over texture graph defaults/links.
    if force_base_color:
        _force_principled_value(bsdf, "Base Color", color)
    if force_surface:
        _force_principled_value(bsdf, "Roughness", roughness)
        _force_principled_value(bsdf, "Metallic", metallic)
        _force_principled_value(bsdf, "Transmission Weight", transmission)
        _force_principled_value(bsdf, "Transmission", transmission)

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


def setup_materials(enemy_finish: str = "default", enemy_hex_color: str = "") -> dict:
    """Create all materials from the shared color palette"""
    materials = {}
    override_color = _parse_hex_color(enemy_hex_color) if enemy_hex_color else None
    finish_roughness, finish_metallic, finish_transmission = ENEMY_FINISH_PRESETS.get(
        enemy_finish,
        ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = enemy_finish != "default"
    force_base_color = override_color is not None
    for name, color in MaterialColors.get_all().items():
        is_metallic = name in MaterialCategories.METALLIC_SHADER
        metallic = 0.8 if is_metallic else 0.0
        roughness = 0.3 if is_metallic else 0.7
        if finish_roughness is not None:
            roughness = finish_roughness
        if finish_metallic is not None:
            metallic = finish_metallic
        transmission = finish_transmission if finish_transmission is not None else 0.0
        alpha = color[3] if len(color) > 3 else 1.0
        material_color = override_color if override_color else color
        materials[name] = create_material(
            name,
            material_color,
            metallic,
            roughness,
            alpha,
            transmission,
            add_texture=True,
            force_surface=force_surface,
            force_base_color=force_base_color,
        )
    return materials


def _palette_base_name_from_material(mat) -> str:
    name = getattr(mat, "name", "") or ""
    if "." in name:
        name = name.rsplit(".", 1)[0]
    if "__feat_" in name:
        return name.split("__feat_", 1)[0]
    return name


def _material_for_finish_hex(
    *,
    base_palette_name: str,
    finish: str,
    hex_str: str,
    instance_suffix: str,
) -> object:
    """Create a themed material variant (palette base + finish + optional hex)."""
    all_colors = MaterialColors.get_all()
    base_color = all_colors.get(base_palette_name)
    if base_color is None:
        base_color = (0.6, 0.5, 0.5, 1.0)
    h = _sanitize_hex_input(hex_str)
    override_color = _parse_hex_color(h) if h else None
    material_color = override_color if override_color is not None else base_color
    finish_roughness, finish_metallic, finish_transmission = ENEMY_FINISH_PRESETS.get(
        finish,
        ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = finish != "default"
    force_base_color = override_color is not None
    is_metallic = base_palette_name in MaterialCategories.METALLIC_SHADER
    metallic = 0.8 if is_metallic else 0.0
    roughness = 0.3 if is_metallic else 0.7
    if finish_roughness is not None:
        roughness = finish_roughness
    if finish_metallic is not None:
        metallic = finish_metallic
    transmission = finish_transmission if finish_transmission is not None else 0.0
    alpha = material_color[3] if len(material_color) > 3 else 1.0
    new_name = f"{base_palette_name}__feat_{instance_suffix}"
    return create_material(
        new_name,
        material_color,
        metallic,
        roughness,
        alpha,
        transmission,
        add_texture=True,
        force_surface=force_surface,
        force_base_color=force_base_color,
    )


def apply_feature_slot_overrides(slot_materials: dict, features: dict | None) -> dict:
    """Re-create body/head/limbs/extra materials when ``features`` sets finish or hex overrides."""
    if not features:
        return slot_materials

    out = dict(slot_materials)

    for slot_key, mat in list(out.items()):
        if mat is None:
            continue
        slot_feat = features.get(slot_key)
        if not isinstance(slot_feat, dict):
            continue
        finish = slot_feat.get("finish") or "default"
        hex_str = (slot_feat.get("hex") or "").strip()
        if finish == "default" and not hex_str:
            continue

        base_palette_name = _palette_base_name_from_material(mat)
        out[slot_key] = _material_for_finish_hex(
            base_palette_name=base_palette_name,
            finish=str(finish),
            hex_str=hex_str,
            instance_suffix=str(slot_key),
        )
    return out


def material_for_zone_part(
    zone: str,
    part_id: str | None,
    slot_materials: dict,
    features: dict | None,
):
    """Resolve material for a sub-part: optional ``features[zone]['parts'][part_id]`` overrides zone slot."""
    base = slot_materials.get(zone)
    if base is None or not part_id or not features:
        return base
    zf = features.get(zone)
    if not isinstance(zf, dict):
        return base
    parts = zf.get("parts")
    if not isinstance(parts, dict):
        return base
    pf = parts.get(part_id)
    if not isinstance(pf, dict):
        return base
    p_hex = _sanitize_hex_input(pf.get("hex", ""))
    p_fin = str(pf.get("finish", "default"))
    z_hex = _sanitize_hex_input(zf.get("hex", ""))
    z_fin = str(zf.get("finish", "default"))
    wants_override = bool(p_hex) or p_fin != "default"
    if not wants_override:
        return base
    eff_fin = p_fin if p_fin != "default" else z_fin
    eff_hex = p_hex or z_hex
    if eff_fin == "default" and not eff_hex:
        return base
    base_palette_name = _palette_base_name_from_material(base)
    safe_part = str(part_id).replace(".", "_")
    return _material_for_finish_hex(
        base_palette_name=base_palette_name,
        finish=eff_fin,
        hex_str=eff_hex,
        instance_suffix=f"{zone}_{safe_part}",
    )


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
        limb_mat = available_mats[2]
        return {
            'body': available_mats[0],
            'head': available_mats[1],
            'limbs': limb_mat,
            'joints': limb_mat,
            'extra': rng.choice(available_mats),
        }
    if count == 2:
        return {
            'body': available_mats[0],
            'head': available_mats[1],
            'limbs': available_mats[0],
            'joints': available_mats[0],
            'extra': available_mats[1],
        }
    fallback = available_mats[0]
    return {
        'body': fallback,
        'head': fallback,
        'limbs': fallback,
        'joints': fallback,
        'extra': fallback,
    }


def get_enemy_materials(enemy_name: str, materials: dict, rng) -> dict:
    """Return a body-part → material mapping for the given enemy type"""
    default_fallback = {
        'body': materials.get(MaterialNames.ORGANIC_BROWN),
        'head': materials.get(MaterialNames.FLESH_PINK),
        'limbs': materials.get(MaterialNames.BONE_WHITE),
        'joints': materials.get(MaterialNames.BONE_WHITE),
        'extra': materials.get(MaterialNames.ORGANIC_BROWN),
    }

    if not MaterialThemes.has_theme(enemy_name):
        return default_fallback

    theme_material_names = MaterialThemes.get_theme(enemy_name)
    available_mats = [materials[n] for n in theme_material_names if n in materials]

    if not available_mats:
        return default_fallback

    return _build_body_part_material_map(available_mats, rng)
