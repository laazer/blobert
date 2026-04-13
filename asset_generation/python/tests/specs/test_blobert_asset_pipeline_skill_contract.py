"""Contract tests for asset_generation/resources/.../blobert-asset-pipeline-mcp/SKILL.md."""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT_DEPTH = 4
_REPO_ROOT = Path(__file__).resolve().parents[_REPO_ROOT_DEPTH]
_SKILL_PATH = (
    _REPO_ROOT
    / "asset_generation/resources/agent_skills/blobert-asset-pipeline-mcp/SKILL.md"
)


def _skill_text() -> str:
    assert _SKILL_PATH.is_file(), f"Missing skill at {_SKILL_PATH}"
    return _SKILL_PATH.read_text(encoding="utf-8")


def _frontmatter_map(text: str) -> dict[str, str]:
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    end = text.index("\n---\n", 4)
    block = text[4:end]
    out: dict[str, str] = {}
    for raw in block.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, val = raw.split(":", 1)
        out[key.strip()] = val.strip()
    return out


def test_skill_file_exists() -> None:
    assert _SKILL_PATH.is_file()


def test_skill_frontmatter_name_and_description() -> None:
    text = _skill_text()
    fm = _frontmatter_map(text)
    assert fm.get("name") == "blobert-asset-pipeline-mcp"
    desc = fm.get("description", "")
    assert len(desc) >= 40
    assert "APMCP" in desc or "asset_pipeline_mcp_spec" in desc


def test_skill_points_to_normative_spec_and_operator_doc() -> None:
    text = _skill_text()
    assert "project_board/specs/asset_pipeline_mcp_spec.md" in text
    assert "asset_generation/mcp/README.md" in text


@pytest.mark.asyncio
async def test_skill_body_mentions_every_registered_mcp_tool() -> None:
    """APMCP-1.1: skill lists the same tool names as the implemented MCP server."""
    from blobert_asset_pipeline_mcp.server import mcp

    skill = _skill_text()
    tools = await mcp.list_tools()
    for t in tools:
        assert f"`{t.name}`" in skill, f"SKILL.md missing backticked tool {t.name}"


def test_resources_readme_indexes_skill() -> None:
    readme = (_REPO_ROOT / "asset_generation/resources/README.md").read_text(
        encoding="utf-8"
    )
    assert "blobert-asset-pipeline-mcp" in readme
    assert "SKILL.md" in readme
