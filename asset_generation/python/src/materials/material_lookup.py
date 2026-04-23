"""Enemy body-part material lookup and fallback mapping."""

from __future__ import annotations

import bpy

from src.utils.materials import MaterialNames, MaterialThemes


def _build_body_part_material_map(
    available_mats: list[bpy.types.Material],
    rng: object | None,
) -> dict[str, bpy.types.Material]:
    count = len(available_mats)
    if count >= 3:
        limb_mat = available_mats[2]
        extra = rng.choice(available_mats) if rng is not None else available_mats[0]
        return {
            "body": available_mats[0],
            "head": available_mats[1],
            "limbs": limb_mat,
            "joints": limb_mat,
            "extra": extra,
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


def get_materials_for_enemy_type(
    enemy_name: str,
    materials: dict[str, bpy.types.Material],
    rng: object | None,
) -> dict[str, bpy.types.Material | None]:
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
