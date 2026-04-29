"""Feature-zone material override logic and pattern dispatch."""

from __future__ import annotations

import bpy

from src.materials.gradient_generator import (
    create_gradient_png_and_load,
    create_spots_png_and_load,
    gradient_image_pixel_buffer,
    sanitize_image_label,
)
from src.materials.material_stripes_zone import material_for_stripes_zone
from src.materials.material_types import (
    FeatureMap,
    ZoneTextureOptions,
    feature_zone_map,
)
from src.materials.presets import (
    ENEMY_FINISH_PRESETS,
    MaterialColors,
    parse_hex_color,
    rgba_from_hex_or_fallback,
    sanitize_hex_input,
)
from src.materials.texture_handlers import create_material
from src.utils.texture_asset_loader import (
    get_texture_asset_filepath,
    infer_texture_asset_id_from_preview,
)


def _palette_base_name_from_material(mat: object) -> str:
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
    """Create a material with preloaded texture as the base color.

    Args:
        base_material: Material to copy and modify
        asset_id: Preloaded texture asset ID (e.g., "stripe_01")
        instance_suffix: Suffix for the material name

    Returns:
        Modified material with texture wired to Base Color, or base material if load fails.
        Always calls img.pack() for GLB embedding.
    """
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
) -> bpy.types.Material:
    all_colors = MaterialColors.get_all()
    base_color = all_colors.get(base_palette_name, (0.6, 0.5, 0.5, 1.0))
    parsed_hex = sanitize_hex_input(hex_str)
    override_color = parse_hex_color(parsed_hex) if parsed_hex else None
    material_color = override_color if override_color is not None else base_color

    finish_roughness, finish_metallic, finish_transmission = ENEMY_FINISH_PRESETS.get(
        finish,
        ENEMY_FINISH_PRESETS["default"],
    )
    force_surface = finish != "default"
    force_base_color = override_color is not None
    is_metallic = base_palette_name in {"Metal_Gray", "Chrome_Silver", "Gold_Yellow", "Copper_Orange"}
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
    zone_features = feature_zone_map(features)
    if not zone_features:
        return dict(slot_materials)
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
        out[slot_key] = _material_for_finish_hex(
            base_palette_name=_palette_base_name_from_material(mat),
            finish=str(finish),
            hex_str=hex_str,
            instance_suffix=str(slot_key),
        )
    return out


def _find_principled_bsdf(nodes: object) -> object | None:  # pragma: no cover
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


def _add_uv_gradient_to_principled(
    mat: bpy.types.Material,
    color_a: tuple[float, float, float, float],
    color_b: tuple[float, float, float, float],
    direction: str,
    *,
    image_label: str = "gradient",
) -> None:
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

    normalized_direction = str(direction or "horizontal").strip().lower()
    if normalized_direction == "vertical":
        width, height = 4, 256
    elif normalized_direction == "radial":
        width, height = 128, 128
    else:
        width, height = 256, 4

    safe_label = sanitize_image_label(image_label)
    image_name = f"BlobertTexGrad_{safe_label}"
    pixel_buffer = gradient_image_pixel_buffer(width, height, color_a, color_b, normalized_direction)
    img = create_gradient_png_and_load(width, height, pixel_buffer, image_name)

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
    palette_base = MaterialColors.get_all().get(base_palette_name, (0.6, 0.5, 0.5, 1.0))
    zone_hex = sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(zone_hex) if len(zone_hex) == 6 else palette_base
    color_a = rgba_from_hex_or_fallback(grad_a_hex, zone_rgba)
    color_b = rgba_from_hex_or_fallback(grad_b_hex, (1.0, 1.0, 1.0, 1.0))

    finish_roughness, _, finish_transmission = ENEMY_FINISH_PRESETS.get(finish, ENEMY_FINISH_PRESETS["default"])
    roughness = finish_roughness if finish_roughness is not None else 0.75
    transmission = finish_transmission if finish_transmission is not None else 0.0
    alpha = color_a[3] if len(color_a) > 3 else 1.0
    mat = create_material(
        f"{base_palette_name}__feat_{instance_suffix}",
        color_a,
        0.0,
        roughness,
        alpha,
        transmission,
        add_texture=False,
        force_surface=finish != "default",
        force_base_color=False,
    )
    _add_uv_gradient_to_principled(mat, color_a, color_b, direction, image_label=instance_suffix)
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
    palette_base = MaterialColors.get_all().get(base_palette_name, (0.6, 0.5, 0.5, 1.0))
    zone_hex = sanitize_hex_input(zone_hex_fallback)
    zone_rgba = parse_hex_color(zone_hex) if len(zone_hex) == 6 else palette_base
    spot_color = rgba_from_hex_or_fallback(spot_hex, zone_rgba)

    finish_roughness, _, finish_transmission = ENEMY_FINISH_PRESETS.get(finish, ENEMY_FINISH_PRESETS["default"])
    roughness = finish_roughness if finish_roughness is not None else 0.75
    transmission = finish_transmission if finish_transmission is not None else 0.0
    alpha = spot_color[3] if len(spot_color) > 3 else 1.0
    mat = create_material(
        f"{base_palette_name}__feat_{instance_suffix}",
        spot_color,
        0.0,
        roughness,
        alpha,
        transmission,
        add_texture=False,
        force_surface=finish != "default",
        force_base_color=False,
    )

    img = create_spots_png_and_load(
        width=128,
        height=128,
        spot_color_hex=sanitize_hex_input(spot_hex),
        bg_color_hex=sanitize_hex_input(bg_hex),
        density=density,
        img_name=f"BlobertTexSpot_{sanitize_image_label(instance_suffix)}",
    )
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


def _material_for_asset_zone(  # pragma: no cover
    base_material: bpy.types.Material,
    asset_id: str,
    tile_repeat: float = 1.0,
    instance_suffix: str = "asset",
) -> bpy.types.Material:
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
        coord_node = nodes.new(type="ShaderNodeTexCoord")
        if tile_repeat != 1.0:
            mapping_node = nodes.new(type="ShaderNodeMapping")
            mapping_node.inputs["Scale"].default_value = (tile_repeat, tile_repeat, 1.0)
            links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
            links.new(mapping_node.outputs["Vector"], tex_node.inputs["Vector"])
        else:
            links.new(coord_node.outputs["UV"], tex_node.inputs["Vector"])
        links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
    except (ValueError, IOError, Exception) as error:
        print(f"Warning: failed to load asset texture {asset_id}: {error}")
    return mat


def apply_zone_texture_pattern_overrides(
    slot_materials: dict[str, bpy.types.Material | None],
    build_options: FeatureMap | None,
) -> dict[str, bpy.types.Material | None]:
    if not build_options:
        return dict(slot_materials)
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
            out[zone] = _material_for_gradient_zone(
                base_palette_name=_palette_base_name_from_material(mat),
                finish=settings.finish,
                grad_a_hex=settings.gradient_a_hex,
                grad_b_hex=settings.gradient_b_hex,
                direction=settings.gradient_direction,
                zone_hex_fallback=settings.zone_hex,
                instance_suffix=f"{zone}_tex_grad",
            )
        elif settings.mode == "assets":
            if settings.asset_id:
                out[zone] = _material_for_asset_zone(
                    base_material=mat,
                    asset_id=settings.asset_id,
                    tile_repeat=settings.tile_repeat,
                    instance_suffix=f"{zone}_tex_asset",
                )
        elif settings.mode == "spots":
            # Preserve historical behavior in this module: invalid density payloads
            # are treated as no-op instead of coercing to defaults.
            try:
                float(build_options.get(f"feat_{zone}_texture_spot_density", 1.0) or 1.0)
            except (TypeError, ValueError):
                continue
            pattern_asset_id = settings.pattern_image_asset_id(("spot_color", "spot_bg_color"))
            if pattern_asset_id:
                out[zone] = _material_for_asset_zone(
                    base_material=mat,
                    asset_id=pattern_asset_id,
                    tile_repeat=settings.tile_repeat,
                    instance_suffix=f"{zone}_tex_asset",
                )
                continue
            out[zone] = material_for_spots_zone(
                base_palette_name=_palette_base_name_from_material(mat),
                finish=settings.finish,
                spot_hex=settings.spot_color.resolved_hex(),
                bg_hex=settings.spot_bg_color.resolved_hex(),
                density=settings.spot_density,
                zone_hex_fallback=settings.zone_hex,
                instance_suffix=f"{zone}_tex_spot",
            )
        elif settings.mode == "stripes":
            pattern_asset_id = settings.pattern_image_asset_id(("stripe_color", "stripe_bg_color"))
            if pattern_asset_id:
                out[zone] = _material_for_asset_zone(
                    base_material=mat,
                    asset_id=pattern_asset_id,
                    tile_repeat=settings.tile_repeat,
                    instance_suffix=f"{zone}_tex_asset",
                )
                continue
            out[zone] = material_for_stripes_zone(
                base_palette_name=_palette_base_name_from_material(mat),
                finish=settings.finish,
                stripe_hex=settings.stripe_color.resolved_hex(),
                bg_hex=settings.stripe_bg_color.resolved_hex(),
                stripe_width=settings.stripe_width,
                stripe_preset=settings.stripe_preset,
                rot_yaw_deg=settings.stripe_yaw,
                rot_pitch_deg=settings.stripe_pitch,
                zone_hex_fallback=settings.zone_hex,
                instance_suffix=f"{zone}_tex_stripe",
            )
    return out


def material_for_zone_part(
    zone: str,
    part_id: str | None,
    slot_materials: dict[str, bpy.types.Material | None],
    features: FeatureMap | None,
) -> bpy.types.Material | None:
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
    p_hex = sanitize_hex_input(pf.hex_value)
    p_fin = str(pf.finish)
    z_hex = sanitize_hex_input(zf.hex_value)
    z_fin = str(zf.finish)
    if not (bool(p_hex) or p_fin != "default"):
        return base
    eff_fin = p_fin if p_fin != "default" else z_fin
    eff_hex = p_hex or z_hex
    if eff_fin == "default" and not eff_hex:
        return base
    safe_part = str(part_id).replace(".", "_")
    return _material_for_finish_hex(
        base_palette_name=_palette_base_name_from_material(base),
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
    base = slot_materials.get(zone)
    if base is None:
        return None
    extra_hex_sanitized = sanitize_hex_input(extra_hex)
    finish = str(extra_finish or "default")
    zone_feature = feature_zone_map(features).get(zone)
    zone_hex = sanitize_hex_input(zone_feature.hex_value) if zone_feature is not None else ""
    zone_finish = str(zone_feature.finish) if zone_feature is not None else "default"
    eff_fin = finish if finish != "default" else zone_finish
    eff_hex = extra_hex_sanitized or zone_hex
    if eff_fin == "default" and not eff_hex:
        return base
    return _material_for_finish_hex(
        base_palette_name=_palette_base_name_from_material(base),
        finish=eff_fin,
        hex_str=eff_hex,
        instance_suffix=f"{zone}_zgeom_extra",
    )
