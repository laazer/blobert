"""Path helpers for M901-04 utility consolidation tests."""

from __future__ import annotations

from pathlib import Path


def asset_generation_python_root() -> Path:
    """Directory that contains ``src/`` and ``tests/`` (``asset_generation/python``)."""
    return Path(__file__).resolve().parents[2]


def utils_src_dir() -> Path:
    return asset_generation_python_root() / "src" / "utils"


def asset_generation_root() -> Path:
    """``asset_generation/`` (parent of ``python/``)."""
    return asset_generation_python_root().parent
