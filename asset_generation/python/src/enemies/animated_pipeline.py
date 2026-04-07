"""
Blender-side pipeline for animated enemy generation (shared by generator + CLI blueprint).
"""

from __future__ import annotations

import random

import bpy

from ..core.blender_utils import clear_scene
from ..materials.material_system import setup_materials
from .animated import AnimatedEnemyBuilder
from .base_enemy import export_enemy


def setup_blender_scene() -> None:
    """Clear scene, camera, and sun (matches generator.py)."""
    clear_scene()
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.1, 0, 0.785398)
    bpy.ops.object.light_add(type="SUN", location=(4, 4, 8))
    light = bpy.context.active_object
    light.data.energy = 3.0


def run_blueprint_export_in_blender(
    blueprint_name: str,
    enemy_type: str,
    generation_seed: int,
    export_dir: str,
) -> bool:
    """Execute inside Blender: build one enemy from blueprint and export GLB."""
    clear_scene()
    materials = setup_materials()
    rng = random.Random(generation_seed)
    built = AnimatedEnemyBuilder.create_enemy(enemy_type, materials, rng)
    if built.armature and built.mesh:
        export_enemy(built.armature, built.mesh, blueprint_name, export_dir, built.attack_profile)
        print(f"✅ Generated {blueprint_name}")
        return True
    print("❌ Generation failed")
    return False
