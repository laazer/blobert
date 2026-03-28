# test_enemy_name_utils_adversarial.gd
#
# Adversarial test suite for EnemyNameUtils.extract_family_name
# (scripts/asset_generation/enemy_name_utils.gd).
#
# Ticket: project_board/5_milestone_5_procedural_enemy_generation/backlog/godot_scene_generator_validation.md
# Spec:   agent_context/agents/2_spec/godot_scene_generator_validation_spec.md
# Stage:  TEST_BREAK
#
# PURPOSE: Expose vulnerabilities the primary suite (test_enemy_name_utils.gd) does not cover.
# Every test here targets a distinct gap — see the vulnerability note above each function.
# All tests are deterministic and produce no side effects.
#
# Adversarial dimensions covered:
#   - Boundary: single segment that IS a valid int (size-guard edge)
#   - Boundary: single segment alternate word (non-"enemy" word, no hardcoding)
#   - Boundary: negative integer trailing segment
#   - Type/structure: non-integer non-"animated" trailing segment kept
#   - Combinatorial: multiple "animated" with no trailing int
#   - Combinatorial: "animated" only repeated (no int, no family)
#   - Combinatorial: "animated" prefix (not just infix/postfix)
#   - Mutation: uppercase/mixed-case "ANIMATED" and "Animated" NOT stripped
#   - Null/empty: leading underscore with int (produces empty-string segment)
#   - Null/empty: double underscore (produces two empty-string segments)
#   - Stress: very long family name with many segments
#   - Determinism: idempotency (same input, two calls, same output)
#   - Return type: result is always a String, never null
#   - Assumption check: size >= 2 guard protects single-segment int from being stripped

extends "res://tests/utils/test_utils.gd"

const _EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Guard: verify preload is alive before any adversarial test runs
# ---------------------------------------------------------------------------

func _guard_load_ok() -> bool:
	var res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	return res != null


# ---------------------------------------------------------------------------
# GSV-ADV-1: Single-segment that IS a valid integer — size guard must fire
#
# Vulnerability: An implementation that does not check parts.size() >= 2 before
# stripping the trailing int would return "" here instead of "00".
# The spec algorithm says: "If the last segment satisfies is_valid_int(), remove it"
# but the algorithm's step 2 only applies when the size guard allows it.
# The original load_assets.gd does check `parts.size() >= 2`. A naive port
# that forgets this guard turns "00" → "" — this test catches that mutation.
# ---------------------------------------------------------------------------

func test_gsv_adv_1_single_segment_valid_int_not_stripped() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-1", "script_res is null — cannot test")
		return
	# "00" splits to ["00"], size == 1, so the size >= 2 guard prevents stripping.
	# Result: "00" is NOT stripped and is re-joined as-is → "00".
	_assert_eq(
		"00",
		EnemyNameUtils.extract_family_name("00"),
		"GSV-ADV-1 — extract_family_name('00') == '00' (single-int segment not stripped)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-2: Single non-int, non-"animated" segment other than "enemy"
#
# Vulnerability: The primary suite uses "enemy" as the single-segment passthrough
# test. A naive implementation could hardcode a check for "enemy" and still pass
# GSV-UTIL-11 while failing for any other single-word input.
# ---------------------------------------------------------------------------

func test_gsv_adv_2_single_segment_other_word_passthrough() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-2", "script_res is null — cannot test")
		return
	_assert_eq(
		"boss",
		EnemyNameUtils.extract_family_name("boss"),
		"GSV-ADV-2 — extract_family_name('boss') == 'boss' (single non-int non-animated passthrough)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-3: Trailing non-integer, non-"animated" word is preserved
#
# Vulnerability: An implementation that strips any non-numeric trailing segment
# (treating the final segment as a variant marker regardless of type) would
# incorrectly return "acid_spitter" here instead of "acid_spitter_v2".
# Only valid-int trailing segments are stripped by the algorithm.
# ---------------------------------------------------------------------------

func test_gsv_adv_3_trailing_non_int_word_kept() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-3", "script_res is null — cannot test")
		return
	# "v2" is not a valid int → not stripped. "acid_spitter_v2" → "acid_spitter_v2".
	_assert_eq(
		"acid_spitter_v2",
		EnemyNameUtils.extract_family_name("acid_spitter_v2"),
		"GSV-ADV-3 — extract_family_name('acid_spitter_v2') == 'acid_spitter_v2' (non-int suffix kept)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-4: Very long family name (many underscore-separated segments)
#
# Vulnerability: An implementation using an off-by-one index into a fixed-length
# assumption would fail with more than ~3 segments. This confirms the algorithm
# scales correctly along the full segment array.
# ---------------------------------------------------------------------------

func test_gsv_adv_4_long_family_name_many_segments() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-4", "script_res is null — cannot test")
		return
	_assert_eq(
		"a_b_c_d_e",
		EnemyNameUtils.extract_family_name("a_b_c_d_e_animated_00"),
		"GSV-ADV-4 — extract_family_name('a_b_c_d_e_animated_00') == 'a_b_c_d_e'"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-5: Multiple "animated" segments with NO trailing integer
#
# Vulnerability: An implementation that only removes "animated" after stripping
# a trailing int (wrong order, or conditional on int removal) would leave one or
# both "animated" segments when no int is present, returning "foo_animated" or
# "foo_animated_animated" instead of "foo".
# The spec algorithm strips the trailing int FIRST (step 2), then removes all
# "animated" segments in a scan (step 3). Step 3 runs even if step 2 was a no-op.
# ---------------------------------------------------------------------------

func test_gsv_adv_5_multiple_animated_no_trailing_int() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-5", "script_res is null — cannot test")
		return
	_assert_eq(
		"foo",
		EnemyNameUtils.extract_family_name("foo_animated_animated"),
		"GSV-ADV-5 — extract_family_name('foo_animated_animated') == 'foo' (animated stripped even without int)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-6: "animated" repeated twice with NO remaining family segments and NO int
#
# Vulnerability: When all segments are "animated" and no int is present, removing
# all "animated" segments should yield an empty array → "". An implementation
# that special-cases only the "animated + int" combination would return "animated"
# (the first segment) here instead of "".
# ---------------------------------------------------------------------------

func test_gsv_adv_6_animated_animated_no_int_empty_result() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-6", "script_res is null — cannot test")
		return
	_assert_eq(
		"",
		EnemyNameUtils.extract_family_name("animated_animated"),
		"GSV-ADV-6 — extract_family_name('animated_animated') == '' (all animated segments removed)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-7: "animated" as a PREFIX (not just infix or suffix)
#
# Vulnerability: The spec (R1 in GSV-UTIL risk analysis) notes that
# "animated_acid_spitter_00" is not a known filename but the algorithm is
# well-defined for it: "animated" is removed wherever it appears, leaving
# "acid_spitter". An implementation that only scans from the right, or only
# removes the penultimate segment, would fail for prefix position.
# ---------------------------------------------------------------------------

func test_gsv_adv_7_animated_prefix_stripped() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-7", "script_res is null — cannot test")
		return
	_assert_eq(
		"acid_spitter",
		EnemyNameUtils.extract_family_name("animated_acid_spitter_00"),
		"GSV-ADV-7 — extract_family_name('animated_acid_spitter_00') == 'acid_spitter' (animated prefix removed)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-8: Case sensitivity — "ANIMATED" (all-caps) must NOT be stripped
#
# Vulnerability: An implementation using case-insensitive comparison
# (e.g., segment.to_lower() == "animated") would incorrectly strip "ANIMATED".
# The spec states: "Segment comparison for 'animated' is case-sensitive.
# 'Animated' or 'ANIMATED' are NOT removed."
# ---------------------------------------------------------------------------

func test_gsv_adv_8_uppercase_animated_not_stripped() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-8", "script_res is null — cannot test")
		return
	_assert_eq(
		"ANIMATED",
		EnemyNameUtils.extract_family_name("ANIMATED"),
		"GSV-ADV-8 — extract_family_name('ANIMATED') == 'ANIMATED' (uppercase not stripped)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-9: Case sensitivity — "Animated" (title-case) must NOT be stripped
#
# Vulnerability: Same as GSV-ADV-8 but tests a different casing variant.
# An implementation using segment.begins_with("Anim") or similar heuristics
# would fail here.
# ---------------------------------------------------------------------------

func test_gsv_adv_9_title_case_animated_not_stripped() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-9", "script_res is null — cannot test")
		return
	_assert_eq(
		"acid_Animated",
		EnemyNameUtils.extract_family_name("acid_Animated"),
		"GSV-ADV-9 — extract_family_name('acid_Animated') == 'acid_Animated' (title-case Animated not stripped)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-10: Leading underscore with trailing int ("_00")
#
# Vulnerability: "_00" splits to ["", "00"]. size == 2, so the int guard fires
# and "00" is stripped, leaving [""]. Re-joining [""] with "_" yields "".
# An implementation that assumes the first segment is always non-empty would
# crash or return an incorrect value here.
# Spec R2 documents this as well-defined: result is "".
# ---------------------------------------------------------------------------

func test_gsv_adv_10_leading_underscore_with_int() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-10", "script_res is null — cannot test")
		return
	_assert_eq(
		"",
		EnemyNameUtils.extract_family_name("_00"),
		"GSV-ADV-10 — extract_family_name('_00') == '' (leading underscore + int: empty-string segment remains)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-11: Underscore-only input ("_")
#
# Vulnerability: "_" splits to ["", ""], size == 2. Neither "" is a valid int
# nor "animated". Re-joining ["", ""] with "_" yields "_". The function must
# not crash on this pathological input.
# ---------------------------------------------------------------------------

func test_gsv_adv_11_underscore_only_no_crash() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-11", "script_res is null — cannot test")
		return
	var result: String = EnemyNameUtils.extract_family_name("_")
	# Must not crash. Result is "_" (two empty segments re-joined).
	_assert_eq(
		"_",
		result,
		"GSV-ADV-11 — extract_family_name('_') == '_' (no crash on underscore-only input)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-12: Negative integer trailing segment is stripped
#
# Vulnerability: The spec explicitly states is_valid_int() returns true for
# negative integers (e.g., "-1"). An implementation that only checks for
# non-negative integers (e.g., using to_int() >= 0) would incorrectly keep "-1"
# and return "acid_spitter_-1" instead of "acid_spitter".
# ---------------------------------------------------------------------------

func test_gsv_adv_12_negative_int_trailing_stripped() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-12", "script_res is null — cannot test")
		return
	# Spec assumption: is_valid_int() returns true for "-1". Trailing "-1" is stripped.
	_assert_eq(
		"acid_spitter",
		EnemyNameUtils.extract_family_name("acid_spitter_-1"),
		"GSV-ADV-12 — extract_family_name('acid_spitter_-1') == 'acid_spitter' (negative int stripped)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-13: Idempotency — calling twice returns the same result
#
# Vulnerability: A non-pure implementation with hidden mutable state (e.g., a
# static array that accumulates segments across calls) would return a different
# result on the second call. This test verifies the function is stateless.
# ---------------------------------------------------------------------------

func test_gsv_adv_13_idempotency_same_input_same_output() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-13", "script_res is null — cannot test")
		return
	var first: String = EnemyNameUtils.extract_family_name("adhesion_bug_animated_00")
	var second: String = EnemyNameUtils.extract_family_name("adhesion_bug_animated_00")
	_assert_eq(
		first,
		second,
		"GSV-ADV-13 — extract_family_name called twice on same input returns identical result"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-14: Return type is always String — never null
#
# Vulnerability: An implementation that returns `null` for edge cases (empty
# input, all-stripped result) instead of `""` would break any caller that
# performs string concatenation or comparison on the return value without a
# null guard. GDScript's type system allows a typed `-> String` function to
# return null at runtime if the implementation is careless.
# ---------------------------------------------------------------------------

func test_gsv_adv_14_return_type_is_string_for_empty_input() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-14", "script_res is null — cannot test")
		return
	var result = EnemyNameUtils.extract_family_name("")
	_assert_true(
		result is String,
		"GSV-ADV-14a — extract_family_name('') returns a String (not null)"
	)
	var result2 = EnemyNameUtils.extract_family_name("animated")
	_assert_true(
		result2 is String,
		"GSV-ADV-14b — extract_family_name('animated') returns a String (not null)"
	)
	var result3 = EnemyNameUtils.extract_family_name("animated_00")
	_assert_true(
		result3 is String,
		"GSV-ADV-14c — extract_family_name('animated_00') returns a String (not null)"
	)


# ---------------------------------------------------------------------------
# GSV-ADV-15: "animated" in middle position only (no int, no leading/trailing)
#
# Vulnerability: An implementation that only removes "animated" when it is the
# last non-int segment, rather than scanning all positions, would incorrectly
# return "foo_bar" with "animated" still embedded when it sits between real
# name segments with no trailing int present. This exercises the scan-all-positions
# requirement distinct from the prefix test (ADV-7) and the multiple-animated test.
# ---------------------------------------------------------------------------

func test_gsv_adv_15_animated_middle_only_stripped() -> void:
	if not _guard_load_ok():
		_fail("GSV-ADV-15", "script_res is null — cannot test")
		return
	_assert_eq(
		"foo_bar",
		EnemyNameUtils.extract_family_name("foo_animated_bar"),
		"GSV-ADV-15 — extract_family_name('foo_animated_bar') == 'foo_bar' (animated in middle position removed)"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_name_utils_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Boundary: size guard
	test_gsv_adv_1_single_segment_valid_int_not_stripped()

	# Boundary: single-segment word variety
	test_gsv_adv_2_single_segment_other_word_passthrough()

	# Type/structure: non-int trailing word preserved
	test_gsv_adv_3_trailing_non_int_word_kept()

	# Stress: long family name
	test_gsv_adv_4_long_family_name_many_segments()

	# Combinatorial: multiple animated without int
	test_gsv_adv_5_multiple_animated_no_trailing_int()

	# Combinatorial: all animated segments, no int
	test_gsv_adv_6_animated_animated_no_int_empty_result()

	# Combinatorial: animated prefix position
	test_gsv_adv_7_animated_prefix_stripped()

	# Mutation: case-sensitive — uppercase ANIMATED not stripped
	test_gsv_adv_8_uppercase_animated_not_stripped()

	# Mutation: case-sensitive — title-case Animated not stripped
	test_gsv_adv_9_title_case_animated_not_stripped()

	# Null/empty: leading underscore with int
	test_gsv_adv_10_leading_underscore_with_int()

	# Null/empty: underscore-only input
	test_gsv_adv_11_underscore_only_no_crash()

	# Boundary: negative integer trailing segment
	test_gsv_adv_12_negative_int_trailing_stripped()

	# Determinism: idempotency
	test_gsv_adv_13_idempotency_same_input_same_output()

	# Return type: always String
	test_gsv_adv_14_return_type_is_string_for_empty_input()

	# Combinatorial: animated in middle position only
	test_gsv_adv_15_animated_middle_only_stripped()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
