"""Tests for opt-in spots compositing debug (no Blender required)."""

from __future__ import annotations

import os

from src.materials.spots_composite_debug import spots_composite_debug_enabled


def test_spots_debug_defaults_off() -> None:
    os.environ.pop("BLOBERT_DEBUG_SPOTS", None)
    assert spots_composite_debug_enabled() is False


def test_spots_debug_enables_with_sentinel(monkeypatch) -> None:
    for val in ("1", "true", "YES", "On"):
        monkeypatch.setenv("BLOBERT_DEBUG_SPOTS", val)
        assert spots_composite_debug_enabled() is True
