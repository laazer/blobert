"""Coverage for per-part material_fill branches in feature_zones (diff-cover)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.materials import feature_zones as fz
from src.materials import material_system as ms
from src.materials.material_types import MaterialFillOptions


def test_material_fill_options_from_mapping_rejects_non_dict() -> None:
    assert MaterialFillOptions.from_mapping("not-a-dict") is None


def test_material_for_zone_part_material_fill_gradient() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "",
            "parts": {
                "leg_0": {
                    "finish": "default",
                    "hex": "",
                    "material_fill": {
                        "mode": "gradient",
                        "grad_a": "ff0000",
                        "grad_b": "0000ff",
                        "grad_direction": "horizontal",
                    },
                }
            },
        }
    }
    new_mat = MagicMock()
    with patch.object(fz, "_material_for_gradient_zone", return_value=new_mat):
        got = fz.material_for_zone_part("limbs", "leg_0", slots, features)
    assert got is new_mat


def test_material_for_zone_part_material_fill_image() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "",
            "parts": {
                "leg_0": {
                    "finish": "default",
                    "hex": "",
                    "material_fill": {
                        "mode": "image",
                        "image_id": "hash_texture",
                        "image_preview": "/api/assets/textures/file/x.png",
                    },
                }
            },
        }
    }
    new_mat = MagicMock()
    with patch.object(fz, "material_for_color_image_zone", return_value=new_mat):
        got = fz.material_for_zone_part("limbs", "leg_0", slots, features)
    assert got is new_mat


def test_material_for_zone_part_material_fill_hex_via_mf() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "",
            "parts": {
                "leg_0": {
                    "finish": "default",
                    "hex": "",
                    "material_fill": {"mode": "single", "hex": "aabbcc"},
                }
            },
        }
    }
    new_mat = MagicMock()
    with patch.object(ms, "create_material", return_value=new_mat):
        got = fz.material_for_zone_part("limbs", "leg_0", slots, features)
    assert got is new_mat


def test_material_for_gradient_zone_uses_material_system_create_material() -> None:
    mat = MagicMock()
    with patch.object(ms, "create_material", return_value=mat) as cm:
        got = fz._material_for_gradient_zone(
            base_palette_name="Bone_White",
            finish="glossy",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="112233",
            instance_suffix="test",
        )
    assert got is mat
    assert cm.called
