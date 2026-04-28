"""Tests for zone + per-part feature materials (no Blender scene required)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.enemies import animated_imp as imp_mod
from src.enemies.base_animated_model import BaseAnimatedModel
from src.materials import material_system as ms
from src.materials import material_system_enemy_themes as ms_enemy_themes
from src.utils.materials import MaterialNames


class _StubAnimatedModel(BaseAnimatedModel):
    def build_mesh_parts(self) -> None:
        pass


def _fake_mat_with_bsdf_for_uv_gradient() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Minimal node_tree stand-in so ``_add_uv_gradient_to_principled`` runs without bpy."""
    bc_in = MagicMock()
    bc_in.links = [MagicMock()]
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {"Base Color": bc_in}

    class _FakeNodes:
        def __init__(self) -> None:
            self.created_types: list[str] = []

        def __iter__(self):
            return iter([bsdf])

        def new(self, *, type: str):
            self.created_types.append(type)
            n = MagicMock()
            n.type = type
            if type == "ShaderNodeUVMap":
                n.outputs = {"UV": MagicMock()}
            elif type == "ShaderNodeTexImage":
                n.inputs = {"Vector": MagicMock()}
                n.outputs = {"Color": MagicMock()}
            elif type == "ShaderNodeSeparateXYZ":
                n.outputs = {"X": MagicMock(), "Y": MagicMock(), "Z": MagicMock()}
            elif type == "ShaderNodeMix":
                n.inputs = {
                    "Factor": MagicMock(),
                    "A": MagicMock(),
                    "B": MagicMock(),
                }
                n.outputs = {"Result": MagicMock()}
            elif type == "ShaderNodeMath":
                n.inputs = [MagicMock(), MagicMock()]
                n.outputs = {"Value": MagicMock()}
            elif type == "ShaderNodeCombineXYZ":
                n.inputs = {"X": MagicMock(), "Y": MagicMock(), "Z": MagicMock()}
                n.outputs = {"Vector": MagicMock()}
            elif type == "ShaderNodeVectorMath":
                n.inputs = {"Vector": MagicMock()}
                n.outputs = {"Value": MagicMock()}
            return n

    class _FakeLinks:
        def __init__(self) -> None:
            self.removed: list = []
            self.new_calls: list = []

        def remove(self, lk):
            self.removed.append(lk)

        def new(self, *args):
            self.new_calls.append(args)

    fnodes = _FakeNodes()
    flinks = _FakeLinks()
    nt = MagicMock()
    nt.nodes = fnodes
    nt.links = flinks
    mat = MagicMock()
    mat.node_tree = nt
    return mat, flinks, bsdf


def test_add_uv_gradient_to_principled_horizontal() -> None:
    mat, links, _bsdf = _fake_mat_with_bsdf_for_uv_gradient()
    ms._add_uv_gradient_to_principled(
        mat, (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0), "horizontal"
    )
    assert len(links.removed) == 1
    assert links.new_calls


def test_add_uv_gradient_to_principled_vertical() -> None:
    mat, links, _ = _fake_mat_with_bsdf_for_uv_gradient()
    ms._add_uv_gradient_to_principled(
        mat, (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0), "vertical"
    )
    assert links.new_calls


def test_add_uv_gradient_to_principled_radial() -> None:
    mat, links, _ = _fake_mat_with_bsdf_for_uv_gradient()
    ms._add_uv_gradient_to_principled(
        mat, (1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 1.0), "radial"
    )
    assert links.new_calls


def test_material_for_gradient_zone_is_diffuse_for_export_even_on_metal_palette() -> (
    None
):
    new_mat = MagicMock()
    with (
        patch.object(ms, "create_material", return_value=new_mat) as cm,
        patch.object(ms, "_add_uv_gradient_to_principled") as grad,
    ):
        got = ms._material_for_gradient_zone(
            base_palette_name="Metal_Silver",
            finish="matte",
            grad_a_hex="ff0000",
            grad_b_hex="0000ff",
            direction="horizontal",
            zone_hex_fallback="",
            instance_suffix="body_tex_grad",
        )
    assert got is new_mat
    assert cm.called
    assert cm.call_args[0][2] == 0.0
    assert grad.called
    assert grad.call_args.kwargs.get("image_label") == "body_tex_grad"


def test_themed_slot_materials_chains_zone_texture_pattern_overrides() -> None:
    rng = MagicMock()
    base_m = MagicMock()
    base_m.name = "Organic_Brown"
    palette = {"Organic_Brown": base_m}
    fake_slots = {
        "body": base_m,
        "head": base_m,
        "limbs": base_m,
        "joints": base_m,
        "extra": base_m,
    }
    grad_mat = MagicMock(name="grad_body")
    with (
        patch(
            "src.enemies.base_animated_model.get_enemy_materials",
            return_value=fake_slots,
        ),
        patch.object(ms, "create_material", return_value=grad_mat),
        patch.object(ms, "_add_uv_gradient_to_principled"),
    ):
        model = _StubAnimatedModel(
            "spider",
            palette,
            rng,
            build_options={
                "feat_body_texture_mode": "gradient",
                "feat_body_texture_grad_color_a": "ff0000",
                "feat_body_texture_grad_color_b": "0000ff",
            },
        )
        out = model._themed_slot_materials_for("spider")
    assert out["body"] is grad_mat


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
        out = ms.apply_feature_slot_overrides(
            slots, {"joints": {"hex": "00aa11", "finish": "matte"}}
        )
    assert out["joints"] is new_mat
    assert cm.called


@patch.object(ms, "_material_for_color_image_zone")
def test_apply_feature_slot_overrides_nested_color_image_delegates_to_image_helper(
    mock_color_img: MagicMock,
) -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    new_mat = MagicMock(name="from_image")
    mock_color_img.return_value = new_mat
    slots = {"body": base}
    out = ms.apply_feature_slot_overrides(
        slots,
        {
            "body": {
                "color_image": {"mode": "image", "id": "demo_textures3"},
            }
        },
    )
    assert out["body"] is new_mat
    mock_color_img.assert_called_once()
    assert mock_color_img.call_args.kwargs["asset_id"] == "demo_textures3"


def test_apply_zone_texture_gradient_replaces_slot_and_calls_gradient_setup() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base, "head": base}
    new_mat = MagicMock(name="grad_mat")
    with (
        patch.object(ms, "create_material", return_value=new_mat) as cm,
        patch.object(ms, "_add_uv_gradient_to_principled") as grad,
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {
                "feat_body_texture_mode": "gradient",
                "feat_body_texture_grad_color_a": "ff0000",
                "feat_body_texture_grad_color_b": "0000ff",
                "feat_body_texture_grad_direction": "horizontal",
            },
        )
    assert out["body"] is new_mat
    assert out["head"] is base
    assert cm.called
    assert grad.called


def test_apply_zone_texture_gradient_uses_zone_hex_when_grad_hexes_empty() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base}
    new_mat = MagicMock(name="grad_mat")
    with (
        patch.object(ms, "create_material", return_value=new_mat) as cm,
        patch.object(ms, "_add_uv_gradient_to_principled"),
    ):
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {
                "feat_body_texture_mode": "gradient",
                "features": {"body": {"finish": "default", "hex": "aabbcc"}},
            },
        )
    assert out["body"] is new_mat
    assert cm.called


def test_apply_zone_texture_gradient_applies_with_fallback_when_no_hex() -> None:
    """Gradients always apply when mode=gradient; empty hex uses fallback logic."""
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base}
    with patch.object(ms, "create_material") as cm:
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {
                "feat_body_texture_mode": "gradient",
                "features": {"body": {"finish": "default", "hex": ""}},
            },
        )
    assert out["body"] is not base
    assert cm.called


def test_rgba_from_hex_or_fallback_returns_fallback_when_parse_raises() -> None:
    with (
        patch.object(ms, "_sanitize_hex_input", return_value="abcdef"),
        patch.object(ms, "_parse_hex_color", side_effect=ValueError),
    ):
        fb = (0.1, 0.2, 0.3, 1.0)
        assert ms._rgba_from_hex_or_fallback("ignored", fb) == fb


def test_add_uv_gradient_returns_when_no_node_tree() -> None:
    mat = MagicMock()
    mat.node_tree = None
    ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")


def test_add_uv_gradient_returns_when_no_bsdf() -> None:
    class _EmptyNodes:
        def __iter__(self):
            return iter([])

    nt = MagicMock()
    nt.nodes = _EmptyNodes()
    mat = MagicMock()
    mat.node_tree = nt
    ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")


def test_add_uv_gradient_returns_when_no_base_color_socket() -> None:
    bsdf = MagicMock()
    bsdf.type = "BSDF_PRINCIPLED"
    bsdf.inputs = {}

    class _OneNode:
        def __iter__(self):
            return iter([bsdf])

    nt = MagicMock()
    nt.nodes = _OneNode()
    mat = MagicMock()
    mat.node_tree = nt
    ms._add_uv_gradient_to_principled(mat, (1, 0, 0, 1), (0, 0, 1, 1), "horizontal")


def test_apply_zone_texture_pattern_overrides_empty_build_options() -> None:
    base = MagicMock()
    slots = {"body": base}
    assert ms.apply_zone_texture_pattern_overrides(slots, {}) is slots
    assert ms.apply_zone_texture_pattern_overrides(slots, None) is slots


def test_apply_zone_texture_none_leaves_slots() -> None:
    base = MagicMock()
    base.name = "Organic_Brown"
    slots = {"body": base}
    with patch.object(ms, "create_material") as cm:
        out = ms.apply_zone_texture_pattern_overrides(
            slots,
            {"feat_body_texture_mode": "none"},
        )
    assert out["body"] is base
    assert not cm.called


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
    assert (
        ms.material_for_zone_geometry_extra("body", slots, {"body": {}}, "default", "")
        is limb
    )


def test_material_for_zone_geometry_extra_creates_when_extra_hex() -> None:
    b = MagicMock()
    b.name = "Organic_Brown"
    slots = {"body": b}
    new_m = MagicMock()
    with patch.object(ms, "create_material", return_value=new_m) as cm:
        got = ms.material_for_zone_geometry_extra(
            "body", slots, None, "default", "ff00aa"
        )
    assert got is new_m
    assert cm.called


def test_material_for_zone_geometry_extra_returns_none_when_slot_missing() -> None:
    assert (
        ms.material_for_zone_geometry_extra("body", {}, {}, "matte", "aabbcc") is None
    )


def test_get_enemy_materials_single_theme_color_fills_all_slots() -> None:
    m0 = MagicMock(name="M0")
    palette = {"M0": m0}
    rng = MagicMock()
    with (
        patch.object(ms_enemy_themes.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms_enemy_themes.MaterialThemes, "get_theme", return_value=("M0",)),
    ):
        out = ms.get_enemy_materials("solo_theme", palette, rng)
    assert out["joints"] is m0
    assert out["limbs"] is m0


def test_get_enemy_materials_joint_slot_matches_limbs_for_three_theme_colors() -> None:
    palette = {f"M{i}": MagicMock(name=f"M{i}") for i in range(3)}
    rng = MagicMock()
    rng.choice = MagicMock(side_effect=lambda seq: seq[-1])
    with (
        patch.object(ms_enemy_themes.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms_enemy_themes.MaterialThemes, "get_theme", return_value=("M0", "M1", "M2")),
    ):
        out = ms.get_enemy_materials("test_enemy", palette, rng)
    assert out["limbs"] is palette["M2"]
    assert out["joints"] is palette["M2"]


def test_get_enemy_materials_unknown_enemy_uses_default_palette_slots() -> None:
    """Enemy names with no registered theme map body/head/limbs/joints/extra from defaults."""
    brown = MagicMock()
    pink = MagicMock()
    bone = MagicMock()
    palette = {
        MaterialNames.ORGANIC_BROWN: brown,
        MaterialNames.FLESH_PINK: pink,
        MaterialNames.BONE_WHITE: bone,
    }
    rng = MagicMock()
    out = ms_enemy_themes.get_enemy_materials(
        "enemy_with_no_theme_registry_entry_901", palette, rng
    )
    assert out["body"] is brown
    assert out["head"] is pink
    assert out["limbs"] is bone
    assert out["joints"] is bone
    assert out["extra"] is brown


def test_get_enemy_materials_two_theme_materials_reuses_first_for_limbs_and_joints() -> None:
    ma, mb = MagicMock(name="MA"), MagicMock(name="MB")
    palette = {"MA": ma, "MB": mb}
    rng = MagicMock()
    with (
        patch.object(ms_enemy_themes.MaterialThemes, "has_theme", return_value=True),
        patch.object(ms_enemy_themes.MaterialThemes, "get_theme", return_value=("MA", "MB")),
    ):
        out = ms_enemy_themes.get_enemy_materials("two_slot_theme", palette, rng)
    assert out["body"] is ma
    assert out["head"] is mb
    assert out["limbs"] is ma
    assert out["joints"] is ma
    assert out["extra"] is mb


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
