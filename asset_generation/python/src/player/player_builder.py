"""
Factory for building and exporting the player slime
"""

import json
import os

from ..core.blender_utils import bind_mesh_to_armature, ensure_mesh_integrity
from ..utils.config import (
    PlayerAnimationConfig,
    PlayerAnimationTypes,
    PlayerBoneNames,
)
from ..utils.export_bake import bake_procedural_stripes_for_export
from .player_animations import PlayerSlimeAnimations
from .player_armature import create_player_slime_armature
from .player_materials import SLIME_COLORS
from .player_slime_body import PlayerSlimeBody


class PlayerSlimeBuilder:
    """Builds, animates, and exports the player slime in one call."""

    @classmethod
    def build(
        cls,
        color: str = "blue",
        rng=None,
        prefab_mesh=None,
        finish: str = "glossy",
        custom_color_hex: str = "",
        build_options: dict | None = None,
    ):
        """Construct the complete player slime and return (armature, mesh).

        Steps:
          1. Build mesh geometry (body, face, arms) — or use prefab_mesh if given
          2. Create armature
          3. Bind mesh to armature
          4. Generate all 8 player animations

        Args:
            color: Slime color key from SLIME_COLORS.
            rng: Optional Random instance for procedural variation.
            prefab_mesh: Optional pre-imported Blender mesh object. When
                provided, procedural body geometry is skipped and this mesh
                is bound directly to the player armature instead.
        """
        if color not in SLIME_COLORS:
            raise ValueError(
                f"Unknown slime color: {color!r}. "
                f"Available: {list(SLIME_COLORS)}"
            )

        if prefab_mesh is not None:
            print("📦 Using prefab mesh — skipping procedural player geometry")
            mesh = prefab_mesh
        else:
            body_builder = PlayerSlimeBody(
                color=color,
                rng=rng,
                finish=finish,
                custom_color_hex=custom_color_hex,
                build_options=build_options,
            )
            mesh = body_builder.build()

        armature = create_player_slime_armature("player_slime")

        mesh = bind_mesh_to_armature(mesh, armature)
        mesh = ensure_mesh_integrity(mesh, armature)

        animator = PlayerSlimeAnimations(armature, rng)
        animator.create_all_animations()

        return armature, mesh

    @classmethod
    def get_available_colors(cls):
        return list(SLIME_COLORS)


def export_player_slime(armature, mesh, filename: str, export_dir: str):
    """Export the player slime to GLB and write a companion metadata JSON."""
    import bpy

    os.makedirs(export_dir, exist_ok=True)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    if armature:
        armature.select_set(True)

    if mesh:
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh

    # Bake procedural stripe materials to image textures for glTF/web viewer parity.
    bake_procedural_stripes_for_export(mesh, export_dir)

    filepath = os.path.join(export_dir, f"{filename}.glb")

    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=True,
        export_format='GLB',
        export_materials='EXPORT',
        export_apply=True,
        export_animations=True,
        export_frame_range=True,
        export_frame_step=1,
    )

    print(f"Exported: {filepath}")
    _export_player_metadata(filename, export_dir)

    return filepath


def _export_player_metadata(filename: str, export_dir: str) -> None:
    """Write a companion JSON describing animations and bone names."""
    animations = []
    for anim_name in PlayerAnimationTypes.get_all():
        length = PlayerAnimationConfig.get_length(anim_name)
        animations.append({
            "name": anim_name,
            "frames": length,
            "duration_seconds": PlayerAnimationConfig.get_duration_seconds(anim_name),
            "loops": anim_name in PlayerAnimationTypes.get_looping(),
        })

    metadata = {
        "filename": filename,
        "character": "player_slime",
        "fps": PlayerAnimationConfig.FPS,
        "bones": PlayerBoneNames.get_all(),
        "animations": animations,
    }

    json_filepath = os.path.join(export_dir, f"{filename}.player.json")
    with open(json_filepath, 'w') as json_file:
        json.dump(metadata, json_file, indent=2)

    print(f"Player metadata: {json_filepath}")
