# Scoped checkpoint — 03_mcp_stdio_server_wrapping_asset_editor_api

**Run:** 2026-04-13 autopilot (single ticket)

### [M23-03] IMPLEMENTATION — import path layout
**Would have asked:** New top-level package vs `src.*` only?
**Assumption made:** Package lives at `asset_generation/python/src/blobert_asset_pipeline_mcp/` with `pytest` `pythonpath` including `src` so `import blobert_asset_pipeline_mcp` matches README `PYTHONPATH=src` run line; existing tests keep `from src.*`.
**Confidence:** High
