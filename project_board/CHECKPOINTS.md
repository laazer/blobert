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

## Run Index

### 2026-03-30-migration
- Ticket: N/A (checkpoint system migration)
- Stage: migration
- Log: `project_board/checkpoints/frozen/CHECKPOINTS-2026-03-30-frozen.md`
- Notes: monolithic checkpoint log frozen and replaced by index-only file.

### first_4_families_in_level / run-2026-03-30-01
- Ticket: `project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md`
- Stage: IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE
- Log: `project_board/checkpoints/first_4_families_in_level/run-2026-03-30-01.md`
- Outcome: generate_enemy_scenes.gd written; 12 .tscn files generated and committed; level updated with 4 family enemies; all 54 FESG tests pass.
