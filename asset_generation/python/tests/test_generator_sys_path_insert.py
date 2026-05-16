"""Exec-only coverage for Blender entry scripts' sys.path bootstrap (diff vs origin/main)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PY_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    ("script", "slice_end_exclusive"),
    [
        ("level_generator.py", 16),
        ("player_generator.py", 17),
    ],
)
def test_generator_inserts_project_root_when_missing_from_path(
    script: str,
    slice_end_exclusive: int,
) -> None:
    path = _PY_ROOT / "src" / script
    lines = path.read_text().splitlines()
    snippet = "\n".join(lines[8:slice_end_exclusive])
    proj = str(path.resolve().parent.parent)
    saved = list(sys.path)
    try:
        sys.path[:] = [p for p in saved if p != proj]
        g: dict[str, object] = {
            "__name__": "_path_snippet",
            "__file__": str(path),
            "__builtins__": __builtins__,
        }
        exec(compile(snippet, str(path), "exec"), g)
        assert proj in sys.path
        assert sys.path[0] == proj
    finally:
        sys.path[:] = saved
