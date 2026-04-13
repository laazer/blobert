# Blobert asset pipeline MCP (FastMCP)

Stdio MCP server that proxies the [APMCP](../../../../project_board/specs/asset_pipeline_mcp_spec.md) tool catalog to the Blobert Asset Editor FastAPI app (`asset_generation/web/backend`).

## Dependencies

Install with the repo Python project (includes `fastmcp` and `httpx`):

```bash
cd asset_generation/python && uv sync --extra mcp
# or full dev + MCP:
uv sync --extra dev
```

## Environment

| Variable | Default | Meaning |
|----------|---------|---------|
| `BLOBERT_ASSET_API_BASE` | `http://127.0.0.1:8000` | Asset editor origin |
| `BLOBERT_ASSET_API_TOKEN` | unset | Optional `X-Blobert-Asset-Token` header |

## Run (one line)

From `asset_generation/python`, with the editor up (`task editor` / `start.sh`):

```bash
PYTHONPATH=src uv run --extra mcp python -m blobert_asset_pipeline_mcp
```

## Cursor / Claude

**Operator guide (copy-paste config + troubleshooting):** [`asset_generation/mcp/README.md`](../../../mcp/README.md) (repo-relative from here: `../../../mcp/README.md`).

## Tools

Tool names match the APMCP spec (`blobert_asset_pipeline_*`). No shell execution; all effects go through HTTP.
