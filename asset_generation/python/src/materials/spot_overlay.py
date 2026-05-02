"""Composite an underlay image onto a spot-plate material (single implementation).

``material_system`` and ``feature_zones`` delegate here so overlay behavior stays in one place.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import bpy

from src.materials.gradient_generator import sanitize_image_label
from src.materials.pattern_composite import combine_pattern_over_base_image
from src.materials.spot_plate_mask import (
    DEFAULT_DARK_THRESHOLD,
    DEFAULT_MASK_BOX_BLUR_RADIUS,
    DEFAULT_MASK_FEATHER,
)
from src.materials.spots_composite_debug import log_spots_composite
from src.materials.uv_atlas import (
    is_full_uv_rect,
    mapping_scale_location_for_uv_rect,
)
from src.utils.texture_asset_loader import get_texture_asset_filepath


def _find_principled_bsdf(nodes: Any) -> object | None:
    """Locate Principled BSDF across Blender versions (``type`` vs ``bl_idname``)."""
    for n in nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
        if n.bl_idname == "ShaderNodeBsdfPrincipled":
            return n
    return None


def _principled_base_color_socket(bsdf: object) -> object | None:
    """English ``Base Color``; some builds expose ``Color`` on Principled."""
    inp = bsdf.inputs.get("Base Color")
    if inp is None:
        inp = bsdf.inputs.get("Color")
    return inp


def _spot_mask_soft_edges_from_material(mat: bpy.types.Material) -> bool:
    """Read mask transition toggle (soft feather + blur vs hard binary edge)."""
    if "blobert_spot_plate_mask_soft_edges" not in mat:
        return True
    raw = mat["blobert_spot_plate_mask_soft_edges"]
    if isinstance(raw, bool):
        return raw
    try:
        i = int(raw)
        return i != 0
    except (TypeError, ValueError):
        return True


def _spot_mask_params(mat: bpy.types.Material) -> tuple[str, float, bool]:
    """Read spot-plate mask options stored on the material by ``material_for_spots_zone_from_image_asset``."""
    mask_mode = str(mat["blobert_spot_plate_mask_mode"] if "blobert_spot_plate_mask_mode" in mat else "auto")
    if not mask_mode:
        mask_mode = "auto"
    dark_thr = DEFAULT_DARK_THRESHOLD
    if "blobert_spot_plate_dark_threshold" in mat:
        try:
            dark_thr = float(mat["blobert_spot_plate_dark_threshold"])
        except (TypeError, ValueError):
            dark_thr = DEFAULT_DARK_THRESHOLD
    return mask_mode, dark_thr, _spot_mask_soft_edges_from_material(mat)


def _resolve_pattern_sources(
    mat: bpy.types.Material,
    existing_src: object | None,
) -> tuple[Path | None, object | None]:
    """Disk path and/or loaded Blender image for the spot plate (prefer tagged paths)."""
    pattern_img = None
    pattern_path: Path | None = None
    tagged_name = str(mat["blobert_spot_image_name"] if "blobert_spot_image_name" in mat else "") or ""
    tagged_path = str(mat["blobert_spot_image_path"] if "blobert_spot_image_path" in mat else "") or ""
    if tagged_path:
        p = Path(tagged_path)
        if p.exists():
            pattern_path = p
    if tagged_name:
        pattern_img = bpy.data.images.get(tagged_name)
    if pattern_img is None and existing_src is not None:
        tex_node = existing_src.node
        if tex_node is not None:
            try:
                linked_img = tex_node.image
            except AttributeError:
                linked_img = None
            if linked_img is not None:
                pattern_img = linked_img
    if pattern_path is None and pattern_img is not None:
        raw_fp = pattern_img.filepath_raw or pattern_img.filepath
        p = Path(bpy.path.abspath(raw_fp))
        if p.exists():
            pattern_path = p
    return pattern_path, pattern_img


def _wire_tex_uv_to_base_color(
    nodes: Any,
    links: Any,
    bc_in: object,
    image: bpy.types.Image,
    uv_rect: tuple[float, float, float, float] | None = None,
) -> None:
    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = image
    coord_node = nodes.new(type="ShaderNodeTexCoord")
    coord_node.location = (-800, 200)
    tex_node.location = (-450, 200)
    use_mapping = uv_rect is not None and not is_full_uv_rect(uv_rect)
    if use_mapping:
        mapping_node = nodes.new(type="ShaderNodeMapping")
        mapping_node.location = (-620, 200)
        scale_vec, loc_vec = mapping_scale_location_for_uv_rect(uv_rect)
        mapping_node.inputs["Scale"].default_value = scale_vec
        mapping_node.inputs["Location"].default_value = loc_vec
        links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
        links.new(mapping_node.outputs["Vector"], tex_node.inputs["Vector"])
    else:
        links.new(coord_node.outputs["UV"], tex_node.inputs["Vector"])
    links.new(tex_node.outputs["Color"], bc_in)


def _wire_multiply_underlay_over_existing(
    nodes: Any,
    links: Any,
    bc_in: object,
    underlay_image: bpy.types.Image,
    existing_src: object,
    uv_rect: tuple[float, float, float, float] | None = None,
) -> None:
    tex_node = nodes.new(type="ShaderNodeTexImage")
    tex_node.image = underlay_image
    coord_node = nodes.new(type="ShaderNodeTexCoord")
    coord_node.location = (-800, 120)
    tex_node.location = (-450, 120)
    use_mapping = uv_rect is not None and not is_full_uv_rect(uv_rect)
    if use_mapping:
        mapping_node = nodes.new(type="ShaderNodeMapping")
        mapping_node.location = (-620, 120)
        scale_vec, loc_vec = mapping_scale_location_for_uv_rect(uv_rect)
        mapping_node.inputs["Scale"].default_value = scale_vec
        mapping_node.inputs["Location"].default_value = loc_vec
        links.new(coord_node.outputs["UV"], mapping_node.inputs["Vector"])
        links.new(mapping_node.outputs["Vector"], tex_node.inputs["Vector"])
    else:
        links.new(coord_node.outputs["UV"], tex_node.inputs["Vector"])
    mix = nodes.new(type="ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 1.0
    links.new(tex_node.outputs["Color"], mix.inputs["Color1"])
    links.new(existing_src, mix.inputs["Color2"])
    links.new(mix.outputs["Color"], bc_in)


def overlay_base_image_onto_material(
    mat: bpy.types.Material,
    *,
    asset_id: str = "",
    base_path: Path | None = None,
    underlay_uv_rect: tuple[float, float, float, float] | None = None,
    log_prefix: str = "",
) -> bpy.types.Material:
    """Replace or multiply-combine base color with underlay; prefer mask composite PNG when possible."""

    def lg(msg: str) -> None:
        log_spots_composite(f"{log_prefix}{msg}" if log_prefix else msg)

    if not asset_id and base_path is None:
        return mat

    if not mat.use_nodes:
        mat.use_nodes = True
    nt = mat.node_tree
    if nt is None:
        return mat
    nodes = nt.nodes
    links = nt.links
    bsdf = _find_principled_bsdf(nodes)
    if bsdf is None:
        return mat
    bc_in = _principled_base_color_socket(bsdf)
    if bc_in is None:
        return mat

    existing_src = bc_in.links[0].from_socket if bc_in.links else None
    for lk in list(bc_in.links):
        links.remove(lk)

    try:
        if base_path is not None:
            resolved_base = Path(base_path).resolve()
        else:
            resolved_base = Path(get_texture_asset_filepath(asset_id))
        underlay_img = bpy.data.images.load(str(resolved_base))
        underlay_img.pack()
    except (ValueError, OSError, IOError, Exception) as e:
        lg(
            "overlay_underlay: failed to load base texture "
            f"asset_id={asset_id!r} base_path={base_path!r}: {type(e).__name__}: {e}",
        )
        if existing_src is not None:
            links.new(existing_src, bc_in)
        return mat

    lg(f"overlay_underlay: loaded base (underlay) asset_id={asset_id!r} path={resolved_base}")

    pattern_path, pattern_img = _resolve_pattern_sources(mat, existing_src)

    if pattern_path is not None or pattern_img is not None:
        pattern_name = str(
            pattern_img.name if pattern_img is not None else (pattern_path.stem if pattern_path is not None else "pattern"),
        )
        combined_name = f"BlobertTexSpotCombined_{sanitize_image_label(pattern_name)}"
        lg(
            "overlay_underlay: attempting mask composite "
            f"(pattern_path={pattern_path!s}, pattern_img={(pattern_img.name if pattern_img is not None else None)!r}) "
            f"over base_path={resolved_base!s}",
        )
        mask_mode, dark_thr, mask_soft_edges = _spot_mask_params(mat)
        combined_img = combine_pattern_over_base_image(
            pattern_path,
            resolved_base,
            combined_name,
            mask_mode=mask_mode,
            dark_threshold=dark_thr,
            mask_feather=DEFAULT_MASK_FEATHER,
            mask_box_blur_radius=DEFAULT_MASK_BOX_BLUR_RADIUS,
            mask_soft_edges=mask_soft_edges,
        )
        if combined_img is not None:
            lg(
                "overlay_underlay: success → base color uses combined image "
                f"{combined_img.name!r} (mask blends pattern × base)",
            )
            _wire_tex_uv_to_base_color(nodes, links, bc_in, combined_img, uv_rect=None)
            return mat
        lg(
            "overlay_underlay: combine_pattern_over_base_image returned None "
            "(see earlier error log); falling back below",
        )
    else:
        lg("overlay_underlay: no pattern_path/image on material; multiply fallback")

    lg(
        "overlay_underlay: FALLBACK multiply blend base×pattern — "
        "not the same as masked composite; expect muddy tint if pattern covers UV.",
    )
    if existing_src is None:
        _wire_tex_uv_to_base_color(nodes, links, bc_in, underlay_img, uv_rect=underlay_uv_rect)
        return mat

    _wire_multiply_underlay_over_existing(
        nodes,
        links,
        bc_in,
        underlay_img,
        existing_src,
        uv_rect=underlay_uv_rect,
    )
    return mat
