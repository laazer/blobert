"""Per-zone procedural texture controls (feat_{zone}_texture_*) — declarations, coercion, serialization.

Texture presets are aligned with material zones (body, head, …) instead of a single global texture_* block.
"""

from __future__ import annotations

import json

import pytest

from src.utils.animated_build_options import (
    _defaults_for_slug,
    _feature_zones,
    _zone_texture_control_defs,
    animated_build_controls_for_api,
    options_for_enemy,
)
from src.utils.animated_build_options_appendage_defs import _texture_control_defs

_ALL_SLUGS = [
    "spider",
    "slug",
    "claw_crawler",
    "imp",
    "carapace_husk",
    "spitter",
    "player_slime",
]

_TEXTURE_TEMPLATE_KEYS = [c["key"] for c in _texture_control_defs()]

_TEXTURE_DEFAULTS = {
    "texture_mode": "none",
    "texture_grad_color_a": "",
    "texture_grad_color_b": "",
    "texture_grad_direction": "horizontal",
    "texture_spot_color": "",
    "texture_spot_bg_color": "",
    "texture_spot_density": 1.0,
    "texture_stripe_color": "",
    "texture_stripe_bg_color": "",
    "texture_stripe_width": 0.2,
    "texture_asset_id": "",
    "texture_asset_tile_repeat": 1.0,
}


def _zone_texture_keys(slug: str) -> list[str]:
    return [c["key"] for c in _zone_texture_control_defs(slug)]


def _global_key_from_zone_texture_key(zone_key: str) -> str:
    """feat_body_texture_mode -> texture_mode."""
    suffix = zone_key.split("_texture_", 1)[1]
    return f"texture_{suffix}"


def _body_prefix(slug: str) -> str:
    zones = _feature_zones(slug)
    assert "body" in zones
    return "feat_body_texture_"


class TestTextureTemplateDefs:
    """Base template (_texture_control_defs) includes gradient, spots, stripes, and asset texture controls."""

    def test_texture_control_defs_returns_12_entries(self) -> None:
        result = _texture_control_defs()
        assert len(result) == 12
        assert [c["key"] for c in result] == [
            "texture_mode",
            "texture_grad_color_a",
            "texture_grad_color_b",
            "texture_grad_direction",
            "texture_spot_color",
            "texture_spot_bg_color",
            "texture_spot_density",
            "texture_stripe_color",
            "texture_stripe_bg_color",
            "texture_stripe_width",
            "texture_asset_id",
            "texture_asset_tile_repeat",
        ]


class TestZoneTextureControlDefs:
    def test_zone_texture_count_matches_zones_times_12(self) -> None:
        for slug in _ALL_SLUGS:
            zones = _feature_zones(slug)
            defs = _zone_texture_control_defs(slug)
            assert len(defs) == len(zones) * 12

    def test_spider_body_texture_mode_shape(self) -> None:
        defs = _zone_texture_control_defs("spider")
        entry = next(d for d in defs if d["key"] == "feat_body_texture_mode")
        assert entry["label"].startswith("Body")
        assert entry["type"] == "select_str"
        assert entry["options"] == ["none", "gradient", "spots", "stripes", "assets"]


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
    d = _defaults_for_slug(slug)
    for zk in _zone_texture_keys(slug):
        assert zk in d
        gk = _global_key_from_zone_texture_key(zk)
        assert d[zk] == _TEXTURE_DEFAULTS[gk]


@pytest.mark.parametrize("slug", _ALL_SLUGS)
def test_options_for_enemy_defaults_match_texture_template(slug: str) -> None:
    d = _defaults_for_slug(slug)
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

    def test_grad_color_passthrough(self) -> None:
        o = options_for_enemy("slug", {f"{self.BP}grad_color_a": "ff0000"})
        assert o[f"{self.BP}grad_color_a"] == "ff0000"


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
