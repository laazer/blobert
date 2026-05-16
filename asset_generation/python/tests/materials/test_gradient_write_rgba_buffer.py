"""write_rgba_buffer_to_gradients_png smoke (creates then deletes artifact)."""

from __future__ import annotations

from pathlib import Path

from src.materials.gradient_generator import write_rgba_buffer_to_gradients_png


def test_write_rgba_buffer_to_gradients_png_writes_minimal_png() -> None:
    label = "__diffcover_tmp_gradient_delete_me__"
    path = write_rgba_buffer_to_gradients_png(1, 1, [0.2, 0.4, 0.6, 1.0], label)
    assert isinstance(path, Path)
    assert path.is_file()
    assert path.suffix == ".png"
    assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    path.unlink()
