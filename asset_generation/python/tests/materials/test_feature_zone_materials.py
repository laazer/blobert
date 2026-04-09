"""Tests for zone + per-part feature materials (no Blender scene required)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.enemies import animated_imp as imp_mod
from src.materials import material_system as ms


def test_palette_base_name_strips_data_name_and_feat_suffix() -> None:
    m = MagicMock()
    m.name = "Organic_Brown__feat_limbs.002"
    assert ms._palette_base_name_from_material(m) == "Organic_Brown"


def test_apply_feature_slot_overrides_updates_joints_slot() -> None:
    base = MagicMock()
    base.name = "Bone_White"
    slots = {"body": base, "head": base, "limbs": base, "joints": base, "extra": base}
    new_mat = MagicMock(name="new_joint_mat")
    with patch.object(ms, "create_material", return_value=new_mat) as cm:
        out = ms.apply_feature_slot_overrides(slots, {"joints": {"hex": "00aa11", "finish": "matte"}})
    assert out["joints"] is new_mat
    assert cm.called


def test_material_for_zone_part_creates_variant_when_part_hex_set() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb, "joints": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "",
            "parts": {"arm_0": {"finish": "default", "hex": "cc00dd"}},
        }
    }
    new_mat = MagicMock()
    with patch.object(ms, "create_material", return_value=new_mat) as cm:
        got = ms.material_for_zone_part("limbs", "arm_0", slots, features)
    assert got is new_mat
    assert cm.called


def test_material_for_zone_part_returns_base_when_no_override() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert ms.material_for_zone_part("limbs", "arm_0", slots, {"limbs": {}}) is limb


def test_material_for_zone_part_returns_none_when_zone_slot_missing() -> None:
    assert ms.material_for_zone_part("limbs", "arm_0", {}, {"limbs": {}}) is None


def test_material_for_zone_part_returns_base_when_zone_feature_not_dict() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert ms.material_for_zone_part("limbs", "arm_0", slots, {"limbs": "nope"}) is limb


def test_material_for_zone_part_inherits_zone_hex_when_part_sets_finish_only() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    features = {
        "limbs": {
            "finish": "default",
            "hex": "aabbcc",
            "parts": {"arm_0": {"finish": "glossy", "hex": ""}},
        }
    }
    new_mat = MagicMock()
    with patch.object(ms, "create_material", return_value=new_mat):
        got = ms.material_for_zone_part("limbs", "arm_0", slots, features)
    assert got is new_mat


def test_material_for_zone_part_ignores_non_dict_parts_map() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert (
        ms.material_for_zone_part(
            "limbs",
            "arm_0",
            slots,
            {"limbs": {"parts": "bad"}},
        )
        is limb
    )


def test_material_for_zone_part_ignores_non_dict_part_payload() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"limbs": limb}
    assert (
        ms.material_for_zone_part(
            "limbs",
            "arm_0",
            slots,
            {"limbs": {"parts": {"arm_0": "nope"}}},
        )
        is limb
    )


def test_material_for_zone_geometry_extra_returns_base_when_no_override() -> None:
    limb = MagicMock()
    limb.name = "Bone_White"
    slots = {"body": limb}
    assert ms.material_for_zone_geometry_extra("body", slots, {"body": {}}, "default", "") is limb


def test_material_for_zone_geometry_extra_creates_when_extra_hex() -> None:
    b = MagicMock()
    b.name = "Organic_Brown"
    slots = {"body": b}
    new_m = MagicMock()
    with patch.object(ms, "create_material", return_value=new_m) as cm:
        got = ms.material_for_zone_geometry_extra("body", slots, None, "default", "ff00aa")
    assert got is new_m
    assert cm.called


def test_material_for_zone_geometry_extra_returns_none_when_slot_missing() -> None:
    assert ms.material_for_zone_geometry_extra("body", {}, {}, "matte", "aabbcc") is None


def test_get_enemy_materials_single_theme_color_fills_all_slots() -> None:
    m0 = MagicMock(name="M0")
    palette = {"M0": m0}
    rng = MagicMock()
    with (
        patch.object(ms.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms.MaterialThemes, "get_theme", return_value=("M0",)),
    ):
        out = ms.get_enemy_materials("solo_theme", palette, rng)
    assert out["joints"] is m0
    assert out["limbs"] is m0


def test_get_enemy_materials_joint_slot_matches_limbs_for_three_theme_colors() -> None:
    palette = {f"M{i}": MagicMock(name=f"M{i}") for i in range(3)}
    rng = MagicMock()
    rng.choice = MagicMock(side_effect=lambda seq: seq[-1])
    with (
        patch.object(ms.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms.MaterialThemes, "get_theme", return_value=("M0", "M1", "M2")),
    ):
        out = ms.get_enemy_materials("test_enemy", palette, rng)
    assert out["limbs"] is palette["M2"]
    assert out["joints"] is palette["M2"]


@pytest.mark.parametrize(
    ("n_seg", "joint_vis", "end_shape", "expected_len"),
    [
        (1, False, "none", 1),
        (2, True, "sphere", 4),
        (1, True, "sphere", 2),
    ],
)
def test_humanoid_limb_part_kinds_length(
    n_seg: int,
    joint_vis: bool,
    end_shape: str,
    expected_len: int,
) -> None:
    seq = imp_mod._humanoid_limb_part_kinds(n_seg, joint_vis, end_shape)
    assert len(seq) == expected_len
