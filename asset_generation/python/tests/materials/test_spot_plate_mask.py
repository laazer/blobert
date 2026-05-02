"""Tests for spot plate compositing mask policy (no Blender)."""

from __future__ import annotations

from src.materials.spot_plate_mask import (
    AUTO_WHITE_FRAC,
    DEFAULT_DARK_THRESHOLD,
    NEAR_WHITE_MIN,
    fraction_near_white_pixels,
    resolve_spot_plate_composite_mode,
)


def _solid_pat(rgb: tuple[float, float, float], n: int) -> tuple[list[float], int, int]:
    w = h = int(n**0.5)
    if w * h != n:
        w, h = n, 1
    buf: list[float] = []
    r, g, b = rgb
    for _ in range(w * h):
        buf.extend([r, g, b, 1.0])
    return buf, w, h


def test_fraction_near_white_all_dark() -> None:
    pat, pw, ph = _solid_pat((0.1, 0.12, 0.11), 16)
    assert fraction_near_white_pixels(pat, pw, ph) == 0.0


def test_fraction_near_white_paper_white() -> None:
    pat, pw, ph = _solid_pat((NEAR_WHITE_MIN, NEAR_WHITE_MIN, NEAR_WHITE_MIN), 4)
    assert fraction_near_white_pixels(pat, pw, ph) == 1.0


def test_auto_picks_dark_spots_when_almost_no_white() -> None:
    pat, pw, ph = _solid_pat((0.13, 0.15, 0.17), 64)
    mode, dt, reason = resolve_spot_plate_composite_mode("auto", pat, pw, ph, DEFAULT_DARK_THRESHOLD)
    assert mode == "dark_spots"
    assert dt == DEFAULT_DARK_THRESHOLD
    assert "white_frac" in reason


def test_auto_picks_white_holes_when_enough_white() -> None:
    # half pixels white, half dark → white_frac 0.5
    pat: list[float] = []
    for _ in range(8):
        pat.extend([0.1, 0.1, 0.1, 1.0])
    for _ in range(8):
        pat.extend([NEAR_WHITE_MIN, NEAR_WHITE_MIN, NEAR_WHITE_MIN, 1.0])
    pw, ph = 4, 4
    wf = fraction_near_white_pixels(pat, pw, ph)
    assert wf >= AUTO_WHITE_FRAC
    mode, _, reason = resolve_spot_plate_composite_mode("auto", pat, pw, ph, DEFAULT_DARK_THRESHOLD)
    assert mode == "white_holes"
    assert "white_frac" in reason


def test_explicit_white_holes() -> None:
    pat, pw, ph = _solid_pat((0.1, 0.1, 0.1), 4)
    mode, _, _ = resolve_spot_plate_composite_mode("white_holes", pat, pw, ph, 0.5)
    assert mode == "white_holes"


def test_explicit_dark_spots() -> None:
    pat, pw, ph = _solid_pat((NEAR_WHITE_MIN, NEAR_WHITE_MIN, NEAR_WHITE_MIN), 4)
    mode, dt, _ = resolve_spot_plate_composite_mode("dark_spots", pat, pw, ph, 0.35)
    assert mode == "dark_spots"
    assert dt == 0.35


def test_dark_spots_soft_blend_is_continuous() -> None:
    """Soft mask uses smoothstep — mid-threshold pixels mix pattern and base (less speckle)."""
    from src.materials.pattern_composite import _mask_blend_t_dark_spots

    t_dark = _mask_blend_t_dark_spots(0.1, 0.42, 0.09)
    t_light = _mask_blend_t_dark_spots(0.85, 0.42, 0.09)
    assert t_dark < 0.2
    assert t_light > 0.8


def test_zone_texture_options_default_mask_from_build() -> None:
    from src.materials.material_types import ZoneTextureOptions, feature_zone_map

    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features=feature_zone_map(None),
        build_options={"feat_body_texture_mode": "spots"},
    )
    assert opts.spot_plate_mask_mode == "auto"
    assert opts.spot_plate_dark_threshold == DEFAULT_DARK_THRESHOLD
    assert opts.spot_plate_mask_soft_edges is True


def test_zone_texture_options_spot_plate_mask_soft_edges_false() -> None:
    from src.materials.material_types import ZoneTextureOptions, feature_zone_map

    opts = ZoneTextureOptions.from_build_options(
        zone="body",
        zone_features=feature_zone_map(None),
        build_options={
            "feat_body_texture_mode": "spots",
            "feat_body_texture_spot_plate_mask_soft_edges": False,
        },
    )
    assert opts.spot_plate_mask_soft_edges is False


def test_hard_dark_spots_binary_edges() -> None:
    from src.materials.pattern_composite import _mask_blend_t_dark_hard

    assert _mask_blend_t_dark_hard(0.1, 0.42) == 0.0
    assert _mask_blend_t_dark_hard(0.85, 0.42) == 1.0


def test_hard_white_holes_binary_edges() -> None:
    from src.materials.pattern_composite import _mask_blend_t_white_hard

    assert _mask_blend_t_white_hard(NEAR_WHITE_MIN - 0.05) == 0.0
    assert _mask_blend_t_white_hard(NEAR_WHITE_MIN) == 1.0
