"""Per-zone procedural texture controls (feat_{zone}_texture_*) — declarations, coercion, serialization.

Texture presets are aligned with material zones (body, head, …) instead of a single global texture_* block.
"""

from __future__ import annotations

import json

import pytest

from src.utils.build_options import (
    animated_build_controls_for_api,
    defaults_for_slug,
    feature_zones,
    options_for_enemy,
    zone_texture_control_defs,
)

_ALL_SLUGS = [
    "spider",
    "slug",
    "claw_crawler",
    "imp",
    "carapace_husk",
    "spitter",
    "player_slime",
]

_TEXTURE_DEFAULTS = {
    "texture_mode": "none",
    # fill_picker controls (no default → None in options_for_enemy)
    "texture_pattern": None,
    "texture_background": None,
    # Per-channel sub-controls for pattern fill
    "texture_pattern_mode": "single",
    "texture_pattern_hex": "",
    "texture_pattern_grad_a": "",
    "texture_pattern_grad_b": "",
    "texture_pattern_grad_direction": "horizontal",
    "texture_pattern_image_id": "",
    "texture_pattern_image_preview": "",
    "texture_pattern_image_uv_rect": "",
    # Per-channel sub-controls for background fill
    "texture_background_mode": "single",
    "texture_background_hex": "",
    "texture_background_grad_a": "",
    "texture_background_grad_b": "",
    "texture_background_grad_direction": "horizontal",
    "texture_background_image_id": "",
    "texture_background_image_preview": "",
    "texture_background_image_uv_rect": "",
    # Spot-specific
    "texture_spot_pattern": "grid",
    "texture_spot_density": 1.0,
    # Stripe-specific
    "texture_stripe_width": 0.2,
    "texture_stripe_direction": "beachball",
    "texture_stripe_rot_yaw": 0.0,
    "texture_stripe_rot_pitch": 0.0,
    # Asset-specific
    "texture_asset_id": "",
    "texture_asset_tile_repeat": 1.0,
}


def _zone_texture_keys(slug: str) -> list[str]:
    return [c["key"] for c in zone_texture_control_defs(slug)]


def _global_key_from_zone_texture_key(zone_key: str) -> str:
    """feat_body_texture_mode -> texture_mode."""
    suffix = zone_key.split("_texture_", 1)[1]
    return f"texture_{suffix}"


def _body_prefix(slug: str) -> str:
    zones = feature_zones(slug)
    assert "body" in zones
    return "feat_body_texture_"


class TestZoneTextureControlDefs:
    """Per-zone texture controls organized by textureMode and pattern type."""

    def test_zone_texture_controls_include_mode_and_fills(self) -> None:
        """Each zone should have textureMode, pattern fill, and background fill controls."""
        for slug in _ALL_SLUGS:
            defs = zone_texture_control_defs(slug)
            zones = feature_zones(slug)

            # Each zone should contribute controls for textureMode, pattern, background,
            # and pattern-specific options (spots, stripes, checkerboard) plus global (asset).
            for zone in zones:
                mode_key = f"feat_{zone}_texture_mode"
                pattern_key = f"feat_{zone}_texture_pattern"
                bg_key = f"feat_{zone}_texture_background"

                mode_control = next((c for c in defs if c["key"] == mode_key), None)
                assert mode_control is not None, f"Missing {mode_key}"
                assert mode_control["type"] == "select_str"

                pattern_control = next((c for c in defs if c["key"] == pattern_key), None)
                assert pattern_control is not None, f"Missing {pattern_key}"

                bg_control = next((c for c in defs if c["key"] == bg_key), None)
                assert bg_control is not None, f"Missing {bg_key}"

    def test_spider_body_texture_mode_shape(self) -> None:
        defs = zone_texture_control_defs("spider")
        entry = next(d for d in defs if d["key"] == "feat_body_texture_mode")
        assert entry["label"].startswith("Body")
        assert entry["type"] == "select_str"
        assert entry["options"] == ["none", "gradient", "spots", "checkerboard", "stripes", "assets"]


@pytest.mark.parametrize("slug", _ALL_SLUGS)
def test_api_includes_all_zone_texture_keys(slug: str) -> None:
    ctrl = animated_build_controls_for_api()
    keys = {c["key"] for c in ctrl[slug]}
    for zk in _zone_texture_keys(slug):
        assert zk in keys


@pytest.mark.parametrize("slug", _ALL_SLUGS)
def test_placement_seed_after_last_zone_texture_key(slug: str) -> None:
    ctrl = animated_build_controls_for_api()
    keys = [c["key"] for c in ctrl[slug]]
    assert keys[-1] == "placement_seed"
    zkeys = _zone_texture_keys(slug)
    assert keys.index(zkeys[-1]) < keys.index("placement_seed")


@pytest.mark.parametrize("slug", _ALL_SLUGS)
def test_defaults_include_zone_texture_keys(slug: str) -> None:
    d = defaults_for_slug(slug)
    for zk in _zone_texture_keys(slug):
        assert zk in d
        gk = _global_key_from_zone_texture_key(zk)
        assert d[zk] == _TEXTURE_DEFAULTS[gk]


@pytest.mark.parametrize("slug", _ALL_SLUGS)
def test_options_for_enemy_defaults_match_texture_template(slug: str) -> None:
    d = defaults_for_slug(slug)
    o = options_for_enemy(slug, {})
    for zk in _zone_texture_keys(slug):
        assert o[zk] == d[zk]


class TestCoercionBodyZone:
    """Coercion uses feat_body_texture_* (body zone exists on all _ALL_SLUGS)."""

    BP = _body_prefix("spider")

    def test_invalid_mode_falls_back_to_none(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}mode": "invalid"})
        assert o[f"{self.BP}mode"] == "none"

    def test_gradient_accepted(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}mode": "gradient"})
        assert o[f"{self.BP}mode"] == "gradient"

    def test_uppercase_gradient(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}mode": "GRADIENT"})
        assert o[f"{self.BP}mode"] == "gradient"

    def test_spot_density_clamped(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}spot_density": 99.0})
        assert o[f"{self.BP}spot_density"] == 5.0

    def test_stripe_width_clamped(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}stripe_width": 99.0})
        assert o[f"{self.BP}stripe_width"] == 1.0

    def test_legacy_stripe_horizontal_vertical_maps_to_presets(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}stripe_direction": "horizontal"})
        assert o[f"{self.BP}stripe_direction"] == "doplar"
        o2 = options_for_enemy("slug", {f"{self.BP}stripe_direction": "vertical"})
        assert o2[f"{self.BP}stripe_direction"] == "beachball"

    def test_legacy_xyz_maps_to_presets(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}stripe_direction": "x"})
        assert o[f"{self.BP}stripe_direction"] == "beachball"
        o2 = options_for_enemy("slug", {f"{self.BP}stripe_direction": "y"})
        assert o2[f"{self.BP}stripe_direction"] == "doplar"
        o3 = options_for_enemy("slug", {f"{self.BP}stripe_direction": "z"})
        assert o3[f"{self.BP}stripe_direction"] == "swirl"

    def test_legacy_stripe_rot_xyz_maps_to_yaw_pitch(self) -> None:
        o = options_for_enemy(
            "slug",
            {
                f"{self.BP}stripe_rot_x": 10.0,
                f"{self.BP}stripe_rot_y": -5.0,
                f"{self.BP}stripe_rot_z": 3.0,
            },
        )
        assert o[f"{self.BP}stripe_rot_pitch"] == 10.0
        assert o[f"{self.BP}stripe_rot_yaw"] == -5.0
        assert f"{self.BP}stripe_rot_x" not in o

    def test_spot_color_defaults_to_empty(self) -> None:
        """Pattern fill controls default to None (fill_picker type)."""
        o = options_for_enemy("slug", {})
        assert o[f"{self.BP}pattern"] is None
        assert o[f"{self.BP}background"] is None


class TestSerialization:
    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_json_round_trip_preserves_zone_texture_defaults(self, slug: str) -> None:
        o = options_for_enemy(slug, {})
        parsed = json.loads(json.dumps(o))
        for zk in _zone_texture_keys(slug):
            gk = _global_key_from_zone_texture_key(zk)
            assert parsed[zk] == _TEXTURE_DEFAULTS[gk]

    @pytest.mark.parametrize("slug", _ALL_SLUGS)
    def test_double_options_for_enemy_idempotent(self, slug: str) -> None:
        o1 = options_for_enemy(slug, {})
        o2 = options_for_enemy(slug, json.loads(json.dumps(o1)))
        for zk in _zone_texture_keys(slug):
            assert o2[zk] == o1[zk]


class TestRegressionExistingControls:
    def test_spider_eye_count_default(self) -> None:
        o = options_for_enemy("spider", {})
        assert o["eye_count"] == 2

    def test_mouth_enabled_default(self) -> None:
        o = options_for_enemy("spider", {})
        assert o["mouth_enabled"] is False
