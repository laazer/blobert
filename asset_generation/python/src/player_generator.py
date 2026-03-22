#!/usr/bin/env python3
"""
Blender-side player slime generator — invoked as a subprocess by main.py.

Usage (via main.py):
    blender --background --python src/player_generator.py -- [color] [count] [seed]
"""

import sys
import os
import random

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.blender_utils import clear_scene
from src.player.player_builder import PlayerSlimeBuilder, export_player_slime
from src.player.player_materials import SLIME_COLORS
from src.utils.constants import PlayerExportConfig


def setup_scene():
    clear_scene()

    bpy.ops.object.camera_add(location=(5, -5, 4))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.1, 0, 0.785398)

    bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
    bpy.context.active_object.data.energy = 3.0


def _load_prefab_mesh_if_requested(prefab_name: str):
    """Load a prefab mesh from the prefabs/ directory, or return None."""
    if not prefab_name:
        return None
    from src.prefabs.prefab_loader import load_prefab_mesh
    print(f"📦 Loading prefab: {prefab_name}")
    mesh, entry = load_prefab_mesh(prefab_name)
    print(f"✅ Prefab loaded: {entry.description}")
    return mesh


def generate_player_slime(
    color: str = "blue",
    count: int = 1,
    seed: int = None,
    export_dir: str = PlayerExportConfig.PLAYER_DIR,
    prefab_name: str = None,
):
    """Generate player slime variants.

    Args:
        color: Slime color key from SLIME_COLORS.
        count: Number of variants to generate.
        seed: Optional random seed for reproducibility.
        export_dir: Output directory for GLB files.
        prefab_name: Optional prefab name; when given, the downloaded model
            replaces procedural body geometry (player animations still applied).
    """
    if seed is not None:
        random.seed(seed)

    for variant_index in range(count):
        print(f"Generating player slime ({color}) #{variant_index:02d}...")

        clear_scene()
        setup_scene()

        rng = random.Random(random.randint(0, 999999))

        try:
            # Reload prefab each iteration — clear_scene() removes imported objects
            prefab_mesh = _load_prefab_mesh_if_requested(prefab_name)

            armature, mesh = PlayerSlimeBuilder.build(color=color, rng=rng, prefab_mesh=prefab_mesh)

            filename = PlayerExportConfig.FILENAME_PATTERN.format(
                color=color, variant=variant_index
            )
            filepath = export_player_slime(armature, mesh, filename, export_dir)
            print(f"✅ Exported: {filepath}")

        except Exception as error:
            print(f"❌ Error generating player slime #{variant_index}: {error}")
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
    separator = "--"
    args = sys.argv[sys.argv.index(separator) + 1:] if separator in sys.argv else []

    color = args[0] if len(args) > 0 and not args[0].startswith('--') else "blue"
    count = int(args[1]) if len(args) > 1 and not args[1].startswith('--') else 1
    seed_str = args[2] if len(args) > 2 and not args[2].startswith('--') else None
    seed = int(seed_str) if seed_str else None
    prefab_name = _parse_prefab_arg(args)

    available_colors = PlayerSlimeBuilder.get_available_colors()
    if color not in available_colors:
        print(f"❌ Unknown color: {color!r}. Available: {available_colors}")
        return

    prefab_note = f" (prefab: {prefab_name})" if prefab_name else ""
    print(f"🫧 Generating {count} × player_slime ({color}){prefab_note}...")
    generate_player_slime(color, count, seed, prefab_name=prefab_name)
    print("✅ Done!")


if __name__ == "__main__":
    main()
