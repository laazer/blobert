# M9-EGMS scoped checkpoint log

- Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/backlog/05_editor_ui_game_model_selection.md`
- Run: `2026-04-09T10-51-52Z-autopilot-single`

### [M9-EGMS] PLANNING — runtime reload + empty enemy slot policy
**Would have asked:** Should player model selection hot-reload immediately in active play sessions, and should empty enemy slot lists hard-fail or fallback?
**Assumption made:** Spec must define deterministic behavior; until then, plan requires explicit contracts for both (A) immediate reload vs restart requirement and (B) empty enemy-slot fallback vs validation error, with tests enforcing whichever is selected.
**Confidence:** Medium

### [M9-EGMS] SPECIFICATION — runtime application and empty-slot fallback
**Would have asked:** Do we require hot-reload for player visual changes, and should enemy families with zero assigned slots block gameplay or fall back?
**Assumption made:** Use restart-required semantics for player active visual changes (no hot reload guarantee) and apply deterministic fallback to the family legacy default visual when slot list is empty, aligned with MRVC-11 empty-pool behavior.
**Confidence:** Medium

### [M9-EGMS] TEST_BREAK — mixed-invalid slot payload status precedence
**Would have asked:** For `PUT /api/registry/model/enemies/{family}/slots` containing both duplicate IDs and unknown IDs, should validation consistently return 400 or 404 first?
**Assumption made:** Encode only the conservative contract: request is rejected atomically and prior slot state remains unchanged; status may be 400 or 404 until precedence is explicitly specified.
**Confidence:** Medium

### [M9-EGMS] TEST_BREAK — service-layer mixed-invalid precedence tightening
**Would have asked:** Should service-level mixed-invalid slot payloads prefer duplicate-ID rejection before unknown-version checks to keep failure semantics deterministic?
**Assumption made:** Yes; enforce deterministic duplicate-first rejection at service level, and encode this in adversarial tests while still preserving atomic no-partial-write guarantees.
**Confidence:** Medium
