"""Material fill_picker keys for geometry extras and per-limb/joint overrides."""

from __future__ import annotations

from src.utils.build_options import animated_build_controls_for_api, options_for_enemy
from src.utils.build_options.schema import (
    _apply_material_fill_field,
    _default_features_dict,
    _merge_features_for_slug,
)


def test_apply_material_fill_field_sanitizes_mode_and_grad_direction() -> None:
    mf: dict[str, object] = {}
    _apply_material_fill_field(mf, "mode", "not-valid")
    assert mf["mode"] == "single"
    _apply_material_fill_field(mf, "grad_direction", "diagonal")
    assert mf["grad_direction"] == "horizontal"
    _apply_material_fill_field(mf, "image_id", "  tex1  ")
    assert mf["image_id"] == "tex1"
    _apply_material_fill_field(mf, "image_preview", None)
    assert mf["image_preview"] is None


def test_merge_features_nested_parts_material_fill() -> None:
    slug = "spider"
    src = {
        "features": {
            "limbs": {
                "parts": {
                    "leg_0": {
                        "finish": "glossy",
                        "material_fill": {"mode": "image", "image_id": "tex1"},
                    },
                    "bad": "skip",
                }
            }
        }
    }
    out = _merge_features_for_slug(slug, src, _default_features_dict(slug))
    assert out["limbs"]["parts"]["leg_0"]["material_fill"]["mode"] == "image"
    assert "bad" not in out["limbs"]["parts"]


def test_extra_zone_material_fill_defs_present_for_spider() -> None:
    keys = {c["key"] for c in animated_build_controls_for_api()["spider"]}
    assert "extra_zone_body_material" in keys
    assert "extra_zone_body_material_mode" in keys
    assert "extra_zone_body_material_hex" in keys
    assert "extra_zone_body_hex" in keys


def test_limb_material_fill_defs_present_for_spider() -> None:
    keys = {c["key"] for c in animated_build_controls_for_api()["spider"]}
    assert "feat_limb_leg_0_material" in keys
    assert "feat_limb_leg_0_material_mode" in keys
    assert "feat_joint_leg_0_root_material" in keys


def test_extra_zone_material_fill_merges_into_zone_geometry_extras() -> None:
    opts = options_for_enemy(
        "spider",
        {
            "extra_zone_body_material_mode": "gradient",
            "extra_zone_body_material_grad_a": "ff0000",
            "extra_zone_body_material_grad_b": "0000ff",
            "extra_zone_body_finish": "matte",
        },
    )
    body = opts["zone_geometry_extras"]["body"]
    mf = body["material_fill"]
    assert mf["mode"] == "gradient"
    assert mf["grad_a"] == "ff0000"
    assert mf["grad_b"] == "0000ff"
    assert body["hex"] == "ff0000"


def test_joint_material_fill_merges_into_features_parts() -> None:
    opts = options_for_enemy(
        "spider",
        {
            "feat_joint_leg_0_j0_material_mode": "single",
            "feat_joint_leg_0_j0_material_hex": "ccddee",
        },
    )
    part = opts["features"]["joints"]["parts"]["leg_0_j0"]
    assert part["material_fill"]["mode"] == "single"
    assert part["material_fill"]["hex"] == "ccddee"


def test_extra_zone_material_fill_unknown_zone_flat_key_is_ignored() -> None:
    opts = options_for_enemy(
        "spider",
        {
            "extra_zone_unknown_zone_material_mode": "single",
            "extra_zone_unknown_zone_material_hex": "aabbcc",
        },
    )
    assert "unknown_zone" not in opts.get("zone_geometry_extras", {})


def test_extra_zone_hex_flat_syncs_material_fill() -> None:
    opts = options_for_enemy(
        "spider",
        {
            "extra_zone_body_kind": "bulbs",
            "extra_zone_body_hex": "ff00aa",
        },
    )
    body = opts["zone_geometry_extras"]["body"]
    assert body["hex"] == "ff00aa"
    assert body["material_fill"]["hex"] == "ff00aa"


def test_limb_material_fill_merges_into_features_parts() -> None:
    opts = options_for_enemy(
        "spider",
        {
            "feat_limb_leg_0_material_mode": "single",
            "feat_limb_leg_0_material_hex": "aabbcc",
        },
    )
    part = opts["features"]["limbs"]["parts"]["leg_0"]
    assert part["material_fill"]["mode"] == "single"
    assert part["material_fill"]["hex"] == "aabbcc"
    assert part["hex"] == "aabbcc"
