"""Run inside Blender: generate a spider with explicit gradient colors to a GLB path (argv after --)."""

from __future__ import annotations

import random
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
from src.enemies.animated_spider import AnimatedSpider
from src.materials.material_system import setup_materials
from src.utils.animated_build_options import options_for_enemy

clear_scene()

build_options = options_for_enemy(
    "spider",
    {
        "feat_body_texture_mode": "gradient",
        "feat_body_texture_grad_color_a": "ff0000",
        "feat_body_texture_grad_color_b": "0000ff",
        "feat_body_texture_grad_direction": "horizontal",
    },
)

rng = random.Random(42)
materials = setup_materials(enemy_finish="default", enemy_hex_color="")
spider = AnimatedSpider("spider", materials=materials, rng=rng, build_options=build_options)
spider.build_mesh_parts()
spider.apply_themed_materials()
mesh = spider.finalize()

bpy.ops.object.select_all(action="DESELECT")
mesh.select_set(True)
bpy.context.view_layer.objects.active = mesh

bpy.ops.export_scene.gltf(
    filepath=str(out_path),
    use_selection=True,
    export_format="GLB",
    export_materials="EXPORT",
)
print(out_path)
