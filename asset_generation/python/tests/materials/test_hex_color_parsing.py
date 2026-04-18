"""Test hex color parsing for gradient materials."""

from __future__ import annotations

from src.materials.material_system import (
    _parse_hex_color,
    _rgba_from_hex_or_fallback,
)


def test_parse_hex_color_red():
    """Parse #ff0000 as red."""
    r, g, b, a = _parse_hex_color("ff0000")
    assert r > 0.99, f"Red should be ~1.0, got {r}"
    assert g < 0.01, f"Green should be ~0.0, got {g}"
    assert b < 0.01, f"Blue should be ~0.0, got {b}"
    assert a > 0.99, f"Alpha should be ~1.0, got {a}"


def test_parse_hex_color_blue():
    """Parse #0000ff as blue."""
    r, g, b, a = _parse_hex_color("0000ff")
    assert r < 0.01, f"Red should be ~0.0, got {r}"
    assert g < 0.01, f"Green should be ~0.0, got {g}"
    assert b > 0.99, f"Blue should be ~1.0, got {b}"
    assert a > 0.99, f"Alpha should be ~1.0, got {a}"


def test_rgba_from_hex_or_fallback_red():
    """Test _rgba_from_hex_or_fallback with red hex."""
    fallback = (0.0, 0.0, 0.0, 1.0)
    result = _rgba_from_hex_or_fallback("ff0000", fallback)
    assert result[0] > 0.99, f"Red should be ~1.0, got {result[0]}"
    assert result[1] < 0.01, f"Green should be ~0.0, got {result[1]}"
    assert result[2] < 0.01, f"Blue should be ~0.0, got {result[2]}"


def test_rgba_from_hex_or_fallback_uses_fallback_for_empty():
    """Test _rgba_from_hex_or_fallback uses fallback for empty hex."""
    fallback = (0.5, 0.5, 0.5, 1.0)
    result = _rgba_from_hex_or_fallback("", fallback)
    assert result == fallback, f"Should use fallback for empty hex, got {result}"


def test_rgba_from_hex_or_fallback_sanitizes_input():
    """Test _rgba_from_hex_or_fallback sanitizes input."""
    fallback = (0.0, 0.0, 0.0, 1.0)
    result = _rgba_from_hex_or_fallback("#FF0000", fallback)
    assert result[0] > 0.99, f"Should handle # prefix, got {result}"
