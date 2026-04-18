"""Run inside Blender: export one cube with a zone gradient material to a GLB path (argv after --)."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

_argv = sys.argv
try:
    _out_idx = _argv.index("--") + 1
except ValueError:
    print("usage: blender -b --python ... -- /path/to/out.glb", file=sys.stderr)
    sys.exit(2)
out_path = Path(_argv[_out_idx]).resolve()

_here = Path(__file__).resolve()
PYTHON_ROOT = _here.parents[2]
sys.path.insert(0, str(PYTHON_ROOT))

from src.core.blender_utils import clear_scene
from src.materials import material_system as ms

clear_scene()
bpy.ops.mesh.primitive_cube_add(size=2)
obj = bpy.context.active_object
mat = ms._material_for_gradient_zone(
    base_palette_name="blood_red",
    finish="default",
    grad_a_hex="ff0000",
    grad_b_hex="0000ff",
    direction="horizontal",
    zone_hex_fallback="ffffff",
    instance_suffix="smoke_grad",
)
obj.data.materials.append(mat)

bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

bpy.ops.export_scene.gltf(
    filepath=str(out_path),
    use_selection=True,
    export_format="GLB",
    export_materials="EXPORT",
)
print(out_path)
