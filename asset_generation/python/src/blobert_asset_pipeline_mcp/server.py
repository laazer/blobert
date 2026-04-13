"""FastMCP stdio server — APMCP tool catalog → Blobert Asset Editor HTTP API."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastmcp import FastMCP

from blobert_asset_pipeline_mcp.http_util import (
    encode_path_segments,
    format_http_response,
    http_client,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "blobert-asset-pipeline",
    instructions=(
        "Blobert asset pipeline: call the local FastAPI asset editor (task editor / :8000). "
        "Use blobert_asset_pipeline_health first. Runs are single-flight — use run_status after 504. "
        "Registry paths must satisfy MRVC allowlists; tools only proxy HTTP (no shell)."
    ),
)


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | list[Any] | None = None,
    read_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    async with http_client(read_timeout_seconds=read_timeout_seconds) as client:
        try:
            r = await client.request(method, path, params=params, json=json_body)
        except httpx.RequestError as e:
            logger.warning("HTTP request failed: %s %s — %s", method, path, e)
            return {"status_code": None, "error": str(e), "data": None}
    return format_http_response(r)


def _run_query_params(
    cmd: str,
    enemy: str | None,
    count: int | None,
    description: str | None,
    difficulty: str | None,
    finish: str | None,
    hex_color: str | None,
    build_options: str | None,
    output_draft: bool,
    max_wait_ms: int | None,
) -> dict[str, Any]:
    params: dict[str, Any] = {"cmd": cmd, "output_draft": output_draft}
    if enemy is not None:
        params["enemy"] = enemy
    if count is not None:
        params["count"] = count
    if description is not None:
        params["description"] = description
    if difficulty is not None:
        params["difficulty"] = difficulty
    if finish is not None:
        params["finish"] = finish
    if hex_color is not None:
        params["hex_color"] = hex_color
    if build_options is not None and str(build_options).strip():
        params["build_options"] = str(build_options).strip()
    if max_wait_ms is not None:
        params["max_wait_ms"] = max_wait_ms
    return params


@mcp.tool(name="blobert_asset_pipeline_health")
async def blobert_asset_pipeline_health() -> dict[str, Any]:
    """Ping the asset editor API. Call this before other tools to verify the backend is up."""
    return await _request("GET", "/api/health")


@mcp.tool(name="blobert_asset_pipeline_run_complete")
async def blobert_asset_pipeline_run_complete(
    cmd: str,
    enemy: str | None = None,
    count: int | None = None,
    description: str | None = None,
    difficulty: str | None = None,
    finish: str | None = None,
    hex_color: str | None = None,
    build_options: str | None = None,
    output_draft: bool = False,
    max_wait_ms: int | None = None,
) -> dict[str, Any]:
    """Run a pipeline command to completion (GET /api/run/complete). Same params as the editor SSE run.

    Allowed cmd values: animated, player, level, smart, stats, test. Use output_draft=true for draft/ subdirs.
    May return HTTP 409 if a run is already active, or 504 with timed_out if max_wait_ms elapses.
    """
    params = _run_query_params(
        cmd,
        enemy,
        count,
        description,
        difficulty,
        finish,
        hex_color,
        build_options,
        output_draft,
        max_wait_ms,
    )
    wait = max_wait_ms if max_wait_ms is not None else 3_600_000
    read_timeout = max(wait / 1000.0 + 120.0, 300.0)
    return await _request(
        "GET",
        "/api/run/complete",
        params=params,
        read_timeout_seconds=read_timeout,
    )


@mcp.tool(name="blobert_asset_pipeline_run_status")
async def blobert_asset_pipeline_run_status() -> dict[str, Any]:
    """Poll whether a subprocess run is active (is_running, run_id). Use after a 504 from run_complete."""
    return await _request("GET", "/api/run/status")


@mcp.tool(name="blobert_asset_pipeline_run_kill")
async def blobert_asset_pipeline_run_kill() -> dict[str, Any]:
    """Terminate the current pipeline subprocess if one is running."""
    return await _request("POST", "/api/run/kill")


@mcp.tool(name="blobert_asset_pipeline_registry_get")
async def blobert_asset_pipeline_registry_get() -> dict[str, Any]:
    """Load the full model_registry manifest JSON (MRVC). Read-only."""
    return await _request("GET", "/api/registry/model")


@mcp.tool(name="blobert_asset_pipeline_registry_patch_enemy_version")
async def blobert_asset_pipeline_registry_patch_enemy_version(
    family: str,
    version_id: str,
    patch: dict[str, Any],
) -> dict[str, Any]:
    """PATCH fields on one enemy version row (paths must stay allowlisted)."""
    path = f"/api/registry/model/enemies/{encode_path_segments(family)}/versions/{encode_path_segments(version_id)}"
    return await _request("PATCH", path, json_body=patch)


@mcp.tool(name="blobert_asset_pipeline_registry_patch_player_active")
async def blobert_asset_pipeline_registry_patch_player_active(patch: dict[str, Any]) -> dict[str, Any]:
    """PATCH player_active_visual (see OpenAPI / backend PlayerVisualPatch)."""
    return await _request("PATCH", "/api/registry/model/player_active_visual", json_body=patch)


@mcp.tool(name="blobert_asset_pipeline_registry_load_existing_candidates")
async def blobert_asset_pipeline_registry_load_existing_candidates() -> dict[str, Any]:
    """List load-existing GLB candidates derived from the registry."""
    return await _request("GET", "/api/registry/model/load_existing/candidates")


@mcp.tool(name="blobert_asset_pipeline_registry_load_existing_open")
async def blobert_asset_pipeline_registry_load_existing_open(body: dict[str, Any]) -> dict[str, Any]:
    """Resolve a load-existing target (kind: enemy|player|path; see backend LoadExistingOpenRequest)."""
    return await _request("POST", "/api/registry/model/load_existing/open", json_body=body)


@mcp.tool(name="blobert_asset_pipeline_registry_put_enemy_slots")
async def blobert_asset_pipeline_registry_put_enemy_slots(
    family: str,
    slots_body: dict[str, Any],
) -> dict[str, Any]:
    """Replace ordered slot list for an enemy family."""
    path = f"/api/registry/model/enemies/{encode_path_segments(family)}/slots"
    return await _request("PUT", path, json_body=slots_body)


@mcp.tool(name="blobert_asset_pipeline_registry_put_player_slots")
async def blobert_asset_pipeline_registry_put_player_slots(slots_body: dict[str, Any]) -> dict[str, Any]:
    """Replace player slot ordering."""
    return await _request("PUT", "/api/registry/model/player/slots", json_body=slots_body)


@mcp.tool(name="blobert_asset_pipeline_registry_sync_animated_exports")
async def blobert_asset_pipeline_registry_sync_animated_exports(family: str) -> dict[str, Any]:
    """Scan animated_exports for family and sync discovered GLBs into the registry."""
    path = f"/api/registry/model/enemies/{encode_path_segments(family)}/sync_animated_exports"
    return await _request("POST", path)


@mcp.tool(name="blobert_asset_pipeline_registry_sync_player_exports")
async def blobert_asset_pipeline_registry_sync_player_exports() -> dict[str, Any]:
    """Scan player_exports and sync into the registry."""
    return await _request("POST", "/api/registry/model/player/sync_player_exports")


@mcp.tool(name="blobert_asset_pipeline_registry_spawn_eligible")
async def blobert_asset_pipeline_registry_spawn_eligible(family: str) -> dict[str, Any]:
    """List spawn-eligible GLB paths for a family."""
    path = f"/api/registry/model/spawn_eligible/{encode_path_segments(family)}"
    return await _request("GET", path)


@mcp.tool(name="blobert_asset_pipeline_registry_delete_enemy_version")
async def blobert_asset_pipeline_registry_delete_enemy_version(
    family: str,
    version_id: str,
    delete_body: dict[str, Any],
) -> dict[str, Any]:
    """Delete an enemy version (requires confirmation fields per MRVC / OpenAPI EnemyVersionDeleteRequest)."""
    path = f"/api/registry/model/enemies/{encode_path_segments(family)}/versions/{encode_path_segments(version_id)}"
    return await _request("DELETE", path, json_body=delete_body)


@mcp.tool(name="blobert_asset_pipeline_registry_delete_player_active")
async def blobert_asset_pipeline_registry_delete_player_active(delete_body: dict[str, Any]) -> dict[str, Any]:
    """Clear player_active_visual with confirmation (PlayerActiveVisualDeleteRequest)."""
    return await _request("DELETE", "/api/registry/model/player_active_visual", json_body=delete_body)


@mcp.tool(name="blobert_asset_pipeline_files_list")
async def blobert_asset_pipeline_files_list() -> dict[str, Any]:
    """List editable .py files under python_root/src (tree)."""
    return await _request("GET", "/api/files")


@mcp.tool(name="blobert_asset_pipeline_files_read")
async def blobert_asset_pipeline_files_read(path: str) -> dict[str, Any]:
    """Read one jailed source file; path is relative to src/ (e.g. enemies/foo.py)."""
    ep = encode_path_segments(path)
    return await _request("GET", f"/api/files/{ep}")


@mcp.tool(name="blobert_asset_pipeline_files_write")
async def blobert_asset_pipeline_files_write(path: str, content: str) -> dict[str, Any]:
    """Write one jailed .py file (atomic on the server)."""
    ep = encode_path_segments(path)
    return await _request("PUT", f"/api/files/{ep}", json_body={"content": content})


@mcp.tool(name="blobert_asset_pipeline_assets_list")
async def blobert_asset_pipeline_assets_list() -> dict[str, Any]:
    """List GLB/JSON assets under export directories."""
    return await _request("GET", "/api/assets")


@mcp.tool(name="blobert_asset_pipeline_assets_get")
async def blobert_asset_pipeline_assets_get(path: str) -> dict[str, Any]:
    """Fetch one asset (GLB or JSON). Binary responses return content_base64 in data."""
    ep = encode_path_segments(path)
    return await _request("GET", f"/api/assets/{ep}")


@mcp.tool(name="blobert_asset_pipeline_meta_enemies")
async def blobert_asset_pipeline_meta_enemies() -> dict[str, Any]:
    """Optional: enemy metadata and animated_build_controls (same as editor meta pane)."""
    return await _request("GET", "/api/meta/enemies")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    mcp.run()


if __name__ == "__main__":
    main()
