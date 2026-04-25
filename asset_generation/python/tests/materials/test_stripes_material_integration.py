"""Integration tests for stripes material system."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestMaterialForStripesZone:
    def test_function_exists(self) -> None:
        from src.materials.material_stripes_zone import (
            material_for_stripes_zone,  # noqa: F401, PYI100
        )

    @patch("src.materials.material_stripes_zone.bpy")
    def test_beachball_calls_baked_texture_path(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_stripes_zone import (
            material_for_stripes_zone,  # noqa: E402, PYI100
        )

        mock_mat = MagicMock()
        mock_mat.use_nodes = True
        mock_mat.node_tree = MagicMock()

        with patch(
            "src.materials.material_stripes_zone.create_stripes_png_and_load"
        ) as mock_png:
            mock_png.return_value = MagicMock()
            with patch(
                "src.materials.material_stripes_zone.create_material"
            ) as mock_create_mat:
                mock_create_mat.return_value = mock_mat

                material_for_stripes_zone(
                    base_palette_name="test_palette",
                    finish="default",
                    stripe_hex="ff0000",
                    bg_hex="ffffff",
                    stripe_width=0.4,
                    stripe_preset="beachball",
                    rot_yaw_deg=-5.0,
                    rot_pitch_deg=10.0,
                    zone_hex_fallback="cccccc",
                    instance_suffix="body_tex_stripe",
                )
                mock_png.assert_called_once()
                kw = mock_png.call_args.kwargs
                assert kw.get("rot_x_deg") == pytest.approx(10.0)
                assert kw.get("rot_y_deg") == pytest.approx(-5.0)
                assert kw.get("rot_z_deg") == pytest.approx(0.0)

    @patch("src.materials.material_stripes_zone.bpy")
    def test_doplar_calls_object_space_projection_path(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_stripes_zone import material_for_stripes_zone

        mock_mat = MagicMock()
        mock_mat.use_nodes = True
        mock_mat.node_tree = MagicMock()
        with patch(
            "src.materials.material_stripes_zone._add_object_space_stripes_to_principled"
        ) as mock_builder:
            with patch("src.materials.material_stripes_zone.create_material") as mock_create_mat:
                mock_create_mat.return_value = mock_mat

                material_for_stripes_zone(
                    base_palette_name="test_palette",
                    finish="default",
                    stripe_hex="ff0000",
                    bg_hex="ffffff",
                    stripe_width=0.4,
                    stripe_preset="doplar",
                    rot_yaw_deg=15.0,
                    rot_pitch_deg=5.0,
                    zone_hex_fallback="cccccc",
                    instance_suffix="body_tex_stripe",
                )
                mock_builder.assert_called_once()

    @patch("src.materials.material_stripes_zone.bpy")
    def test_equivalent_rotations_share_canonical_image_name(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_stripes_zone import material_for_stripes_zone

        mock_mat = MagicMock()
        mock_mat.use_nodes = True
        mock_mat.node_tree = MagicMock()
        with patch(
            "src.materials.material_stripes_zone._add_object_space_stripes_to_principled"
        ) as mock_builder:
            with patch("src.materials.material_stripes_zone.create_material") as mock_create_mat:
                mock_create_mat.return_value = mock_mat

                material_for_stripes_zone(
                    base_palette_name="test_palette",
                    finish="default",
                    stripe_hex="ff0000",
                    bg_hex="ffffff",
                    stripe_width=0.4,
                    stripe_preset="doplar",
                    rot_yaw_deg=-90.0,
                    rot_pitch_deg=10.0,
                    zone_hex_fallback="cccccc",
                    instance_suffix="body_tex_stripe",
                )
                first_name = mock_create_mat.call_args.kwargs["name"]

                material_for_stripes_zone(
                    base_palette_name="test_palette",
                    finish="default",
                    stripe_hex="ff0000",
                    bg_hex="ffffff",
                    stripe_width=0.4,
                    stripe_preset="doplar",
                    rot_yaw_deg=270.0,
                    rot_pitch_deg=-10.0,
                    zone_hex_fallback="cccccc",
                    instance_suffix="body_tex_stripe",
                )
                second_name = mock_create_mat.call_args.kwargs["name"]

                assert first_name == second_name
                assert mock_builder.call_count == 2


class TestApplyZoneTexturePatternOverridesStripes:
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
            "feat_body_texture_stripe_direction": "y",
            "feat_body_texture_stripe_rot_pitch": 10.0,
            "feat_body_texture_stripe_rot_yaw": -5.0,
            "features": {"body": {"hex": "cccccc", "finish": "default"}},
        }

        with patch(
            "src.materials.material_stripes_zone.material_for_stripes_zone"
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
                assert kw.get("stripe_preset") == "doplar"
                assert kw.get("rot_pitch_deg") == pytest.approx(10.0)
                assert kw.get("rot_yaw_deg") == pytest.approx(-5.0)

    @patch("src.materials.material_system.bpy")
    def test_stripes_width_clamped_in_apply_overrides(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_system import apply_zone_texture_pattern_overrides

        mock_mat = MagicMock()
        slot_materials = {"body": mock_mat}
        build_options = {
            "feat_body_texture_mode": "stripes",
            "feat_body_texture_stripe_color": "ff0000",
            "feat_body_texture_stripe_bg_color": "ffffff",
            "feat_body_texture_stripe_width": -2.0,
            "features": {"body": {"hex": "cccccc", "finish": "default"}},
        }

        with patch("src.materials.material_stripes_zone.material_for_stripes_zone") as mock_factory:
            mock_factory.return_value = mock_mat
            with patch("src.materials.material_system._palette_base_name_from_material"):
                apply_zone_texture_pattern_overrides(slot_materials, build_options)
                assert mock_factory.call_args.kwargs["stripe_width"] == pytest.approx(0.05)

    @patch("src.materials.material_system.bpy")
    def test_stripes_rotation_nan_inf_are_sanitized(self, mock_bpy) -> None:  # noqa: ARG002
        from src.materials.material_system import apply_zone_texture_pattern_overrides

        mock_mat = MagicMock()
        slot_materials = {"body": mock_mat}
        build_options = {
            "feat_body_texture_mode": "stripes",
            "feat_body_texture_stripe_color": "ff0000",
            "feat_body_texture_stripe_bg_color": "ffffff",
            "feat_body_texture_stripe_width": 0.3,
            "feat_body_texture_stripe_rot_pitch": float("nan"),
            "feat_body_texture_stripe_rot_yaw": float("inf"),
            "features": {"body": {"hex": "cccccc", "finish": "default"}},
        }

        with patch("src.materials.material_stripes_zone.material_for_stripes_zone") as mock_factory:
            mock_factory.return_value = mock_mat
            with patch("src.materials.material_system._palette_base_name_from_material"):
                # CHECKPOINT: conservative assumption is NaN/Inf rotations are coerced to 0.0.
                apply_zone_texture_pattern_overrides(slot_materials, build_options)
                kw = mock_factory.call_args.kwargs
                assert kw["rot_pitch_deg"] == pytest.approx(0.0)
                assert kw["rot_yaw_deg"] == pytest.approx(0.0)
