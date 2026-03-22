#!/usr/bin/env python3
"""
Organized enemy generator using the modular system
"""

import sys
import os
import random

# Blender imports
import bpy

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.blender_utils import clear_scene
from src.materials.material_system import setup_materials
from src.enemies.animated_enemies import AnimatedEnemyBuilder
from src.enemies.base_enemy import export_enemy
from src.utils.constants import ExportConfig


def setup_scene():
    """Set up Blender scene for enemy generation"""
    clear_scene()
    
    # Basic camera setup
    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.1, 0, 0.785398)  # Look down at center
    
    # Basic lighting
    bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
    light = bpy.context.active_object
    light.data.energy = 3.0


def _load_prefab_mesh_if_requested(prefab_name: str):
    """Load a prefab mesh from the prefabs/ directory, or return None."""
    if not prefab_name:
        return None
    from src.prefabs.prefab_loader import load_prefab_mesh
    print(f"📦 Loading prefab: {prefab_name}")
    mesh, entry = load_prefab_mesh(prefab_name)
    print(f"✅ Prefab loaded: {entry.description}")
    return mesh


def generate_animated_enemy(
    enemy_type,
    count: int = 1,
    seed: int = None,
    export_dir: str = ExportConfig.ANIMATED_DIR,
    prefab_name: str = None,
):
    """Generate animated enemies using the organised system.

    Args:
        enemy_type: Registered enemy type string.
        count: Number of variants to generate.
        seed: Optional random seed for reproducibility.
        export_dir: Output directory for GLB files.
        prefab_name: Optional prefab name; when given, the downloaded model
            is used as the mesh base instead of procedural geometry.
    """
    if seed is not None:
        random.seed(seed)

    setup_scene()

    # Initialize material system
    materials = setup_materials()

    # Generate enemies
    for i in range(count):
        print(f"Generating {enemy_type} #{i:02d}...")

        # Clear scene for each enemy
        clear_scene()
        setup_scene()

        # Create random number generator
        rng = random.Random(random.randint(0, 999999))

        # Generate enemy
        try:
            # Load prefab per-iteration (each clear_scene removes imported objects)
            prefab_mesh = _load_prefab_mesh_if_requested(prefab_name)

            armature, mesh, attack_profile = AnimatedEnemyBuilder.create_enemy(
                enemy_type, materials, rng, prefab_mesh=prefab_mesh
            )

            if armature and mesh:
                suffix = f"_prefab_{prefab_name}" if prefab_name else ""
                filename = f"{enemy_type}_animated{suffix}_{i:02d}"
                filepath = export_enemy(armature, mesh, filename, export_dir, attack_profile)
                print(f"✅ Exported: {filepath}")
            else:
                print(f"❌ Failed to generate {enemy_type} #{i}")

        except Exception as e:
            print(f"❌ Error generating {enemy_type} #{i}: {e}")
            import traceback
            traceback.print_exc()


def _parse_prefab_arg(args) -> str:
    """Extract --prefab <name> from a positional args list, or return None."""
    if '--prefab' in args:
        prefab_idx = args.index('--prefab')
        if prefab_idx + 1 < len(args):
            return args[prefab_idx + 1]
    return None


def main():
    """Main entry point for the organised generator."""
    positional_args = []
    if "--" in sys.argv:
        idx = sys.argv.index("--") + 1
        positional_args = sys.argv[idx:]

    if len(positional_args) < 1:
        print("Usage: blender --background --python generator.py -- <enemy_type> [count] [seed] [--prefab <name>]")
        print("Available types:", AnimatedEnemyBuilder.get_available_types())
        return

    enemy_type = positional_args[0]
    count = int(positional_args[1]) if len(positional_args) > 1 and not positional_args[1].startswith('--') else 1
    seed_str = positional_args[2] if len(positional_args) > 2 and not positional_args[2].startswith('--') else None
    seed = int(seed_str) if seed_str else None
    prefab_name = _parse_prefab_arg(positional_args)

    if enemy_type not in AnimatedEnemyBuilder.get_available_types():
        print(f"❌ Unknown enemy type: {enemy_type}")
        print("Available types:", AnimatedEnemyBuilder.get_available_types())
        return

    prefab_note = f" (prefab: {prefab_name})" if prefab_name else ""
    print(f"🎮 Generating {count} {enemy_type}(s){prefab_note}...")
    generate_animated_enemy(enemy_type, count, seed, prefab_name=prefab_name)
    print("✅ Generation complete!")


if __name__ == "__main__":
    main()