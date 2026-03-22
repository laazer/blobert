"""
Base class for all level objects and the export helper
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List

from ..core.blender_utils import apply_smooth_shading, join_objects
from .level_object_data import TrapData


class BaseLevelObject(ABC):
    """Base class for all level objects (platforms, walls, traps, checkpoints)."""

    def __init__(self, name: str, rng):
        self.name = name
        self.rng = rng
        self.parts = []

    @abstractmethod
    def create_structure(self):
        """Build the mesh geometry for this object."""
        pass

    def apply_materials(self):
        """Apply materials to all parts. Override in subclasses for custom materials."""
        pass

    def get_trap_data(self) -> List[TrapData]:
        """Return combat data for this object if it is a trap. Default: no traps."""
        return []

    def get_object_metadata(self) -> Dict:
        """Return extra metadata (e.g. movement speed, crumble delay) for export."""
        return {}

    def finalize(self):
        """Join all parts into a single mesh and apply smooth shading."""
        if not self.parts:
            return None
        mesh = join_objects(self.parts)
        apply_smooth_shading(mesh)
        return mesh

    def build(self):
        """Build the complete level object and return the final mesh."""
        self.create_structure()
        self.apply_materials()
        return self.finalize()


def export_level_object(mesh, filename: str, export_dir: str, level_object: BaseLevelObject = None):
    """Export a level object mesh to GLB and write a companion .object.json if needed."""
    import bpy

    os.makedirs(export_dir, exist_ok=True)

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    if mesh:
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh

    filepath = os.path.join(export_dir, f"{filename}.glb")

    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=True,
        export_format='GLB',
        export_materials='EXPORT',
        export_apply=True,
        export_animations=False,
    )

    print(f"Exported: {filepath}")

    if level_object is not None:
        trap_data = level_object.get_trap_data()
        metadata = level_object.get_object_metadata()
        if trap_data or metadata:
            _export_object_json(filename, export_dir, level_object.name, trap_data, metadata)

    return filepath


def _export_object_json(
    filename: str,
    export_dir: str,
    object_type: str,
    trap_data: List[TrapData],
    metadata: Dict,
) -> None:
    """Write a companion JSON file with trap data and metadata for the exported object."""
    object_data = {
        "filename": filename,
        "type": object_type,
    }

    if metadata:
        object_data["metadata"] = metadata

    if trap_data:
        object_data["traps"] = [trap.to_dict() for trap in trap_data]

    json_filepath = os.path.join(export_dir, f"{filename}.object.json")
    with open(json_filepath, 'w') as json_file:
        json.dump(object_data, json_file, indent=2)

    print(f"Object data: {json_filepath}")
