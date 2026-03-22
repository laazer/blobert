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
TEST_BREAK

## Revision
4

## Last Updated By
Test Designer Agent

## Next Responsible Agent
Test Breaker Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
None

## Escalation Notes
- The ticket description listed "fusion room" in the sequence but no fusion room .tscn exists. Resolved by treating the run sequence as intro → combat (2) → mutation_tease → boss. Logged in CHECKPOINTS.md [PRC] Planning — Sequence mismatch.
- Spec Rev2 supersedes Rev1 (2026-03-21). API signature changed: `generate(sequence: Array[String], pool: Dictionary, seed: int) -> Array[String]`. Return type is now Array[String] (paths only, not Dicts). All Rev1 test IDs (PRC-SEQ-*, PRC-DEDUP-*, PRC-SCHEMA-*, PRC-POOL-*) are superseded by PRC-GEN-*, PRC-SEED-*, PRC-ADV-*. See spec file for full breakage notes.
- Pending CHECKPOINTS.md entries staged at: `agent_context/agents/2_spec/prc_spec_rev2_checkpoints.md` — must be appended to CHECKPOINTS.md.

---

# NEXT ACTION

## Next Responsible Agent
Test Breaker Agent

## Required Input Schema
```json
{
  "spec_file": "agent_context/agents/2_spec/procedural_room_chaining_spec.md",
  "spec_revision": 2,
  "room_pool": {
    "intro": ["res://scenes/rooms/room_intro_01.tscn"],
    "combat": ["res://scenes/rooms/room_combat_01.tscn", "res://scenes/rooms/room_combat_02.tscn"],
    "mutation_tease": ["res://scenes/rooms/room_mutation_tease_01.tscn"],
    "boss": ["res://scenes/rooms/room_boss_01.tscn"]
  },
  "run_sequence": ["intro", "combat", "combat", "mutation_tease", "boss"],
  "RoomChainGenerator_class": "extends RefCounted — pure logic, no SceneTree API",
  "RoomChainGenerator_signature": "func generate(sequence: Array[String], pool: Dictionary, seed: int) -> Array[String]",
  "RunSceneAssembler_class": "extends Node — scene loading + positioning, owns its own RunStateManager instance",
  "test_prefix": "PRC-",
  "test_paths": {
    "primary": "res://tests/rooms/test_room_chain_generator.gd",
    "adversarial": "res://tests/rooms/test_room_chain_generator_adversarial.gd"
  }
}
```

## Status
Proceed

## Reason
Test suite complete. Two test files written at tests/rooms/test_room_chain_generator.gd (9 tests: PRC-GEN-1 through PRC-GEN-7, PRC-SEED-1, PRC-SEED-2) and tests/rooms/test_room_chain_generator_adversarial.gd (10 tests: PRC-ADV-1 through PRC-ADV-10). All tests confirmed to parse and execute in red phase (all FAILing with "script not found" — correct behavior before implementation). Staged CHECKPOINTS from prc_spec_rev2_checkpoints.md merged into CHECKPOINTS.md. Three new Test Design checkpoints filed. Test Breaker Agent should attempt to find flaws in the test logic and spec coverage before passing to Implementation Agent.
