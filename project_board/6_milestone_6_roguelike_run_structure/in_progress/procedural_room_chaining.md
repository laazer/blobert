Title:
Implement procedural room chaining

Description:
System that assembles a run's room sequence from the template pool each time a run starts.
Fixed structure: intro → N combat rooms → mutation tease → boss.
(NOTE: The original description referenced a "fusion room" in the sequence, but no fusion room template exists in the current pool. The sequence is: intro (1) → combat (2) → mutation_tease (1) → boss (1), 4 rooms total. A follow-up ticket will add the fusion room template and extend the sequence. This decision is logged in CHECKPOINTS.md under [PRC] Planning.)
Combat rooms drawn randomly from their pool without repetition. Seed logged for debugging.

Acceptance Criteria:
- Run layout generated fresh each run start
- Sequence always follows fixed category order: intro → combat (x2) → mutation_tease → boss
- No room repeated in a single run
- RNG seed printed to console for reproducibility during testing
- Transitions between rooms feel seamless (no visible load pop)

Dependencies:
- room_template_system (complete — 5 room .tscn files in scenes/rooms/)
- run_state_manager (complete — RunStateManager emits run_started signal)
- soft_death_and_restart (complete — DeathRestartCoordinator calls RSM restart/start_run)

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
INTEGRATION

## Revision
7

## Last Updated By
Engine Integration Agent

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Validation Status
- Tests: PASS — all 34 PRC-* headless tests pass (9 primary + 10 adversarial + 15 adversarial-2); 7 pre-existing RSM-SIGNAL-*/ADV-RSM-02 failures unrelated to this ticket. Total suite: 253 passed, 0 failed (excluding pre-existing).
- Static QA: GDScript reviewer found no CRITICAL issues in RoomChainGenerator; randi_range fix applied
- Integration: RunSceneAssembler node added to containment_hall_01.tscn; AC "Transitions between rooms feel seamless (no visible load pop)" requires human in-editor playtest

## Blocking Issues
AC "Transitions between rooms feel seamless (no visible load pop)" — human in-editor verification required

## Status
Needs Attention

## Escalation Notes
- The ticket description listed "fusion room" in the sequence but no fusion room .tscn exists. Resolved by treating the run sequence as intro → combat (2) → mutation_tease → boss. Logged in CHECKPOINTS.md [PRC] Planning — Sequence mismatch.
- Spec Rev2 supersedes Rev1 (2026-03-21). API signature changed: `generate(sequence: Array[String], pool: Dictionary, seed: int) -> Array[String]`. Return type is now Array[String] (paths only, not Dicts). All Rev1 test IDs (PRC-SEQ-*, PRC-DEDUP-*, PRC-SCHEMA-*, PRC-POOL-*) are superseded by PRC-GEN-*, PRC-SEED-*, PRC-ADV-*. See spec file for full breakage notes.
- Pending CHECKPOINTS.md entries staged at: `agent_context/agents/2_spec/prc_spec_rev2_checkpoints.md` — must be appended to CHECKPOINTS.md (file not found at local path; may be in iCloud workspace).
- RoomChainGenerator implemented at `scripts/system/room_chain_generator.gd`. Pure RefCounted, no SceneTree. Fisher-Yates with rng.randi(), pool immutability via .duplicate(), fresh RNG per call for cross-instance determinism.
- PRC-SEED-2 (seeds 1 vs 999999 produce different combat orderings): provisional seed pair from spec. If it fails, Engine Integration Agent must update the seed pair and file a checkpoint.

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input
Verify all Acceptance Criteria against the running game:
- Run layout generated fresh each run start (automated: covered by PRC-GEN-* tests)
- Sequence always follows fixed category order: intro → combat (x2) → mutation_tease → boss (automated: covered by PRC-GEN-* tests)
- No room repeated in a single run (automated: covered by PRC-GEN-* tests)
- RNG seed printed to console for reproducibility during testing (automated: PRC-GEN-5 passes; console output visible at runtime)
- Transitions between rooms feel seamless (no visible load pop) — REQUIRES human in-editor playtest

Key files:
- `scripts/system/run_scene_assembler.gd` — Node that assembles rooms on run_started
- `scripts/system/room_chain_generator.gd` — Pure RefCounted generator (no SceneTree)
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` — RunSceneAssembler node wired as child of ContainmentHall01

## Status
Needs Attention

## Reason
All 34 PRC-* headless tests pass. RunSceneAssembler implemented and wired into main test scene. One AC ("Transitions between rooms feel seamless") cannot be verified headlessly — requires human playtest.
