# Epic: Milestone 22 – Game Control MCP (Agent-Driven Playtest)

**Goal:** A small MCP server lets Claude or Cursor send high-level commands to a running Godot game (or headless harness) so agents can regression-test levels, movement, and combat without clicking through the editor.

## Scope

- Expose a minimal RPC surface: launch or attach to a game process, load a level/run seed, inject input (move, jump, attack, pause), and read structured state (player HP, position, room id, death/game over).
- Security: localhost-only by default; no arbitrary file or shell execution from MCP tools; document threat model.
- Document how to run the MCP alongside the project (`direnv`, `timeout` for Godot per `CLAUDE.md`).
- Optional: record short event traces for failing tests.

## Dependencies

- M6 — run/room state to observe
- M9+ — meaningful levels to drive (soft dependency)

## Exit Criteria

From a Cursor/Claude session with the MCP enabled, an agent can step through a scripted sequence (e.g. start run → enter combat room → confirm player took damage or enemy died) using documented tools, with failures surfaced as structured errors.

## Status Folders

- `backlog/` – Approved, not yet scheduled
- `ready/` – Clearly defined, has acceptance criteria
- `in_progress/` – Actively being worked on
- `blocked/` – Waiting on dependency or decision
- `testing/` – Implemented, awaiting playtest validation
- `done/` – Playable, tested, merged
