# TICKET: 04_documentation_cursor_and_claude_mcp_setup

Title: Documentation — Enable Asset Pipeline MCP for Cursor and Claude Code

## Description

Document end-to-end setup so agents and humans can enable the MCP:

- Prerequisite: `task editor` or `bash asset_generation/web/start.sh` (backend on `:8000`).
- Where the MCP package lives, how to install/run it, required env vars (`BLOBERT_ASSET_API_BASE`, optional auth header if implemented).
- **Cursor:** example `mcp.json` fragment or pointer to Cursor docs for stdio servers.
- **Claude Code:** equivalent if applicable (project `.mcp.json` or documented `claude mcp` flow — follow repo conventions).
- Short **troubleshooting** section: connection refused, CORS (should not apply to local MCP→localhost), run already in progress.

**Placement:** Minimal, authoritative updates — e.g. `asset_generation/web/README.md` or a short `asset_generation/mcp/README.md` plus a single bullet in `CLAUDE.md` under Common Workflows pointing to the full doc. Avoid duplicating large blocks in multiple files.

## Acceptance Criteria

- A new contributor can follow the doc once and get **one successful tool call** (health or files get) from Cursor with MCP enabled.
- `CLAUDE.md` (or linked doc) mentions this milestone’s MCP **in one place** so coding agents discover it.
- Doc points to the agent skill path under `asset_generation/resources/` from ticket `06` (install / symlink into Cursor or Claude skills as appropriate).
- Security reminder: local-only; do not expose the editor API to the public internet without additional controls.

## Dependencies

- Ticket `03_mcp_stdio_server_wrapping_asset_editor_api.md` (MCP package runnable)

## Workflow State

Stage: BACKLOG
