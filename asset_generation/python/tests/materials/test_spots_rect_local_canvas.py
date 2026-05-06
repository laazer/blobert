"""Spots + image underlay: procedural raster must match atlas crop (rect-local 0–1 domain)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.materials.material_types import FeatureZoneOptions, ZoneTextureOptions
from src.materials.spots_zone_pipeline import apply_spots_zone_pattern


def test_apply_spots_zone_pattern_sizes_spot_raster_to_atlas_crop() -> None:
    """Image background + UV rect → ``material_for_spots_zone`` gets crop width×height."""
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_mode": "spots",
            "feat_body_texture_pattern_mode": "single",
            "feat_body_texture_pattern_hex": "ff0000",
            "feat_body_texture_background_mode": "image",
            "feat_body_texture_background_image_id": "demo_atlas",
            "feat_body_texture_background_image_uv_rect": '{"u0":0.25,"v0":0.25,"u1":0.75,"v1":0.75}',
            "feat_body_texture_spot_density": 1.0,
        },
    )
    fake_mat = MagicMock(name="spots_mat")
    underlay_uv = (0.25, 0.25, 0.75, 0.75)
    with (
        patch("src.materials.material_system.material_for_spots_zone", return_value=fake_mat) as msz,
        patch(
            "src.materials.material_system.overlay_base_image_on_zone_material",
            return_value=fake_mat,
        ),
        patch(
            "src.materials.material_system.resolve_texture_pattern_overlay_uv_rect",
            return_value=underlay_uv,
        ),
        patch("src.materials.material_system.resolve_zone_color_image_asset_id", return_value=""),
        patch(
            "src.materials.spots_zone_pipeline.texture_sample_pixel_dimensions",
            return_value=(120, 80),
        ) as tsd,
        patch(
            "src.materials.spots_zone_pipeline.get_texture_asset_filepath",
            return_value=str(Path("/tmp/fake_atlas.png")),
        ),
    ):
        out = apply_spots_zone_pattern(
            base_palette_name="Organic_Brown",
            settings=opts,
            zone="body",
            build_options={},
            zone_feature=zf,
        )
    assert out is fake_mat
    msz.assert_called_once()
    assert msz.call_args.kwargs["spot_texture_width"] == 120
    assert msz.call_args.kwargs["spot_texture_height"] == 80
    tsd.assert_called_once()
    assert tsd.call_args[0][1] == underlay_uv


def test_apply_spots_zone_pattern_full_atlas_uv_matches_sample_pixel_size() -> None:
    """Resolved UV is whole atlas (None → full image): spot raster matches that pixel size."""
    zf = FeatureZoneOptions.from_mapping({"finish": "default", "hex": ""})
    assert zf is not None
    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features={"body": zf},
        build_options={
            "feat_body_texture_mode": "spots",
            "feat_body_texture_pattern_mode": "single",
            "feat_body_texture_pattern_hex": "ff0000",
            "feat_body_texture_background_mode": "image",
            "feat_body_texture_background_image_id": "huge_atlas",
            "feat_body_texture_spot_density": 1.0,
        },
    )
    fake_mat = MagicMock(name="spots_mat")
    with (
        patch("src.materials.material_system.material_for_spots_zone", return_value=fake_mat) as msz,
        patch(
            "src.materials.material_system.overlay_base_image_on_zone_material",
            return_value=fake_mat,
        ),
        patch(
            "src.materials.material_system.resolve_texture_pattern_overlay_uv_rect",
            return_value=None,
        ),
        patch("src.materials.material_system.resolve_zone_color_image_asset_id", return_value=""),
        patch(
            "src.materials.spots_zone_pipeline.texture_sample_pixel_dimensions",
            return_value=(4096, 4096),
        ),
        patch(
            "src.materials.spots_zone_pipeline.get_texture_asset_filepath",
            return_value=str(Path("/tmp/huge.png")),
        ),
    ):
        apply_spots_zone_pattern(
            base_palette_name="Organic_Brown",
            settings=opts,
            zone="body",
            build_options={},
            zone_feature=zf,
        )
    assert msz.call_args.kwargs["spot_texture_width"] == 4096
    assert msz.call_args.kwargs["spot_texture_height"] == 4096
