"""Thin orchestration surface for material setup and assignment."""

from __future__ import annotations

import bpy

from src.materials.material_lookup import get_materials_for_enemy_type
from src.materials.presets import ENEMY_FINISH_PRESETS, MaterialColors, parse_hex_color
from src.materials.texture_handlers import create_material
from src.utils.materials import MaterialCategories


def setup_materials(
    enemy_finish: str = "default",
    enemy_hex_color: str = "",
) -> dict[str, bpy.types.Material]:
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
        materials[name] = create_material(
            name=name,
            color=override_color if override_color else color,
            metallic=metallic,
            roughness=roughness,
            alpha=alpha,
            transmission=transmission,
            add_texture=True,
            force_surface=force_surface,
            force_base_color=force_base_color,
        )
    return materials


def get_enemy_materials(
    enemy_name: str,
    materials: dict[str, bpy.types.Material],
    rng,
) -> dict[str, bpy.types.Material | None]:
    return get_materials_for_enemy_type(enemy_name, materials, rng)


def apply_material_to_object(obj: object, material: bpy.types.Material | None) -> None:
    if obj and getattr(obj, "type", None) == "MESH" and material:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(material)
        else:
            obj.data.materials[0] = material
