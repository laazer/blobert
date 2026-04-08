"""Contract tests for project_board/specs/model_registry_draft_versions_spec.md (MRVC)."""

from pathlib import Path

import pytest

# tests/specs → tests → python → asset_generation → repo root
_REPO_ROOT_DEPTH = 4
_REPO_ROOT = Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]
_SPEC_PATH = _REPO_ROOT / "project_board/specs/model_registry_draft_versions_spec.md"

_REQUIRED_SECTION_MARKERS = (
    "## Architecture Decision Records",
    "### ADR-001",
    "## Requirement MRVC-1",
    "## Requirement MRVC-3",
    "## Requirement MRVC-4",
    "## Requirement MRVC-5",
    "## Requirement MRVC-6",
    "## Requirement MRVC-7",
    "## Requirement MRVC-8",
    "## Requirement MRVC-9",
    "## Requirement MRVC-10",
    "## Requirement MRVC-11",
    "## Requirement MRVC-12",
)

_DOWNSTREAM_TICKETS = (
    "04_editor_ui_draft_status_for_exports.md",
    "05_editor_ui_game_model_selection.md",
    "06_editor_load_existing_models_allowlist.md",
    "07_editor_delete_draft_and_in_use_models.md",
    "08_runtime_spawn_random_enemy_visual_variant.md",
    "09_automated_tests_registry_allowlist_delete.md",
)


def _spec_text() -> str:
    assert _SPEC_PATH.is_file(), f"Missing spec at {_SPEC_PATH}"
    return _SPEC_PATH.read_text(encoding="utf-8")


def test_spec_file_exists() -> None:
    assert _SPEC_PATH.is_file()


def test_spec_contains_stable_path_banner() -> None:
    text = _spec_text()
    assert "model_registry_draft_versions_spec.md" in text
    assert "**Spec ID prefix:** MRVC" in text


@pytest.mark.parametrize("marker", _REQUIRED_SECTION_MARKERS)
def test_spec_contains_section_markers(marker: str) -> None:
    assert marker in _spec_text()


def test_spec_mentions_manifest_and_schema_version() -> None:
    text = _spec_text()
    assert "model_registry.json" in text
    assert "schema_version" in text


def test_spec_mentions_allowlist_export_roots() -> None:
    text = _spec_text()
    for root in ("animated_exports/", "player_exports/", "exports/", "level_exports/"):
        assert root in text


def test_spec_traces_downstream_tickets() -> None:
    text = _spec_text()
    for name in _DOWNSTREAM_TICKETS:
        assert name in text, f"Downstream ticket {name} must be referenced for contract closure"


def test_spec_documents_spawn_resolver_hook() -> None:
    text = _spec_text()
    assert "resolve_enemy_visual_paths" in text


def test_spec_documents_deletion_cases() -> None:
    text = _spec_text()
    assert "D1" in text and "D4" in text


# CHECKPOINT: adversarial contract — empty-pool fallback must remain documented for spawn safety
def test_spec_empty_pool_fallback_documented() -> None:
    assert "MRVC-11" in _spec_text() and "fallback" in _spec_text().lower()


# CHECKPOINT: adversarial contract — draft excluded from default spawn pool
def test_spec_draft_excluded_from_spawn_pool() -> None:
    text = _spec_text()
    assert "draft" in text.lower()
    assert "spawn" in text.lower()
    assert "MRVC-4" in text
