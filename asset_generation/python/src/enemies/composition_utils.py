"""Composition utilities for enemy builders - shared rotation, appendage, and semantic part tagging."""

from __future__ import annotations

import math
from typing import Any, Mapping, Tuple

from mathutils import Euler, Vector


def rotate_part_by_semantic_name(
    obj: Any,
    semantic_name: str,
    base_rotation: Euler | None = None,
) -> None:
    """Apply rotation based on semantic part name.
    
    Args:
        obj: Blender object to rotate
        semantic_name: Semantic identifier (e.g., 'head', 'left_arm', 'tail')
        base_rotation: Optional base rotation to apply before semantic adjustment
    """
    if base_rotation is not None:
        obj.rotation_euler = base_rotation.copy()
    
    # Semantic-based rotation adjustments
    if "left" in semantic_name.lower():
        obj.rotation_euler.z += math.radians(180)
    elif "right" in semantic_name.lower():
        obj.rotation_euler.z -= math.radians(180)
    elif "top" in semantic_name.lower():
        obj.rotation_euler.x += math.radians(90)
    elif "bottom" in semantic_name.lower():
        obj.rotation_euler.x -= math.radians(90)


def position_appendage_at_anchor(
    appendage: Any,
    anchor_ratio: Tuple[float, float, float],
    body_radii: Vector,
    offset_z: float = 0.0,
) -> None:
    """Position appendage at calculated anchor point on body surface.
    
    Args:
        appendage: Blender object for the appendage
        anchor_ratio: Normalized ratio (x, y, z) for position along body surface
        body_radii: Body radii vector for scaling anchor position
        offset_z: Additional Z-axis offset from surface
    """
    position = Vector(
        (
            anchor_ratio[0] * body_radii[0],
            anchor_ratio[1] * body_radii[1],
            anchor_ratio[2] * body_radii[2] + offset_z,
        )
    )
    appendage.location = position


def tag_part_semantically(
    obj: Any,
    semantic_name: str,
    part_type: str,
    metadata: Mapping[str, Any] | None = None,
) -> None:
    """Tag object with semantic metadata for material assignment.
    
    Args:
        obj: Blender object to tag
        semantic_name: Human-readable name (e.g., 'head', 'left_claw')
        part_type: Category type (e.g., 'body', 'appendage', 'feature')
        metadata: Optional additional metadata dictionary
    """
    if not hasattr(obj, "blobert_metadata"):
        obj.blobert_metadata = {}
    
    obj.blobert_metadata["semantic_name"] = semantic_name
    obj.blobert_metadata["part_type"] = part_type
    
    if metadata:
        for key, value in metadata.items():
            obj.blobert_metadata[key] = value


def calculate_limb_anchor_positions(
    body_radii: Vector,
    leg_count: int,
    anchor_ratios: Tuple[Tuple[float, float, float], ...],
    scale_factor: float = 1.0,
) -> list[Vector]:
    """Calculate anchor positions for multiple limbs based on ratios.
    
    Args:
        body_radii: Body radii vector for scaling
        leg_count: Number of legs to position
        anchor_ratios: Tuple of (x, y, z) ratios for each potential anchor
        scale_factor: Overall scale multiplier
        
    Returns:
        List of Vector positions for each limb anchor
    """
    positions = []
    for i in range(min(leg_count, len(anchor_ratios))):
        ratio = anchor_ratios[i]
        position = Vector(
            (
                ratio[0] * body_radii[0] * scale_factor,
                ratio[1] * body_radii[1] * scale_factor,
                ratio[2] * body_radii[2] * scale_factor,
            )
        )
        positions.append(position)
    return positions


def apply_material_by_semantic_part(
    obj: Any,
    material_func: callable,
    semantic_name: str,
    part_zone: str,
) -> None:
    """Apply material based on semantic part and zone.
    
    Args:
        obj: Blender object to apply material to
        material_func: Function that takes (zone_part, semantic_name) and returns material
        semantic_name: Semantic identifier for the part
        part_zone: Zone category (e.g., 'body', 'head', 'appendage')
    """
    material = material_func(part_zone, semantic_name)
    if material is not None:
        # Apply material to object's materials slot
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)


__all__ = [
    "rotate_part_by_semantic_name",
    "position_appendage_at_anchor",
    "tag_part_semantically",
    "calculate_limb_anchor_positions",
    "apply_material_by_semantic_part",
]
