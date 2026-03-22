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
IMPLEMENTATION_CORE

## Revision
5

## Last Updated By
Test Breaker Agent

## Next Responsible Agent
Core Simulation Agent

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
Core Simulation Agent

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
Test Breaker Agent has extended the adversarial suite. 15 new tests added in tests/rooms/test_room_chain_generator_adversarial_2.gd (PRC-ADV2-01 through PRC-ADV2-15). Coverage gaps filled: duplicate pool entries (dedup-by-index contract), non-Array pool value (caller contract violation path), empty-string and whitespace category sequences, 3-slot / 2-room and 5-slot / 2-room exhaustion chains (extending PRC-GEN-7), exact-path assertions at indices 0/3/4, pool mutation invariant, negative seeds (-1, INT32_MIN), cross-instance determinism, stability over 10 seeds, and RNG state isolation between successive calls. Three CHECKPOINTS filed. Implementation Agent should implement RoomChainGenerator to pass all three test files: test_room_chain_generator.gd, test_room_chain_generator_adversarial.gd, and test_room_chain_generator_adversarial_2.gd.
