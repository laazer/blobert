"""
Base enemy class: procedural mesh via BaseAnimatedModel + armature + export helpers.
"""

from __future__ import annotations

import json
import os
from abc import abstractmethod
from typing import List

from ..utils.export_bake import bake_procedural_stripes_for_export
from .base_animated_model import BaseAnimatedModel


class BaseEnemy(BaseAnimatedModel):
    """Enemy mesh + rig + animation orchestration."""

    @abstractmethod
    def get_body_type(self):
        """Return body type enum for the animation system."""

    @abstractmethod
    def create_armature(self):
        """Create Blender armature for this mesh, or None."""

    def get_attack_profile(self) -> List:
        from ..combat.enemy_attack_profiles import get_attack_profile

        return get_attack_profile(self.name)

    def build(self, prefab_mesh=None):
        """Build mesh and rig; returns (armature, mesh) or bare mesh."""
        if prefab_mesh is not None:
            print("📦 Using prefab mesh — skipping procedural geometry")
            self._estimate_dimensions_from_prefab(prefab_mesh)
            mesh = prefab_mesh
        else:
            self.parts = []
            self.build_mesh_parts()
            self.apply_themed_materials()
            mesh = self.finalize()

        armature = self.create_armature()
        if armature and mesh:
            from ..animations.animation_system import create_all_animations
            from ..core.blender_utils import (
                bind_mesh_to_armature,
                ensure_mesh_integrity,
            )

            mesh = bind_mesh_to_armature(mesh, armature)
            mesh = ensure_mesh_integrity(mesh, armature)
            create_all_animations(armature, self.get_body_type(), self.rng, animation_set="all")

            return armature, mesh

        return mesh


def export_enemy(armature, mesh, filename, export_dir, attack_profile=None):
    """Export enemy to GLB format with an optional companion attack-profile JSON"""
    import bpy

    os.makedirs(export_dir, exist_ok=True)

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")

    if armature:
        armature.select_set(True)
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            print(f"Active animation for export: {action.name}")
            print(f"Available actions: {[a.name for a in bpy.data.actions if a.users > 0]}")

    if mesh:
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh

    # Bake procedural stripe materials to image textures for glTF/web viewer parity.
    bake_procedural_stripes_for_export(mesh, export_dir)

    filepath = os.path.join(export_dir, f"{filename}.glb")

    debug_filepath = filepath.replace(".glb", ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=debug_filepath)
    print(f"Debug export: {debug_filepath}")

    try:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            use_selection=True,
            export_format="GLB",
            export_materials="EXPORT",
            export_apply=True,
            export_animations=True,
            export_frame_range=True,
            export_frame_step=1,
            export_nla_strips=True,
        )
    except TypeError:
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            use_selection=True,
            export_format="GLB",
            export_materials="EXPORT",
            export_apply=True,
            export_animations=True,
            export_frame_range=True,
            export_frame_step=1,
        )

    print(f"Exported: {filepath}")

    if attack_profile:
        _export_attack_profile_json(filename, export_dir, attack_profile)

    return filepath


def _export_attack_profile_json(filename: str, export_dir: str, attack_profile: List) -> None:
    profile_data = {
        "filename": filename,
        "attacks": [attack.to_dict() for attack in attack_profile],
    }
    json_filepath = os.path.join(export_dir, f"{filename}.attacks.json")
    with open(json_filepath, "w") as json_file:
        json.dump(profile_data, json_file, indent=2)
    print(f"Attack profile: {json_filepath}")
