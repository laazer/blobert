#
# test_room_chain_generator_adversarial_2.gd
#
# Second adversarial suite for RoomChainGenerator.
# Spec: agent_context/agents/2_spec/procedural_room_chaining_spec.md (Rev 2)
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/procedural_room_chaining.md
#
# All tests are headless-safe: no SceneTree, no await, no physics.
# Red phase: RoomChainGenerator script does not exist yet — all tests report explicit FAIL.
# Green phase: all assertions pass after Implementation Agent authors the class.
#
# WHY this file exists — coverage gaps in the Test Designer suite (adversarial_1):
#
#   PRC-ADV2-01  Duplicate pool entries — pool["combat"] has two identical strings.
#                Dedup is by slot index, not by value; identical strings may both appear
#                in output. The existing PRC-GEN-3 only checks the standard pool.
#
#   PRC-ADV2-02  Pool value is a non-Array (String) — spec says runtime error may occur.
#                No existing test covers graceful-or-crash behavior for this contract
#                violation.
#
#   PRC-ADV2-03  Sequence contains empty string "" — "" is not a key in the standard
#                pool. Should fire push_error and return [] or partial. Not covered.
#
#   PRC-ADV2-04  3 combat slots but only 2 combat rooms — exhaustion at slot 3, partial
#                of length 2 returned. PRC-GEN-7 tests 2 slots / 1 room (exhaustion at
#                slot 2). This tests one step further.
#
#   PRC-ADV2-05  Exact intro path at index 0 — must equal the literal string
#                "res://scenes/rooms/room_intro_01.tscn", not merely be "in pool['intro']".
#
#   PRC-ADV2-06  Exact boss path at index 4 — must equal
#                "res://scenes/rooms/room_boss_01.tscn".
#
#   PRC-ADV2-07  Exact mutation_tease path at index 3 — must equal
#                "res://scenes/rooms/room_mutation_tease_01.tscn".
#
#   PRC-ADV2-08  Pool must not be mutated by generate() — spec: "The method must not
#                modify the caller's pool dictionary or any Array within it."
#                Zero existing tests verify the pool is untouched.
#
#   PRC-ADV2-09  Negative seed — seed = -1, seed = -2147483648 — no crash, length 5.
#
#   PRC-ADV2-10  Two separate generator instances, same seed → identical output —
#                tests that determinism is per-generate()-call, not per-instance.
#
#   PRC-ADV2-11  Stability: 10 consecutive calls with varied seeds → all return length 5,
#                no nulls, no crashes.
#
#   PRC-ADV2-12  Result never contains empty string "" even with edge pool inputs.
#
#   PRC-ADV2-13  Sequence with whitespace category " " — not in pool → push_error,
#                no crash, similar to "" but distinct key.
#
#   PRC-ADV2-14  Large exhaustion: sequence has 5 "combat" slots, pool has 2 combat
#                rooms → partial of length 2, push_error at slot 3 (index 2).
#
#   PRC-ADV2-15  Fisher-Yates vs Array.shuffle() mutation check: two calls with seed=42
#                on two fresh instances must produce same results — catches a broken impl
#                that stores RNG state at instance level and reuses it across calls.
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

const INTRO_PATH:   String = "res://scenes/rooms/room_intro_01.tscn"
const COMBAT_01:    String = "res://scenes/rooms/room_combat_01.tscn"
const COMBAT_02:    String = "res://scenes/rooms/room_combat_02.tscn"
const TEASE_PATH:   String = "res://scenes/rooms/room_mutation_tease_01.tscn"
const BOSS_PATH:    String = "res://scenes/rooms/room_boss_01.tscn"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0


func _make_generator(test_id: String) -> Object:
	var script: GDScript = load(SCRIPT_PATH)
	if script == null:
		_fail(test_id, "script not found at " + SCRIPT_PATH)
		return null
	var gen: Object = script.new()
	if gen == null:
		_fail(test_id, "script.new() returned null")
	return gen


func _pool_copy() -> Dictionary:
	var copy: Dictionary = {}
	for key in POOL:
		copy[key] = (POOL[key] as Array).duplicate()
	return copy


# ---------------------------------------------------------------------------
# PRC-ADV2-01: Duplicate pool entries — pool["combat"] = [room_a, room_a]
#
# WHY: PRC-GEN-3 only verifies no-duplicates on the *standard* pool.
# An impl that deduplicates by value (Set-based) would incorrectly drop one
# entry. Dedup must be by slot index, not by string value. With a pool of two
# identical strings, the spec's Fisher-Yates shuffle followed by draw-index
# increment will draw the same string for both combat slots, producing a
# result with a repeated path. The spec says deduplication is achieved by
# "not repeating the same pool entry" — specifically the shuffled-pool
# draw-index mechanism. For identical strings the output may contain the same
# path twice: this is consistent with the spec contract (dedup by index, not
# by value).
#
# This test does NOT assert no-duplicate output (which would be wrong for
# this input). It asserts:
#   1. No crash.
#   2. Return is Array of length 2 (both slots filled from a 2-item pool).
#   3. Each element is a String.
# CHECKPOINT: see CHECKPOINTS.md [PRC] Test Break — duplicate pool entries
# ---------------------------------------------------------------------------
func _test_prc_adv2_01() -> int:
	const TEST_ID := "PRC-ADV2-01"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	# Pool with two identical combat entries — value-dedup would wrongly
	# reduce this to a 1-item effective pool.
	var dup_pool: Dictionary = {
		"combat": [COMBAT_01, COMBAT_01],
	}
	var seq: Array = ["combat", "combat"]

	var result = gen.generate(seq, dup_pool, 42)

	if result == null:
		_fail(TEST_ID, "generate() returned null — must return Array even with duplicate pool entries")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array (type=" + str(typeof(result)) + ")")
		return 1

	if (result as Array).size() != 2:
		_fail(TEST_ID, "expected length 2 (both slots drawn by index), got " + str((result as Array).size()))
		return 1

	for i in range((result as Array).size()):
		if not result[i] is String:
			_fail(TEST_ID, "result[" + str(i) + "] is not a String")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-02: Pool value is a non-Array (String) — contract violation
#
# WHY: Spec §Assumptions: "If a pool value is not an Array, GDScript runtime
# errors may occur — this is a caller contract violation, not a class
# responsibility." No existing test exercises this path. An impl that does
# `pool[cat].size()` blindly will produce an error because String.size()
# does not exist in GDScript 4. The test documents no-crash is NOT required
# per spec — the test accepts any outcome (crash, null, error-return) and
# passes as long as the test runner itself does not abort the process.
# We cannot catch Godot runtime errors in GDScript, so the test uses a
# conditional pass approach: if no crash occurs and result is not null, pass.
# If a crash occurs, the test runner will surface it as an unhandled exception.
# This test exists to expose that the implementation has NO guard for this
# case, making the spec's "caller contract" assumption load-bearing.
#
# CHECKPOINT: [PRC] Test Break — non-Array pool value behavior
# ---------------------------------------------------------------------------
func _test_prc_adv2_02() -> int:
	const TEST_ID := "PRC-ADV2-02"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	# String instead of Array — caller contract violation per spec.
	# The spec says runtime errors may occur; this test documents that the
	# implementation makes NO defensive check here (by design).
	# We pass a typed pool with a String value to trigger the path.
	var bad_pool: Dictionary = {
		"combat": "not_an_array",
	}
	var seq: Array = ["combat"]

	# Attempt the call. If it throws a runtime error in GDScript, the test
	# runner's script.new().run_all() path will surface it. If it returns
	# gracefully, we accept any non-null Array result or [] as passing.
	var result = gen.generate(seq, bad_pool, 0)

	# If we reach here, no fatal crash occurred.
	# The spec permits runtime errors for this path; a graceful [] or any
	# Array is acceptable as a courtesy return. Null is the only strict failure.
	if result == null:
		_fail(TEST_ID, "generate() returned null; expected graceful [] or Array (or runtime error per spec)")
		return 1

	# Accept any Array return — spec does not mandate a specific outcome.
	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-03: Sequence contains empty string "" — not in pool
#
# WHY: PRC-ADV-10 tests a missing category ("fusion") — a non-empty string
# absent from the pool. The empty string "" is a degenerate case. An impl
# that does `pool.has(category)` treats "" the same as "fusion". But an
# impl that does a string-length check first might behave differently.
# Spec §Method behavior step 4: missing key → push_error + return [].
# This test verifies: no crash, result is Array (not null).
# ---------------------------------------------------------------------------
func _test_prc_adv2_03() -> int:
	const TEST_ID := "PRC-ADV2-03"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var pool_without_empty_key: Dictionary = {
		"intro": [INTRO_PATH],
	}
	var seq_with_empty: Array = ["intro", ""]

	var result = gen.generate(seq_with_empty, pool_without_empty_key, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null for sequence with empty-string category — must return Array")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array (type=" + str(typeof(result)) + ")")
		return 1

	# Per spec: missing key → return [] or partial. Either is acceptable.
	# Critically: result must NOT contain an empty string from the "" slot.
	for i in range((result as Array).size()):
		if result[i] == "":
			_fail(TEST_ID, "result[" + str(i) + "] is an empty string — empty-category slot must not produce empty-string output")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-04: 3 combat slots, pool has only 2 combat rooms → exhaustion
#              at slot 3, partial array of length 2 returned
#
# WHY: PRC-GEN-7 covers 2 slots / 1 room (partial length 1). This extends
# the exhaustion path one step further: 3 slots / 2 rooms. The implementation
# must: fill slot 1 (combat_01 or combat_02), fill slot 2 (the other), then
# fire push_error at slot 3 and return partial of length 2. An impl that
# uses Array.pop_front() without an exhaustion guard would panic or return
# wrong data here.
# ---------------------------------------------------------------------------
func _test_prc_adv2_04() -> int:
	const TEST_ID := "PRC-ADV2-04"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var limited_pool: Dictionary = {
		"combat": [COMBAT_01, COMBAT_02],
	}
	var seq_3_combat: Array = ["combat", "combat", "combat"]

	var result = gen.generate(seq_3_combat, limited_pool, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null — must return partial array")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array")
		return 1

	# Expect partial of length 2 (first two combat slots filled, third exhausted).
	if (result as Array).size() != 2:
		_fail(TEST_ID, "expected partial array of length 2 (exhaustion at slot 3), got length " + str((result as Array).size()) + ": " + str(result))
		return 1

	# Both filled slots must be valid combat paths.
	var valid_combat: Array = [COMBAT_01, COMBAT_02]
	for i in range(2):
		if not valid_combat.has(result[i]):
			_fail(TEST_ID, "result[" + str(i) + "] = \"" + str(result[i]) + "\" is not a valid combat path")
			return 1

	# The two filled slots must be distinct (since pool has 2 distinct entries).
	if result[0] == result[1]:
		_fail(TEST_ID, "both combat slots are identical — Fisher-Yates deduplication failed: \"" + str(result[0]) + "\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-05: Exact intro path at result[0]
#
# WHY: PRC-GEN-4 checks "result[0] is in pool['intro']" which passes as long
# as the result is ANY element from the intro pool array. Since intro has
# exactly one entry, "in pool" is equivalent to "equals the literal", but the
# test never asserts the literal. A mutation that substitutes a fake path into
# the intro pool copy would pass PRC-GEN-4 but fail here. This test also
# enforces the spec's exact expected values (PRC-GEN-4 clause: "must equal
# 'res://scenes/rooms/room_intro_01.tscn'").
# ---------------------------------------------------------------------------
func _test_prc_adv2_05() -> int:
	const TEST_ID := "PRC-ADV2-05"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: null or wrong length")
		return 1

	if result[0] != INTRO_PATH:
		_fail(TEST_ID, "result[0] = \"" + str(result[0]) + "\" — expected exact path \"" + INTRO_PATH + "\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-06: Exact boss path at result[4]
#
# WHY: Same gap as PRC-ADV2-05 but for the boss slot. PRC-GEN-4 only checks
# membership in pool["boss"], not the exact literal path.
# ---------------------------------------------------------------------------
func _test_prc_adv2_06() -> int:
	const TEST_ID := "PRC-ADV2-06"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: null or wrong length")
		return 1

	if result[4] != BOSS_PATH:
		_fail(TEST_ID, "result[4] = \"" + str(result[4]) + "\" — expected exact path \"" + BOSS_PATH + "\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-07: Exact mutation_tease path at result[3]
#
# WHY: Same exact-path gap for the mutation_tease slot (index 3). The spec
# says result[3] must equal "res://scenes/rooms/room_mutation_tease_01.tscn".
# PRC-GEN-4 only checks membership in pool["mutation_tease"].
# ---------------------------------------------------------------------------
func _test_prc_adv2_07() -> int:
	const TEST_ID := "PRC-ADV2-07"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: null or wrong length")
		return 1

	if result[3] != TEASE_PATH:
		_fail(TEST_ID, "result[3] = \"" + str(result[3]) + "\" — expected exact path \"" + TEASE_PATH + "\"")
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-08: Pool must not be mutated by generate()
#
# WHY: Spec: "The method must not modify the caller's pool dictionary or any
# Array within it." Zero existing tests verify this invariant. An impl that
# calls source.shuffle() or .pop_front() on the pool arrays directly would
# modify them. This test saves a snapshot of pool arrays before the call and
# compares element-by-element after.
# ---------------------------------------------------------------------------
func _test_prc_adv2_08() -> int:
	const TEST_ID := "PRC-ADV2-08"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var pool: Dictionary = _pool_copy()

	# Snapshot pool state before the call.
	var snapshot: Dictionary = {}
	for key in pool:
		snapshot[key] = (pool[key] as Array).duplicate()

	var result = gen.generate(SEQUENCE, pool, 42)

	if result == null:
		_fail(TEST_ID, "generate() returned null — cannot verify pool mutation")
		return 1

	# Compare pool arrays to snapshot.
	for key in snapshot:
		if not pool.has(key):
			_fail(TEST_ID, "pool key \"" + key + "\" was removed by generate()")
			return 1
		var before: Array = snapshot[key]
		var after: Array = pool[key]
		if before.size() != after.size():
			_fail(TEST_ID, "pool[\"" + key + "\"] size changed: " + str(before.size()) + " → " + str(after.size()))
			return 1
		for i in range(before.size()):
			if before[i] != after[i]:
				_fail(TEST_ID, "pool[\"" + key + "\"][" + str(i) + "] mutated: \"" + str(before[i]) + "\" → \"" + str(after[i]) + "\"")
				return 1

	# Check that no new keys were added to pool.
	for key in pool:
		if not snapshot.has(key):
			_fail(TEST_ID, "pool gained unexpected key \"" + key + "\" after generate()")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-09: Negative seed values — seed=-1 and seed=-2147483648
#
# WHY: PRC-ADV-7 covers seed=0, PRC-ADV-8 covers INT32_MAX. No test covers
# negative seeds. GDScript int is 64-bit; RandomNumberGenerator.seed is 64-bit
# unsigned. Assigning a negative int to seed triggers GDScript implicit cast.
# An impl that does `rng.seed = seed` with seed=-1 gets rng.seed = UINT64_MAX.
# This must not crash and must return length 5.
# ---------------------------------------------------------------------------
func _test_prc_adv2_09() -> int:
	const TEST_ID := "PRC-ADV2-09"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	# Negative seed: -1 (wraps to UINT64_MAX as rng.seed)
	var result_neg1: Array = gen.generate(SEQUENCE, _pool_copy(), -1)
	if result_neg1 == null:
		_fail(TEST_ID, "generate() returned null with seed=-1")
		return 1
	if result_neg1.size() != 5:
		_fail(TEST_ID, "seed=-1: expected length 5, got " + str(result_neg1.size()))
		return 1

	# Negative seed: INT32_MIN = -2147483648
	const INT32_MIN: int = -2147483648
	var result_min: Array = gen.generate(SEQUENCE, _pool_copy(), INT32_MIN)
	if result_min == null:
		_fail(TEST_ID, "generate() returned null with seed=INT32_MIN")
		return 1
	if result_min.size() != 5:
		_fail(TEST_ID, "seed=INT32_MIN: expected length 5, got " + str(result_min.size()))
		return 1

	# Both calls must produce consistent results (same seed → same output).
	var result_neg1_again: Array = gen.generate(SEQUENCE, _pool_copy(), -1)
	if result_neg1_again == null:
		_fail(TEST_ID, "second call with seed=-1 returned null")
		return 1
	for i in range(result_neg1.size()):
		if result_neg1[i] != result_neg1_again[i]:
			_fail(TEST_ID, "seed=-1 not deterministic at index " + str(i) + ": \"" + str(result_neg1[i]) + "\" vs \"" + str(result_neg1_again[i]) + "\"")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-10: Two separate generator instances, same seed → identical output
#
# WHY: PRC-SEED-1 and PRC-ADV-3 call generate() twice on the SAME instance.
# An impl that stores RNG state as an instance variable (rather than
# constructing it fresh per generate() call) would pass the per-instance
# determinism tests but fail cross-instance tests. This test creates two
# separate generator objects and confirms they produce the same output for
# seed=42.
# ---------------------------------------------------------------------------
func _test_prc_adv2_10() -> int:
	const TEST_ID := "PRC-ADV2-10"

	var script: GDScript = load(SCRIPT_PATH)
	if script == null:
		_fail(TEST_ID, "script not found at " + SCRIPT_PATH)
		return 1

	var gen_a: Object = script.new()
	var gen_b: Object = script.new()
	if gen_a == null or gen_b == null:
		_fail(TEST_ID, "script.new() returned null for one or both instances")
		return 1

	var result_a: Array = gen_a.generate(SEQUENCE, _pool_copy(), 42)
	var result_b: Array = gen_b.generate(SEQUENCE, _pool_copy(), 42)

	if result_a == null or result_b == null:
		_fail(TEST_ID, "one or both generate() calls returned null")
		return 1

	if result_a.size() != result_b.size():
		_fail(TEST_ID, "cross-instance result lengths differ: " + str(result_a.size()) + " vs " + str(result_b.size()))
		return 1

	for i in range(result_a.size()):
		if result_a[i] != result_b[i]:
			_fail(TEST_ID, "cross-instance divergence at index " + str(i) + ": \"" + str(result_a[i]) + "\" vs \"" + str(result_b[i]) + "\" — instance-level RNG state leaking between calls")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-11: Stability — 10 consecutive calls with varied seeds
#
# WHY: No existing test runs generate() more than 2–3 times. Stress/load
# dimension. A bad impl that mutates a class-level array or fails to reset
# per-category draw indices between calls would produce wrong-length results
# on the second or later call. Seeds use prime-spaced values to avoid trivial
# collision with the existing test seeds (42, 1, 999999, 0, 12345, etc.).
# ---------------------------------------------------------------------------
func _test_prc_adv2_11() -> int:
	const TEST_ID := "PRC-ADV2-11"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var seeds: Array = [7, 13, 97, 211, 1009, 4999, 10007, 100003, 499979, 1000003]

	for i in range(seeds.size()):
		var seed_val: int = seeds[i]
		var result = gen.generate(SEQUENCE, _pool_copy(), seed_val)

		if result == null:
			_fail(TEST_ID, "call " + str(i) + " (seed=" + str(seed_val) + ") returned null")
			return 1

		if not result is Array:
			_fail(TEST_ID, "call " + str(i) + " (seed=" + str(seed_val) + ") returned non-Array")
			return 1

		if (result as Array).size() != 5:
			_fail(TEST_ID, "call " + str(i) + " (seed=" + str(seed_val) + ") returned length " + str((result as Array).size()) + ", expected 5")
			return 1

		for j in range((result as Array).size()):
			if not result[j] is String:
				_fail(TEST_ID, "call " + str(i) + " result[" + str(j) + "] is not a String")
				return 1
			if (result[j] as String).length() == 0:
				_fail(TEST_ID, "call " + str(i) + " result[" + str(j) + "] is an empty string")
				return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-12: Result never contains empty string ""
#
# WHY: PRC-GEN-1 requires size 5 and PRC-ADV2-11 checks each element is
# non-empty in the stress loop, but there is no standalone focused test.
# A mutation of the Fisher-Yates step where `shuffled[j]` is mistakenly
# swapped with a default-initialized variable would produce "" at a slot.
# This test checks the standard-pool result for empty strings as a dedicated
# invariant.
# ---------------------------------------------------------------------------
func _test_prc_adv2_12() -> int:
	const TEST_ID := "PRC-ADV2-12"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result == null or result.size() != 5:
		_fail(TEST_ID, "prerequisite failed: null or wrong length")
		return 1

	for i in range(result.size()):
		if result[i] == "":
			_fail(TEST_ID, "result[" + str(i) + "] is an empty string — Fisher-Yates swap produced uninitialized slot")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-13: Sequence with whitespace category " " (space) — not in pool
#
# WHY: Similar to PRC-ADV2-03 (empty string) but a single space. An impl
# using strip_edges() on categories before lookup would silently normalize
# " " to "", which is also absent. Neither path should produce output for
# the whitespace slot. Test asserts: no crash, result is Array, whitespace
# category slot did not produce an entry.
# CHECKPOINT: [PRC] Test Break — whitespace category behavior
# ---------------------------------------------------------------------------
func _test_prc_adv2_13() -> int:
	const TEST_ID := "PRC-ADV2-13"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var pool_no_space: Dictionary = {
		"intro": [INTRO_PATH],
	}
	var seq_with_space: Array = ["intro", " "]

	var result = gen.generate(seq_with_space, pool_no_space, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null for sequence with whitespace category")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array")
		return 1

	# If result is non-empty, verify no slot contains a whitespace-only string.
	for i in range((result as Array).size()):
		var elem: String = result[i]
		if elem.strip_edges().length() == 0:
			_fail(TEST_ID, "result[" + str(i) + "] is blank/whitespace-only — whitespace category must not produce blank output")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-14: Large exhaustion — sequence has 5 "combat" slots, pool has 2
#              → partial of length 2, push_error at slot 3 (index 2)
#
# WHY: PRC-GEN-7 is 2 slots / 1 room (exhaustion at slot 2). PRC-ADV2-04
# is 3 slots / 2 rooms (exhaustion at slot 3). This test is the maximum
# pressure case: 5 slots against the standard 2-room pool. It verifies:
# - Partial array of length 2 is returned (not 5, not 0, not crash).
# - draw_index overflow check fires at slot 3 (i.e., not at slot 2 or 4+).
# - The two returned paths are distinct (Fisher-Yates used both pool items).
# ---------------------------------------------------------------------------
func _test_prc_adv2_14() -> int:
	const TEST_ID := "PRC-ADV2-14"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var limited_pool: Dictionary = {
		"combat": [COMBAT_01, COMBAT_02],
	}
	var seq_5_combat: Array = ["combat", "combat", "combat", "combat", "combat"]

	var result = gen.generate(seq_5_combat, limited_pool, 0)

	if result == null:
		_fail(TEST_ID, "generate() returned null for 5-slot / 2-room exhaustion")
		return 1

	if not result is Array:
		_fail(TEST_ID, "return value is not an Array")
		return 1

	# Expect partial of length 2 (both pool items drawn, exhaustion at slot 3).
	if (result as Array).size() != 2:
		_fail(TEST_ID, "expected partial array of length 2, got " + str((result as Array).size()) + ": " + str(result))
		return 1

	# The two results must be the two distinct combat paths (in some order).
	var slots: Array = [result[0], result[1]]
	if not slots.has(COMBAT_01):
		_fail(TEST_ID, "COMBAT_01 not found in partial result: " + str(slots))
		return 1
	if not slots.has(COMBAT_02):
		_fail(TEST_ID, "COMBAT_02 not found in partial result: " + str(slots))
		return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# PRC-ADV2-15: Instance-level RNG state isolation — successive calls on same
#              instance with different seeds must not bleed state
#
# WHY: PRC-SEED-1 and PRC-ADV-3 test same-seed repeatability on one instance.
# They do NOT test that calling with seed=X followed by seed=Y followed by
# seed=X again produces the same result as the first seed=X call. An impl
# that does not reset rng.seed on every call (e.g., only sets it once in
# __init__) would produce wrong results after the first call. This test:
#   1. Call gen.generate(SEQ, pool, 42)  → save result_a
#   2. Call gen.generate(SEQ, pool, 999) → discard (contaminant call)
#   3. Call gen.generate(SEQ, pool, 42)  → save result_c
#   4. Assert result_a == result_c
# ---------------------------------------------------------------------------
func _test_prc_adv2_15() -> int:
	const TEST_ID := "PRC-ADV2-15"
	var gen: Object = _make_generator(TEST_ID)
	if gen == null:
		return 1

	var result_a: Array = gen.generate(SEQUENCE, _pool_copy(), 42)
	# Contaminant call with a different seed — must not corrupt instance state.
	var _discard = gen.generate(SEQUENCE, _pool_copy(), 999)
	var result_c: Array = gen.generate(SEQUENCE, _pool_copy(), 42)

	if result_a == null or result_c == null:
		_fail(TEST_ID, "one or both generate() calls returned null")
		return 1

	if result_a.size() != result_c.size():
		_fail(TEST_ID, "result sizes differ after contaminant call: " + str(result_a.size()) + " vs " + str(result_c.size()))
		return 1

	for i in range(result_a.size()):
		if result_a[i] != result_c[i]:
			_fail(TEST_ID, "RNG state leaked across calls at index " + str(i) + ": first seed=42 gave \"" + str(result_a[i]) + "\", second seed=42 gave \"" + str(result_c[i]) + "\" (contaminant seed=999 call between them)")
			return 1

	_pass(TEST_ID)
	return 0


# ---------------------------------------------------------------------------
# run_all: entry point called by the test runner
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_room_chain_generator_adversarial_2.gd ---")
	_pass_count = 0
	_fail_count = 0

	_test_prc_adv2_01()
	_test_prc_adv2_02()
	_test_prc_adv2_03()
	_test_prc_adv2_04()
	_test_prc_adv2_05()
	_test_prc_adv2_06()
	_test_prc_adv2_07()
	_test_prc_adv2_08()
	_test_prc_adv2_09()
	_test_prc_adv2_10()
	_test_prc_adv2_11()
	_test_prc_adv2_12()
	_test_prc_adv2_13()
	_test_prc_adv2_14()
	_test_prc_adv2_15()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
