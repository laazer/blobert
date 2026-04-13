#!/usr/bin/env python3
"""
Blender-side level object generator — invoked as a subprocess by main.py.

Usage (via main.py):
    blender --background --python src/level_generator.py -- <object_type> [count] [seed]
"""

import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.core.blender_utils import clear_scene
from src.level.level_object_builder import LevelObjectBuilder
from src.utils.export_subdir import level_export_directory, variant_start_index


def setup_scene():
    """Set up a minimal Blender scene for level object generation."""
    clear_scene()

    bpy.ops.object.camera_add(location=(7, -7, 5))
    camera = bpy.context.active_object
    camera.rotation_euler = (1.1, 0, 0.785398)

    bpy.ops.object.light_add(type='SUN', location=(4, 4, 8))
    bpy.context.active_object.data.energy = 3.0


def generate_level_object(
    object_type: str,
    count: int = 1,
    seed: int = None,
    export_dir: str | None = None,
):
    """Generate one or more variants of the specified level object type."""
    if export_dir is None:
        export_dir = level_export_directory()
    if seed is not None:
        random.seed(seed)

    start = variant_start_index()
    for offset in range(count):
        variant_index = start + offset
        print(f"Generating {object_type} #{variant_index:02d}...")

        clear_scene()
        setup_scene()

        rng = random.Random(random.randint(0, 999999))

        try:
            filepath = LevelObjectBuilder.export(
                object_type=object_type,
                rng=rng,
                variant_index=variant_index,
                export_dir=export_dir,
            )
            print(f"✅ Exported: {filepath}")
        except Exception as error:
            print(f"❌ Error generating {object_type} #{variant_index}: {error}")
            import traceback
            traceback.print_exc()


def parse_args():
    """Parse arguments passed after the '--' separator."""
    separator = "--"
    if separator not in sys.argv:
        return [], {}

    raw = sys.argv[sys.argv.index(separator) + 1:]
    args = []
    kwargs = {}

    index = 0
    while index < len(raw):
        token = raw[index]
        if token.startswith("--"):
            key = token[2:].replace("-", "_")
            if index + 1 < len(raw) and not raw[index + 1].startswith("--"):
                kwargs[key] = raw[index + 1]
                index += 2
            else:
                kwargs[key] = True
                index += 1
        else:
            args.append(token)
            index += 1

    return args, kwargs


def main():
    args, kwargs = parse_args()

    if not args:
        print("Usage: blender --background --python src/level_generator.py -- <object_type> [count] [seed]")
        print("Available types:", LevelObjectBuilder.get_available_types())
        return

    object_type = args[0]
    count = int(args[1]) if len(args) > 1 else 1
    seed = int(args[2]) if len(args) > 2 else None

    if object_type not in LevelObjectBuilder.get_available_types():
        print(f"❌ Unknown level object type: {object_type!r}")
        print("Available types:", LevelObjectBuilder.get_available_types())
        return

    print(f"🏗️  Generating {count} × {object_type}...")
    generate_level_object(object_type, count, seed)
    print("✅ Generation complete!")


if __name__ == "__main__":
    main()
