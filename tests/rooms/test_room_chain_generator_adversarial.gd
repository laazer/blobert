#
# test_room_chain_generator_adversarial.gd
#
# Adversarial behavioral tests for RoomChainGenerator.
# Spec: agent_context/agents/2_spec/procedural_room_chaining_spec.md (Rev 2)
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/procedural_room_chaining.md
#
# All tests are headless-safe: no SceneTree, no await, no physics.
# Red phase: RoomChainGenerator script does not exist yet — all tests report explicit FAIL.
# Green phase: all assertions pass after Implementation Agent authors the class.
#
# Spec requirement traceability:
#   PRC-ADV-1  → single-slot sequence with 1-item pool → length 1, path contains "intro"
#   PRC-ADV-2  → 2 combat slots, exactly 2 combat rooms → no error, length 5
#   PRC-ADV-3  → seed=12345 called twice → identical results (determinism repeat)
#   PRC-ADV-4  → empty sequence [] → returns [], no crash
#   PRC-ADV-5  → 1-item pool, sequence requests it once → returns exact path
#   PRC-ADV-6  → 2 combat slots, 2-item pool → both rooms appear exactly once
#   PRC-ADV-7  → seed=0 → no crash, returns length 5
#   PRC-ADV-8  → seed=2147483647 (INT32_MAX) → no crash, returns length 5
#   PRC-ADV-9  → return value type check: Array, each element is String
#   PRC-ADV-10 → sequence category not in pool → push_error, returns [] or partial, no crash
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Script loaded via load() so red-phase null returns FAIL immediately.

extends Object

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


func _pass(test_id: String) -> void:
	_pass_count += 1
	print("  PASS [" + test_id + "]")


func _fail(test_id: String, reason: String) -> void:
	_fail_count += 1
	print("  FAIL [" + test_id + "] " + reason)


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
# PRC-ADV-1: sequence=["intro"], pool with only intro key
#            → returns array of length 1, path is the intro room
# Spec: single-slot degenerate sequence, well-formed pool
# ---------------------------------------------------------------------------
func _test_prc_adv_1() -> int:
	const TEST_ID := "PRC-ADV-1"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var single_pool: Dictionary = {
		"intro": ["res://scenes/rooms/room_intro_01.tscn"],
	}
	var single_seq: Array = ["intro"]

	var result: Array = gen.generate(single_seq, single_pool, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null")
		return 1

	if result.size() != 1:
		_fail(TEST_ID, "expected length 1, got " + str(result.size()))
		return 1

	if not result[0].contains("intro"):
		_fail(TEST_ID, "result[0] = \"" + str(result[0]) + "\" does not contain \"intro\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-2: pool has exactly 2 combat rooms, sequence has 2 combat slots
#            → no push_error, both slots filled (full length 5)
# Spec: exact pool-size match for combat — deduplication succeeds
# ---------------------------------------------------------------------------
func _test_prc_adv_2() -> int:
	const TEST_ID := "PRC-ADV-2"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	# Standard params already satisfy this: 2 combat rooms in pool, 2 combat slots in sequence.
	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null")
		return 1

	if result.size() != 5:
		_fail(TEST_ID, "expected length 5 (both combat slots filled), got " + str(result.size()))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-3: generate() called twice with seed=12345 → identical results
# Spec: PRC-ADV-3 — determinism repeat with explicit seed
# ---------------------------------------------------------------------------
func _test_prc_adv_3() -> int:
	const TEST_ID := "PRC-ADV-3"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result_a: Array = gen.generate(SEQUENCE, _pool_copy(), 12345)
	var result_b: Array = gen.generate(SEQUENCE, _pool_copy(), 12345)

	if result_a == null or result_b == null:
		_fail(TEST_ID, "one or both calls returned null")
		return 1

	if result_a.size() != result_b.size():
		_fail(TEST_ID, "array lengths differ: " + str(result_a.size()) + " vs " + str(result_b.size()))
		return 1

	for i in range(result_a.size()):
		if result_a[i] != result_b[i]:
			_fail(TEST_ID, "divergence at index " + str(i) + ": \"" + str(result_a[i]) + "\" vs \"" + str(result_b[i]) + "\"")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-4: generate() with empty sequence [] → returns [], no crash
# Spec: PRC-ADV-4 — "empty sequence is valid degenerate input; returns []"
# Per spec §Method behavior step 2: empty sequence returns [] with no push_error.
# ---------------------------------------------------------------------------
func _test_prc_adv_4() -> int:
	const TEST_ID := "PRC-ADV-4"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate([], _pool_copy(), 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null instead of []")
		return 1

	if result.size() != 0:
		_fail(TEST_ID, "expected [] (size 0), got size " + str(result.size()) + ": " + str(result))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-5: pool has 1 item for a category, sequence requests it once
#            → succeeds, returns that exact path
# Spec: PRC-ADV-5 — single-item pool single-draw
# ---------------------------------------------------------------------------
func _test_prc_adv_5() -> int:
	const TEST_ID := "PRC-ADV-5"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var single_item_pool: Dictionary = {
		"boss": ["res://scenes/rooms/room_boss_01.tscn"],
	}
	var single_item_seq: Array = ["boss"]

	var result: Array = gen.generate(single_item_seq, single_item_pool, 99)

	if result == null:
		_fail(TEST_ID, "generate() returned null")
		return 1

	if result.size() != 1:
		_fail(TEST_ID, "expected length 1, got " + str(result.size()))
		return 1

	if result[0] != "res://scenes/rooms/room_boss_01.tscn":
		_fail(TEST_ID, "expected \"res://scenes/rooms/room_boss_01.tscn\", got \"" + str(result[0]) + "\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-6: 2 combat slots, pool combat has 2 rooms → both combat rooms appear in result
# Spec: PRC-ADV-6 — exhaustive deduplication: all pool items used when slots == pool size
# The Fisher-Yates shuffle of a 2-item pool always produces both items in some order.
# ---------------------------------------------------------------------------
func _test_prc_adv_6() -> int:
	const TEST_ID := "PRC-ADV-6"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: result is null or wrong length")
		return 1

	var combat_01: String = "res://scenes/rooms/room_combat_01.tscn"
	var combat_02: String = "res://scenes/rooms/room_combat_02.tscn"

	# Both combat rooms must appear among result[1] and result[2].
	var combat_slots: Array = [result[1], result[2]]
	if not combat_slots.has(combat_01):
		_fail(TEST_ID, "combat_01 not found in combat slots " + str(combat_slots))
		return 1
	if not combat_slots.has(combat_02):
		_fail(TEST_ID, "combat_02 not found in combat slots " + str(combat_slots))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-7: generate() with seed=0 → no crash, returns array of length 5
# Spec: PRC-ADV-7 — boundary: seed=0 is a valid seed value
# ---------------------------------------------------------------------------
func _test_prc_adv_7() -> int:
	const TEST_ID := "PRC-ADV-7"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null with seed=0")
		return 1

	if result.size() != 5:
		_fail(TEST_ID, "expected length 5 with seed=0, got " + str(result.size()))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-8: generate() with seed=2147483647 (INT32_MAX) → no crash, returns length 5
# Spec: PRC-ADV-8 — boundary: largest positive 32-bit int seed
# ---------------------------------------------------------------------------
func _test_prc_adv_8() -> int:
	const TEST_ID := "PRC-ADV-8"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	const INT32_MAX: int = 2147483647
	var result: Array = gen.generate(SEQUENCE, _pool_copy(), INT32_MAX)

	if result == null:
		_fail(TEST_ID, "generate() returned null with seed=2147483647")
		return 1

	if result.size() != 5:
		_fail(TEST_ID, "expected length 5 with seed=2147483647, got " + str(result.size()))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-9: return value type check — result is Array, each element is String
# Spec: PRC-ADV-9 — "return value type: Array, each element is String"
# Verifies typed return: the spec mandates Array[String], not Array of mixed types.
# ---------------------------------------------------------------------------
func _test_prc_adv_9() -> int:
	const TEST_ID := "PRC-ADV-9"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null:
		_fail(TEST_ID, "generate() returned null")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array (type=" + str(typeof(result)) + ")")
		return 1

	for i in range((result as Array).size()):
		var elem = result[i]
		if not elem is String:
			_fail(TEST_ID, "result[" + str(i) + "] is not a String (type=" + str(typeof(elem)) + ", value=" + str(elem) + ")")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV-10: sequence requests category not in pool → push_error, returns [] or partial
#             The key requirement is no crash.
# Spec: PRC-ADV-10 — missing pool key → push_error + return [] (validation phase abort)
# Per spec: if category from sequence is not present as a key in pool, push_error and
# return [] (the missing-key check happens before any draw, so no partial result).
# ---------------------------------------------------------------------------
func _test_prc_adv_10() -> int:
	const TEST_ID := "PRC-ADV-10"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	# "fusion" category is not present in the pool.
	var incomplete_pool: Dictionary = {
		"intro": ["res://scenes/rooms/room_intro_01.tscn"],
	}
	var bad_seq: Array = ["intro", "fusion"]

	var result = gen.generate(bad_seq, incomplete_pool, 0)

	# Must not crash (if we reached here, it did not crash).
	# Result must be [] or a partial Array — either is acceptable per the spec's
	# statement "returns [] or partial (no crash)".
	if result == null:
		_fail(TEST_ID, "generate() returned null instead of [] or partial Array")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array (type=" + str(typeof(result)) + ")")
		return 1

	# Per spec §Method behavior step 4: missing key is caught in the validation phase
	# before any draws, so result should be []. Accept both [] and partial as valid
	# no-crash outcomes, but prefer [] per spec.
	# NOTE: If implementation returns partial (non-empty) array, that is also accepted
	# as a no-crash outcome per the task brief. Only a crash or null is a failure.
	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# run_all: entry point called by the test runner
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_room_chain_generator_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	_test_prc_adv_1()
	_test_prc_adv_2()
	_test_prc_adv_3()
	_test_prc_adv_4()
	_test_prc_adv_5()
	_test_prc_adv_6()
	_test_prc_adv_7()
	_test_prc_adv_8()
	_test_prc_adv_9()
	_test_prc_adv_10()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
