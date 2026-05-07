"""Shared color parsing helpers for pattern generators."""

from __future__ import annotations


def hex_to_rgba(
    hex_str: str,
    default_rgba: tuple[float, float, float, float],
    *,
    allow_invalid: bool = False,
) -> tuple[float, float, float, float]:
    """Parse 6-char hex string to RGBA or return default."""
    raw = (hex_str or "").strip()
    h = raw.lstrip("#").lower()
    if not h:
        return default_rgba
    if raw.startswith("#"):
        if raw.count("#") > 1:
            if allow_invalid:
                return default_rgba
            raise ValueError("hex color must be valid hexadecimal")
    elif any(ch not in "0123456789abcdefABCDEF" for ch in raw):
        if allow_invalid:
            return default_rgba
        raise ValueError("hex color must be valid hexadecimal")
    if len(h) != 6:
        if allow_invalid:
            return default_rgba
        raise ValueError(f"hex color must be 6 characters (RRGGBB), got {h!r}")
    try:
        r = int(h[0:2], 16) / 255.0
        g = int(h[2:4], 16) / 255.0
        b = int(h[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    except ValueError as exc:
        if allow_invalid:
            return default_rgba
        raise ValueError("hex color must be valid hexadecimal") from exc
