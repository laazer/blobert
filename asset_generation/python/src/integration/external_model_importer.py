"""
External Model Integration System
Import external models and animations into the enemy generation pipeline
"""

from pathlib import Path
from typing import Dict, List

import bpy

from ..animations.animation_system import create_all_animations
from ..core.blender_utils import (
    apply_smooth_shading,
    clear_scene,
    ensure_mesh_integrity,
)
from ..core.rig_models import (
    imported_blob_rig,
    imported_humanoid_rig,
    imported_quadruped_rig,
)
from ..materials.material_system import apply_material_to_object, get_enemy_materials
from ..utils.constants import ExportConfig


class ExternalModelImporter:
    """Import and integrate external models into the enemy generation pipeline"""
    
    SUPPORTED_FORMATS = {'.fbx', '.obj', '.dae', '.gltf', '.glb', '.blend'}
    REQUIRED_ANIMATIONS = ['idle', 'move', 'attack', 'damage', 'death']
    
    def __init__(self):
        self.imported_objects = []
        self.armature = None
        self.mesh = None
        self.existing_animations = []
        
    def import_model(self, filepath: str, enemy_name: str = None) -> Dict:
        """
        Import external model and analyze its contents
        
        Args:
            filepath: Path to model file
            enemy_name: Optional enemy name for materials
            
        Returns:
            Dict with import results and analysis
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Model file not found: {filepath}")
            
        if filepath.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {filepath.suffix}. Supported: {self.SUPPORTED_FORMATS}")
        
        print(f"🎮 Importing model: {filepath.name}")
        
        # Clear scene before import
        clear_scene()
        
        # Import based on file type
        try:
            if filepath.suffix.lower() == '.fbx':
                bpy.ops.import_scene.fbx(filepath=str(filepath))
            elif filepath.suffix.lower() == '.obj':
                bpy.ops.import_scene.obj(filepath=str(filepath))
            elif filepath.suffix.lower() == '.dae':
                bpy.ops.wm.collada_import(filepath=str(filepath))
            elif filepath.suffix.lower() in ['.gltf', '.glb']:
                bpy.ops.import_scene.gltf(filepath=str(filepath))
            elif filepath.suffix.lower() == '.blend':
                # Import from blend file
                with bpy.data.libraries.load(str(filepath)) as (data_from, data_to):
                    data_to.objects = data_from.objects
                    data_to.armatures = data_from.armatures
                    data_to.actions = data_from.actions
                    
                # Link objects to scene
                for obj in data_to.objects:
                    if obj:
                        bpy.context.collection.objects.link(obj)
            
            print("✅ Model imported successfully")
            
        except Exception as e:
            raise RuntimeError(f"Failed to import model: {e}")
        
        # Analyze imported content
        return self._analyze_imported_model(enemy_name or filepath.stem)
    
    def _analyze_imported_model(self, enemy_name: str) -> Dict:
        """Analyze the imported model structure"""
        print("🔍 Analyzing imported model...")
        
        # Find armature and mesh objects
        armatures = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
        
        self.armature = armatures[0] if armatures else None
        self.mesh = meshes[0] if len(meshes) == 1 else None
        
        # If multiple meshes, try to join them
        if len(meshes) > 1:
            print(f"🔧 Found {len(meshes)} mesh objects, joining...")
            self.mesh = self._join_meshes(meshes)
        
        # Analyze existing animations
        if self.armature and self.armature.animation_data:
            self.existing_animations = [action.name for action in bpy.data.actions if action.users > 0]
        
        analysis = {
            'has_armature': self.armature is not None,
            'has_mesh': self.mesh is not None,
            'armature_name': self.armature.name if self.armature else None,
            'mesh_name': self.mesh.name if self.mesh else None,
            'existing_animations': self.existing_animations,
            'missing_animations': self._get_missing_animations(),
            'bone_count': len(self.armature.data.bones) if self.armature else 0,
            'vertex_count': len(self.mesh.data.vertices) if self.mesh else 0,
            'enemy_name': enemy_name
        }
        
        print("📊 Analysis complete:")
        print(f"   Armature: {'✅' if analysis['has_armature'] else '❌'} ({analysis['bone_count']} bones)")
        print(f"   Mesh: {'✅' if analysis['has_mesh'] else '❌'} ({analysis['vertex_count']} vertices)")
        print(f"   Existing animations: {len(analysis['existing_animations'])}")
        print(f"   Missing animations: {len(analysis['missing_animations'])}")
        
        return analysis
    
    def _join_meshes(self, meshes: List) -> bpy.types.Object:
        """Join multiple meshes into one"""
        if not meshes:
            return None
            
        # Select all meshes
        bpy.ops.object.select_all(action='DESELECT')
        for mesh in meshes:
            mesh.select_set(True)
        
        # Set active object
        bpy.context.view_layer.objects.active = meshes[0]
        
        # Join them
        bpy.ops.object.join()
        return bpy.context.active_object
    
    def _get_missing_animations(self) -> List[str]:
        """Get list of missing required animations"""
        if not self.existing_animations:
            return self.REQUIRED_ANIMATIONS.copy()
            
        return [anim for anim in self.REQUIRED_ANIMATIONS if anim not in self.existing_animations]
    
    def ensure_compatibility(self, target_body_type: str = 'quadruped') -> bool:
        """
        Ensure the model is compatible with our animation system
        
        Args:
            target_body_type: Target body type for animations
            
        Returns:
            True if compatible or made compatible
        """
        print("🔧 Ensuring pipeline compatibility...")
        
        if not self.mesh:
            raise RuntimeError("No mesh found to make compatible")
        
        # Ensure armature exists
        if not self.armature:
            print("⚠️ No armature found, creating basic armature...")
            self.armature = self._create_basic_armature(target_body_type)
        
        # Ensure proper binding
        if self.armature and self.mesh:
            print("🔗 Ensuring proper mesh-armature binding...")
            from ..core.blender_utils import bind_mesh_to_armature
            self.mesh = bind_mesh_to_armature(self.mesh, self.armature)
            self.mesh = ensure_mesh_integrity(self.mesh, self.armature)
        
        # Apply our enhanced materials
        self._apply_pipeline_materials()
        
        # Ensure smooth shading
        apply_smooth_shading(self.mesh)
        
        print("✅ Model is now pipeline compatible")
        return True
    
    def _create_basic_armature(self, body_type: str) -> bpy.types.Object:
        """Create a basic armature for models without one (import path — not an enemy class)."""
        from ..animations.keyframe_system import create_simple_armature

        print(f"🦴 Creating {body_type} armature...")
        if body_type == "blob":
            rig = imported_blob_rig()
        elif body_type == "humanoid":
            rig = imported_humanoid_rig()
        else:
            rig = imported_quadruped_rig()
        return create_simple_armature("imported_model", rig)
    
    def _apply_pipeline_materials(self):
        """Apply our enhanced material system to imported model"""
        print("🎨 Applying pipeline materials...")
        
        if not self.mesh:
            return
        
        # Get materials for generic imported model
        from ..materials.material_system import setup_materials
        materials = setup_materials()
        enemy_materials = get_enemy_materials("imported_model", materials, None)
        
        # Apply primary material to mesh
        apply_material_to_object(self.mesh, enemy_materials['body'])
    
    def generate_missing_animations(self, body_type: str = 'quadruped', animation_set: str = 'all'):
        """
        Generate missing animations using our animation system
        
        Args:
            body_type: Body type for animation generation
            animation_set: Animation set to generate ('core', 'extended', 'all')
        """
        if not self.armature:
            raise RuntimeError("No armature available for animation generation")
        
        missing = self._get_missing_animations()
        
        if not missing and animation_set == 'core':
            print("✅ All required core animations already exist")
            return
        
        print(f"🎬 Generating {animation_set} animations for {body_type} model...")
        
        # Import body type enum
        from ..utils.constants import EnemyBodyTypes
        
        # Map string to enum
        body_type_map = {
            'blob': EnemyBodyTypes.BLOB,
            'quadruped': EnemyBodyTypes.QUADRUPED, 
            'humanoid': EnemyBodyTypes.HUMANOID
        }
        
        body_type_enum = body_type_map.get(body_type, EnemyBodyTypes.QUADRUPED)
        
        # Generate animations using our system
        create_all_animations(self.armature, body_type_enum, None, animation_set)
        
        # Update existing animations list
        self.existing_animations = [action.name for action in bpy.data.actions if action.users > 0]
        
        print(f"✅ Generated animations: {', '.join(self.existing_animations)}")
    
    def export_integrated_model(self, output_path: str, filename: str = None) -> str:
        """
        Export the integrated model in our pipeline format
        
        Args:
            output_path: Directory to export to
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            filename = f"{self.mesh.name}_integrated"
        
        print(f"📦 Exporting integrated model as {filename}...")
        
        # Use our standard export function
        from ..enemies.base_enemy import export_enemy
        filepath = export_enemy(self.armature, self.mesh, filename, output_path)
        
        print(f"✅ Exported to: {filepath}")
        return filepath
    
    def get_integration_report(self) -> str:
        """Generate a comprehensive integration report"""
        if not self.mesh and not self.armature:
            return "❌ No model imported yet"
        
        report = f"""
🎮 External Model Integration Report

📊 Model Info:
   • Mesh: {self.mesh.name if self.mesh else 'None'}
   • Armature: {self.armature.name if self.armature else 'None'} 
   • Vertices: {len(self.mesh.data.vertices) if self.mesh else 0}
   • Bones: {len(self.armature.data.bones) if self.armature else 0}

🎬 Animation Status:
   • Existing: {len(self.existing_animations)} ({', '.join(self.existing_animations)})
   • Missing Core: {len(self._get_missing_animations())} ({', '.join(self._get_missing_animations())})
   • Pipeline Compatible: {'✅' if self.armature and self.mesh else '❌'}

🔧 Next Steps:
   {'✅ Ready for export' if not self._get_missing_animations() else '⚠️ Run generate_missing_animations()'}
   {'✅ Materials applied' if self.mesh and len(self.mesh.data.materials) > 0 else '⚠️ Run ensure_compatibility()'}
        """
        
        return report.strip()


def import_external_model(filepath: str, body_type: str = 'quadruped',
                         animation_set: str = 'all', output_dir: str = ExportConfig.ANIMATED_DIR) -> str:
    """
    Convenience function to fully integrate an external model
    
    Args:
        filepath: Path to model file
        body_type: Target body type ('blob', 'quadruped', 'humanoid')  
        animation_set: Animations to generate ('core', 'extended', 'all')
        output_dir: Export directory
        
    Returns:
        Path to integrated model file
    """
    importer = ExternalModelImporter()
    
    try:
        # Import and analyze
        analysis = importer.import_model(filepath)
        print(importer.get_integration_report())
        
        # Ensure compatibility
        importer.ensure_compatibility(body_type)
        
        # Generate missing animations
        importer.generate_missing_animations(body_type, animation_set)
        
        # Export integrated model
        filename = f"{analysis['enemy_name']}_integrated"
        output_path = importer.export_integrated_model(output_dir, filename)
        
        print(f"\n🎊 Integration complete! Model ready at: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Integration failed: {e}")
        raise