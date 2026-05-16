"""Unit coverage for pattern_composite + spot_overlay helpers (diff-cover)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import src.materials.pattern_composite as pc
import src.materials.spot_overlay as so


def test_median_max_rgb_empty_and_nonempty() -> None:
    assert pc._median_max_rgb([]) == pc.DEFAULT_DARK_THRESHOLD
    pat = [0.1, 0.2, 0.3, 1.0, 0.9, 0.9, 0.9, 1.0]
    assert pc._median_max_rgb(pat) > 0.0


def test_smoothstep_degenerate_and_normal() -> None:
    assert pc._smoothstep(1.0, 1.0, 1.5) == 1.0
    assert pc._smoothstep(1.0, 1.0, 0.5) == 0.0
    assert 0.0 <= pc._smoothstep(0.0, 1.0, 0.25) <= 1.0


def test_clamped_feather_bounds() -> None:
    assert pc._clamped_feather_for_threshold(0.5, 0.5) > 0.0


def test_mask_blend_variants() -> None:
    assert pc._mask_blend_t_white_holes(0.99, 0.99, 0.99, 0.05) >= 0.0
    assert pc._mask_blend_t_dark_spots(0.5, 0.42, 0.05) >= 0.0
    assert pc._mask_blend_t_white_hard(0.99) == 1.0
    assert pc._mask_blend_t_dark_hard(0.5, 0.4) in (0.0, 1.0)


def test_scalar_mask_field_modes() -> None:
    pat = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    w = h = 1
    wh = pc._scalar_mask_field(pat, w, h, "white_holes")
    ds = pc._scalar_mask_field(pat, w, h, "dark_spots")
    assert len(wh) == 1 and len(ds) == 1


def test_box_blur_radius_zero_returns_copy() -> None:
    field = [1.0, 0.0, 0.0, 0.0]
    assert pc._box_blur_separable(field, 1, 1, 0) == field


def test_find_principled_bsdf_by_bl_idname() -> None:
    n = MagicMock()
    n.type = "OTHER"
    n.bl_idname = "ShaderNodeBsdfPrincipled"
    assert so._find_principled_bsdf([n]) is n


def test_principled_base_color_socket_color_fallback() -> None:
    bsdf = MagicMock()
    bc = MagicMock()
    bsdf.inputs = {"Color": bc}
    assert so._principled_base_color_socket(bsdf) is bc


def test_spot_mask_soft_edges_from_material_branches() -> None:
    m: dict[str, object] = {}
    assert so._spot_mask_soft_edges_from_material(m) is True
    m["blobert_spot_plate_mask_soft_edges"] = False
    assert so._spot_mask_soft_edges_from_material(m) is False
    m["blobert_spot_plate_mask_soft_edges"] = 0
    assert so._spot_mask_soft_edges_from_material(m) is False
    m["blobert_spot_plate_mask_soft_edges"] = "x"
    assert so._spot_mask_soft_edges_from_material(m) is True


def test_spot_mask_params_invalid_float_threshold() -> None:
    m = {
        "blobert_spot_plate_mask_mode": "auto",
        "blobert_spot_plate_dark_threshold": "not_a_float",
    }
    mode, thr, soft = so._spot_mask_params(m)
    assert mode == "auto"
    assert thr == so.DEFAULT_DARK_THRESHOLD


def test_resolve_pattern_sources_prefers_tagged_path(tmp_path: Path) -> None:
    png = tmp_path / "p.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 40)
    m = MagicMock()
    m.__contains__ = lambda self, k: True  # noqa: ARG005
    m.__getitem__ = MagicMock(
        side_effect=lambda k: "nm" if "name" in k else str(png),
    )
    path, _img = so._resolve_pattern_sources(m, None)
    assert path == png


def test_combine_pattern_returns_none_when_missing_files(tmp_path: Path) -> None:
    missing = tmp_path / "nope.png"
    assert pc.combine_pattern_over_base_image(missing, tmp_path / "also.png", "x") is None


def test_pattern_mask_stats_counts_soft_edges() -> None:
    pat = [0.1, 0.1, 0.1, 1.0, 0.95, 0.95, 0.95, 1.0]
    sig = [0.1, 0.95]
    b, ink, mr, mg, mb = pc._pattern_mask_stats(
        pat,
        2,
        1,
        effective_mode="white_holes",
        dark_threshold=0.42,
        mask_feather=0.05,
        mask_soft_edges=True,
        sig_smooth=sig,
    )
    assert b + ink == 2
    assert mr >= 0.0


def test_blend_pattern_and_base_pixels_smoke() -> None:
    pat = [1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    bas = [0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    sig = [0.2, 0.8]
    out = pc._blend_pattern_and_base_pixels(
        pat=pat,
        bas=bas,
        pw=2,
        ph=1,
        bw=2,
        bh=1,
        sig_smooth=sig,
        effective_mode="dark_spots",
        eff_dt=0.5,
        mask_soft_edges=False,
        fe_used=0.0,
    )
    assert len(out) == 8
