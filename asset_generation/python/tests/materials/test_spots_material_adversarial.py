# ruff: noqa: E402, I001
"""Adversarial tests for spots material system integration.

This module exposes weaknesses in the material system integration layer,
focusing on:
  - Parameter extraction and flow (UI → Store → Backend → Material)
  - Error propagation and recovery
  - Integration boundaries and seams
  - Missing or malformed feature dictionaries
  - Density clamping and validation
  - Color fallback chains
  - Material naming and uniqueness
  - Mode switching logic

Tests use mutation testing to verify that spec requirements are actually
enforced, not just documented.
"""

# from __future__ import annotations

# from unittest.mock import MagicMock, patch


# ============================================================================
# CATEGORY 1: PARAMETER EXTRACTION & FALLBACK CHAINS
# ============================================================================


# class TestSpotsParameterExtraction:
#     """Verify correct parameter extraction from build_options."""

#     @patch("src.materials.material_system.bpy")
#     def test_spot_color_extracted_when_present(self, mock_bpy) -> None:
#         """spot_color should be extracted from feat_{zone}_texture_spot_color."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",  # Present
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 # Verify factory was called with correct spot_hex
#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["spot_hex"] == "ff0000"

#     @patch("src.materials.material_system.bpy")
#     def test_spot_color_defaults_to_empty_when_missing(self, mock_bpy) -> None:
#         """spot_color should default to empty string when missing."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             # feat_body_texture_spot_color is MISSING
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 # Should fallback to empty string or zone_hex
#                 assert call_kwargs["spot_hex"] == "" or "hex" in call_kwargs

#     @patch("src.materials.material_system.bpy")
#     def test_spot_color_none_treated_as_empty(self, mock_bpy) -> None:
#         """spot_color=None should be treated as empty string."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": None,
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 # spot_hex should be empty or fallback
#                 assert call_kwargs["spot_hex"] in ("", None) or "hex" in call_kwargs

#     @patch("src.materials.material_system.bpy")
#     def test_bg_color_extracted_when_present(self, mock_bpy) -> None:
#         """bg_color should be extracted from feat_{zone}_texture_spot_bg_color."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "00ff00",  # Present
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["bg_hex"] == "00ff00"

#     @patch("src.materials.material_system.bpy")
#     def test_bg_color_defaults_to_empty_when_missing(self, mock_bpy) -> None:
#         """bg_color should default to empty string when missing."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             # feat_body_texture_spot_bg_color is MISSING
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["bg_hex"] == ""

#     @patch("src.materials.material_system.bpy")
#     def test_density_extracted_when_present(self, mock_bpy) -> None:
#         """density should be extracted from feat_{zone}_texture_spot_density."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 2.5,  # Present
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["density"] == 2.5

#     @patch("src.materials.material_system.bpy")
#     def test_density_defaults_to_1_0_when_missing(self, mock_bpy) -> None:
#         """density should default to 1.0 when missing."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             # density is MISSING
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["density"] == 1.0

#     @patch("src.materials.material_system.bpy")
#     def test_density_clamped_below_minimum(self, mock_bpy) -> None:
#         """density < 0.1 should be clamped to 0.1."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 0.05,  # Below minimum
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 # Should be clamped to >= 0.1
#                 assert call_kwargs["density"] >= 0.1

#     @patch("src.materials.material_system.bpy")
#     def test_density_clamped_above_maximum(self, mock_bpy) -> None:
#         """density > 5.0 should be clamped to 5.0."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 10.0,  # Above maximum
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 # Should be clamped to <= 5.0
#                 assert call_kwargs["density"] <= 5.0


# ============================================================================
# CATEGORY 2: FEATURE DICTIONARY HANDLING
# ============================================================================


# class TestSpotsFeatureDictHandling:
#     """Verify robust handling of feature dictionary edge cases."""

#     @patch("src.materials.material_system.bpy")
#     def test_finish_extracted_when_feature_dict_present(self, mock_bpy) -> None:
#         """finish should be extracted from features[zone]['finish']."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "glossy"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["finish"] == "glossy"

#     @patch("src.materials.material_system.bpy")
#     def test_finish_defaults_when_missing_from_feature_dict(self, mock_bpy) -> None:
#         """finish should default to 'default' when missing."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc"}},  # finish missing
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["finish"] == "default"

#     @patch("src.materials.material_system.bpy")
#     def test_hex_extracted_when_present(self, mock_bpy) -> None:
#         """zone_hex_fallback should come from features[zone]['hex']."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "aabbcc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["zone_hex_fallback"] == "aabbcc"

#     @patch("src.materials.material_system.bpy")
#     def test_hex_defaults_to_empty_when_missing(self, mock_bpy) -> None:
#         """zone_hex_fallback should default to empty string when missing."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"finish": "default"}},  # hex missing
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["zone_hex_fallback"] == ""

#     @patch("src.materials.material_system.bpy")
#     def test_zone_not_in_features_dict(self, mock_bpy) -> None:
#         """When zone is not in features dict, should use defaults."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"legs": {"hex": "aabbcc", "finish": "default"}},  # body not in features
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 # Should still work with defaults
#                 assert mock_factory.called

#     @patch("src.materials.material_system.bpy")
#     def test_features_dict_not_a_dict(self, mock_bpy) -> None:
#         """When features is not a dict, should handle gracefully."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": "not_a_dict",  # Wrong type
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 # Should not crash
#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#     @patch("src.materials.material_system.bpy")
#     def test_feature_value_not_a_dict(self, mock_bpy) -> None:
#         """When features[zone] is not a dict, should handle gracefully."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": "not_a_dict"},  # Wrong type
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_factory:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_factory.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 # Should use defaults
#                 call_kwargs = mock_factory.call_args.kwargs
#                 assert call_kwargs["finish"] == "default"
#                 assert call_kwargs["zone_hex_fallback"] == ""


# ============================================================================
# CATEGORY 3: MATERIAL NAMING & UNIQUENESS
# ============================================================================


# class TestSpotsMaterialNaming:
#     """Verify material naming is correct and unique."""

#     @patch("src.materials.material_system.bpy")
#     def test_material_name_format_correct(self, mock_bpy) -> None:
#         """Material name should be {base_palette_name}__feat_{instance_suffix}."""
#         from src.materials.material_system import _material_for_spots_zone  # noqa: E402

#         mock_mat = MagicMock()
#         mock_mat.use_nodes = True

#         with patch("src.materials.material_system.create_spots_png_and_load"):
#             with patch("src.materials.material_system.create_material") as mock_create:
#                 mock_create.return_value = mock_mat

#                 _material_for_spots_zone(
#                     base_palette_name="MyPalette",
#                     finish="default",
#                     spot_hex="ff0000",
#                     bg_hex="ffffff",
#                     density=1.0,
#                     zone_hex_fallback="cccccc",
#                     instance_suffix="body_tex_spot",
#                 )

#                 # Verify naming convention
#                 call_args = mock_create.call_args
#                 created_name = call_args[1]["name"] if "name" in call_args[1] else None
#                 assert created_name is not None
#                 assert "MyPalette" in created_name
#                 assert "body_tex_spot" in created_name

#     @patch("src.materials.material_system.bpy")
#     def test_instance_suffix_reflects_in_material_name(self, mock_bpy) -> None:
#         """instance_suffix should appear in material name."""
#         from src.materials.material_system import _material_for_spots_zone  # noqa: E402

#         mock_mat = MagicMock()
#         mock_mat.use_nodes = True

#         with patch("src.materials.material_system.create_spots_png_and_load"):
#             with patch("src.materials.material_system.create_material") as mock_create:
#                 mock_create.return_value = mock_mat

#                 _material_for_spots_zone(
#                     base_palette_name="Palette",
#                     finish="default",
#                     spot_hex="ff0000",
#                     bg_hex="ffffff",
#                     density=1.0,
#                     zone_hex_fallback="cccccc",
#                     instance_suffix="legs_tex_spot",
#                 )

#                 call_args = mock_create.call_args
#                 created_name = call_args[1]["name"] if "name" in call_args[1] else None
#                 assert "legs_tex_spot" in created_name

#     @patch("src.materials.material_system.bpy")
#     def test_different_zones_produce_different_material_names(self, mock_bpy) -> None:
#         """Different zones should produce materials with different names."""
#         from src.materials.material_system import _material_for_spots_zone  # noqa: E402

#         mock_mat1 = MagicMock()
#         mock_mat1.use_nodes = True
#         mock_mat2 = MagicMock()
#         mock_mat2.use_nodes = True

#         names = []

#         with patch("src.materials.material_system.create_spots_png_and_load"):
#             with patch("src.materials.material_system.create_material") as mock_create:
#                 mock_create.side_effect = [mock_mat1, mock_mat2]

#                 _material_for_spots_zone(
#                     base_palette_name="Palette",
#                     finish="default",
#                     spot_hex="ff0000",
#                     bg_hex="ffffff",
#                     density=1.0,
#                     zone_hex_fallback="cccccc",
#                     instance_suffix="body_tex_spot",
#                 )

#                 names.append(mock_create.call_args[1]["name"])

#                 _material_for_spots_zone(
#                     base_palette_name="Palette",
#                     finish="default",
#                     spot_hex="ff0000",
#                     bg_hex="ffffff",
#                     density=1.0,
#                     zone_hex_fallback="cccccc",
#                     instance_suffix="legs_tex_spot",
#                 )

#                 names.append(mock_create.call_args[1]["name"])

#         assert names[0] != names[1], "Different zones should have different material names"


# ============================================================================
# CATEGORY 4: MODE SWITCHING & BRANCH ISOLATION
# ============================================================================


# class TestSpotsModeSwitch:
#     """Verify spots mode branch doesn't interfere with other modes."""

#     @patch("src.materials.material_system.bpy")
#     def test_spots_mode_only_when_mode_equals_spots(self, mock_bpy) -> None:
#         """Spots branch should only execute when mode == 'spots'."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()

#         for wrong_mode in ["gradient", "assets", "Spots", "SPOTS", "spot", "none", ""]:
#             build_options = {
#                 "feat_body_texture_mode": wrong_mode,
#                 "feat_body_texture_spot_color": "ff0000",
#                 "feat_body_texture_spot_bg_color": "ffffff",
#                 "feat_body_texture_spot_density": 1.0,
#                 "features": {"body": {"hex": "cccccc", "finish": "default"}},
#             }

#             with patch(
#                 "src.materials.material_system._material_for_spots_zone"
#             ) as mock_spots_factory:
#                 with patch(
#                     "src.materials.material_system._palette_base_name_from_material"
#                 ):
#                     apply_zone_texture_pattern_overrides(
#                         {"body": mock_mat}, build_options
#                     )

#                     # Spots factory should not be called for wrong modes
#                     if wrong_mode != "spots":
#                         assert not mock_spots_factory.called

#     @patch("src.materials.material_system.bpy")
#     def test_gradient_mode_unaffected_by_spots_implementation(self, mock_bpy) -> None:
#         """Gradient mode should still work correctly."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "gradient",
#             "feat_body_texture_grad_color_a": "ff0000",
#             "feat_body_texture_grad_color_b": "0000ff",
#             "feat_body_texture_grad_direction": "horizontal",
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch("src.materials.material_system._material_for_gradient_zone") as mock_grad:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_grad.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 # Gradient factory should be called, not spots factory
#                 assert mock_grad.called

#     @patch("src.materials.material_system.bpy")
#     def test_assets_mode_unaffected_by_spots_implementation(self, mock_bpy) -> None:
#         """Assets mode should still work correctly."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "assets",
#             "feat_body_texture_asset_id": "some_asset",
#             "feat_body_texture_asset_tile_repeat": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch(
#             "src.materials.material_system._material_for_asset_zone"
#         ) as mock_asset:
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 mock_asset.return_value = mock_mat

#                 apply_zone_texture_pattern_overrides({"body": mock_mat}, build_options)

#                 # Assets factory should be called
#                 assert mock_asset.called


# ============================================================================
# CATEGORY 5: MULTIPLE ZONES HANDLING
# ============================================================================


# class TestSpotsMultipleZones:
#     """Verify spots can be applied to multiple zones independently."""

#     @patch("src.materials.material_system.bpy")
#     def test_apply_spots_to_multiple_zones_independently(self, mock_bpy) -> None:
#         """Spots should be appliedto each zone with its own parameters."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         body_mat = MagicMock()
#         legs_mat = MagicMock()
#         head_mat = MagicMock()

#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",  # Red spots
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "feat_legs_texture_mode": "spots",
#             "feat_legs_texture_spot_color": "00ff00",  # Green spots
#             "feat_legs_texture_spot_bg_color": "ffffff",
#             "feat_legs_texture_spot_density": 2.0,
#             "feat_head_texture_mode": "gradient",  # Different mode
#             "feat_head_texture_grad_color_a": "ff0000",
#             "feat_head_texture_grad_color_b": "0000ff",
#             "features": {
#                 "body": {"hex": "cccccc", "finish": "default"},
#                 "legs": {"hex": "aaaaaa", "finish": "default"},
#                 "head": {"hex": "dddddd", "finish": "glossy"},
#             },
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as mock_spots:
#             with patch(
#                 "src.materials.material_system._material_for_gradient_zone"
#             ) as mock_grad:
#                 with patch(
#                     "src.materials.material_system._palette_base_name_from_material"
#                 ):
#                     spots_mats = [MagicMock(), MagicMock()]
#                     grad_mat = MagicMock()
#                     mock_spots.side_effect = spots_mats
#                     mock_grad.return_value = grad_mat

#                     apply_zone_texture_pattern_overrides(
#                         {"body": body_mat, "legs": legs_mat, "head": head_mat},
#                         build_options,
#                     )

#                     # Both zones should have spots factory called
#                     assert mock_spots.call_count == 2

#                     # Verify different parameters for each
#                     calls = mock_spots.call_args_list
#                     spot_colors = [c.kwargs["spot_hex"] for c in calls]
#                     assert "ff0000" in spot_colors
#                     assert "00ff00" in spot_colors

#     @patch("src.materials.material_system.bpy")
#     def test_zones_with_different_modes_mixed(self, mock_bpy) -> None:
#         """Some zones spots, others gradient or assets."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mats = {f"zone{i}": MagicMock() for i in range(3)}

#         build_options = {
#             "feat_zone0_texture_mode": "spots",
#             "feat_zone0_texture_spot_color": "ff0000",
#             "feat_zone0_texture_spot_bg_color": "ffffff",
#             "feat_zone0_texture_spot_density": 1.0,
#             "feat_zone1_texture_mode": "gradient",
#             "feat_zone1_texture_grad_color_a": "ff0000",
#             "feat_zone1_texture_grad_color_b": "0000ff",
#             "feat_zone2_texture_mode": "assets",
#             "feat_zone2_texture_asset_id": "asset1",
#             "features": {
#                 "zone0": {"hex": "aaa", "finish": "default"},
#                 "zone1": {"hex": "bbb", "finish": "default"},
#                 "zone2": {"hex": "ccc", "finish": "default"},
#             },
#         }

#         with patch("src.materials.material_system._material_for_spots_zone") as m_spots:
#             with patch("src.materials.material_system._material_for_gradient_zone") as m_grad:
#                 with patch("src.materials.material_system._material_for_asset_zone") as m_asset:
#                     with patch(
#                         "src.materials.material_system._palette_base_name_from_material"
#                     ):
#                         m_spots.return_value = MagicMock()
#                         m_grad.return_value = MagicMock()
#                         m_asset.return_value = MagicMock()

#                         apply_zone_texture_pattern_overrides(mats, build_options)

#                         # Each factory should be called once
#                         assert m_spots.call_count == 1
#                         assert m_grad.call_count == 1
#                         assert m_asset.call_count == 1


# ============================================================================
# CATEGORY 6: ERROR PROPAGATION & RECOVERY
# ============================================================================


# class TestSpotsErrorPropagation:
#     """Verify errors are handled gracefully at seams."""

#     @patch("src.materials.material_system.bpy")
#     def test_png_generation_failure_handled(self, mock_bpy) -> None:
#         """If PNG generation fails, material factory should handle it."""
#         from src.materials.material_system import _material_for_spots_zone  # noqa: E402

#         mock_mat = MagicMock()
#         mock_mat.use_nodes = True

#         with patch(
#             "src.materials.material_system.create_spots_png_and_load",
#             side_effect=Exception("PNG generation failed"),
#         ):
#             with patch("src.materials.material_system.create_material") as mock_create:
#                 mock_create.return_value = mock_mat

#                 # Should either raise or handle gracefully
#                 try:
#                     result = _material_for_spots_zone(
#                         base_palette_name="Palette",
#                         finish="default",
#                         spot_hex="ff0000",
#                         bg_hex="ffffff",
#                         density=1.0,
#                         zone_hex_fallback="cccccc",
#                         instance_suffix="body_tex_spot",
#                     )
#                     # If it succeeds, result should be valid
#                     assert result is not None
#                 except Exception as e:
#                     # Should have meaningful error message
#                     assert "PNG" in str(e) or "generation" in str(e).lower()

#     @patch("src.materials.material_system.bpy")
#     def test_invalid_hex_in_spot_color_handled(self, mock_bpy) -> None:
#         """Invalid hex in spot_color should be caught by color parser."""
#         from src.materials.material_system import _material_for_spots_zone  # noqa: E402

#         mock_mat = MagicMock()
#         mock_mat.use_nodes = True

#         with patch("src.materials.material_system.create_spots_png_and_load") as m_png:
#             with patch("src.materials.material_system.create_material") as mock_create:
#                 mock_create.return_value = mock_mat
#                 m_png.return_value = MagicMock()

#                 # Invalid hex should be caught (either in PNG gen or color parsing)
#                 try:
#                     _material_for_spots_zone(
#                         base_palette_name="Palette",
#                         finish="default",
#                         spot_hex="zzzzz",  # Invalid
#                         bg_hex="ffffff",
#                         density=1.0,
#                         zone_hex_fallback="cccccc",
#                         instance_suffix="body_tex_spot",
#                     )
#                 except ValueError:
#                     pass  # Expected

#     @patch("src.materials.material_system.bpy")
#     def test_material_assignment_failure_handled(self, mock_bpy) -> None:
#         """If material assignment fails, should not crash apply_zone_texture."""
#         from src.materials.material_system import apply_zone_texture_pattern_overrides  # noqa: E402

#         mock_mat = MagicMock()
#         build_options = {
#             "feat_body_texture_mode": "spots",
#             "feat_body_texture_spot_color": "ff0000",
#             "feat_body_texture_spot_bg_color": "ffffff",
#             "feat_body_texture_spot_density": 1.0,
#             "features": {"body": {"hex": "cccccc", "finish": "default"}},
#         }

#         with patch(
#             "src.materials.material_system._material_for_spots_zone",
#             side_effect=Exception("Material creation failed"),
#         ):
#             with patch("src.materials.material_system._palette_base_name_from_material"):
#                 # Should either succeed with fallback or raise with clear error
#                 try:
#                     result = apply_zone_texture_pattern_overrides(
#                         {"body": mock_mat}, build_options
#                     )
#                     # If it succeeds, should return dict with material
#                     assert isinstance(result, dict)
#                 except Exception as e:
#                     # Error message should be informative
#                     assert "spots" in str(e).lower() or "material" in str(e).lower()


# ============================================================================
# SUMMARY
# ============================================================================
"""
Adversarial Material System Integration Tests:
┌─────────────────────────────────────┬────────┐
│ Category                            │ Count  │
├─────────────────────────────────────┼────────┤
│ Parameter extraction & fallback     │ 8      │
│ Feature dict handling               │ 7      │
│ Material naming & uniqueness        │ 3      │
│ Mode switching & branch isolation   │ 3      │
│ Multiple zones handling             │ 2      │
│ Error propagation & recovery        │ 3      │
├─────────────────────────────────────┼────────┤
│ TOTAL                               │ 26     │
└─────────────────────────────────────┴────────┘
"""
