"""Integration tests for stripes material system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestMaterialForStripesZone:
    def test_function_exists(self) -> None:
        from src.materials.material_stripes_zone import (
            _material_for_stripes_zone,  # noqa: F401
        )

    @patch("src.materials.material_stripes_zone.bpy")
    def test_calls_create_stripes_png_and_load(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_stripes_zone import (
            _material_for_stripes_zone,  # noqa: E402
        )

        mock_mat = MagicMock()
        mock_mat.use_nodes = True
        mock_mat.node_tree = MagicMock()

        with patch(
            "src.materials.material_stripes_zone.create_stripes_png_and_load"
        ) as mock_png:
            with patch(
                "src.materials.material_system.create_material"
            ) as mock_create_mat:
                mock_png.return_value = MagicMock()
                mock_create_mat.return_value = mock_mat

                _material_for_stripes_zone(
                    base_palette_name="test_palette",
                    finish="default",
                    stripe_hex="ff0000",
                    bg_hex="ffffff",
                    stripe_width=0.4,
                    zone_hex_fallback="cccccc",
                    instance_suffix="body_tex_stripe",
                )
                mock_png.assert_called_once()


class TestApplyZoneTexturePatternOverridesStripes:
    def test_stripes_branch_in_source(self) -> None:
        import inspect

        from src.materials.material_system import apply_zone_texture_pattern_overrides

        src = inspect.getsource(apply_zone_texture_pattern_overrides)
        assert "stripes" in src

    @patch("src.materials.material_system.bpy")
    def test_stripes_mode_calls_factory(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_system import apply_zone_texture_pattern_overrides

        mock_mat = MagicMock()
        slot_materials = {"body": mock_mat}
        build_options = {
            "feat_body_texture_mode": "stripes",
            "feat_body_texture_stripe_color": "ff0000",
            "feat_body_texture_stripe_bg_color": "ffffff",
            "feat_body_texture_stripe_width": 0.35,
            "features": {"body": {"hex": "cccccc", "finish": "default"}},
        }

        with patch(
            "src.materials.material_stripes_zone._material_for_stripes_zone"
        ) as mock_factory:
            mock_factory.return_value = mock_mat
            with patch(
                "src.materials.material_system._palette_base_name_from_material"
            ) as mock_palette:
                mock_palette.return_value = "test_palette"
                apply_zone_texture_pattern_overrides(slot_materials, build_options)
                mock_factory.assert_called_once()
                kw = mock_factory.call_args.kwargs
                assert kw.get("stripe_width") == pytest.approx(0.35)
