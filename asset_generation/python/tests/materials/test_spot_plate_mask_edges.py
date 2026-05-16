"""spot_plate_mask edge branches."""

from __future__ import annotations

from src.materials.spot_plate_mask import (
    fraction_near_white_pixels,
    resolve_spot_plate_composite_mode,
)


def test_fraction_near_white_zero_dimension() -> None:
    assert fraction_near_white_pixels([], 0, 10) == 0.0


def test_resolve_spot_plate_unknown_mode_treated_as_auto() -> None:
    pat = [1.0, 1.0, 1.0, 1.0] * 4
    mode, _thr, reason = resolve_spot_plate_composite_mode("bogus", pat, 2, 1, 0.42)
    assert mode in ("white_holes", "dark_spots")
    assert "auto" in reason
