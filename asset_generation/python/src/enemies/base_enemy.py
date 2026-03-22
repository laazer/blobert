"""
Base enemy class and common functionality
"""

import json
import os
from abc import ABC, abstractmethod
from typing import List

from ..core.blender_utils import apply_smooth_shading, join_objects
from ..materials.material_system import get_enemy_materials, apply_material_to_object


class BaseEnemy(ABC):
    """Base class for all enemy types"""
    
    def __init__(self, name, materials, rng):
        self.name = name
        self.materials = materials
        self.rng = rng
        self.parts = []
        
    @abstractmethod
    def create_body(self):
        """Create the main body structure"""
        pass
    
    @abstractmethod
    def create_head(self):
        """Create the head structure"""
        pass
    
    @abstractmethod
    def create_limbs(self):
        """Create limbs (legs, arms, etc.)"""
        pass
    
    def apply_materials(self):
        """Apply themed materials to enemy parts"""
        enemy_mats = get_enemy_materials(self.name, self.materials, self.rng)
        
        # Default material application - can be overridden in subclasses
        if len(self.parts) >= 1:
            apply_material_to_object(self.parts[0], enemy_mats['body'])
        if len(self.parts) >= 2:
            apply_material_to_object(self.parts[1], enemy_mats['head'])
        
        # Apply limb materials to remaining parts
        for part in self.parts[2:]:
            apply_material_to_object(part, enemy_mats['limbs'])
    
    def finalize(self):
        """Join parts and apply final processing"""
        if not self.parts:
            return None
            
        # Join all parts into single mesh
        mesh = join_objects(self.parts)
        apply_smooth_shading(mesh)
        return mesh
    
    def create_armature(self):
        """Create armature for animation - to be overridden in subclasses"""
        return None
    
    def get_body_type(self):
        """Get body type for animation system - to be overridden"""
        from ..utils.constants import EnemyBodyTypes
        return EnemyBodyTypes.QUADRUPED  # Default

    def get_attack_profile(self) -> List:
        """Return the list of AttackData for this enemy type."""
        from ..combat.enemy_attack_profiles import get_attack_profile
        return get_attack_profile(self.name)
    
    def _estimate_dimensions_from_prefab(self, prefab_mesh) -> None:
        """Populate dimension attributes from a prefab mesh bounding box.

        Enemy subclasses store procedural dimensions (body_scale, body_height,
        etc.) in create_body(). When skipping procedural geometry we derive
        equivalent values from the imported mesh so armature builders receive
        sensible proportions.
        """
        from ..core.blender_utils import detect_body_scale_from_mesh
        scale = detect_body_scale_from_mesh(prefab_mesh)
        self.body_scale = scale
        self.body_height = scale * 2.0
        self.height = scale * 2.0
        self.length = scale * 2.0
        self.width = scale
        self.head_scale = scale * 0.6
        self.body_width = scale * 0.4

    def build(self, prefab_mesh=None):
        """Build the complete enemy.

        Args:
            prefab_mesh: Optional pre-imported Blender mesh object. When
                provided, procedural geometry generation is skipped and this
                mesh is bound directly to the generated armature.
        """
        if prefab_mesh is not None:
            print("📦 Using prefab mesh — skipping procedural geometry")
            self._estimate_dimensions_from_prefab(prefab_mesh)
            mesh = prefab_mesh
        else:
            self.create_body()
            self.create_head()
            self.create_limbs()
            self.apply_materials()
            mesh = self.finalize()

        # Create armature and animations for animated enemies
        armature = self.create_armature()
        if armature and mesh:
            from ..core.blender_utils import bind_mesh_to_armature, ensure_mesh_integrity
            from ..animations.animation_system import create_all_animations

            mesh = bind_mesh_to_armature(mesh, armature)
            mesh = ensure_mesh_integrity(mesh, armature)
            create_all_animations(armature, self.get_body_type(), self.rng, animation_set='all')

            return armature, mesh

        return mesh


def export_enemy(armature, mesh, filename, export_dir, attack_profile=None):
    """Export enemy to GLB format with an optional companion attack-profile JSON"""
    import bpy
    
    os.makedirs(export_dir, exist_ok=True)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    
    if armature:
        armature.select_set(True)
        if armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action
            print(f"Active animation for export: {action.name}")
            print(f"Available actions: {[a.name for a in bpy.data.actions if a.users > 0]}")
    
    if mesh:
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh
    
    filepath = os.path.join(export_dir, f"{filename}.glb")
    
    # Also export as .blend for debugging
    debug_filepath = filepath.replace('.glb', '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=debug_filepath)
    print(f"Debug export: {debug_filepath}")
    
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=True,
        export_format='GLB',
        export_materials='EXPORT',
        export_apply=True,
        export_animations=True,
        export_frame_range=True,
        export_frame_step=1
    )
    
    print(f"Exported: {filepath}")

    if attack_profile:
        _export_attack_profile_json(filename, export_dir, attack_profile)

    return filepath


def _export_attack_profile_json(filename: str, export_dir: str, attack_profile: List) -> None:
    """Write a companion JSON file containing combat stats for the exported enemy."""
    profile_data = {
        "filename": filename,
        "attacks": [attack.to_dict() for attack in attack_profile],
    }
    json_filepath = os.path.join(export_dir, f"{filename}.attacks.json")
    with open(json_filepath, 'w') as json_file:
        json.dump(profile_data, json_file, indent=2)
    print(f"Attack profile: {json_filepath}")