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
COMPLETE

## Revision
8

## Last Updated By
Human

## Next Responsible Agent
Human

## Validation Status
- Tests: PASS — all 34 PRC-* headless tests pass (9 primary + 10 adversarial + 15 adversarial-2); 7 pre-existing RSM-SIGNAL-*/ADV-RSM-02 failures unrelated to this ticket. Total suite: 253 passed, 0 failed (excluding pre-existing).
- Static QA: GDScript reviewer found no CRITICAL issues in RoomChainGenerator; randi_range fix applied.
- AC coverage detail:
  - AC "Run layout generated fresh each run start": covered by PRC-GEN-5 (no crash, non-null return). RunSceneAssembler uses Time.get_ticks_msec() as seed on every run_started signal, guaranteeing a different layout per run.
  - AC "Sequence always follows fixed category order: intro → combat (x2) → mutation_tease → boss": covered by PRC-GEN-4 (slot-by-pool membership), PRC-ADV2-05 (exact intro path at index 0), PRC-ADV2-06 (exact boss path at index 4), PRC-ADV2-07 (exact mutation_tease path at index 3).
  - AC "No room repeated in a single run": covered by PRC-GEN-3 (no duplicate paths in result), PRC-ADV-6 (both combat rooms appear exactly once).
  - AC "RNG seed printed to console for reproducibility": evidenced by code inspection — `print("[RoomChainGenerator] seed: %d" % seed)` is unconditional at line 23 of scripts/system/room_chain_generator.gd, before any early return. Confirmed present during Static QA review. PRC-GEN-5 passing confirms the code path executes. Automated stdout capture is not available in the headless test runner; code review is the evidence basis for this criterion.
  - AC "Transitions between rooms feel seamless (no visible load pop)": Human playtest 2026-03-27: PASS — 5-room sequence loads; transitions between rooms seamless with no visible pop or freeze.
- Integration: RunSceneAssembler node added to containment_hall_01.tscn as child of ContainmentHall01. Rooms are positioned end-to-end using Exit Marker3D local X as the cursor advance. push_warning fires for rooms missing an Exit node, falling back to 30.0 units.

## Blocking Issues
None

## Status
Proceed

## Escalation Notes
- The ticket description listed "fusion room" in the sequence but no fusion room .tscn exists. Resolved by treating the run sequence as intro → combat (2) → mutation_tease → boss. Logged in CHECKPOINTS.md [PRC] Planning — Sequence mismatch.
- Spec Rev2 supersedes Rev1 (2026-03-21). API signature changed: `generate(sequence: Array[String], pool: Dictionary, seed: int) -> Array[String]`. Return type is now Array[String] (paths only, not Dicts). All Rev1 test IDs (PRC-SEQ-*, PRC-DEDUP-*, PRC-SCHEMA-*, PRC-POOL-*) are superseded by PRC-GEN-*, PRC-SEED-*, PRC-ADV-*. See spec file for full breakage notes.
- Pending CHECKPOINTS.md entries staged at: `agent_context/agents/2_spec/prc_spec_rev2_checkpoints.md` — must be appended to CHECKPOINTS.md (file not found at local path; may be in iCloud workspace).
- RoomChainGenerator implemented at `scripts/system/room_chain_generator.gd`. Pure RefCounted, no SceneTree. Fisher-Yates with rng.randi(), pool immutability via .duplicate(), fresh RNG per call for cross-instance determinism.
- PRC-SEED-2 (seeds 1 vs 999999 produce different combat orderings): provisional seed pair from spec. If it fails, Engine Integration Agent must update the seed pair and file a checkpoint.

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input
Manual in-editor playtest to verify AC "Transitions between rooms feel seamless (no visible load pop)":
1. Open the project in the Godot editor.
2. Run scenes/levels/containment_hall_01/containment_hall_01.tscn.
3. Observe that all 5 rooms (intro → combat → combat → mutation_tease → boss) appear end-to-end.
4. Confirm no visible pop, freeze, or missing room during the load sequence.
5. Confirm the Output panel shows a line matching "[RoomChainGenerator] seed: <number>" (verifying AC "RNG seed printed to console").
6. Record the observation (e.g., update Validation Status and remove the Blocking Issue, then advance Stage to COMPLETE and move ticket to done/).

Key files:
- `scripts/system/run_scene_assembler.gd` — Node that assembles rooms on run_started
- `scripts/system/room_chain_generator.gd` — Pure RefCounted generator (no SceneTree)
- `scenes/levels/containment_hall_01/containment_hall_01.tscn` — RunSceneAssembler node wired as child of ContainmentHall01

## Status
Needs Attention

## Reason
4 of 5 acceptance criteria are fully evidenced by automated headless tests and code review. One criterion ("Transitions between rooms feel seamless — no visible load pop") is inherently a visual/runtime judgment that cannot be verified headlessly. The ticket is held at INTEGRATION pending this single human playtest. Once the playtest is recorded, Stage may be advanced to COMPLETE.
