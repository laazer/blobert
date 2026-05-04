"""Unit tests for ``material_types`` helpers (no Blender scene)."""

from __future__ import annotations

from unittest.mock import patch

from src.materials.material_types import (
    FeatureZoneOptions,
    GradientFill,
    ImageFill,
    SolidFill,
    ZoneTextureOptions,
    feature_zone_map,
    fill_material_from_build_options,
)

# -- feature_zone_map ---------------------------------------------------------


def test_feature_zone_map_empty_inputs() -> None:
    assert feature_zone_map(None) == {}
    assert feature_zone_map({}) == {}


def test_feature_zone_map_skips_non_string_keys() -> None:
    out = feature_zone_map(
        {
            99: {"finish": "default", "hex": ""},
            "body": {"finish": "matte", "hex": "aa"},
        }
    )
    assert list(out.keys()) == ["body"]
    assert out["body"].finish == "matte"


# -- FillMaterial dispatch -----------------------------------------------------


def test_fill_material_defaults_to_solid_fill() -> None:
    fill = fill_material_from_build_options(zone="body", field="pattern", build_options={})
    assert isinstance(fill, SolidFill)
    assert fill.hex_value == ""


def test_fill_material_single_mode_reads_hex() -> None:
    fill = fill_material_from_build_options(
        zone="body",
        field="pattern",
        build_options={
            "feat_body_texture_pattern_mode": "single",
            "feat_body_texture_pattern_hex": "ff0000",
        },
    )
    assert isinstance(fill, SolidFill)
    assert fill.hex_value == "ff0000"


def test_fill_material_gradient_mode_reads_a_b_direction() -> None:
    fill = fill_material_from_build_options(
        zone="body",
        field="pattern",
        build_options={
            "feat_body_texture_pattern_mode": "gradient",
            "feat_body_texture_pattern_a": "ff0000",
            "feat_body_texture_pattern_b": "0000ff",
            "feat_body_texture_pattern_direction": "vertical",
        },
    )
    assert isinstance(fill, GradientFill)
    assert fill.hex_a == "ff0000"
    assert fill.hex_b == "0000ff"
    assert fill.direction == "vertical"


def test_fill_material_gradient_defaults_direction_horizontal() -> None:
    fill = fill_material_from_build_options(
        zone="body",
        field="background",
        build_options={"feat_body_texture_background_mode": "gradient"},
    )
    assert isinstance(fill, GradientFill)
    assert fill.direction == "horizontal"


def test_fill_material_image_mode_reads_asset_id() -> None:
    fill = fill_material_from_build_options(
        zone="body",
        field="pattern",
        build_options={
            "feat_body_texture_pattern_mode": "image",
            "feat_body_texture_pattern_image_id": "demo_textures3",
        },
    )
    assert isinstance(fill, ImageFill)
    assert fill.asset_id == "demo_textures3"


def test_fill_material_image_mode_infers_asset_from_preview() -> None:
    with patch(
        "src.materials.material_types.infer_texture_asset_id_from_preview",
        return_value="inferred_asset",
    ) as mock_infer:
        fill = fill_material_from_build_options(
            zone="body",
            field="pattern",
            build_options={
                "feat_body_texture_pattern_mode": "image",
                "feat_body_texture_pattern_image_preview": "/some/preview.png",
            },
        )
    assert isinstance(fill, ImageFill)
    assert fill.asset_id == "inferred_asset"
    mock_infer.assert_called_once_with("/some/preview.png")


def test_fill_material_image_mode_parses_uv_rect() -> None:
    fill = fill_material_from_build_options(
        zone="head",
        field="pattern",
        build_options={
            "feat_head_texture_pattern_mode": "image",
            "feat_head_texture_pattern_image_id": "atlas1",
            "feat_head_texture_pattern_image_uv_rect": '{"u0":0.0,"v0":0.0,"u1":0.5,"v1":0.5}',
        },
    )
    assert isinstance(fill, ImageFill)
    assert fill.uv_rect == (0.0, 0.0, 0.5, 0.5)


def test_fill_material_image_mode_no_uv_rect_is_none() -> None:
    fill = fill_material_from_build_options(
        zone="body",
        field="pattern",
        build_options={
            "feat_body_texture_pattern_mode": "image",
            "feat_body_texture_pattern_image_id": "some_asset",
        },
    )
    assert isinstance(fill, ImageFill)
    assert fill.uv_rect is None


def test_fill_material_unknown_mode_defaults_to_empty_solid() -> None:
    fill = fill_material_from_build_options(
        zone="body",
        field="pattern",
        build_options={"feat_body_texture_pattern_mode": "unknown_garbage"},
    )
    assert isinstance(fill, SolidFill)
    assert fill.hex_value == ""


# -- ZoneTextureOptions --------------------------------------------------------


def test_zone_texture_options_reads_legacy_stripe_rot_y() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={"feat_body_texture_stripe_rot_y": 33.0},
    )
    assert opts.stripe_yaw == 33.0


def test_zone_texture_options_reads_legacy_stripe_rot_x() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={"feat_body_texture_stripe_rot_x": 22.5},
    )
    assert opts.stripe_pitch == 22.5


def test_safe_bool_coerces_build_strings() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    off = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_spot_plate_mask_soft_edges": "false",
        },
    )
    assert off.spot_plate_mask_soft_edges is False
    on = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_spot_plate_mask_soft_edges": "1",
        },
    )
    assert on.spot_plate_mask_soft_edges is True


def test_safe_float_coerces_invalid_to_default() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={"feat_body_texture_spot_density": "not-a-float"},
    )
    assert opts.spot_density == 1.0


def test_spot_pattern_image_asset_id_from_pattern_fill() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_pattern_mode": "image",
            "feat_body_texture_pattern_image_id": "foreground_asset",
        },
    )
    assert opts.spot_pattern_image_asset_id() == "foreground_asset"


def test_spot_pattern_image_asset_id_empty_for_solid_fill() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_pattern_mode": "single",
            "feat_body_texture_pattern_hex": "ff0000",
        },
    )
    assert opts.spot_pattern_image_asset_id() == ""


def test_zone_texture_options_constructs_fill_materials() -> None:
    """pattern_fill and background_fill are constructed from build_options."""
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_pattern_mode": "single",
            "feat_body_texture_pattern_hex": "aabb00",
            "feat_body_texture_background_mode": "gradient",
            "feat_body_texture_background_a": "ff0000",
            "feat_body_texture_background_b": "00ff00",
        },
    )
    assert isinstance(opts.pattern_fill, SolidFill)
    assert opts.pattern_fill.hex_value == "aabb00"
    assert isinstance(opts.background_fill, GradientFill)
    assert opts.background_fill.hex_a == "ff0000"
    assert opts.background_fill.hex_b == "00ff00"
