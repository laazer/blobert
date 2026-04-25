"""Shared material finish presets and color parsing helpers."""

from __future__ import annotations

from typing import TypeAlias

from src.utils.materials import MaterialColors as _MaterialColors

RGBA: TypeAlias = tuple[float, float, float, float]
MaterialColors = _MaterialColors

ENEMY_FINISH_PRESETS: dict[str, tuple[float | None, float | None, float | None]] = {
    "default": (None, None, None),
    "glossy": (0.12, 0.05, 0.0),
    "matte": (0.8, 0.0, 0.0),
    "metallic": (0.25, 0.75, 0.0),
    "gel": (0.08, 0.0, 0.35),
}


def sanitize_hex_input(raw: str) -> str:
    cleaned = "".join(c for c in str(raw or "").strip().lower() if c in "0123456789abcdef")
    return cleaned[:6]


def parse_hex_color(hex_value: str) -> RGBA:
    raw = (hex_value or "").strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError("hex color must be 6 characters (RRGGBB)")
    try:
        r = int(raw[0:2], 16) / 255.0
        g = int(raw[2:4], 16) / 255.0
        b = int(raw[4:6], 16) / 255.0
    except ValueError as error:
        raise ValueError("hex color must be valid hexadecimal") from error
    return (r, g, b, 1.0)


def rgba_from_hex_or_fallback(hex_str: str, fallback_rgba: RGBA) -> RGBA:
    parsed = sanitize_hex_input(hex_str)
    if len(parsed) != 6:
        return fallback_rgba
    try:
        return parse_hex_color(parsed)
    except ValueError:
        return fallback_rgba
