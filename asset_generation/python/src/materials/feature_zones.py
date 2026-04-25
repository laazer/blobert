"""Feature-zone material override logic and pattern dispatch."""

from __future__ import annotations

import math
from collections.abc import Mapping

import bpy

from src.materials.gradient_generator import (
    create_gradient_png_and_load,
    create_spots_png_and_load,
    gradient_image_pixel_buffer,
    sanitize_image_label,
)
from src.materials.material_stripes_zone import material_for_stripes_zone
from src.materials.presets import (
    ENEMY_FINISH_PRESETS,
    MaterialColors,
    parse_hex_color,
    rgba_from_hex_or_fallback,
    sanitize_hex_input,
)
from src.materials.texture_handlers import create_material
from src.utils.texture_asset_loader import get_texture_asset_filepath


def _palette_base_name_from_material(mat: object) -> str:
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
    features: Mapping[str, object] | None,
) -> dict[str, bpy.types.Material | None]:
    if not features:
        return dict(slot_materials)
    out: dict[str, bpy.types.Material | None] = dict(slot_materials)
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
        if node.type == "BSDF" and isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
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
    build_options: Mapping[str, object] | None,
) -> dict[str, bpy.types.Material | None]:
    if not build_options:
        return dict(slot_materials)
    out: dict[str, bpy.types.Material | None] = dict(slot_materials)
    features = build_options.get("features")
    feature_dict: dict[str, object] = features if isinstance(features, dict) else {}

    for zone, mat in list(out.items()):
        if mat is None:
            continue
        mode = str(build_options.get(f"feat_{zone}_texture_mode", "none")).strip().lower()
        if mode == "gradient":
            zf = feature_dict.get(zone)
            finish = str(zf.get("finish", "default")) if isinstance(zf, dict) else "default"
            zone_hex = (zf.get("hex") or "").strip() if isinstance(zf, dict) else ""
            out[zone] = _material_for_gradient_zone(
                base_palette_name=_palette_base_name_from_material(mat),
                finish=finish,
                grad_a_hex=str(build_options.get(f"feat_{zone}_texture_grad_color_a", "") or ""),
                grad_b_hex=str(build_options.get(f"feat_{zone}_texture_grad_color_b", "") or ""),
                direction=str(build_options.get(f"feat_{zone}_texture_grad_direction", "horizontal") or "horizontal"),
                zone_hex_fallback=zone_hex,
                instance_suffix=f"{zone}_tex_grad",
            )
        elif mode == "assets":
            asset_id = str(build_options.get(f"feat_{zone}_texture_asset_id", "") or "").strip()
            if asset_id:
                tile_raw = build_options.get(f"feat_{zone}_texture_asset_tile_repeat", 1.0) or 1.0
                out[zone] = _material_for_asset_zone(
                    base_material=mat,
                    asset_id=asset_id,
                    tile_repeat=float(tile_raw),
                    instance_suffix=f"{zone}_tex_asset",
                )
        elif mode == "spots":
            zf = feature_dict.get(zone)
            finish = str(zf.get("finish", "default")) if isinstance(zf, dict) else "default"
            zone_hex = (zf.get("hex") or "").strip() if isinstance(zf, dict) else ""
            try:
                density = float(build_options.get(f"feat_{zone}_texture_spot_density", 1.0) or 1.0)
            except (TypeError, ValueError):
                continue
            density = max(0.1, min(5.0, density))
            out[zone] = material_for_spots_zone(
                base_palette_name=_palette_base_name_from_material(mat),
                finish=finish,
                spot_hex=str(build_options.get(f"feat_{zone}_texture_spot_color", "") or ""),
                bg_hex=str(build_options.get(f"feat_{zone}_texture_spot_bg_color", "") or ""),
                density=density,
                zone_hex_fallback=zone_hex,
                instance_suffix=f"{zone}_tex_spot",
            )
        elif mode == "stripes":
            zf = feature_dict.get(zone)
            finish = str(zf.get("finish", "default")) if isinstance(zf, dict) else "default"
            zone_hex = (zf.get("hex") or "").strip() if isinstance(zf, dict) else ""
            stripe_width = float(build_options.get(f"feat_{zone}_texture_stripe_width", 0.2) or 0.2)
            stripe_width = max(0.05, min(1.0, stripe_width))
            stripe_preset = str(build_options.get(f"feat_{zone}_texture_stripe_direction", "beachball") or "beachball").strip().lower()
            if stripe_preset in ("horizontal", "y"):
                stripe_preset = "doplar"
            elif stripe_preset in ("vertical", "x"):
                stripe_preset = "beachball"
            elif stripe_preset == "z":
                stripe_preset = "swirl"
            if stripe_preset not in ("beachball", "doplar", "swirl"):
                stripe_preset = "beachball"

            def _stripe_rot(key: str) -> float:
                try:
                    value = float(build_options.get(key, 0.0) or 0.0)
                except (TypeError, ValueError):
                    value = 0.0
                if math.isnan(value) or math.isinf(value):
                    value = 0.0
                return max(-360.0, min(360.0, value))

            yaw_key = f"feat_{zone}_texture_stripe_rot_yaw"
            pitch_key = f"feat_{zone}_texture_stripe_rot_pitch"
            yaw = _stripe_rot(yaw_key)
            pitch = _stripe_rot(pitch_key)
            if pitch_key not in build_options and f"feat_{zone}_texture_stripe_rot_x" in build_options:
                pitch = _stripe_rot(f"feat_{zone}_texture_stripe_rot_x")
            if yaw_key not in build_options and f"feat_{zone}_texture_stripe_rot_y" in build_options:
                yaw = _stripe_rot(f"feat_{zone}_texture_stripe_rot_y")

            out[zone] = material_for_stripes_zone(
                base_palette_name=_palette_base_name_from_material(mat),
                finish=finish,
                stripe_hex=str(build_options.get(f"feat_{zone}_texture_stripe_color", "") or ""),
                bg_hex=str(build_options.get(f"feat_{zone}_texture_stripe_bg_color", "") or ""),
                stripe_width=stripe_width,
                stripe_preset=stripe_preset,
                rot_yaw_deg=yaw,
                rot_pitch_deg=pitch,
                zone_hex_fallback=zone_hex,
                instance_suffix=f"{zone}_tex_stripe",
            )
    return out


def material_for_zone_part(
    zone: str,
    part_id: str | None,
    slot_materials: dict[str, bpy.types.Material | None],
    features: Mapping[str, object] | None,
) -> bpy.types.Material | None:
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
    p_hex = sanitize_hex_input(pf.get("hex", ""))
    p_fin = str(pf.get("finish", "default"))
    z_hex = sanitize_hex_input(zf.get("hex", ""))
    z_fin = str(zf.get("finish", "default"))
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
    features: Mapping[str, object] | None,
    extra_finish: str,
    extra_hex: str,
) -> bpy.types.Material | None:
    base = slot_materials.get(zone)
    if base is None:
        return None
    extra_hex_sanitized = sanitize_hex_input(extra_hex)
    finish = str(extra_finish or "default")
    zone_feature = (features or {}).get(zone) if features else None
    zone_hex = sanitize_hex_input(zone_feature.get("hex", "")) if isinstance(zone_feature, dict) else ""
    zone_finish = str(zone_feature.get("finish", "default")) if isinstance(zone_feature, dict) else "default"
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
