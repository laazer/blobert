# [M901-07-enemy-builder-template] Specification Checkpoint Log

- Ticket: `project_board/901_milestone_901_asset_generation_refactoring/ready/07_enemy_builder_template.md`
- Run: `2026-04-22T12:10:00Z`
- Stage: `SPECIFICATION`

### [M901-07-enemy-builder-template] SPECIFICATION — parity validation contract
**Would have asked:** Should acceptance require byte-identical GLB output for all 5 enemies, or behavior-level parity constraints?
**Assumption made:** Enforce behavior-level parity (build success/failure, deterministic seeded behavior, object/material/zone-extra invariants) and avoid brittle byte-level equality constraints.
**Confidence:** Medium

### [M901-07-enemy-builder-template] SPECIFICATION — LOC threshold interpretation
**Would have asked:** Is the 80-120 LOC target for each enemy builder a hard gate or a quality target that can flex to preserve behavior/readability?
**Assumption made:** Treat 80-120 LOC as target guidance; enforce measurable reduction and deduplication as hard requirements while allowing minor LOC variance when needed for safe parity.
**Confidence:** High
