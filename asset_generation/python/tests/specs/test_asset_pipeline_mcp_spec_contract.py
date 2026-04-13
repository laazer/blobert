"""Contract tests for project_board/specs/asset_pipeline_mcp_spec.md (APMCP)."""

from pathlib import Path

import pytest

_REPO_ROOT_DEPTH = 4
_REPO_ROOT = Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]
_SPEC_PATH = _REPO_ROOT / "project_board/specs/asset_pipeline_mcp_spec.md"

_REQUIRED_HEADINGS = (
    "## Threat model",
    "## MRVC and registry path enforcement",
    "## Endpoint freeze",
    "## Validation precedence",
    "## Failure taxonomy",
    "## APMCP-RUN — Agent run completion API",
    "## MCP tool catalog",
)

_FROZEN_TOOLS = (
    "blobert_asset_pipeline_health",
    "blobert_asset_pipeline_run_complete",
    "blobert_asset_pipeline_run_status",
    "blobert_asset_pipeline_run_kill",
    "blobert_asset_pipeline_registry_get",
    "blobert_asset_pipeline_files_read",
    "blobert_asset_pipeline_files_write",
)

_DOWNSTREAM = (
    "02_backend_blocking_or_polled_run_endpoint.md",
    "03_mcp_stdio_server_wrapping_asset_editor_api.md",
    "04_documentation_cursor_and_claude_mcp_setup.md",
    "06_agent_skill_blobert_asset_pipeline_mcp.md",
)


def _spec_text() -> str:
    assert _SPEC_PATH.is_file(), f"Missing spec at {_SPEC_PATH}"
    return _SPEC_PATH.read_text(encoding="utf-8")


def test_spec_file_exists() -> None:
    assert _SPEC_PATH.is_file()


def test_spec_banner_and_id() -> None:
    text = _spec_text()
    assert "**Spec ID prefix:** APMCP" in text
    assert "asset_pipeline_mcp_spec.md" in text


def test_spec_requires_fastmcp_for_python_mcp() -> None:
    text = _spec_text()
    assert "FastMCP" in text
    assert "ADR-APMCP-003" in text


@pytest.mark.parametrize("heading", _REQUIRED_HEADINGS)
def test_spec_required_headings(heading: str) -> None:
    assert heading in _spec_text()


@pytest.mark.parametrize("tool", _FROZEN_TOOLS)
def test_spec_frozen_tool_names(tool: str) -> None:
    assert tool in _spec_text()


def test_spec_milestone_readme_traceability() -> None:
    text = _spec_text()
    assert "23_milestone_23_asset_editor_pipeline_mcp/README.md" in text


def test_spec_mrvc_no_bypass() -> None:
    text = _spec_text()
    assert "_ALLOWLIST_PREFIXES" in text
    assert "MUST NOT" in text or "must not" in text.lower()


def test_spec_run_query_parity_named() -> None:
    text = _spec_text()
    for param in ("cmd", "enemy", "count", "build_options", "output_draft", "max_wait_ms"):
        assert param in text


def test_spec_normative_complete_route() -> None:
    assert "/api/run/complete" in _spec_text()


def test_spec_preserves_sse_stream() -> None:
    text = _spec_text()
    assert "/api/run/stream" in text


def test_downstream_tickets_listed() -> None:
    text = _spec_text()
    for ticket in _DOWNSTREAM:
        assert ticket in text, f"Missing downstream reference {ticket}"


def test_spec_mentions_security_threats() -> None:
    text = _spec_text().lower()
    assert "shell" in text and "localhost" in text


def test_spec_frozen_log_byte_cap_documented() -> None:
    assert "262_144" in _spec_text() or "262144" in _spec_text()
