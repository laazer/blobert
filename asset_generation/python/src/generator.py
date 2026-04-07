#!/usr/bin/env python3
"""
Organized enemy generator using the modular system
"""

import os
import random
import sys

# Blender imports

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.blender_utils import clear_scene
from src.enemies.animated import AnimatedEnemyBuilder
from src.enemies.animated_pipeline import setup_blender_scene
from src.enemies.base_enemy import export_enemy
from src.materials.material_system import ENEMY_FINISH_PRESETS, setup_materials
from src.prefabs.prefab_loader import load_prefab_mesh_if_requested
from src.utils.animated_build_options import options_for_enemy, parse_build_options_json
from src.utils.constants import ExportConfig
from src.utils.enemy_slug_registry import normalize_animated_slug
from src.utils.export_naming import animated_export_stem


def _build_options_for_current_enemy(enemy_type: str) -> dict:
    raw = parse_build_options_json(os.environ.get("BLOBERT_BUILD_OPTIONS_JSON"))
    return options_for_enemy(enemy_type, raw)


def setup_scene():
    """Set up Blender scene for enemy generation."""
    setup_blender_scene()


def generate_animated_enemy(
    enemy_type,
    count: int = 1,
    seed: int = None,
    export_dir: str = ExportConfig.ANIMATED_DIR,
    prefab_name: str = None,
    finish: str = "default",
    hex_color: str = "",
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
    materials = setup_materials(enemy_finish=finish, enemy_hex_color=hex_color)

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
            prefab_mesh = load_prefab_mesh_if_requested(prefab_name)

            built = AnimatedEnemyBuilder.create_enemy(
                enemy_type,
                materials,
                rng,
                prefab_mesh=prefab_mesh,
                build_options=_build_options_for_current_enemy(enemy_type),
            )
            armature, mesh, attack_profile = built.armature, built.mesh, built.attack_profile

            if armature and mesh:
                filename = animated_export_stem(enemy_type, i, prefab_name=prefab_name)
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


def _parse_flag_arg(args, flag_name: str) -> str:
    if flag_name in args:
        flag_idx = args.index(flag_name)
        if flag_idx + 1 < len(args):
            return args[flag_idx + 1]
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

    enemy_type = normalize_animated_slug(positional_args[0])
    count = int(positional_args[1]) if len(positional_args) > 1 and not positional_args[1].startswith('--') else 1
    seed_str = positional_args[2] if len(positional_args) > 2 and not positional_args[2].startswith('--') else None
    seed = int(seed_str) if seed_str else None
    prefab_name = _parse_prefab_arg(positional_args)
    finish = _parse_flag_arg(positional_args, "--finish") or "default"
    hex_color = _parse_flag_arg(positional_args, "--hex-color") or ""
    build_json = _parse_flag_arg(positional_args, "--build-json")
    if build_json:
        os.environ["BLOBERT_BUILD_OPTIONS_JSON"] = build_json

    if enemy_type not in AnimatedEnemyBuilder.get_available_types():
        print(f"❌ Unknown enemy type: {enemy_type}")
        print("Available types:", AnimatedEnemyBuilder.get_available_types())
        return
    if finish not in ENEMY_FINISH_PRESETS:
        print(f"❌ Unknown finish: {finish}")
        print(f"Available finishes: {list(ENEMY_FINISH_PRESETS)}")
        return

    prefab_note = f" (prefab: {prefab_name})" if prefab_name else ""
    hex_note = f", hex={hex_color}" if hex_color else ""
    print(f"🎮 Generating {count} {enemy_type}(s), finish={finish}{hex_note}{prefab_note}...")
    generate_animated_enemy(enemy_type, count, seed, prefab_name=prefab_name, finish=finish, hex_color=hex_color)
    print("✅ Generation complete!")


if __name__ == "__main__":
    main()