# Checkpoint — `06_agent_skill_blobert_asset_pipeline_mcp`

**Run:** 2026-04-13

## Summary

Added bundled agent skill + `asset_generation/resources/README.md`, cross-links in `asset_generation/mcp/README.md` and root `CLAUDE.md`, and `tests/specs/test_blobert_asset_pipeline_skill_contract.py` (frontmatter + registered tool parity via `mcp.list_tools()`).

## Would have asked

- Whether to add PyYAML for frontmatter parsing → **Assumption:** stdlib line split for simple single-line keys.

## Assumption made

- `diff_cover_preflight.sh` failure on aggregate MCP package coverage is a branch-level issue; ticket validation documents it rather than blocking on unrelated line coverage.

## Confidence

High
