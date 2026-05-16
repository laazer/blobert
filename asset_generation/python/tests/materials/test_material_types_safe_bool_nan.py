"""ZoneTextureOptions coercion covers _safe_bool float NaN path."""

from __future__ import annotations

from src.materials.material_types import (
    ZoneTextureOptions,
    _normalized_stripe_preset,
    _safe_bool,
    feature_zone_map,
)


def test_zone_texture_options_nan_mask_soft_edges_falls_back_to_default() -> None:
    build = {
        "features": {"body": {"finish": "default", "hex": "", "parts": {}}},
        "feat_body_texture_mode": "spots",
        "feat_body_texture_spot_density": 1.0,
        "feat_body_texture_spot_plate_mask_soft_edges": float("nan"),
    }
    zf = feature_zone_map(build["features"])
    z = ZoneTextureOptions.from_build_options(zone="body", zone_features=zf, build_options=build)
    assert z.spot_plate_mask_soft_edges is True


def test_zone_texture_options_mask_soft_edges_string_truthy() -> None:
    build = {
        "features": {"body": {"finish": "default", "hex": "", "parts": {}}},
        "feat_body_texture_mode": "spots",
        "feat_body_texture_spot_density": 1.0,
        "feat_body_texture_spot_plate_mask_soft_edges": " yes ",
    }
    zf = feature_zone_map(build["features"])
    z = ZoneTextureOptions.from_build_options(zone="body", zone_features=zf, build_options=build)
    assert z.spot_plate_mask_soft_edges is True


def test_zone_texture_options_mask_soft_edges_string_falsey() -> None:
    build = {
        "features": {"body": {"finish": "default", "hex": "", "parts": {}}},
        "feat_body_texture_mode": "spots",
        "feat_body_texture_spot_density": 1.0,
        "feat_body_texture_spot_plate_mask_soft_edges": "off",
    }
    zf = feature_zone_map(build["features"])
    z = ZoneTextureOptions.from_build_options(zone="body", zone_features=zf, build_options=build)
    assert z.spot_plate_mask_soft_edges is False


def test_normalized_stripe_preset_unknown_maps_to_beachball() -> None:
    assert _normalized_stripe_preset("diagonal_weird") == "beachball"


def test_safe_bool_unrecognized_string_uses_default() -> None:
    assert _safe_bool("maybe", default=True) is True
    assert _safe_bool("maybe", default=False) is False


def test_safe_bool_none_returns_default() -> None:
    assert _safe_bool(None, default=True) is True
    assert _safe_bool(None, default=False) is False


def test_zone_texture_options_mask_soft_edges_int_zero() -> None:
    build = {
        "features": {"body": {"finish": "default", "hex": "", "parts": {}}},
        "feat_body_texture_mode": "spots",
        "feat_body_texture_spot_density": 1.0,
        "feat_body_texture_spot_plate_mask_soft_edges": 0,
    }
    zf = feature_zone_map(build["features"])
    z = ZoneTextureOptions.from_build_options(zone="body", zone_features=zf, build_options=build)
    assert z.spot_plate_mask_soft_edges is False
