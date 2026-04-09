# M9-ATRAD — Scoped Checkpoint Log

Run ID: `run-2026-04-09-autopilot`  
Ticket: `project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/09_automated_tests_registry_allowlist_delete.md`

### [M9-ATRAD] PLANNING — bootstrap malformed ticket
**Would have asked:** Ticket lacks required workflow state and next-action blocks; should I normalize it before running staged agents?  
**Assumption made:** Yes. Normalize immediately with conservative default `Stage=PLANNING`, `Revision=1`, `Next Responsible Agent=Planner Agent`, then continue pipeline.  
**Confidence:** High

### [M9-ATRAD] PLANNING — cross-cutting test-scope baseline
**Would have asked:** Should this ticket author new frontend tests if backend contract coverage already validates allowlist/delete invariants end-to-end?  
**Assumption made:** Prefer backend pytest-first for contract-critical invariants and add frontend tests only where behavior is UI-specific and not already guaranteed by lower-layer API tests.  
**Confidence:** Medium

### [M9-ATRAD] SPECIFICATION — minimum delete-invariant scenario scope
**Would have asked:** For the required delete scenario inherited from ticket `07`, should this ticket encode only the blocked sole-in-use invariant or also require one successful in-use delete with post-state cleanup assertions?  
**Assumption made:** Require both: one blocked invariant case (safety guard) and one allowed delete case with deterministic post-delete invariant checks; this is the conservative cross-cutting baseline to catch both over-permissive and over-restrictive regressions.
**Confidence:** High

### [M9-ATRAD] TEST_DESIGN — strict rejection status class pinning
**Would have asked:** Should ATRAD allowlist/traversal rejection tests assert a broad class (`400/403`) or exact status per vector?  
**Assumption made:** Pin exact statuses where router contract is deterministic from current implementation (`allowlist-prefix` -> `403`, traversal normalization failure -> `400`) to maximize regression detection strictness.
**Confidence:** Medium

### [M9-ATRAD] TEST_DESIGN — draft-only spawn pool fallback semantics
**Would have asked:** For families containing only draft versions, should default spawn-eligible response be empty or include fallback entries?  
**Assumption made:** Assert empty list (`[]`) as strictest defensible contract for default reader, because draft entries must never leak into default game-pool semantics.
**Confidence:** Medium

### [M9-ATRAD] TEST_BREAK — draft delete confirmation strictness
**Would have asked:** If `confirm_text` is provided for a draft delete but is blank/whitespace, should backend treat it as omitted (allow) or malformed (reject)?  
**Assumption made:** Reject blank explicit `confirm_text` with `400` as the conservative safety contract; explicit but empty confirmation should not bypass intent checks.  
**Confidence:** Medium
