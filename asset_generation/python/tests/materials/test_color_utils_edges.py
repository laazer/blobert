"""Edge coverage for color_utils.hex_to_rgba (invalid / exception paths)."""

from __future__ import annotations

import builtins
from unittest.mock import patch

import pytest

from src.materials.color_utils import hex_to_rgba


def test_hex_to_rgba_double_hash_invalid_raises() -> None:
    with pytest.raises(ValueError, match="hex color"):
        hex_to_rgba("##ff0000", (0.0, 0.0, 0.0, 1.0), allow_invalid=False)


def test_hex_to_rgba_invalid_chars_raises() -> None:
    with pytest.raises(ValueError, match="hex color"):
        hex_to_rgba("gg0000", (0.0, 0.0, 0.0, 1.0), allow_invalid=False)


def test_hex_to_rgba_wrong_length_uses_allow_invalid() -> None:
    assert hex_to_rgba("ff00", (0.1, 0.2, 0.3, 1.0), allow_invalid=True) == (0.1, 0.2, 0.3, 1.0)


def test_hex_to_rgba_wrong_length_raises() -> None:
    with pytest.raises(ValueError, match="6 characters"):
        hex_to_rgba("#abcde", (0.1, 0.2, 0.3, 1.0), allow_invalid=False)


def test_hex_to_rgba_int_conversion_error_wraps_valueerror() -> None:
    real_int = builtins.int
    calls = {"n": 0}

    def guarded_int(x: str | bytes | bytearray, base: int = 10) -> int:
        calls["n"] += 1
        if calls["n"] == 1:
            raise ValueError("simulated")
        return real_int(x, base)

    with patch.object(builtins, "int", guarded_int):
        with pytest.raises(ValueError, match="hex color"):
            hex_to_rgba("#010203", (0.0, 0.0, 0.0, 1.0), allow_invalid=False)


def test_hex_to_rgba_int_conversion_returns_default_when_allowed() -> None:
    def boom_int(_x: str | bytes | bytearray, _base: int = 10) -> int:
        raise ValueError("simulated")

    with patch.object(builtins, "int", boom_int):
        out = hex_to_rgba("#010203", (0.25, 0.5, 0.75, 1.0), allow_invalid=True)
    assert out == (0.25, 0.5, 0.75, 1.0)
