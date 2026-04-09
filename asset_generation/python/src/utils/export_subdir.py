"""Blender export directories: optional ``draft/`` subtree via environment."""

from __future__ import annotations

import os

from src.utils.constants import ExportConfig, LevelExportConfig, PlayerExportConfig

_EXPORT_USE_DRAFT_ENV = "BLOBERT_EXPORT_USE_DRAFT_SUBDIR"
_DRAFT = "draft"


def _use_draft_subdir() -> bool:
    return os.environ.get(_EXPORT_USE_DRAFT_ENV) == "1"


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
