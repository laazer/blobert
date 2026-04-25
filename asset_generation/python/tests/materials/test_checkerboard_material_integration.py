"""Integration tests for checkerboard texture mode wiring."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@patch("src.materials.material_system.bpy")
def test_checkerboard_mode_calls_checkerboard_factory(mock_bpy) -> None:  # noqa: ARG001
    from src.materials.material_system import apply_zone_texture_pattern_overrides

    mock_mat = MagicMock()
    slot_materials = {"body": mock_mat}
    build_options = {
        "feat_body_texture_mode": "checkerboard",
        "feat_body_texture_spot_color": "ff0000",
        "feat_body_texture_spot_bg_color": "ffffff",
        "feat_body_texture_spot_density": 1.5,
        "features": {"body": {"hex": "cccccc", "finish": "default"}},
    }

    with patch("src.materials.material_system._material_for_checkerboard_zone") as mock_factory:
        mock_factory.return_value = mock_mat
        with patch("src.materials.material_system._palette_base_name_from_material") as mock_palette:
            mock_palette.return_value = "test_palette"
            apply_zone_texture_pattern_overrides(slot_materials, build_options)
            mock_factory.assert_called_once()
            kw = mock_factory.call_args.kwargs
            assert kw.get("base_palette_name") == "test_palette"
            assert kw.get("color_a_hex") == "ff0000"
            assert kw.get("color_b_hex") == "ffffff"
            assert kw.get("density") == pytest.approx(1.5)
