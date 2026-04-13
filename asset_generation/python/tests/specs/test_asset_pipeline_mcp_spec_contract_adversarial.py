"""Adversarial contract tests for APMCP spec (checkpoint-marked)."""

from pathlib import Path

_REPO_ROOT_DEPTH = 4
_REPO_ROOT = Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]
_SPEC_PATH = _REPO_ROOT / "project_board/specs/asset_pipeline_mcp_spec.md"


def _text() -> str:
    return _SPEC_PATH.read_text(encoding="utf-8")


# CHECKPOINT: registry tools must remain HTTP-only — no direct manifest writes advertised
def test_spec_forbids_direct_registry_json_writes() -> None:
    t = _text()
    low = t.lower()
    assert "must not" in low
    assert "model_registry.json" in t
    assert "directly from the mcp" in low


# CHECKPOINT: allowlist roots must match MRVC / registry router
def test_spec_lists_four_allowlist_prefixes() -> None:
    t = _text()
    for p in ("animated_exports/", "exports/", "player_exports/", "level_exports/"):
        assert p in t


# CHECKPOINT: single-flight conflict frozen to 409 for /complete (not 429)
def test_spec_mentions_conflict_status_for_runs() -> None:
    t = _text()
    assert "409" in t
    assert "504" in t and "timed_out" in t.lower()
