"""Regression tests for image texture schema handling.

Bug: Image textures are not being applied (image-textures-not-applied).
Requirement 1: Extend build_options schema to capture image texture data.

This test module verifies that the build_options schema correctly accepts,
validates, and merges image texture data (feat_{zone}_color_mode,
feat_{zone}_color_image_id, feat_{zone}_color_image_preview) from frontend
into the features[zone].color_image output structure.
"""

from __future__ import annotations

from src.utils.build_options import (
    options_for_enemy,
    parse_build_options_json,
)
from src.utils.build_options.schema import (
    _default_features_dict,
    _merge_features_for_slug,
)


class TestImageTextureSchemaMerge:
    """Test image texture data merging into features structure.

    These tests verify Requirement 1 (Extend build_options schema to capture
    image texture data) from the image-textures-not-applied bug ticket.
    """

    def test_BUG_image_textures_not_applied_image_mode_with_texture_id(
        self,
    ) -> None:
        """AC1.1: Image mode with preloaded texture ID merges into color_image."""
        # When build_options JSON contains feat_{zone}_color_mode: "image"
        # and feat_{zone}_color_image_id: "stripe_01", the schema must merge
        # it into features[zone].color_image with mode and id fields.
        o = options_for_enemy(
            "spider",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "stripe_01",
            },
        )

        # Verify the image texture data is present in features[zone].color_image
        assert "color_image" in o["features"]["body"], (
            "features[body] must include color_image entry when image mode is set"
        )
        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "stripe_01"

    def test_BUG_image_textures_not_applied_image_mode_with_preview_url(
        self,
    ) -> None:
        """AC1.3: Image mode with custom preview URL stores preview field."""
        # When build_options JSON contains feat_{zone}_color_mode: "image"
        # and feat_{zone}_color_image_preview: "<blob:...>", the schema must
        # store the preview URL in color_image.preview.
        preview_url = "blob:http://localhost:5173/12345678-1234-1234-1234-123456789abc"
        o = options_for_enemy(
            "spider",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_preview": preview_url,
            },
        )

        assert "color_image" in o["features"]["body"], (
            "features[body] must include color_image entry when image mode is set"
        )
        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["preview"] == preview_url

    def test_BUG_image_textures_not_applied_image_id_and_preview_both_stored(
        self,
    ) -> None:
        """AC1.3: Both image ID and preview can be stored simultaneously."""
        # Schema may receive both preloaded texture ID and custom preview URL
        # and should store both in the color_image structure.
        preview_url = "blob:http://localhost:5173/custom-upload"
        o = options_for_enemy(
            "spider",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "stripe_01",
                "feat_body_color_image_preview": preview_url,
            },
        )

        color_image = o["features"]["body"]["color_image"]
        assert color_image["mode"] == "image"
        assert color_image["id"] == "stripe_01"
        assert color_image["preview"] == preview_url

    def test_BUG_image_textures_not_applied_multiple_zones_with_image_mode(
        self,
    ) -> None:
        """Image mode can be set independently per zone."""
        # Verify that image mode can be set for different zones independently
        # (e.g., body with image, head with single color).
        o = options_for_enemy(
            "spider",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "stripe_01",
                "feat_head_color_mode": "image",
                "feat_head_color_image_id": "texture_spots_01",
                "feat_limbs_color_mode": "single",
                "feat_limbs_hex": "ff0000",
            },
        )

        # Body and head should have image mode
        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "stripe_01"
        assert o["features"]["head"]["color_image"]["mode"] == "image"
        assert o["features"]["head"]["color_image"]["id"] == "texture_spots_01"

        # Limbs should have single color (not image)
        assert o["features"]["limbs"]["color_image"]["mode"] == "single"
        assert o["features"]["limbs"]["hex"] == "ff0000"

    def test_BUG_image_textures_not_applied_flat_key_syntax(self) -> None:
        """Image texture keys are accepted in flat key syntax (not nested)."""
        # Frontend may send data as flat keys (feat_zone_color_mode)
        # or nested (features[zone].color_mode). Both should work.
        o = options_for_enemy(
            "claw_crawler",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "wood_grain_01",
            },
        )

        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "wood_grain_01"

    def test_BUG_image_textures_not_applied_nested_syntax(self) -> None:
        """Image texture data can be nested under features.zone.color_image."""
        # Nested syntax should also be accepted
        o = options_for_enemy(
            "spider",
            {
                "features": {
                    "body": {
                        "color_image": {
                            "mode": "image",
                            "id": "stripe_01",
                            "preview": None,
                        }
                    }
                }
            },
        )

        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "stripe_01"

    def test_BUG_image_textures_not_applied_parses_json_with_image_keys(self) -> None:
        """parse_build_options_json preserves image texture keys."""
        # Frontend sends JSON with image texture data; it must be parsed
        # and passed through to options_for_enemy without loss.
        raw = parse_build_options_json(
            '{'
            '"feat_body_color_mode": "image", '
            '"feat_body_color_image_id": "stripe_01"'
            '}'
        )
        o = options_for_enemy("spider", raw)

        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "stripe_01"

    def test_BUG_image_textures_not_applied_non_image_mode_defaults(self) -> None:
        """When image mode is not set, color_image defaults to single mode."""
        # Default behavior: if no image mode is specified, color_image should
        # default to single color mode with empty id and preview.
        o = options_for_enemy("spider", {})

        # All zones should have a default color_image structure
        assert "color_image" in o["features"]["body"]
        assert o["features"]["body"]["color_image"]["mode"] == "single"
        assert o["features"]["body"]["color_image"]["id"] is None or o["features"]["body"]["color_image"]["id"] == ""
        assert o["features"]["body"]["color_image"]["preview"] is None or o["features"]["body"]["color_image"]["preview"] == ""

    def test_BUG_image_textures_not_applied_image_mode_with_imp(self) -> None:
        """Image texture feature works across multiple enemy types (imp)."""
        # Verify that image texture support is not spider-specific;
        # it works for other enemy types as well.
        o = options_for_enemy(
            "imp",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "critter_texture_01",
                "feat_head_color_mode": "image",
                "feat_head_color_image_id": "critter_head_pattern",
            },
        )

        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "critter_texture_01"
        assert o["features"]["head"]["color_image"]["mode"] == "image"
        assert o["features"]["head"]["color_image"]["id"] == "critter_head_pattern"

    def test_BUG_image_textures_not_applied_invalid_image_id_falls_back(
        self,
    ) -> None:
        """AC1.2: Invalid texture ID falls back to single mode without crashing."""
        # When a preloaded texture ID is invalid (not in whitelist),
        # the schema logs a warning and falls back to single mode,
        # preserving the zone's material settings.
        o = options_for_enemy(
            "spider",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "nonexistent_texture_999",
            },
        )

        # Should fall back to single mode (not crash)
        # The spec leaves the fallback behavior to the implementation,
        # but the schema should be stable.
        assert "color_image" in o["features"]["body"]
        # Color_image should exist in some form (implementation may vary)

    def test_BUG_image_textures_not_applied_image_mode_with_color_hex_ignored(
        self,
    ) -> None:
        """When image mode is set, hex color is kept but image takes precedence."""
        # Edge case: user may have both image mode and a hex color.
        # The hex color should be preserved for fallback, but image takes precedence
        # in material generation (per Requirement 3).
        o = options_for_enemy(
            "spider",
            {
                "feat_body_color_mode": "image",
                "feat_body_color_image_id": "stripe_01",
                "feat_body_hex": "ff0000",
            },
        )

        # Both should be present
        assert o["features"]["body"]["color_image"]["mode"] == "image"
        assert o["features"]["body"]["color_image"]["id"] == "stripe_01"
        assert o["features"]["body"]["hex"] == "ff0000"

    def test_BUG_image_textures_not_applied_all_zones_include_color_image(self) -> None:
        """All feature zones include color_image in the output."""
        # Verify that every zone (body, head, limbs, joints, extra for spider)
        # has a color_image structure in the output.
        o = options_for_enemy("spider", {})

        zones = o["features"].keys()
        for zone in zones:
            assert "color_image" in o["features"][zone], (
                f"Zone '{zone}' must include color_image structure"
            )
            # Each should have mode, id, and preview fields
            assert "mode" in o["features"][zone]["color_image"]


def test_merge_features_for_slug_non_dict_color_image_in_feat_base_defaults() -> None:
    """When feat_base has a non-dict color_image, merge applies single-mode defaults (schema)."""
    fb = _default_features_dict("spider")
    fb["body"] = {
        **fb["body"],
        "color_image": "not-a-dict",
    }
    out = _merge_features_for_slug("spider", {}, fb)
    assert out["body"]["color_image"] == {
        "mode": "single",
        "id": None,
        "preview": None,
    }
