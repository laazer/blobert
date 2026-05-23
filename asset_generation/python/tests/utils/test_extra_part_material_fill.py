"""Material fill_picker keys for geometry extras and per-limb/joint overrides."""

from __future__ import annotations

from src.utils.build_options import animated_build_controls_for_api, options_for_enemy


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
