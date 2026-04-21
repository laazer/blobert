"""``BLOBERT_EXPORT_USE_DRAFT_SUBDIR`` selects ``…/draft`` export roots."""

import os

import pytest

from src.utils.export import (
    animated_export_directory,
    level_export_directory,
    player_export_directory,
)


@pytest.fixture(autouse=True)
def _clear_draft_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BLOBERT_EXPORT_USE_DRAFT_SUBDIR", raising=False)


def test_default_export_dirs_are_live_roots() -> None:
    assert animated_export_directory() == "animated_exports"
    assert player_export_directory() == "player_exports"
    assert level_export_directory() == "level_exports"


def test_draft_env_uses_draft_subdir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLOBERT_EXPORT_USE_DRAFT_SUBDIR", "1")
    assert animated_export_directory() == os.path.join("animated_exports", "draft")
    assert player_export_directory() == os.path.join("player_exports", "draft")
    assert level_export_directory() == os.path.join("level_exports", "draft")
