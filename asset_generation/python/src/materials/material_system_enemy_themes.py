"""Body-part material selection for themed enemies (split from material_system for file-size limits)."""

from __future__ import annotations

import bpy

from src.utils.materials import MaterialNames, MaterialThemes


def _build_body_part_material_map(
    available_mats: list[bpy.types.Material],
    rng,
) -> dict[str, bpy.types.Material]:
    """Map body part names to materials given a list of available theme materials"""
    count = len(available_mats)
    if count >= 3:
        limb_mat = available_mats[2]
        return {
            "body": available_mats[0],
            "head": available_mats[1],
            "limbs": limb_mat,
            "joints": limb_mat,
            "extra": rng.choice(available_mats),
        }
    if count == 2:
        return {
            "body": available_mats[0],
            "head": available_mats[1],
            "limbs": available_mats[0],
            "joints": available_mats[0],
            "extra": available_mats[1],
        }
    fallback = available_mats[0]
    return {
        "body": fallback,
        "head": fallback,
        "limbs": fallback,
        "joints": fallback,
        "extra": fallback,
    }


def get_enemy_materials(
    enemy_name: str,
    materials: dict[str, bpy.types.Material],
    rng,
) -> dict[str, bpy.types.Material | None]:
    """Return a body-part → material mapping for the given enemy type"""
    default_fallback = {
        "body": materials.get(MaterialNames.ORGANIC_BROWN),
        "head": materials.get(MaterialNames.FLESH_PINK),
        "limbs": materials.get(MaterialNames.BONE_WHITE),
        "joints": materials.get(MaterialNames.BONE_WHITE),
        "extra": materials.get(MaterialNames.ORGANIC_BROWN),
    }

    if not MaterialThemes.has_theme(enemy_name):
        return default_fallback

    theme_material_names = MaterialThemes.get_theme(enemy_name)
    available_mats = [materials[n] for n in theme_material_names if n in materials]

    if not available_mats:
        return default_fallback

    return _build_body_part_material_map(available_mats, rng)
