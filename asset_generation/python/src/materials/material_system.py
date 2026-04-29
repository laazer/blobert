"""
Material creation system with procedural textures
"""

from typing import Any, Callable, Mapping

import bpy

from src.materials import material_system_enemy_themes as _material_system_enemy_themes
from src.materials.gradient_generator import (
    create_gradient_png_and_load,
    create_spots_png_and_load,
    gradient_image_pixel_buffer,
    sanitize_image_label,
)
from src.materials.material_types import (
    RGBA,
    FeatureMap,
    ZoneTextureOptions,
    feature_zone_map,
)
from src.materials.presets import parse_hex_color
from src.utils.materials import (
    MaterialCategories,
    MaterialColors,
)
from src.utils.texture_asset_loader import infer_texture_asset_id_from_preview

get_enemy_materials = _material_system_enemy_themes.get_enemy_materials

TextureHandler = Callable[..., None]

# Map texture type → handler function (populated after handler definitions below)
_TEXTURE_HANDLERS: dict[str, TextureHandler] = {}

ENEMY_FINISH_PRESETS = {
    "default": (None, None, None),
    "glossy": (0.12, 0.05, 0.0),
    "matte": (0.8, 0.0, 0.0),
    "metallic": (0.25, 0.75, 0.0),
    "gel": (0.08, 0.0, 0.35),
}

# Organic handler: keep base color near palette (was 0.3 multiply — too muddy in GLTF).
_ORGANIC_BASE_COLOR_DETAIL_FAC = 0.12


def _sanitize_hex_input(raw: str) -> str:
    s = "".join(c for c in str(raw or "").strip().lower() if c in "0123456789abcdef")
    return s[:6]


def _force_principled_value(bsdf: Any, input_name: str, value: object) -> None:
    """Force a Principled input to a value by removing inbound links."""
    socket = bsdf.inputs.get(input_name)
    if socket is None:
        return
    for link in list(socket.links):
        bsdf.id_data.links.remove(link)
    socket.default_value = value


def create_material(
    name: str,
    color: RGBA,
    metallic: float = 0.0,
    roughness: float = 0.5,
    alpha: float = 1.0,
    transmission: float = 0.0,
    add_texture: bool = True,
    force_surface: bool = False,
    force_base_color: bool = False,
) -> bpy.types.Material:
    """Create an enhanced material with optional procedural textures"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    output = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    bsdf.location = (0, 0)
    output.location = (300, 0)

    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = transmission

    if alpha < 1.0:
        mat.blend_method = "BLEND"
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


def add_organic_texture(mat: Any, nodes: Any, links: Any, bsdf: Any, base_color: RGBA) -> None:
    """Add organic/biological texture details"""
    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (-600, 200)
    noise.inputs["Scale"].default_value = 15.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.6

    ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (-400, 200)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[1].position = 0.7

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-200, 0)
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = _ORGANIC_BASE_COLOR_DETAIL_FAC
    mix.inputs["Color1"].default_value = base_color

    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


def add_metallic_texture(_mat: Any, _nodes: Any, _links: Any, bsdf: Any, _base_color: RGBA) -> None:
    """Emphasize metal response without driving roughness from noise (PMCP-1)."""
    bsdf.inputs["Metallic"].default_value = 0.9


def add_emissive_texture(mat: Any, nodes: Any, links: Any, bsdf: Any, base_color: RGBA) -> None:
    """Add glowing/emissive texture"""
    emission = nodes.new(type="ShaderNodeEmission")
    emission.location = (0, -200)
    dim_color = (base_color[0] * 0.5, base_color[1] * 0.5, base_color[2] * 0.5, 1.0)
    emission.inputs["Color"].default_value = dim_color
    emission.inputs["Strength"].default_value = 1.5

    try:
        mix_shader = nodes.new(type="ShaderNodeMixShader")
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

    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (-400, -200)
    noise.inputs["Scale"].default_value = 25.0

    math_node = nodes.new(type="ShaderNodeMath")
    math_node.location = (-200, -200)
    math_node.operation = "MULTIPLY"
    math_node.inputs[1].default_value = 0.5

    links.new(noise.outputs["Fac"], math_node.inputs[0])
    links.new(math_node.outputs["Value"], bsdf.inputs["Emission Strength"])


def add_rocky_texture(mat: Any, nodes: Any, links: Any, bsdf: Any, base_color: RGBA) -> None:
    """Add rocky/stone texture"""
    noise_large = nodes.new(type="ShaderNodeTexNoise")
    noise_large.location = (-600, 100)
    noise_large.inputs["Scale"].default_value = 8.0
    noise_large.inputs["Detail"].default_value = 6.0

    noise_detail = nodes.new(type="ShaderNodeTexNoise")
    noise_detail.location = (-600, -100)
    noise_detail.inputs["Scale"].default_value = 30.0
    noise_detail.inputs["Detail"].default_value = 12.0

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-400, 0)
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.5

    color_mix = nodes.new(type="ShaderNodeMixRGB")
    color_mix.location = (-200, 0)
    color_mix.blend_type = "MULTIPLY"
    color_mix.inputs["Fac"].default_value = 0.4
    color_mix.inputs["Color1"].default_value = base_color

    links.new(noise_large.outputs["Fac"], mix.inputs["Color1"])
    links.new(noise_detail.outputs["Fac"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], color_mix.inputs["Color2"])
    links.new(color_mix.outputs["Color"], bsdf.inputs["Base Color"])

    bsdf.inputs["Roughness"].default_value = 0.9


def add_crystalline_texture(mat: Any, nodes: Any, links: Any, bsdf: Any, base_color: RGBA) -> None:
    """Add ice/crystal texture"""
    bsdf.inputs["Roughness"].default_value = 0.1
    if "Transmission" in bsdf.inputs:
        bsdf.inputs["Transmission"].default_value = 0.8
        bsdf.inputs["IOR"].default_value = 1.31
    elif "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = 0.7
        mat.blend_method = "BLEND"

    noise = nodes.new(type="ShaderNodeTexNoise")
    noise.location = (-400, 0)
    noise.inputs["Scale"].default_value = 20.0
    noise.inputs["Detail"].default_value = 4.0

    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.location = (-200, 0)
    mix.blend_type = "MIX"
    mix.inputs["Fac"].default_value = 0.1
    mix.inputs["Color1"].default_value = base_color

    links.new(noise.outputs["Color"], mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])


# Register handlers after all functions are defined
_TEXTURE_HANDLERS = {
    "organic": add_organic_texture,
    "metallic": add_metallic_texture,
    "emissive": add_emissive_texture,
    "rocky": add_rocky_texture,
    "crystalline": add_crystalline_texture,
}


def setup_materials(
    enemy_finish: str = "default",
    enemy_hex_color: str = "",
) -> dict[str, bpy.types.Material]:
    """Create all materials from the shared color palette"""
    materials: dict[str, bpy.types.Material] = {}
    override_color = parse_hex_color(enemy_hex_color) if enemy_hex_color else None
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


def _palette_base_name_from_material(mat: bpy.types.Material) -> str:
    name = getattr(mat, "name", "") or ""
    if "." in name:
        name = name.rsplit(".", 1)[0]
    if "__feat_" in name:
        return name.split("__feat_", 1)[0]
    return name


def _material_for_color_image_zone(
    base_material: bpy.types.Material,
    asset_id: str,
    instance_suffix: str = "color_img",
) -> bpy.types.Material:
    """Create a material with preloaded texture as the base color."""
    from ..utils.texture_asset_loader import get_texture_asset_filepath

    mat = base_material.copy()
    mat.name = f"{base_material.name}_{instance_suffix}"
    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    principled = None
    for node in nodes:
        if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
            principled = node
            break
    if not principled:
        return mat

    try:
        asset_path = get_texture_asset_filepath(asset_id)
        image = bpy.data.images.load(str(asset_path))
        image.pack()

        # Create UV and TexImage nodes
        coord_node = nodes.new(type="ShaderNodeTexCoord")
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.image = image

        # Wire: UV → TexImage Color → Base Color
        links.new(coord_node.outputs["UV"], tex_node.inputs["Vector"])
        links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
    except (ValueError, IOError, Exception) as error:
        print(f"Warning: failed to load color image texture {asset_id}: {error}")
    return mat


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
    override_color = parse_hex_color(h) if h else None
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


def apply_feature_slot_overrides(
    slot_materials: dict[str, bpy.types.Material | None],
    features: FeatureMap | None,
    build_options: FeatureMap | None = None,
) -> dict[str, bpy.types.Material | None]:
    """Re-create body/head/limbs/extra materials when ``features`` sets finish or hex overrides."""
    zone_features = feature_zone_map(features)
    if not zone_features:
        return slot_materials
    if build_options is None:
        build_options = {}

    out: dict[str, bpy.types.Material | None] = dict(slot_materials)

    for slot_key, mat in list(out.items()):
        if mat is None:
            continue
        slot_feat = zone_features.get(slot_key)
        if slot_feat is None:
            continue

        # Check for image mode first (priority over hex/finish)
        # Read from nested color_image structure (already merged from flat keys by schema)
        color_image = slot_feat.color_image
        if color_image is not None and color_image.mode == "image":
            asset_id = color_image.asset_id
            if not asset_id:
                asset_id = infer_texture_asset_id_from_preview(color_image.preview) or ""
            if asset_id:
                out[slot_key] = _material_for_color_image_zone(
                    base_material=mat,
                    asset_id=asset_id,
                    instance_suffix=f"{slot_key}_color_img",
                )
                continue  # Skip hex/finish branch for this zone

        # Existing hex/finish handling
        finish = slot_feat.finish or "default"
        hex_str = slot_feat.hex_value.strip()
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


def _rgba_from_hex_or_fallback(
    hex_str: str, fallback_rgba: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    h = _sanitize_hex_input(hex_str)
    if len(h) != 6:
        return fallback_rgba
    try:
        return parse_hex_color(h)
    except ValueError:
        return fallback_rgba


def _find_principled_bsdf(nodes: Any) -> object | None:
    """Locate Principled BSDF across Blender versions (``type`` vs ``bl_idname``)."""
    for n in nodes:
        if getattr(n, "type", None) == "BSDF_PRINCIPLED":
            return n
        if getattr(n, "bl_idname", "") == "ShaderNodeBsdfPrincipled":
            return n
    return None


def _principled_base_color_socket(bsdf) -> object | None:
    """English ``Base Color``; some builds expose ``Color`` on Principled."""
    inp = bsdf.inputs.get("Base Color")
    if inp is None:
        inp = bsdf.inputs.get("Color")
    return inp


def _add_uv_gradient_to_principled(
    mat: bpy.types.Material,
    color_a: tuple[float, float, float, float],
    color_b: tuple[float, float, float, float],
    direction: str,
    *,
    image_label: str = "gradient",
) -> None:
    """Use a packed ``ShaderNodeTexImage`` so glTF exports ``baseColorTexture`` reliably.

    Procedural shader graphs are often ignored or approximated by ``export_scene.gltf``.
    """
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

    d = str(direction or "horizontal").strip().lower()
    if d == "vertical":
        gw, gh = 4, 256
    elif d == "radial":
        gw, gh = 128, 128
    else:
        gw, gh = 256, 4

    safe = sanitize_image_label(image_label)
    img_name = f"BlobertTexGrad_{safe}"
    buf = gradient_image_pixel_buffer(gw, gh, color_a, color_b, d)

    img = create_gradient_png_and_load(gw, gh, buf, img_name)

    tex = nodes.new(type="ShaderNodeTexImage")
    tex.location = (-450, 200)
    tex.image = img
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    uv = nodes.new(type="ShaderNodeUVMap")
    uv.location = (-800, 200)
    links.new(uv.outputs["UV"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], bc_in)


def _material_for_gradient_zone(
    *,
    base_palette_name: str,
    finish: str,
    grad_a_hex: str,
    grad_b_hex: str,
    direction: str,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Solid base material (no organic noise) with UV gradient between two hex colors."""
    all_colors = MaterialColors.get_all()
    palette_base = all_colors.get(base_palette_name)
    if palette_base is None:
        palette_base = (0.6, 0.5, 0.5, 1.0)
    h_zone = _sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(h_zone) if len(h_zone) == 6 else palette_base

    # Use sensible defaults: color_a from hex or zone, color_b from hex or white for contrast
    default_for_b = (1.0, 1.0, 1.0, 1.0)
    color_a = _rgba_from_hex_or_fallback(grad_a_hex, zone_rgba)
    color_b = _rgba_from_hex_or_fallback(grad_b_hex, default_for_b)

    finish_roughness, _finish_metallic, finish_transmission = ENEMY_FINISH_PRESETS.get(
        finish,
        ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = finish != "default"
    # UV gradients are diffuse-first: high metallic + Principled reads as blown-out white in
    # glTF/Three.js; keep metal response off so exported baseColor shows the blend.
    metallic = 0.0
    roughness = 0.75
    if finish_roughness is not None:
        roughness = finish_roughness
    transmission = finish_transmission if finish_transmission is not None else 0.0
    alpha = color_a[3] if len(color_a) > 3 else 1.0
    new_name = f"{base_palette_name}__feat_{instance_suffix}"
    mat = create_material(
        new_name,
        color_a,
        metallic,
        roughness,
        alpha,
        transmission,
        add_texture=False,
        force_surface=force_surface,
        force_base_color=False,
    )
    _add_uv_gradient_to_principled(
        mat, color_a, color_b, direction, image_label=instance_suffix
    )
    return mat


def material_for_spots_zone(
    *,
    base_palette_name: str,
    finish: str,
    spot_hex: str,
    bg_hex: str,
    density: float,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Solid base material with baked spots texture.

    Analogous to _material_for_gradient_zone, but for polka-dot patterns.
    """
    all_colors = MaterialColors.get_all()
    palette_base = all_colors.get(base_palette_name)
    if palette_base is None:
        palette_base = (0.6, 0.5, 0.5, 1.0)
    h_zone = _sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(h_zone) if len(h_zone) == 6 else palette_base

    # Spots color from hex or fallback to zone color
    spot_color = _rgba_from_hex_or_fallback(spot_hex, zone_rgba)

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
    alpha = spot_color[3] if len(spot_color) > 3 else 1.0

    new_name = f"{base_palette_name}__feat_{instance_suffix}"
    mat = create_material(
        name=new_name,
        color=spot_color,
        metallic=metallic,
        roughness=roughness,
        alpha=alpha,
        transmission=transmission,
        add_texture=False,
        force_surface=force_surface,
        force_base_color=False,
    )

    # Generate and apply spots texture
    safe = sanitize_image_label(instance_suffix)
    img_name = f"BlobertTexSpot_{safe}"
    img = create_spots_png_and_load(
        width=128,
        height=128,
        spot_color_hex=_sanitize_hex_input(spot_hex),
        bg_color_hex=_sanitize_hex_input(bg_hex),
        density=density,
        img_name=img_name,
    )

    # Attach to material via UV-mapped texture node
    nt = mat.node_tree
    if nt is not None:
        nodes = nt.nodes
        links = nt.links
        bsdf = _find_principled_bsdf(nodes)
        if bsdf is not None:
            bc_in = _principled_base_color_socket(bsdf)
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


def _material_for_checkerboard_zone(
    *,
    base_palette_name: str,
    finish: str,
    color_a_hex: str,
    color_b_hex: str,
    density: float,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Solid base material with object-space procedural checkerboard texture."""
    all_colors = MaterialColors.get_all()
    palette_base = all_colors.get(base_palette_name)
    if palette_base is None:
        palette_base = (0.6, 0.5, 0.5, 1.0)
    h_zone = _sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(h_zone) if len(h_zone) == 6 else palette_base

    color_a = _rgba_from_hex_or_fallback(color_a_hex, zone_rgba)
    color_b = _rgba_from_hex_or_fallback(color_b_hex, (1.0, 1.0, 1.0, 1.0))

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
    alpha = color_a[3] if len(color_a) > 3 else 1.0

    new_name = f"{base_palette_name}__feat_{instance_suffix}"
    mat = create_material(
        name=new_name,
        color=color_a,
        metallic=metallic,
        roughness=roughness,
        alpha=alpha,
        transmission=transmission,
        add_texture=False,
        force_surface=force_surface,
        force_base_color=False,
    )

    # Tag for export-time bake so GLTF/web viewer preserves procedural look.
    mat["blobert_checker_procedural"] = True
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

                tex_coord = nodes.new(type="ShaderNodeTexCoord")
                tex_coord.location = (-1000, 220)

                mapping = nodes.new(type="ShaderNodeMapping")
                mapping.location = (-800, 220)
                density_clamped = max(0.1, min(5.0, float(density)))
                mapping.inputs["Scale"].default_value = (
                    density_clamped,
                    density_clamped,
                    density_clamped,
                )

                checker = nodes.new(type="ShaderNodeTexChecker")
                checker.location = (-600, 220)
                checker.inputs["Color1"].default_value = color_a
                checker.inputs["Color2"].default_value = color_b

                links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
                links.new(mapping.outputs["Vector"], checker.inputs["Vector"])
                links.new(checker.outputs["Color"], bc_in)
    return mat


def _material_for_asset_zone(
    base_material: bpy.types.Material,
    asset_id: str,
    tile_repeat: float = 1.0,
    instance_suffix: str = "asset",
) -> bpy.types.Material:
    """Create material with image texture applied from asset."""
    from ..utils.texture_asset_loader import get_texture_asset_filepath
    mat = base_material.copy()
    mat.name = f"{base_material.name}_{instance_suffix}"

    if not mat.use_nodes:
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    principled = None
    for node in nodes:
        if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
            principled = node
            break

    if not principled:
        return mat

    try:
        asset_path = get_texture_asset_filepath(asset_id)
        image = bpy.data.images.load(str(asset_path))
        image.pack()

        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.image = image

        if tile_repeat != 1.0:
            mapping_node = nodes.new(type="ShaderNodeMapping")
            mapping_node.inputs["Scale"].default_value = (tile_repeat, tile_repeat, 1.0)

            coord_node = nodes.new(type="ShaderNodeTexCoord")
            links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
            links.new(mapping_node.outputs["Vector"], tex_node.inputs["Vector"])
        else:
            coord_node = nodes.new(type="ShaderNodeTexCoord")
            links.new(coord_node.outputs["UV"], tex_node.inputs["Vector"])

        links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])

    except (ValueError, IOError, Exception) as e:
        print(f"Warning: failed to load asset texture {asset_id}: {e}")

    return mat


def _apply_gradient_pattern(
    mat: bpy.types.Material,
    settings: ZoneTextureOptions,
) -> bpy.types.Material:
    return _material_for_gradient_zone(
        base_palette_name=_palette_base_name_from_material(mat),
        finish=settings.finish,
        grad_a_hex=settings.gradient_a_hex,
        grad_b_hex=settings.gradient_b_hex,
        direction=settings.gradient_direction,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=f"{settings.zone}_tex_grad",
    )


def _apply_asset_pattern(mat: bpy.types.Material, settings: ZoneTextureOptions) -> bpy.types.Material | None:
    if not settings.asset_id:
        return None
    return _material_for_asset_zone(
        base_material=mat,
        asset_id=settings.asset_id,
        tile_repeat=settings.tile_repeat,
        instance_suffix=f"{settings.zone}_tex_asset",
    )


def _apply_spots_pattern(
    mat: bpy.types.Material,
    settings: ZoneTextureOptions,
) -> bpy.types.Material:
    pattern_asset_id = settings.pattern_image_asset_id(("spot_color", "spot_bg_color"))
    if pattern_asset_id:
        return _material_for_asset_zone(
            base_material=mat,
            asset_id=pattern_asset_id,
            tile_repeat=settings.tile_repeat,
            instance_suffix=f"{settings.zone}_tex_asset",
        )
    return material_for_spots_zone(
        base_palette_name=_palette_base_name_from_material(mat),
        finish=settings.finish,
        spot_hex=settings.spot_color.resolved_hex(),
        bg_hex=settings.spot_bg_color.resolved_hex(),
        density=settings.spot_density,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=f"{settings.zone}_tex_spot",
    )


def _apply_checkerboard_pattern(
    mat: bpy.types.Material,
    settings: ZoneTextureOptions,
) -> bpy.types.Material:
    pattern_asset_id = settings.pattern_image_asset_id(("spot_color", "spot_bg_color"))
    if pattern_asset_id:
        return _material_for_asset_zone(
            base_material=mat,
            asset_id=pattern_asset_id,
            tile_repeat=settings.tile_repeat,
            instance_suffix=f"{settings.zone}_tex_asset",
        )
    return _material_for_checkerboard_zone(
        base_palette_name=_palette_base_name_from_material(mat),
        finish=settings.finish,
        color_a_hex=settings.spot_color.resolved_hex(),
        color_b_hex=settings.spot_bg_color.resolved_hex(),
        density=settings.spot_density,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=f"{settings.zone}_tex_checker",
    )


def _apply_stripes_pattern(
    mat: bpy.types.Material,
    settings: ZoneTextureOptions,
) -> bpy.types.Material:
    pattern_asset_id = settings.pattern_image_asset_id(("stripe_color", "stripe_bg_color"))
    if pattern_asset_id:
        return _material_for_asset_zone(
            base_material=mat,
            asset_id=pattern_asset_id,
            tile_repeat=settings.tile_repeat,
            instance_suffix=f"{settings.zone}_tex_asset",
        )
    from .material_stripes_zone import material_for_stripes_zone

    return material_for_stripes_zone(
        base_palette_name=_palette_base_name_from_material(mat),
        finish=settings.finish,
        stripe_hex=settings.stripe_color.resolved_hex(),
        bg_hex=settings.stripe_bg_color.resolved_hex(),
        stripe_width=settings.stripe_width,
        stripe_preset=settings.stripe_preset,
        rot_yaw_deg=settings.stripe_yaw,
        rot_pitch_deg=settings.stripe_pitch,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=f"{settings.zone}_tex_stripe",
    )


def apply_zone_texture_pattern_overrides(
    slot_materials: dict[str, bpy.types.Material | None],
    build_options: Mapping[str, Any] | None,
) -> dict[str, bpy.types.Material | None]:
    """Apply ``feat_{zone}_texture_*`` flat keys (gradient / …) after feature finish/hex overrides."""
    if not build_options:
        return slot_materials

    out: dict[str, bpy.types.Material | None] = dict(slot_materials)
    features = build_options.get("features")
    zone_features = feature_zone_map(features if isinstance(features, dict) else None)

    for zone, mat in list(out.items()):
        if mat is None:
            continue
        settings = ZoneTextureOptions.from_build_options(
            zone=zone,
            zone_features=zone_features,
            build_options=build_options,
        )
        if settings.mode == "gradient":
            out[zone] = _apply_gradient_pattern(mat, settings)
        elif settings.mode == "assets":
            maybe = _apply_asset_pattern(mat, settings)
            if maybe is not None:
                out[zone] = maybe
        elif settings.mode == "spots":
            out[zone] = _apply_spots_pattern(mat, settings)
        elif settings.mode == "checkerboard":
            out[zone] = _apply_checkerboard_pattern(mat, settings)
        elif settings.mode == "stripes":
            out[zone] = _apply_stripes_pattern(mat, settings)
    return out


def material_for_zone_part(
    zone: str,
    part_id: str | None,
    slot_materials: dict[str, bpy.types.Material | None],
    features: FeatureMap | None,
) -> bpy.types.Material | None:
    """Resolve material for a sub-part: optional ``features[zone]['parts'][part_id]`` overrides zone slot."""
    base = slot_materials.get(zone)
    if base is None or not part_id or not features:
        return base
    zone_features = feature_zone_map(features)
    zf = zone_features.get(zone)
    if zf is None:
        return base
    pf = zf.parts.get(part_id)
    if pf is None:
        return base
    p_hex = _sanitize_hex_input(pf.hex_value)
    p_fin = str(pf.finish)
    z_hex = _sanitize_hex_input(zf.hex_value)
    z_fin = str(zf.finish)
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


def material_for_zone_geometry_extra(
    zone: str,
    slot_materials: dict[str, bpy.types.Material | None],
    features: FeatureMap | None,
    extra_finish: str,
    extra_hex: str,
) -> bpy.types.Material | None:
    """Material for procedural geometry overlay on ``zone``, using extra finish/hex with feature-zone fallback."""
    base = slot_materials.get(zone)
    if base is None:
        return None
    xz = _sanitize_hex_input(extra_hex)
    fin = str(extra_finish or "default")
    zf = feature_zone_map(features).get(zone)
    z_hex = _sanitize_hex_input(zf.hex_value) if zf is not None else ""
    z_fin = str(zf.finish) if zf is not None else "default"
    eff_fin = fin if fin != "default" else z_fin
    eff_hex = xz or z_hex
    if eff_fin == "default" and not eff_hex:
        return base
    base_palette_name = _palette_base_name_from_material(base)
    return _material_for_finish_hex(
        base_palette_name=base_palette_name,
        finish=eff_fin,
        hex_str=eff_hex,
        instance_suffix=f"{zone}_zgeom_extra",
    )


def apply_material_to_object(obj: Any, material: bpy.types.Material | None) -> None:
    """Apply material to a mesh object"""
    if obj and obj.type == "MESH" and material:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
