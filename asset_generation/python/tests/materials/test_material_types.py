"""Unit tests for ``material_types`` helpers (no Blender scene)."""

from __future__ import annotations

from unittest.mock import patch

from src.materials.material_types import (
    FeatureZoneOptions,
    PatternChannelOptions,
    ZoneTextureOptions,
    feature_zone_map,
)


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


def test_pattern_channel_resolved_hex_gradient_blends() -> None:
    ch = PatternChannelOptions.from_build_options(
        zone="body",
        field="spot_color",
        build_options={
            "feat_body_texture_spot_color_mode": "gradient",
            "feat_body_texture_spot_color_a": "ff0000",
            "feat_body_texture_spot_color_b": "0000ff",
        },
    )
    assert ch.resolved_hex() == "7f007f"


def test_pattern_channel_resolved_hex_gradient_one_side_empty() -> None:
    ch = PatternChannelOptions.from_build_options(
        zone="body",
        field="spot_color",
        build_options={
            "feat_body_texture_spot_color_mode": "gradient",
            "feat_body_texture_spot_color_a": "",
            "feat_body_texture_spot_color_b": "00ff00",
        },
    )
    assert ch.resolved_hex() == "00ff00"


def test_pattern_channel_resolved_hex_gradient_empty_pair() -> None:
    ch = PatternChannelOptions.from_build_options(
        zone="body",
        field="spot_color",
        build_options={
            "feat_body_texture_spot_color_mode": "gradient",
            "feat_body_texture_spot_color_a": "",
            "feat_body_texture_spot_color_b": "",
            "feat_body_texture_spot_color": "aabbcc",
        },
    )
    assert ch.resolved_hex() == "aabbcc"


def test_pattern_channel_resolved_hex_image_uses_average_pipeline() -> None:
    with patch(
        "src.materials.material_types._pattern_image_average_hex",
        return_value="112233",
    ) as mock_avg:
        ch = PatternChannelOptions.from_build_options(
            zone="body",
            field="spot_color",
            build_options={
                "feat_body_texture_spot_color_mode": "image",
                "feat_body_texture_spot_color_image_id": "demo_textures3",
            },
        )
        assert ch.resolved_hex() == "112233"
    mock_avg.assert_called_once_with("demo_textures3")


def test_pattern_channel_resolved_hex_image_falls_back_to_channel_hex() -> None:
    with patch("src.materials.material_types._pattern_image_average_hex", return_value=""):
        ch = PatternChannelOptions.from_build_options(
            zone="body",
            field="spot_color",
            build_options={
                "feat_body_texture_spot_color_mode": "image",
                "feat_body_texture_spot_color_hex": "abcdef",
            },
        )
        assert ch.resolved_hex() == "abcdef"


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


def test_safe_float_coerces_invalid_to_default() -> None:
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={"feat_body_texture_spot_density": "not-a-float"},
    )
    assert opts.spot_density == 1.0
