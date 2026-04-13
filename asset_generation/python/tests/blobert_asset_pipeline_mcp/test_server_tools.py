"""FastMCP server: tool registration (APMCP names)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_mcp_registers_apmcp_tool_names() -> None:
    from blobert_asset_pipeline_mcp.server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    for required in (
        "blobert_asset_pipeline_health",
        "blobert_asset_pipeline_run_complete",
        "blobert_asset_pipeline_run_status",
        "blobert_asset_pipeline_run_kill",
        "blobert_asset_pipeline_registry_get",
        "blobert_asset_pipeline_files_read",
        "blobert_asset_pipeline_files_write",
        "blobert_asset_pipeline_meta_enemies",
    ):
        assert required in names
    assert len(names) >= 20
