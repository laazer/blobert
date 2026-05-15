# Title

GDScript committed code: gdformat + gdlint in CI with formatting/lint fixes or baseline

# Context

The MVP includes Godot static analysis (`gdformat`, `gdlint`). This ticket applies it to committed GDScript so agents cannot regress formatting/lint rules silently.

# Scope

- Target paths: `scripts/`, `tests/`, and GDScript files under `scenes/` as applicable (exclude third-party/vendor paths if any exist).
- Integrate with canonical test commands (`task hooks:gd-review`, `timeout 300 godot ...`) without introducing `godot --check-only`.

# Acceptance Criteria

- CI runs gdformat/gdlint (or documented equivalent) on the scoped paths.
- Either: (a) committed code is formatted/clean, or (b) violations are captured in `.governance-baseline.json` with owners/expiry and “new violation fails” behavior.
- Hook scripts remain bounded/timeboxed per repo policy.

# Agent Execution Prompt

Apply gdformat/gdlint enforcement to committed Godot code.

Goal: Add CI + (optional) lefthook integration and fix or baseline violations.

Constraints:
- Follow `CLAUDE.md` Godot CLI constraints.
- Do not mass-touch unrelated scenes.

Expected output:
- Config + CI wiring + either formatting commit or baseline entries.

# Failure Handling Prompt

If blocked, ask:

- What dependency is missing? (gdformat/gdlint not installed in CI image)
- What assumption cannot be verified? (Godot version compatibility)
- What ambiguity prevents completion? (which scene scripts are generated)

# Clarification Prompt

If unclear, ask:

- What specific ambiguity exists about excluding `assets/` GDScript?
- What decision needs to be made about auto-formatting vs manual fixes?
- What are the possible interpretations of “committed code” for vendor kits?

# Dependencies

- Mandatory static analysis gate: Python, TypeScript/React, Godot, and duplication tooling (Milestone 902)

# Definition of Done

- CI enforces GDScript checks with a clear failure mode and documented local command.
