"""Branch coverage for spots_zone_pipeline background image dimension resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.materials.material_types import feature_zone_map
from src.materials.spots_zone_pipeline import apply_spots_zone_pattern


def _body_zone_settings(build_options: dict) -> tuple[dict, object]:
    feats = build_options.get("features")
    zf = feature_zone_map(feats if isinstance(feats, dict) else None)
    from src.materials.material_types import ZoneTextureOptions

    settings = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features=zf,
        build_options=build_options,
    )
    return zf, settings


def test_apply_spots_zone_pattern_background_image_dims_error_falls_back_to_128() -> None:
    build_options = {
        "features": {"body": {"finish": "default", "hex": "ffffff", "parts": {}}},
        "feat_body_texture_mode": "spots",
        "feat_body_texture_spot_density": 1.0,
        "feat_body_texture_background_mode": "image",
        "feat_body_texture_background_image_id": "bg_tex",
        "feat_body_texture_pattern_mode": "single",
        "feat_body_texture_pattern_hex": "000000",
    }
    zf_map, settings = _body_zone_settings(build_options)

    with (
        patch(
            "src.materials.spots_zone_pipeline.get_texture_asset_filepath",
            return_value=Path("/nope/missing_asset.png"),
        ),
        patch(
            "src.materials.spots_zone_pipeline.texture_sample_pixel_dimensions",
            side_effect=OSError("no read"),
        ),
        patch("src.materials.material_system.material_for_spots_zone", return_value=MagicMock(name="spots_mat")) as mspot,
        patch("builtins.print") as pr,
    ):
        apply_spots_zone_pattern(
            base_palette_name="Organic_Brown",
            settings=settings,
            zone="body",
            build_options=build_options,
            zone_feature=zf_map.get("body"),
        )

    kw = mspot.call_args.kwargs
    assert kw.get("spot_texture_width") == 128
    assert kw.get("spot_texture_height") == 128
    assert any("blobert:spots-pipeline" in str(c) for c in pr.call_args_list)
