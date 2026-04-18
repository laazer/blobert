"""Test that gradient materials export metallic=0.0 to GLB correctly.

This test is best run via Blender subprocess. If run in regular pytest,
it will skip because bpy.ops requires an active Blender context.
"""

from __future__ import annotations

import json
import struct
import tempfile
from pathlib import Path

import pytest

from src.materials import material_system as ms


def _parse_glb(glb_bytes: bytes) -> tuple[dict, bytes]:
    """Parse GLB and return (JSON header, binary data)."""
    json_length, json_type = struct.unpack("<II", glb_bytes[12:20])
    glb_json = json.loads(glb_bytes[20 : 20 + json_length])
    bin_start = 20 + json_length + 8
    bin_data = glb_bytes[bin_start : bin_start + struct.unpack("<I", glb_bytes[bin_start - 4 : bin_start])[0]]
    return glb_json, bin_data


@pytest.mark.skip(reason="Requires Blender subprocess context (use test_gradient_blender_glb_export_smoke.py)")
def test_gradient_material_metallic_exported_to_glb() -> None:
    """Gradient material must export metallic=0.0 to GLB (not undefined).

    This test documents the expected behavior: exported GLB must include
    pbrMetallicRoughness.metallicFactor = 0.0 in material definition.

    To run this test: execute Blender with the gradient fixture script
    (see test_gradient_blender_glb_export_smoke.py for subprocess approach).
    """
    bpy = pytest.importorskip("bpy")

    bpy.data.batch_remove(bpy.data.objects)
    bpy.data.batch_remove(bpy.data.materials)

    with tempfile.TemporaryDirectory() as tmp:
        out_glb = Path(tmp) / "grad_metallic_test.glb"

        bpy.ops.mesh.primitive_cube_add(size=2)
        obj = bpy.context.active_object

        mat = ms._material_for_gradient_zone(
            base_palette_name="blood_red",
            finish="default",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="ffffff",
            instance_suffix="test_grad",
        )
        obj.data.materials.append(mat)

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        bpy.ops.export_scene.gltf(
            filepath=str(out_glb),
            use_selection=True,
            export_format="GLB",
            export_materials="EXPORT",
        )

        glb_data = out_glb.read_bytes()
        glb_json, _ = _parse_glb(glb_data)

        materials = glb_json.get("materials", [])
        assert len(materials) > 0, "GLB must contain at least one material"

        mat_def = materials[0]
        pbr = mat_def.get("pbrMetallicRoughness", {})

        metallic_val = pbr.get("metallicFactor")
        assert metallic_val is not None, (
            f"Material must export metallicFactor (got {metallic_val}). "
            "Blender glTF exporter may not be including PBR values."
        )
        assert metallic_val == 0.0, f"metallicFactor must be 0.0 (got {metallic_val})"

        roughness_val = pbr.get("roughnessFactor")
        assert roughness_val is not None, f"Material must export roughnessFactor (got {roughness_val})"
        assert 0.7 <= roughness_val <= 0.8, f"roughnessFactor should be ~0.75 (got {roughness_val})"
