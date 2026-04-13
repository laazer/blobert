# TICKET: 06_agent_skill_blobert_asset_pipeline_mcp

Title: Agent skill — Blobert asset pipeline MCP usage (`asset_generation/resources`)

## Description

Add a **Cursor/Claude-compatible agent skill** (YAML frontmatter + body per repo skill conventions) that teaches agents **when and how** to use the Blobert Asset Pipeline MCP tools from ticket `03`, including:

- Prerequisite: asset editor stack running (`task editor` / `asset_generation/web/start.sh`); backend reachable at the configured base URL.
- **Workflow patterns:** edit jailed `.py` → run generation (draft vs published paths, `build_options` if relevant) → interpret exit code and log tail → read/update registry per MRVC → optional follow-up run.
- **Tool selection:** which MCP tool maps to which user intent (avoid raw `curl` when MCP is enabled; fall back to documented HTTP only if MCP unavailable).
- **Safety:** localhost-only posture; no asking to expose the API; respect allowlists and single-flight run semantics.
- **Pointers:** link to `project_board/specs/asset_pipeline_mcp_spec.md` (or final spec filename from ticket `01`) and ticket `04` operator doc paths.

**Location (required):** Place the skill under a **new subdirectory** of `asset_generation/resources/`, for example:

- `asset_generation/resources/agent_skills/blobert-asset-pipeline-mcp/SKILL.md`

Create `asset_generation/resources/` and the chosen subdirs if they do not exist. Optionally add a one-line `asset_generation/resources/README.md` listing bundled skills and how humans symlink or copy them into `.cursor/skills` / Claude plugin paths (keep minimal — detailed install steps may stay on ticket `04`).

## Acceptance Criteria

- `SKILL.md` exists under `asset_generation/resources/<subdir>/` with valid frontmatter (`name`, `description`, optional `argument-hint` if useful).
- Content is accurate relative to the implemented MCP tool names and the spec from ticket `01` (update skill in same PR as MCP if names change).
- Ticket `04` documentation references this skill path so operators know where to install it from.
- No duplicate of the full HTTP reference — skill is **procedural**; normative API detail stays in the spec.

## Dependencies

- Ticket `01_spec_asset_pipeline_mcp_and_agent_http_api.md` (tool names and flows)
- Ticket `03_mcp_stdio_server_wrapping_asset_editor_api.md` (implemented tools)
- Ticket `04_documentation_cursor_and_claude_mcp_setup.md` (cross-link from docs to skill)

## Workflow State

Stage: BACKLOG
