#
# test_room_chain_generator.gd
#
# Primary behavioral tests for RoomChainGenerator.
# Spec: agent_context/agents/2_spec/procedural_room_chaining_spec.md (Rev 2)
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/procedural_room_chaining.md
#
# All tests are headless-safe: no SceneTree, no await, no physics.
# Red phase: RoomChainGenerator script does not exist yet — all tests report explicit FAIL.
# Green phase: all assertions pass after Implementation Agent authors the class.
#
# Spec requirement traceability:
#   PRC-GEN-1  → generate() with standard params returns array of length 5
#   PRC-GEN-2  → all returned paths begin with "res://scenes/rooms/"
#   PRC-GEN-3  → no duplicate paths in returned array
#   PRC-GEN-4  → sequence order preserved: result[0] in intro pool, result[4] in boss pool
#   PRC-GEN-5  → generate() with seed=42 does not crash; return value is non-null
#   PRC-GEN-6  → pool category mapped to empty array [] → generate() returns []
#   PRC-GEN-7  → pool has 1 combat item, sequence requests combat twice → partial array + push_error
#   PRC-SEED-1 → same seed (42) called twice → identical arrays element by element
#   PRC-SEED-2 → seed=1 vs seed=999999 → combat slots differ (determinism divergence)
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Script loaded via load() so red-phase null returns FAIL immediately.

extends "res://tests/utils/test_utils.gd"

# ---------------------------------------------------------------------------
# Script under test
# ---------------------------------------------------------------------------

const SCRIPT_PATH: String = "res://scripts/system/room_chain_generator.gd"

# ---------------------------------------------------------------------------
# Standard test parameters (authoritative values from ticket schema)
# ---------------------------------------------------------------------------

const SEQUENCE: Array = ["intro", "combat", "combat", "mutation_tease", "boss"]

const POOL: Dictionary = {
	"intro":          ["res://scenes/rooms/room_intro_01.tscn"],
	"combat":         ["res://scenes/rooms/room_combat_01.tscn", "res://scenes/rooms/room_combat_02.tscn"],
	"mutation_tease": ["res://scenes/rooms/room_mutation_tease_01.tscn"],
	"boss":           ["res://scenes/rooms/room_boss_01.tscn"],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0


# Load and instantiate the RoomChainGenerator script.
# Returns null and records FAIL with the given test_id if the script cannot be loaded.
func _make_generator(test_id: String) -> Object:
	var script: GDScript = load(SCRIPT_PATH)
	if script == null:
		_fail(test_id, "script not found at " + SCRIPT_PATH)
		return null
	var gen: Object = script.new()
	if gen == null:
		_fail(test_id, "script.new() returned null")
	return gen


# Returns a duplicate of POOL so individual tests can mutate their copy safely.
func _pool_copy() -> Dictionary:
	var copy: Dictionary = {}
	for key in POOL:
		copy[key] = (POOL[key] as Array).duplicate()
	return copy


# ---------------------------------------------------------------------------
# PRC-GEN-1: generate() with standard params returns array of length 5
# Spec: PRC-GEN-1 — "returns an Array[String] with .size() == 5"
# ---------------------------------------------------------------------------
func _test_prc_gen_1() -> int:
	const TEST_ID := "PRC-GEN-1"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null:
		_fail(TEST_ID, "generate() returned null")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array (got " + str(typeof(result)) + ")")
		return 1

	if (result as Array).size() != 5:
		_fail(TEST_ID, "expected length 5, got " + str((result as Array).size()))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-GEN-2: all returned paths begin with "res://scenes/rooms/"
# Spec: PRC-GEN-2 — "all 5 returned paths start with the prefix 'res://scenes/rooms/'"
# ---------------------------------------------------------------------------
func _test_prc_gen_2() -> int:
	const TEST_ID := "PRC-GEN-2"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: result is null or wrong length")
		return 1

	var prefix: String = "res://scenes/rooms/"
	for i in range(result.size()):
		var path: String = result[i]
		if not path.begins_with(prefix):
			_fail(TEST_ID, "result[" + str(i) + "] = \"" + path + "\" does not begin with \"" + prefix + "\"")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-GEN-3: no two paths in returned array are identical
# Spec: PRC-GEN-3 — "the returned array has no duplicate strings"
# ---------------------------------------------------------------------------
func _test_prc_gen_3() -> int:
	const TEST_ID := "PRC-GEN-3"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: result is null or wrong length")
		return 1

	# Check all pairs for duplicates.
	for i in range(result.size()):
		for j in range(i + 1, result.size()):
			if result[i] == result[j]:
				_fail(TEST_ID, "duplicate found: result[" + str(i) + "] == result[" + str(j) + "] == \"" + str(result[i]) + "\"")
				return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-GEN-4: sequence order preserved — first path is intro, last is boss
# Spec: PRC-GEN-4 — result[0] in pool["intro"], result[4] in pool["boss"]
# Also checks result[1] and result[2] are in pool["combat"],
# and result[3] is in pool["mutation_tease"].
# ---------------------------------------------------------------------------
func _test_prc_gen_4() -> int:
	const TEST_ID := "PRC-GEN-4"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var pool: Dictionary = _pool_copy()
	var result: Array = gen.generate(SEQUENCE, pool, 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: result is null or wrong length")
		return 1

	# Slot 0: must be an intro room
	if not (pool["intro"] as Array).has(result[0]):
		_fail(TEST_ID, "result[0] = \"" + str(result[0]) + "\" is not in pool[\"intro\"]")
		return 1

	# Slot 1: must be a combat room
	if not (pool["combat"] as Array).has(result[1]):
		_fail(TEST_ID, "result[1] = \"" + str(result[1]) + "\" is not in pool[\"combat\"]")
		return 1

	# Slot 2: must be a combat room
	if not (pool["combat"] as Array).has(result[2]):
		_fail(TEST_ID, "result[2] = \"" + str(result[2]) + "\" is not in pool[\"combat\"]")
		return 1

	# Slot 3: must be a mutation_tease room
	if not (pool["mutation_tease"] as Array).has(result[3]):
		_fail(TEST_ID, "result[3] = \"" + str(result[3]) + "\" is not in pool[\"mutation_tease\"]")
		return 1

	# Slot 4: must be a boss room
	if not (pool["boss"] as Array).has(result[4]):
		_fail(TEST_ID, "result[4] = \"" + str(result[4]) + "\" is not in pool[\"boss\"]")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-GEN-5: generate() with seed=42 does not crash; return value is non-null
# Spec: PRC-GEN-5 — "coverage-only: no crash, return value non-null"
# Note: Console output "RoomChainGenerator seed: 42" is a behavioral requirement per spec
# but cannot be captured in headless GDScript tests without output redirection.
# The test asserts no crash and non-null return.
# ---------------------------------------------------------------------------
func _test_prc_gen_5() -> int:
	const TEST_ID := "PRC-GEN-5"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null:
		_fail(TEST_ID, "generate() returned null (expected non-null Array)")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-GEN-6: pool category mapped to empty array [] → generate() returns []
# Spec: PRC-GEN-6 — "pool['intro'] mapped to [] → generate(['intro'], pool, 0) returns []"
# push_error is emitted by the implementation; the test verifies return is []
# and does not crash.
# ---------------------------------------------------------------------------
func _test_prc_gen_6() -> int:
	const TEST_ID := "PRC-GEN-6"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var bad_pool: Dictionary = {
		"intro": [],
	}
	var result: Array = gen.generate(["intro"], bad_pool, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null instead of []")
		return 1

	if result.size() != 0:
		_fail(TEST_ID, "expected [] (size 0), got size " + str(result.size()) + ": " + str(result))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-GEN-7: pool has 1 combat item, sequence requests combat twice
#            → push_error emitted, partial array of length 1 returned
# Spec: PRC-GEN-7 — pool exhaustion mid-sequence → partial result (not [])
# Note: The task brief described PRC-GEN-7 as "empty array → returns []", but the
# authoritative spec (Rev 2, §Acceptance Criteria) defines it as the pool-exhaustion
# partial-return case. This test follows the spec. See CHECKPOINTS.md [PRC] Test Design
# — PRC-GEN-7 definition conflict.
# ---------------------------------------------------------------------------
func _test_prc_gen_7() -> int:
	const TEST_ID := "PRC-GEN-7"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	# Pool has only 1 combat item; sequence requests "combat" twice → exhaustion.
	var limited_pool: Dictionary = {
		"combat": ["res://scenes/rooms/room_combat_01.tscn"],
	}
	var limited_seq: Array = ["combat", "combat"]

	var result: Array = gen.generate(limited_seq, limited_pool, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null instead of a partial array")
		return 1

	# Per spec: partial array is returned — length 1 (first combat slot filled,
	# second slot missing because pool was exhausted).
	if result.size() != 1:
		_fail(TEST_ID, "expected partial array of length 1, got length " + str(result.size()) + ": " + str(result))
		return 1

	if result[0] != "res://scenes/rooms/room_combat_01.tscn":
		_fail(TEST_ID, "expected result[0] = \"res://scenes/rooms/room_combat_01.tscn\", got \"" + str(result[0]) + "\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-SEED-1: same seed → same output (called twice with seed=42)
# Spec: PRC-SEED-1 — "two calls with same seed produce identical arrays"
# ---------------------------------------------------------------------------
func _test_prc_seed_1() -> int:
	const TEST_ID := "PRC-SEED-1"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result_a: Array = gen.generate(SEQUENCE, _pool_copy(), 42)
	var result_b: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result_a == null or result_b == null:
		_fail(TEST_ID, "one or both calls returned null")
		return 1

	if result_a.size() != result_b.size():
		_fail(TEST_ID, "arrays have different sizes: " + str(result_a.size()) + " vs " + str(result_b.size()))
		return 1

	for i in range(result_a.size()):
		if result_a[i] != result_b[i]:
			_fail(TEST_ID, "result_a[" + str(i) + "] = \"" + str(result_a[i]) + "\" != result_b[" + str(i) + "] = \"" + str(result_b[i]) + "\"")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-SEED-2: different seeds → different outputs (seed=1 vs seed=999999)
# Spec: PRC-SEED-2 — "at least one combat slot differs between the two seeds"
#
# NOTE: With a 2-item combat pool, there are only 2 possible orderings:
# [combat_01, combat_02] and [combat_02, combat_01].
# Seeds 1 and 999999 are specified by the ticket as a concrete test pair.
# Per the Spec Agent's CHECKPOINT ([PRC] Spec Rev2 — PRC-SEED-2 seed pair validity),
# these seeds were declared provisional and the Test Designer Agent is required to
# verify they produce different combat orderings at implementation time.
#
# CHECKPOINT FILED: [PRC] Test Design — PRC-SEED-2 seed pair pre-computation
# Since RoomChainGenerator does not exist yet (red phase), we cannot pre-compute
# the outputs. The test is written per the spec's requirement. If the implementation
# reveals both seeds produce identical combat orderings, the seed pair must be
# updated and a new CHECKPOINT filed. The test is written to fail on convergence.
# ---------------------------------------------------------------------------
func _test_prc_seed_2() -> int:
	const TEST_ID := "PRC-SEED-2"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result_1: Array = gen.generate(SEQUENCE, _pool_copy(), 1)
	var result_999999: Array = gen.generate(SEQUENCE, _pool_copy(), 999999)

	if result_1 == null or result_999999 == null:
		_fail(TEST_ID, "one or both calls returned null")
		return 1

	if result_1.size() != 5 or result_999999.size() != 5:
		_fail(TEST_ID, "unexpected result lengths: " + str(result_1.size()) + " and " + str(result_999999.size()))
		return 1

	# Check that at least one of the two combat slots differs between the two seeds.
	# Combat slots are at indices 1 and 2 per the standard sequence.
	# NOTE: There is a theoretical chance (~50%) that both seeds happen to produce the
	# same combat ordering. If this test starts failing on a valid implementation, the
	# seed pair must be replaced with a pair confirmed to diverge.
	var combat_same: bool = (result_1[1] == result_999999[1]) and (result_1[2] == result_999999[2])

	if combat_same:
		_fail(TEST_ID, "seeds 1 and 999999 produced identical combat orderings: [" + str(result_1[1]) + ", " + str(result_1[2]) + "]. Seed pair must be replaced with a diverging pair.")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# run_all: entry point called by the test runner
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_room_chain_generator.gd ---")
	_pass_count = 0
	_fail_count = 0

	_test_prc_gen_1()
	_test_prc_gen_2()
	_test_prc_gen_3()
	_test_prc_gen_4()
	_test_prc_gen_5()
	_test_prc_gen_6()
	_test_prc_gen_7()
	_test_prc_seed_1()
	_test_prc_seed_2()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
