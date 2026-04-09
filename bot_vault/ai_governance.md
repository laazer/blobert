# AI Governance

This directory is AI-focused documentation. It complements user-facing docs and must remain evidence-based.

## Purpose

- Keep machine-oriented architecture/runtime context in one place.
- Reduce guesswork for coding agents working across Godot, Python, and web stacks.

## Writable vs Protected Areas

### AI-writable

- `bot_vault/**`
- `project_board/checkpoints/<ticket-id>/<run-id>.md` (scoped checkpoint logs only)

### Protected or restricted

- `reference_projects/**` (read-only upstream references)
- `agent_context/agents/**` (do not edit role/workflow definitions)
- `project_board/CHECKPOINTS.md` (index-only, no full checkpoint bodies)

## Read/Update Protocol

1. Read `CLAUDE.md` first, then relevant subsystem files.
2. Classify target runtime before edits:
   - Godot gameplay/runtime
   - Python asset pipeline
   - Web editor backend/frontend
3. Record only claims that are backed by repository files.
4. For absent layers (Docker image, deployed service), write `N/A` instead of inferring.
5. Prefer command references from `Taskfile.yml` and scripts over prose docs when conflicts exist.

## Agent-System Precedence

When guidance overlaps, apply in this order:

1. System/developer/user instructions in the active session
2. Repository `CLAUDE.md`
3. `agent_context` role/ownership constraints
4. `.claude/skills/**` implementation workflow guidance
5. `bot_vault/**` summaries and maps

`bot_vault` should reflect source truth and not override higher-priority instructions.

## Validation Matrix Before Claiming Completion

| Change surface | Minimum validation |
| --- | --- |
| Godot scripts/scenes/tests | `timeout 300 godot --headless -s tests/run_tests.gd` (or `timeout 300 ci/scripts/run_tests.sh` for full suite) |
| Python under `asset_generation/python` | `bash .lefthook/scripts/py-tests.sh` and applicable staged-file hooks |
| Web backend/frontend | Run relevant test command(s) already defined (`cd asset_generation/web/frontend && npm test` for frontend; backend checks via existing Python/hook pipeline) |
| Cross-surface changes | Prefer full suite: `timeout 300 ci/scripts/run_tests.sh` plus targeted checks |

## Memory Freshness Rule

When writing memory notes, include:

- `Last verified:` `<date>`
- `Verified against:` `<commit or branch>`

If freshness metadata is missing or old, treat the note as advisory and re-verify from source files.
