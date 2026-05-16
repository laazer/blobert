"""spots_composite_debug opt-in print path."""

from __future__ import annotations

from src.materials.spots_composite_debug import (
    log_spots_composite,
    spots_composite_debug_enabled,
)


def test_spots_composite_debug_toggle(monkeypatch) -> None:
    monkeypatch.delenv("BLOBERT_DEBUG_SPOTS", raising=False)
    assert spots_composite_debug_enabled() is False
    monkeypatch.setenv("BLOBERT_DEBUG_SPOTS", "1")
    assert spots_composite_debug_enabled() is True


def test_log_spots_composite_prints_when_enabled(capsys, monkeypatch) -> None:
    monkeypatch.setenv("BLOBERT_DEBUG_SPOTS", "true")
    log_spots_composite("unit-test-msg")
    out = capsys.readouterr().out
    assert "[blobert:spots]" in out
    assert "unit-test-msg" in out
