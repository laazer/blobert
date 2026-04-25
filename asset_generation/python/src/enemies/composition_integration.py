"""Integration helpers for using composition utilities with existing enemy builders."""

from __future__ import annotations

from typing import Any, Mapping

from mathutils import Euler, Vector

from .composition_utils import (
    apply_material_by_semantic_part,
    calculate_limb_anchor_positions,
    position_appendage_at_anchor,
    rotate_part_by_semantic_name,
    tag_part_semantically,
)


def build_body_with_composition(
    builder: Any,
    body_scale: float,
    mesh_scale_y: float,
    mesh_scale_z: float,
    build_options: Mapping[str, Any],
) -> None:
    """Build body/head/feature meshes using composition utilities.
    
    Args:
        builder: Enemy builder instance with _create_mesh method
        body_scale: Base scale for body dimensions
        mesh_scale_y: Y-axis scaling factor
        mesh_scale_z: Z-axis scaling factor
        build_options: Build configuration options
    """
    from ..utils.body_type_presets import spider_body_type_scales
    
    rx, ry, rz, leg_m = spider_body_type_scales(build_options)
    
    body_radii = Vector(
        (
            body_scale * rx,
            body_scale * mesh_scale_y * ry,
            body_scale * mesh_scale_z * rz,
        )
    )
    
    # Build head with semantic tagging
    head_mesh = builder._create_mesh("head", body_radii)
    tag_part_semantically(head_mesh, "head", "feature")
    rotate_part_by_semantic_name(head_mesh, "head", base_rotation=Euler((0, 0, 0)))
    
    # Build body with semantic tagging
    body_mesh = builder._create_mesh("body", body_radii)
    tag_part_semantically(body_mesh, "body", "feature")


def build_limbs_with_composition(
    builder: Any,
    leg_count: int,
    leg_segments: int,
    leg_nominal: float,
    anchor_ratios: tuple[tuple[float, float, float], ...],
    body_radii: Vector,
) -> None:
    """Build appendage meshes using composition utilities.
    
    Args:
        builder: Enemy builder instance with _create_limb method
        leg_count: Number of legs to build
        leg_segments: Segments per leg
        leg_nominal: Nominal leg length
        anchor_ratios: Anchor position ratios for each leg
        body_radii: Body radii vector for scaling
    """
    positions = calculate_limb_anchor_positions(
        body_radii=body_radii,
        leg_count=min(leg_count, len(anchor_ratios)),
        anchor_ratios=anchor_ratios,
        scale_factor=1.0,
    )
    
    for i, position in enumerate(positions):
        limb = builder._create_limb(i, leg_segments)
        
        # Position at calculated anchor
        position_appendage_at_anchor(
            appendage=limb,
            anchor_ratio=anchor_ratios[i],
            body_radii=body_radii,
            offset_z=0.0,
        )
        
        # Tag with semantic metadata
        side = "left" if i < leg_count // 2 else "right"
        tag_part_semantically(
            obj=limb,
            semantic_name=f"{side}_leg_{i}",
            part_type="appendage",
            metadata={"segments": leg_segments},
        )


def apply_materials_with_composition(
    builder: Any,
    material_func: callable,
) -> None:
    """Apply materials using semantic part tagging.
    
    Args:
        builder: Enemy builder instance with mesh objects
        material_func: Function that takes (zone_part, semantic_name) and returns material
    """
    # Apply to head
    if hasattr(builder, "head_mesh"):
        apply_material_by_semantic_part(
            obj=builder.head_mesh,
            material_func=material_func,
            semantic_name="head",
            part_zone="head",
        )
    
    # Apply to body
    if hasattr(builder, "body_mesh"):
        apply_material_by_semantic_part(
            obj=builder.body_mesh,
            material_func=material_func,
            semantic_name="body",
            part_zone="body",
        )


__all__ = [
    "build_body_with_composition",
    "build_limbs_with_composition",
    "apply_materials_with_composition",
]
