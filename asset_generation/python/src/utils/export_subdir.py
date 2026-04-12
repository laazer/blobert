"""Blender export directories and variant start index: configurable via environment."""

from __future__ import annotations

import os

from src.utils.constants import ExportConfig, LevelExportConfig, PlayerExportConfig

_EXPORT_USE_DRAFT_ENV = "BLOBERT_EXPORT_USE_DRAFT_SUBDIR"
_EXPORT_START_INDEX_ENV = "BLOBERT_EXPORT_START_INDEX"
_DRAFT = "draft"


def _use_draft_subdir() -> bool:
    return os.environ.get(_EXPORT_USE_DRAFT_ENV) == "1"


def variant_start_index() -> int:
    """Starting variant index for this export run.

    Set ``BLOBERT_EXPORT_START_INDEX`` in the environment to start from a
    non-zero index and avoid overwriting existing variants.  Defaults to 0.
    """
    val = os.environ.get(_EXPORT_START_INDEX_ENV)
    if val is not None:
        try:
            return max(0, int(val))
        except ValueError:
            pass
    return 0


def animated_export_directory() -> str:
    base = ExportConfig.ANIMATED_DIR
    if _use_draft_subdir():
        return os.path.join(base, _DRAFT)
    return base


def player_export_directory() -> str:
    base = PlayerExportConfig.PLAYER_DIR
    if _use_draft_subdir():
        return os.path.join(base, _DRAFT)
    return base


def level_export_directory() -> str:
    base = LevelExportConfig.LEVEL_DIR
    if _use_draft_subdir():
        return os.path.join(base, _DRAFT)
    return base
