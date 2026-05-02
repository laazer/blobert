"""Spot plate image compositing mask policy (linear RGB, Blender ``Image.pixels`` layout).

``white_holes``: show base underlay where all channels >= NEAR_WHITE_MIN (classic stencil).

``dark_spots``: treat darker texels as spot *ink* and lighter texels as *body* — show base where
max(R,G,B) >= ``dark_threshold`` (use when the plate is mostly dark with ~no paper-white pixels).

``auto``: use ``white_holes`` when at least ``AUTO_WHITE_FRAC`` of pixels qualify as near-white;
otherwise use ``dark_spots`` (fixes common “dark texture / leopard” plates that logged ~0% white holes).
"""

from __future__ import annotations

NEAR_WHITE_MIN = 0.94
AUTO_WHITE_FRAC = 0.02
DEFAULT_DARK_THRESHOLD = 0.42
# Half-width of the soft transition in linear RGB (reduces speckle / “noisy mask” from binary threshold).
DEFAULT_MASK_FEATHER = 0.09
# Odd radius; separable box blur on mask signal before smoothstep (cuts grain from noisy plates).
# Scalar mask is blurred before smoothstep to suppress per-pixel noise in spot plates.
DEFAULT_MASK_BOX_BLUR_RADIUS = 5


def fraction_near_white_pixels(pat: list[float], pw: int, ph: int) -> float:
    """Fraction of pixels where linear R,G,B each >= NEAR_WHITE_MIN."""
    n = pw * ph
    if n <= 0:
        return 0.0
    w = 0
    i = 0
    while i < len(pat):
        pr, pg, pb = pat[i], pat[i + 1], pat[i + 2]
        if pr >= NEAR_WHITE_MIN and pg >= NEAR_WHITE_MIN and pb >= NEAR_WHITE_MIN:
            w += 1
        i += 4
    return w / float(n)


def resolve_spot_plate_composite_mode(
    mask_mode: str,
    pat: list[float],
    pw: int,
    ph: int,
    dark_threshold: float,
) -> tuple[str, float, str]:
    """Pick ``white_holes`` vs ``dark_spots`` and return (mode, threshold, reason).

    ``mask_mode`` is one of ``white_holes``, ``dark_spots``, ``auto`` (case-insensitive).
    Unknown values are treated as ``auto``.
    """
    raw = (mask_mode or "auto").strip().lower()
    if raw not in ("white_holes", "dark_spots", "auto"):
        raw = "auto"
    wf = fraction_near_white_pixels(pat, pw, ph)
    if raw == "white_holes":
        return "white_holes", dark_threshold, "explicit"
    if raw == "dark_spots":
        return "dark_spots", dark_threshold, "explicit"
    # auto
    if wf >= AUTO_WHITE_FRAC:
        return "white_holes", dark_threshold, f"auto:white_frac={wf:.2%}>={AUTO_WHITE_FRAC:.0%}"
    return "dark_spots", dark_threshold, f"auto:white_frac={wf:.2%} (using dark_spots)"
