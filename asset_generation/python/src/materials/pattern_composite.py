"""Shared pattern/image compositing helpers for material pipelines."""

from __future__ import annotations

from pathlib import Path

import bpy

from src.materials.spot_plate_mask import (
    DEFAULT_DARK_THRESHOLD,
    DEFAULT_MASK_BOX_BLUR_RADIUS,
    DEFAULT_MASK_FEATHER,
    NEAR_WHITE_MIN,
    resolve_spot_plate_composite_mode,
)
from src.materials.spots_composite_debug import (
    log_spots_composite,
    spots_composite_debug_enabled,
)


def _median_max_rgb(pat: list[float]) -> float:
    """Median of per-pixel max(linear R,G,B) for adaptive ``dark_spots`` threshold."""
    if not pat:
        return DEFAULT_DARK_THRESHOLD
    maxes: list[float] = []
    i = 0
    while i < len(pat):
        maxes.append(max(pat[i], pat[i + 1], pat[i + 2]))
        i += 4
    maxes.sort()
    mid = len(maxes) // 2
    return maxes[mid] if maxes else DEFAULT_DARK_THRESHOLD


def _smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Hermite 0..1 ramp; outside [edge0,edge1] clamps to 0 or 1."""
    if edge1 <= edge0:
        return 1.0 if x >= edge0 else 0.0
    t = (x - edge0) / (edge1 - edge0)
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _clamped_feather_for_threshold(dt: float, feather: float) -> float:
    """Keep soft band inside (0,1) so smoothstep edges stay valid."""
    return max(0.02, min(feather, dt - 0.02, 0.98 - dt, 0.18))


def _mask_blend_t_white_scalar(min_rgb: float, feather: float) -> float:
    """``min_rgb`` may come from a spatially blurred mask signal."""
    fe = _clamped_feather_for_threshold(NEAR_WHITE_MIN, feather)
    lo = NEAR_WHITE_MIN - fe
    hi = NEAR_WHITE_MIN + fe
    return _smoothstep(lo, hi, min_rgb)


def _mask_blend_t_white_holes(pr: float, pg: float, pb: float, feather: float) -> float:
    """1 = full base underlay, 0 = full spot ink (near-white reveals base)."""
    return _mask_blend_t_white_scalar(min(pr, pg, pb), feather)


def _mask_blend_t_dark_spots(mx: float, dt: float, feather: float) -> float:
    """1 = base shows through (lighter plate), 0 = spot ink (darker)."""
    fe = _clamped_feather_for_threshold(dt, feather)
    lo = dt - fe
    hi = dt + fe
    return _smoothstep(lo, hi, mx)


def _mask_blend_t_white_hard(min_rgb: float) -> float:
    """1 = base underlay (hole), 0 = spot ink — binary edge at ``NEAR_WHITE_MIN``."""
    return 1.0 if min_rgb >= NEAR_WHITE_MIN else 0.0


def _mask_blend_t_dark_hard(mx: float, dt: float) -> float:
    """1 = base shows through (lighter), 0 = ink — binary edge at ``dt``."""
    return 1.0 if mx >= dt else 0.0


def _scalar_mask_field(pat: list[float], pw: int, ph: int, effective_mode: str) -> list[float]:
    """One linear value per pixel: min RGB (white holes) or max RGB (dark spots)."""
    n = pw * ph
    sig: list[float] = [0.0] * n
    idx = 0
    i = 0
    while idx < n:
        pr, pg, pb = pat[i], pat[i + 1], pat[i + 2]
        sig[idx] = min(pr, pg, pb) if effective_mode == "white_holes" else max(pr, pg, pb)
        idx += 1
        i += 4
    return sig


def _box_blur_separable(field: list[float], w: int, h: int, radius: int) -> list[float]:
    """Cheap spatial smooth — reduces single-pixel mask flicker / grain."""
    if radius <= 0 or len(field) != w * h:
        return field[:]
    span = float(2 * radius + 1)
    tmp = [0.0] * len(field)
    out = [0.0] * len(field)
    for y in range(h):
        row = y * w
        for x in range(w):
            acc = 0.0
            for dx in range(-radius, radius + 1):
                xx = min(w - 1, max(0, x + dx))
                acc += field[row + xx]
            tmp[row + x] = acc / span
    for y in range(h):
        for x in range(w):
            acc = 0.0
            for dy in range(-radius, radius + 1):
                yy = min(h - 1, max(0, y + dy))
                acc += tmp[yy * w + x]
            out[y * w + x] = acc / span
    return out


def _pattern_mask_stats(
    pat: list[float],
    pw: int,
    ph: int,
    *,
    effective_mode: str,
    dark_threshold: float,
    mask_feather: float,
    mask_soft_edges: bool,
    sig_smooth: list[float],
) -> tuple[int, int, float, float, float]:
    """Counts for debug: pixels where blend factor t > 0.5 favor base (matches composite)."""
    base_show = 0
    ink = 0
    sr = sg = sb = 0.0
    n = pw * ph
    idx = 0
    i = 0
    while idx < n:
        pr, pg, pb = pat[i], pat[i + 1], pat[i + 2]
        sr += pr
        sg += pg
        sb += pb
        sv = sig_smooth[idx]
        if mask_soft_edges:
            if effective_mode == "white_holes":
                t = _mask_blend_t_white_scalar(sv, mask_feather)
            else:
                t = _mask_blend_t_dark_spots(sv, dark_threshold, mask_feather)
        elif effective_mode == "white_holes":
            t = _mask_blend_t_white_hard(sv)
        else:
            t = _mask_blend_t_dark_hard(sv, dark_threshold)
        if t > 0.5:
            base_show += 1
        else:
            ink += 1
        idx += 1
        i += 4
    if n > 0:
        return base_show, ink, sr / n, sg / n, sb / n
    return 0, 0, 0.0, 0.0, 0.0


def _blend_pattern_and_base_pixels(
    *,
    pat: list[float],
    bas: list[float],
    pw: int,
    ph: int,
    bw: int,
    bh: int,
    sig_smooth: list[float],
    effective_mode: str,
    eff_dt: float,
    mask_soft_edges: bool,
    fe_used: float,
) -> list[float]:
    """Composite pattern × base into linear RGBA buffer ``pat`` dimensions."""
    out = [0.0] * (pw * ph * 4)
    for y in range(ph):
        for x in range(pw):
            pi = (y * pw + x) * 4
            idx_px = y * pw + x
            by = min(bh - 1, int((y * bh) / ph))
            bx = min(bw - 1, int((x * bw) / pw))
            bi = (by * bw + bx) * 4
            pr, pg, pb, pa = pat[pi], pat[pi + 1], pat[pi + 2], pat[pi + 3]
            br, bg, bb, ba = bas[bi], bas[bi + 1], bas[bi + 2], bas[bi + 3]
            sv = sig_smooth[idx_px]
            if mask_soft_edges:
                if effective_mode == "white_holes":
                    t = _mask_blend_t_white_scalar(sv, fe_used)
                else:
                    t = _mask_blend_t_dark_spots(sv, eff_dt, fe_used)
            elif effective_mode == "white_holes":
                t = _mask_blend_t_white_hard(sv)
            else:
                t = _mask_blend_t_dark_hard(sv, eff_dt)
            om = 1.0 - t
            out[pi] = t * br + om * pr
            out[pi + 1] = t * bg + om * pg
            out[pi + 2] = t * bb + om * pb
            out[pi + 3] = t * ba + om * pa
    return out


def _log_combine_pattern_over_base_image_debug(
    *,
    pattern_path: Path,
    base_path: Path,
    pw: int,
    ph: int,
    bw: int,
    bh: int,
    mask_mode: str,
    effective_mode: str,
    policy_reason: str,
    eff_dt: float,
    mask_soft_edges: bool,
    fe_used: float,
    r_blur: int,
    bcnt: int,
    fcnt: int,
    mr: float,
    mg: float,
    mb: float,
) -> None:
    tot = bcnt + fcnt
    pct = (100.0 * bcnt / tot) if tot else 0.0
    if mask_soft_edges:
        if effective_mode == "white_holes":
            rule = f"soft white-hole blend around min(R,G,B)≈{NEAR_WHITE_MIN}"
        else:
            rule = f"soft dark-spots blend around max(R,G,B)≈{eff_dt:.3f}"
        blur_note = "(spatial blur on mask signal before smoothstep)"
    else:
        if effective_mode == "white_holes":
            rule = f"hard white-hole cut at min(R,G,B)≈{NEAR_WHITE_MIN}"
        else:
            rule = f"hard dark-spots cut at max(R,G,B)≈{eff_dt:.3f}"
        blur_note = "(no mask blur; binary blend)"
    log_spots_composite(
        "combine_pattern_over_base_image: "
        f"pattern={pattern_path.name} ({pw}x{ph}), base={base_path.name} ({bw}x{bh}). "
        f"mask_mode={mask_mode!r} → effective={effective_mode!r} ({policy_reason}). "
        f"{rule}; mask_soft_edges={mask_soft_edges}; mask_feather={fe_used:.3f}; "
        f"mask_box_blur_radius={r_blur} {blur_note}. "
        f"base>50%≈{bcnt}/{tot} px ({pct:.2f}%). "
        f"Mean pattern RGB=({mr:.3f},{mg:.3f},{mb:.3f})."
    )


def combine_pattern_over_base_image(
    pattern_path: Path | None,
    base_path: Path | str,
    out_name: str,
    *,
    mask_mode: str = "auto",
    dark_threshold: float = DEFAULT_DARK_THRESHOLD,
    mask_feather: float = DEFAULT_MASK_FEATHER,
    mask_box_blur_radius: int = DEFAULT_MASK_BOX_BLUR_RADIUS,
    mask_soft_edges: bool = True,
) -> bpy.types.Image | None:
    """Create a concrete combined PNG from pattern and base image.

    This runs in Blender's Python runtime (no external Pillow dependency).
    Default ``mask_mode`` is ``auto``: uses classic near-white holes when enough pixels qualify;
    otherwise uses ``dark_spots`` (lighter texels reveal the base — suited to dark animal prints).

    Set ``mask_soft_edges=False`` for a binary mask (no spatial blur on the mask signal and no
    smoothstep feather). Build option: ``feat_<zone>_texture_spot_plate_mask_soft_edges``.

    See ``spot_plate_mask.py``.
    """
    try:
        if pattern_path is None:
            return None
        base_path = Path(str(base_path))
        if not pattern_path.exists() or not base_path.exists():
            return None

        pat_img = bpy.data.images.load(filepath=str(pattern_path), check_existing=True)
        base_img = bpy.data.images.load(filepath=str(base_path), check_existing=True)
        pw, ph = int(pat_img.size[0]), int(pat_img.size[1])
        bw, bh = int(base_img.size[0]), int(base_img.size[1])
        if pw <= 0 or ph <= 0 or bw <= 0 or bh <= 0:
            return None

        pat = [0.0] * (pw * ph * 4)
        bas = [0.0] * (bw * bh * 4)
        pat_img.pixels.foreach_get(pat)
        base_img.pixels.foreach_get(bas)

        effective_mode, eff_dt, policy_reason = resolve_spot_plate_composite_mode(
            mask_mode,
            pat,
            pw,
            ph,
            dark_threshold,
        )
        raw_mode = (mask_mode or "auto").strip().lower()
        if effective_mode == "dark_spots" and raw_mode == "auto":
            med = _median_max_rgb(pat)
            eff_dt = max(0.05, min(0.95, med))
            policy_reason = f"{policy_reason}; auto_dark_threshold=median_max_rgb={med:.4f}"

        if mask_soft_edges:
            fe_used = max(0.02, min(mask_feather, 0.25))
            r_blur = max(0, min(int(mask_box_blur_radius), 12))
        else:
            fe_used = 0.0
            r_blur = 0
        sig_raw = _scalar_mask_field(pat, pw, ph, effective_mode)
        sig_smooth = _box_blur_separable(sig_raw, pw, ph, r_blur)

        if spots_composite_debug_enabled():
            bcnt, fcnt, mr, mg, mb = _pattern_mask_stats(
                pat,
                pw,
                ph,
                effective_mode=effective_mode,
                dark_threshold=eff_dt,
                mask_feather=fe_used,
                mask_soft_edges=mask_soft_edges,
                sig_smooth=sig_smooth,
            )
            _log_combine_pattern_over_base_image_debug(
                pattern_path=pattern_path,
                base_path=base_path,
                pw=pw,
                ph=ph,
                bw=bw,
                bh=bh,
                mask_mode=mask_mode,
                effective_mode=effective_mode,
                policy_reason=policy_reason,
                eff_dt=eff_dt,
                mask_soft_edges=mask_soft_edges,
                fe_used=fe_used,
                r_blur=r_blur,
                bcnt=bcnt,
                fcnt=fcnt,
                mr=mr,
                mg=mg,
                mb=mb,
            )

        out = _blend_pattern_and_base_pixels(
            pat=pat,
            bas=bas,
            pw=pw,
            ph=ph,
            bw=bw,
            bh=bh,
            sig_smooth=sig_smooth,
            effective_mode=effective_mode,
            eff_dt=eff_dt,
            mask_soft_edges=mask_soft_edges,
            fe_used=fe_used,
        )

        spots_dir = Path(__file__).parent.parent.parent / "animated_exports" / "spots"
        spots_dir.mkdir(parents=True, exist_ok=True)
        out_path = spots_dir / f"{out_name}.png"

        img = bpy.data.images.new(name=out_name, width=pw, height=ph, alpha=True)
        img.pixels.foreach_set(out)
        img.filepath_raw = str(out_path)
        img.file_format = "PNG"
        img.save()
        img.name = out_name
        img.pack()
        return img
    except Exception as e:
        log_spots_composite(f"combine_pattern_over_base_image failed: {type(e).__name__}: {e}")
        return None
