# Checkpoint Index

This file is intentionally small and acts as an index only.
Full checkpoint bodies live under `project_board/checkpoints/`.

## Index-only rules (agents must follow)

- **Do not** append checkpoint decision bodies here: no `**Would have asked:**`, no `**Assumption made:**`, no multi-paragraph assumptions.
- **Do** write those only under `project_board/checkpoints/<ticket-id>/<run-id>.md`.
- **Do** keep entries here short: run/resume headers, ticket path, stage, `Log:` path, and optional one-line outcome summaries.

## Migration

- Monolithic log frozen on 2026-03-30:
  - `project_board/checkpoints/frozen/CHECKPOINTS-2026-03-30-frozen.md`
- New write target for checkpoint details:
  - `project_board/checkpoints/<ticket-id>/<run-id>.md`
- Backward compatibility:
  - If a consumer cannot find a scoped log yet, it may read the frozen file.

---

## Run: 2026-04-11T23-59-00Z-planner-decomposition
- Ticket: `project_board/inbox/in_progress/registry-fix-versions-slots-load.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/registry-fix-versions-slots-load/run-2026-04-11-autopilot.md`
- Outcome: Execution plan appended to ticket; assumptions logged in scoped checkpoint.

## Run: 2026-04-11T22-15-00Z-autopilot-description
- Queue mode: single ticket (created from description)
- Queue scope: registry: multiple versions, empty slots, load existing models
- Lean: no
- Log root: project_board/checkpoints/registry-fix-versions-slots-load/
- Created ticket from description: project_board/inbox/in_progress/registry-fix-versions-slots-load.md

## Run: 2026-04-11T19-59-11Z-autopilot-description
- Queue mode: single ticket (created from description)
- Queue scope: "fix the extras so that the shell is actually visible and spikes properly appear on top too"
- Lean: no
- Log root: project_board/checkpoints/extras-shell-visible-spikes-on-top/
- Created ticket from description: project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md

## Run: 2026-04-11T00-00-00Z-autopilot-single
- Queue mode: single ticket
- Queue scope: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/17_zone_extras_offset_xyz_controls.md` → `in_progress/17_zone_extras_offset_xyz_controls.md`
- Lean: no
- Log root: project_board/checkpoints/17_zone_extras_offset_xyz_controls/

## Resume: 2026-04-11T15-05-00Z-ap-continue
- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/done/17_zone_extras_offset_xyz_controls.md`
- Resuming at Stage: `TEST_BREAK` → implementation → `COMPLETE`
- Next Agent: (completed in-session) Engine Integration + frontend + AC closure
- Log: `project_board/checkpoints/17_zone_extras_offset_xyz_controls/run-2026-04-11-test-break.md`

### [17_zone_extras_offset_xyz_controls] — OUTCOME: COMPLETE
Per-zone offset X/Y/Z in `animated_build_options` + `zone_geometry_extras_attach`; Extras UI `SUFFIX_ORDER` / `suffixRank` / `rowDisabled`; tests + `timeout 300 ci/scripts/run_tests.sh` exit 0.
Log: `project_board/checkpoints/17_zone_extras_offset_xyz_controls/run-2026-04-11-test-break.md`

## Run: 2026-04-11T20-30-00Z-planner-decomposition
- Ticket: `project_board/inbox/in_progress/extras-shell-visible-spikes-on-top.md`
- Stage: PLANNING → SPECIFICATION
- Next Agent: Spec Agent
- Log: `project_board/checkpoints/extras-shell-visible-spikes-on-top/run-2026-04-11-autopilot.md`
