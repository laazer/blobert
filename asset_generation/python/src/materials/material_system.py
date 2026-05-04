"""
Material creation system with procedural textures
"""

from pathlib import Path
from typing import Any, Callable, Mapping

import bpy

from src.materials import material_system_enemy_themes as _material_system_enemy_themes
from src.materials.gradient_generator import (
    create_gradient_png_and_load,
    create_spots_png_and_load,
    gradient_image_pixel_buffer,
    sanitize_image_label,
    write_rgba_buffer_to_gradients_png,
)
from src.materials.material_types import (
    RGBA,
    FeatureMap,
    FeatureZoneOptions,
    FillMaterial,
    GradientFill,
    ImageFill,
    SolidFill,
    ZoneTextureOptions,
    feature_zone_map,
    pattern_normalize_hex6,
)
from src.materials.presets import parse_hex_color
from src.materials.spot_overlay import (
    overlay_base_image_onto_material as _spot_overlay_base_image,
)
from src.materials.spot_plate_mask import DEFAULT_DARK_THRESHOLD
from src.materials.spots_composite_debug import log_spots_composite
from src.materials.spots_zone_pipeline import apply_spots_zone_pattern
from src.materials.uv_atlas import (
    is_full_uv_rect,
    mapping_scale_location_for_uv_rect,
    parse_uv_rect,
    resolved_asset_path_for_image_sampling,
)
from src.utils.materials import (
    MaterialCategories,
    MaterialColors,
)
from src.utils.texture_asset_loader import (
    get_texture_asset_filepath,
    infer_texture_asset_id_from_preview,
)

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


def fill_material_hex(fill: FillMaterial, fallback: str = "") -> str:
    """Extract a hex string from any FillMaterial type.

    - SolidFill: return hex_value
    - GradientFill: return hex_a (color endpoint)
    - ImageFill: return fallback (images don't have a hex equivalent)
    """
    if isinstance(fill, SolidFill):
        return fill.hex_value
    elif isinstance(fill, GradientFill):
        return fill.hex_a
    else:  # ImageFill
        return fallback


def fill_material_image_asset_id(fill: FillMaterial) -> str:
    """Extract image asset_id from FillMaterial, or empty string if not an image.

    - SolidFill: return ""
    - GradientFill: return ""
    - ImageFill: return asset_id
    """
    if isinstance(fill, ImageFill):
        return fill.asset_id
    return ""


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


def material_for_color_image_zone(
    base_material: bpy.types.Material,
    asset_id: str,
    instance_suffix: str = "color_img",
    uv_rect: tuple[float, float, float, float] | None = None,
) -> bpy.types.Material:
    """Create a material with preloaded texture as the base color.

    Optional ``uv_rect`` selects a normalized sub-rectangle of an atlas (same UV convention as Blender).
    """
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

        coord_node = nodes.new(type="ShaderNodeTexCoord")
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.image = image

        use_mapping = uv_rect is not None and not is_full_uv_rect(uv_rect)
        if use_mapping:
            mapping_node = nodes.new(type="ShaderNodeMapping")
            scale_vec, loc_vec = mapping_scale_location_for_uv_rect(uv_rect)
            mapping_node.inputs["Scale"].default_value = scale_vec
            mapping_node.inputs["Location"].default_value = loc_vec
            links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
            links.new(mapping_node.outputs["Vector"], tex_node.inputs["Vector"])
        else:
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
                out[slot_key] = material_for_color_image_zone(
                    base_material=mat,
                    asset_id=asset_id,
                    instance_suffix=f"{slot_key}_color_img",
                    uv_rect=color_image.uv_rect,
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
    pattern_fill: FillMaterial,
    background_fill: FillMaterial,
    density: float,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Solid base material with baked spots texture.

    Analogous to _material_for_gradient_zone, but for polka-dot patterns.
    """
    spot_hex = fill_material_hex(pattern_fill, zone_hex_fallback)
    bg_hex = fill_material_hex(background_fill, "ffffff")

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
    mat["blobert_spot_image_name"] = img.name
    spots_dir = Path(__file__).parent.parent.parent / "animated_exports" / "spots"
    mat["blobert_spot_image_path"] = str(spots_dir / f"{img_name}.png")

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


def _wire_spot_plate_image_to_principled(
    mat: bpy.types.Material,
    image: bpy.types.Image,
    *,
    use_atlas_mapping: bool,
    uv_rect: tuple[float, float, float, float] | None,
) -> None:
    """Attach packed spot-plate image to Principled Base Color with optional atlas Mapping."""
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
    tex = nodes.new(type="ShaderNodeTexImage")
    tex.location = (-450, 200)
    tex.image = image
    tex.interpolation = "Linear"
    tex.extension = "REPEAT"

    uv = nodes.new(type="ShaderNodeUVMap")
    uv.location = (-800, 200)
    # Always apply UV mapping when uv_rect is provided, regardless of atlas resolution
    if uv_rect is not None:
        mapping_node = nodes.new(type="ShaderNodeMapping")
        mapping_node.location = (-650, 200)
        scale_vec, loc_vec = mapping_scale_location_for_uv_rect(uv_rect)
        mapping_node.inputs["Scale"].default_value = scale_vec
        mapping_node.inputs["Location"].default_value = loc_vec
        links.new(uv.outputs["UV"], mapping_node.inputs["Vector"])
        links.new(mapping_node.outputs["Vector"], tex.inputs["Vector"])
    else:
        links.new(uv.outputs["UV"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], bc_in)


def material_for_spots_zone_from_image_asset(
    *,
    base_palette_name: str,
    finish: str,
    asset_id: str,
    zone_hex_fallback: str,
    instance_suffix: str,
    spot_plate_mask_mode: str = "auto",
    spot_plate_dark_threshold: float = DEFAULT_DARK_THRESHOLD,
    spot_plate_mask_soft_edges: bool = True,
    uv_rect: tuple[float, float, float, float] | None = None,
) -> bpy.types.Material:
    """Solid base material with a user image as the spot plate (same combine rules as procedural spots).

    Compositing mask policy is ``spot_plate_mask_mode`` / ``spot_plate_dark_threshold`` (see ``spot_plate_mask``).
    """
    all_colors = MaterialColors.get_all()
    palette_base = all_colors.get(base_palette_name)
    if palette_base is None:
        palette_base = (0.6, 0.5, 0.5, 1.0)
    h_zone = _sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(h_zone) if len(h_zone) == 6 else palette_base

    finish_roughness, _finish_metallic, finish_transmission = ENEMY_FINISH_PRESETS.get(
        finish,
        ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = finish != "default"
    metallic = 0.0
    roughness = 0.75
    if finish_roughness is not None:
        roughness = finish_roughness
    # Pattern images are always fully opaque, no transmission
    transmission = 0.0
    alpha = zone_rgba[3] if len(zone_rgba) > 3 else 1.0

    new_name = f"{base_palette_name}__feat_{instance_suffix}"
    mat = create_material(
        name=new_name,
        color=zone_rgba,
        metallic=metallic,
        roughness=roughness,
        alpha=alpha,
        transmission=transmission,
        add_texture=False,
        force_surface=force_surface,
        force_base_color=False,
    )

    asset_path = Path(get_texture_asset_filepath(asset_id))
    partial_atlas = uv_rect is not None and not is_full_uv_rect(uv_rect)
    resolved_path = (
        resolved_asset_path_for_image_sampling(asset_path, uv_rect) if partial_atlas else asset_path
    )
    atlas_mapping_fallback = partial_atlas and resolved_path == asset_path

    image = bpy.data.images.load(str(resolved_path), check_existing=True)
    try:
        image.pack()
    except Exception:  # pragma: no cover
        pass

    mat["blobert_spot_image_name"] = image.name
    mat["blobert_spot_image_path"] = str(resolved_path)
    mat["blobert_spot_plate_mask_mode"] = str(spot_plate_mask_mode or "auto")
    mat["blobert_spot_plate_dark_threshold"] = float(spot_plate_dark_threshold)
    mat["blobert_spot_plate_mask_soft_edges"] = 1 if spot_plate_mask_soft_edges else 0

    log_spots_composite(
        "spot_plate_from_image: "
        f"asset_id={asset_id!r} filepath={resolved_path} "
        f"image_size={tuple(image.size)!r} "
        f"mask_mode={spot_plate_mask_mode!r} dark_threshold={spot_plate_dark_threshold!r} "
        f"mask_soft_edges={spot_plate_mask_soft_edges!r} "
        "→ full UV texture from file (not reprocedural dots). "
        "Composite uses ``spot_plate_mask`` policy (auto picks white-holes vs dark-spots).",
    )

    _wire_spot_plate_image_to_principled(
        mat,
        image,
        use_atlas_mapping=atlas_mapping_fallback,
        uv_rect=uv_rect,
    )

    return mat


def _material_for_checkerboard_zone(
    *,
    base_palette_name: str,
    finish: str,
    pattern_fill: FillMaterial,
    background_fill: FillMaterial,
    density: float,
    zone_hex_fallback: str,
    instance_suffix: str,
) -> bpy.types.Material:
    """Solid base material with object-space procedural checkerboard texture."""
    color_a_hex = fill_material_hex(pattern_fill, zone_hex_fallback)
    color_b_hex = fill_material_hex(background_fill, "ffffff")

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
    # Pattern colors are always fully opaque, no transmission
    transmission = 0.0
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


def _zone_color_image_asset_id(zone_feature: FeatureZoneOptions | None) -> str:
    if zone_feature is None:
        return ""
    color_image = zone_feature.color_image
    if color_image is None or color_image.mode != "image":
        return ""
    if color_image.asset_id:
        return color_image.asset_id
    return infer_texture_asset_id_from_preview(color_image.preview) or ""


def resolve_zone_color_image_asset_id(
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
) -> str:
    """Asset id for the zone body/base image used to composite under patterns.

    Prefer nested ``build_options["features"][zone].color_image`` (merged schema).
    Fall back to flat ``feat_{zone}_color_mode`` / ``feat_{zone}_color_image_*`` so
    Blender and minimal payloads still get the underlay for spot/stripe combine.
    """
    nested = _zone_color_image_asset_id(zone_feature)
    if nested:
        log_spots_composite(
            f"zone_body_underlay zone={zone}: source=nested_features color_image.id={nested!r}",
        )
        return nested
    mode = str(build_options.get(f"feat_{zone}_color_mode") or "").strip().lower()
    if mode != "image":
        return ""
    asset_id = str(build_options.get(f"feat_{zone}_color_image_id") or "").strip()
    if asset_id:
        log_spots_composite(f"zone_body_underlay zone={zone}: source=flat_keys feat_*_color_image_id={asset_id!r}")
        return asset_id
    preview = build_options.get(f"feat_{zone}_color_image_preview")
    if isinstance(preview, str) and preview.strip():
        inferred = infer_texture_asset_id_from_preview(preview) or ""
        log_spots_composite(
            f"zone_body_underlay zone={zone}: source=flat_preview inferred_asset_id={inferred!r}",
        )
        return inferred
    log_spots_composite(f"zone_body_underlay zone={zone}: image mode but no id/preview -> underlay empty")
    return ""


def resolve_zone_color_image_uv_rect(
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
) -> tuple[float, float, float, float] | None:
    """Normalized atlas rectangle for zone ``color_image`` (if any)."""
    if zone_feature is not None and zone_feature.color_image is not None:
        nested = zone_feature.color_image.uv_rect
        if nested is not None:
            return nested
    raw = build_options.get(f"feat_{zone}_color_image_uv_rect")
    return parse_uv_rect(raw)


def resolve_texture_pattern_overlay_uv_rect(
    *,
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
    pattern_asset_id: str,
    zone_image_asset_id: str,
    channel_uv_rect: tuple[float, float, float, float] | None,
) -> tuple[float, float, float, float] | None:
    """Atlas UV for checker/stripe pattern overlay sampling.

    Prefer bounds from the pattern channel (``channel_uv_rect``). When the overlay reuses the
    zone body texture (same asset id as ``feat_*_color_image_*``) because stripe/spot pattern
    channels are not in ``image`` mode, use the zone ``color_image`` atlas bounds.
    """
    if channel_uv_rect is not None:
        return channel_uv_rect
    if pattern_asset_id and zone_image_asset_id and pattern_asset_id == zone_image_asset_id:
        return resolve_zone_color_image_uv_rect(zone, build_options, zone_feature)
    return None


def _read_png_ihdr_dimensions(path: Path) -> tuple[int, int]:
    """Return width, height from a PNG without PIL (IHDR only)."""
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    if data[12:16] != b"IHDR":
        raise ValueError(f"missing IHDR: {path}")
    w = int.from_bytes(data[16:20], "big")
    h = int.from_bytes(data[20:24], "big")
    if w <= 0 or h <= 0:
        raise ValueError(f"invalid PNG dimensions: {path}")
    return w, h


def _spot_bg_rgba_endpoints(
    fill: FillMaterial,
    zone_hex: str,
) -> tuple[RGBA, RGBA]:
    """Two RGBA colors for a horizontal UV gradient underlay (equal = solid)."""
    z = _sanitize_hex_input(zone_hex)
    zone_rgba: RGBA = parse_hex_color(z) if len(z) == 6 else (0.92, 0.92, 0.92, 1.0)

    if isinstance(fill, GradientFill):
        ha = pattern_normalize_hex6(fill.hex_a) or pattern_normalize_hex6(fill.hex_b) or pattern_normalize_hex6(z or "ffffff")
        hb = pattern_normalize_hex6(fill.hex_b) or pattern_normalize_hex6(fill.hex_a) or pattern_normalize_hex6(z or "ffffff")
        if not ha and not hb:
            hx = _sanitize_hex_input(z or "ffffff")
            c = parse_hex_color(hx) if len(hx) == 6 else zone_rgba
            return c, c
        ra = parse_hex_color(ha) if len(ha) == 6 else zone_rgba
        rb = parse_hex_color(hb) if len(hb) == 6 else zone_rgba
        return ra, rb
    elif isinstance(fill, SolidFill):
        hx = _sanitize_hex_input(fill.hex_value or z or "ffffff")
        c = parse_hex_color(hx) if len(hx) == 6 else zone_rgba
        return c, c
    else:  # ImageFill
        # Images handled separately; return white endpoints
        return (1.0, 1.0, 1.0, 1.0), (1.0, 1.0, 1.0, 1.0)


def _write_spot_background_underlay_png(
    *,
    zone: str,
    spot_pattern_id: str,
    width: int,
    height: int,
    spot_bg: FillMaterial,
    zone_hex: str,
) -> Path | None:
    """Raster matching spot plate size for mask composite (background_fill, not zone color_image)."""
    try:
        ca, cb = _spot_bg_rgba_endpoints(spot_bg, zone_hex)
        pixels = gradient_image_pixel_buffer(width, height, ca, cb, "horizontal")
        label = f"BlobertSpotUnderlay_{sanitize_image_label(zone)}_{sanitize_image_label(spot_pattern_id)[:24]}"
        out = write_rgba_buffer_to_gradients_png(width, height, pixels, label)
        log_spots_composite(
            f"spots_underlay: wrote synthesized spot_bg raster {out.name} ({width}x{height}) for composite",
        )
        return out
    except (OSError, ValueError, TypeError, KeyError) as e:
        log_spots_composite(f"spots_underlay: failed to write synthesized underlay: {type(e).__name__}: {e}")
        return None


def resolve_spots_composite_underlay(
    *,
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
    settings: ZoneTextureOptions,
    spot_pattern_id: str,
) -> tuple[str, Path | None]:
    """Texture asset id and/or disk path to composite *under* an image spot plate.

    Priority: background_fill as image (texture-specific) > zone color_image (global fallback).
    If neither image is set, synthesize underlay from background_fill hex/gradient.
    """
    # Primary: background_fill image (texture-mode-specific)
    bg_fill = settings.background_fill
    if isinstance(bg_fill, ImageFill):
        bid = bg_fill.asset_id
        if bid and bid != spot_pattern_id:
            log_spots_composite(f"spots_underlay: using background_fill image asset_id={bid!r} (primary)")
            return (bid, None)

    # Fallback: zone color_image (global base material)
    zone_id = resolve_zone_color_image_asset_id(zone, build_options, zone_feature)
    if zone_id and zone_id != spot_pattern_id:
        log_spots_composite(
            f"spots_underlay: zone color_image asset_id={zone_id!r} used as fallback "
            f"(background_fill not an image)",
        )
        return (zone_id, None)

    if not spot_pattern_id:
        return ("", None)
    try:
        pat_path = Path(get_texture_asset_filepath(spot_pattern_id))
    except (ValueError, OSError, TypeError) as e:
        log_spots_composite(f"spots_underlay: cannot resolve spot plate path: {type(e).__name__}: {e}")
        return ("", None)
    if not pat_path.is_file():
        log_spots_composite(f"spots_underlay: spot plate path missing: {pat_path}")
        return ("", None)
    try:
        w, h = _read_png_ihdr_dimensions(pat_path)
    except (ValueError, OSError) as e:
        log_spots_composite(f"spots_underlay: cannot read spot PNG dimensions: {type(e).__name__}: {e}")
        return ("", None)
    syn = _write_spot_background_underlay_png(
        zone=zone,
        spot_pattern_id=spot_pattern_id,
        width=w,
        height=h,
        spot_bg=bg_fill,
        zone_hex=settings.zone_hex,
    )
    return ("", syn)


def overlay_base_image_on_zone_material(
    mat: bpy.types.Material,
    *,
    asset_id: str = "",
    base_path: Path | None = None,
    underlay_uv_rect: tuple[float, float, float, float] | None = None,
    log_prefix: str = "",
) -> bpy.types.Material:
    """Overlay a texture asset or PNG onto the zone pattern material (combined PNG when applicable)."""
    return _spot_overlay_base_image(
        mat,
        asset_id=asset_id,
        base_path=base_path,
        underlay_uv_rect=underlay_uv_rect,
        log_prefix=log_prefix,
    )


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
    *,
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
) -> bpy.types.Material:
    return apply_spots_zone_pattern(
        base_palette_name=_palette_base_name_from_material(mat),
        settings=settings,
        zone=zone,
        build_options=build_options,
        zone_feature=zone_feature,
    )


def _apply_checkerboard_pattern(
    mat: bpy.types.Material,
    settings: ZoneTextureOptions,
    *,
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
    zone_image_asset_id: str = "",
) -> bpy.types.Material:
    """Apply checkerboard pattern. Background_fill as image triggers overlay."""
    # Check if background_fill is an image (that's the overlay)
    bg_fill_is_image = isinstance(settings.background_fill, ImageFill)
    pattern_asset_id = settings.background_fill.asset_id if bg_fill_is_image else ""

    checker_mat = _material_for_checkerboard_zone(
        base_palette_name=_palette_base_name_from_material(mat),
        finish=settings.finish,
        pattern_fill=settings.pattern_fill,
        background_fill=settings.background_fill,
        density=settings.spot_density,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=f"{settings.zone}_tex_checker",
    )
    if not pattern_asset_id:
        return checker_mat

    # Overlay background_fill image onto checkerboard
    bg_uv_rect = None
    if bg_fill_is_image:
        bg_uv_rect = settings.background_fill.uv_rect

    underlay_uv = resolve_texture_pattern_overlay_uv_rect(
        zone=zone,
        build_options=build_options,
        zone_feature=zone_feature,
        pattern_asset_id=pattern_asset_id,
        zone_image_asset_id=zone_image_asset_id,
        channel_uv_rect=bg_uv_rect,
    )
    return overlay_base_image_on_zone_material(
        checker_mat,
        asset_id=pattern_asset_id,
        underlay_uv_rect=underlay_uv,
    )


def _apply_stripes_pattern(
    mat: bpy.types.Material,
    settings: ZoneTextureOptions,
    *,
    zone: str,
    build_options: Mapping[str, Any],
    zone_feature: FeatureZoneOptions | None,
    zone_image_asset_id: str = "",
) -> bpy.types.Material:
    """Apply stripes pattern. Background_fill as image triggers overlay."""
    # Check if background_fill is an image (that's the overlay)
    bg_fill_is_image = isinstance(settings.background_fill, ImageFill)
    pattern_asset_id = settings.background_fill.asset_id if bg_fill_is_image else ""

    from .material_stripes_zone import material_for_stripes_zone

    stripe_mat = material_for_stripes_zone(
        base_palette_name=_palette_base_name_from_material(mat),
        finish=settings.finish,
        pattern_fill=settings.pattern_fill,
        background_fill=settings.background_fill,
        stripe_width=settings.stripe_width,
        stripe_preset=settings.stripe_preset,
        rot_yaw_deg=settings.stripe_yaw,
        rot_pitch_deg=settings.stripe_pitch,
        zone_hex_fallback=settings.zone_hex,
        instance_suffix=f"{settings.zone}_tex_stripe",
    )
    if not pattern_asset_id:
        return stripe_mat

    # Overlay background_fill image onto stripes
    bg_uv_rect = None
    if bg_fill_is_image:
        bg_uv_rect = settings.background_fill.uv_rect

    underlay_uv = resolve_texture_pattern_overlay_uv_rect(
        zone=zone,
        build_options=build_options,
        zone_feature=zone_feature,
        pattern_asset_id=pattern_asset_id,
        zone_image_asset_id=zone_image_asset_id,
        channel_uv_rect=bg_uv_rect,
    )
    return overlay_base_image_on_zone_material(
        stripe_mat,
        asset_id=pattern_asset_id,
        underlay_uv_rect=underlay_uv,
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
        zone_feature = zone_features.get(zone)
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
            out[zone] = _apply_spots_pattern(
                mat,
                settings,
                zone=zone,
                build_options=build_options,
                zone_feature=zone_feature,
            )
        elif settings.mode == "checkerboard":
            out[zone] = _apply_checkerboard_pattern(
                mat,
                settings,
                zone=zone,
                build_options=build_options,
                zone_feature=zone_feature,
                zone_image_asset_id=resolve_zone_color_image_asset_id(zone, build_options, zone_feature),
            )
        elif settings.mode == "stripes":
            out[zone] = _apply_stripes_pattern(
                mat,
                settings,
                zone=zone,
                build_options=build_options,
                zone_feature=zone_feature,
                zone_image_asset_id=resolve_zone_color_image_asset_id(zone, build_options, zone_feature),
            )

        image_asset_id = resolve_zone_color_image_asset_id(zone, build_options, zone_feature)
        if image_asset_id and out.get(zone) is not None and settings.mode in ("gradient", "checkerboard", "stripes"):
            out[zone] = overlay_base_image_on_zone_material(
                out[zone],
                asset_id=image_asset_id,
                underlay_uv_rect=resolve_zone_color_image_uv_rect(zone, build_options, zone_feature),
            )
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
