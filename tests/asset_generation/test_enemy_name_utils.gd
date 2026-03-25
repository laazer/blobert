# test_enemy_name_utils.gd
#
# Behavioral tests for EnemyNameUtils.extract_family_name
# (scripts/asset_generation/enemy_name_utils.gd).
#
# Ticket: project_board/5_milestone_5_procedural_enemy_generation/backlog/godot_scene_generator_validation.md
# Spec:   agent_context/agents/2_spec/godot_scene_generator_validation_spec.md
# Stage:  TEST_DESIGN (red-phase — tests will fail until enemy_name_utils.gd is created)
#
# Coverage: GSV-UTIL-1 through GSV-UTIL-18, plus GSV-UTIL-8b (19 tests total)
#
# Instantiation note: extract_family_name is static. Tests call it via the
# registered class name EnemyNameUtils.extract_family_name(x). The file-scope
# preload forces class registration before any test function runs, resolving
# the class-cache timing risk documented in GSV-TEST R1.
# If enemy_name_utils.gd does not yet exist, the preload fails at load time and
# this file will not load — which is the correct red-phase failure mode.

extends Object

const _EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _assert_eq(expected: Variant, actual: Variant, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


# ---------------------------------------------------------------------------
# GSV-UTIL-1: Script load guard
# ---------------------------------------------------------------------------

func test_gsv_util_1_script_loads_non_null() -> void:
	# GSV-UTIL-1 / GSV-UTIL-AC-1
	# Verifies load() returns a non-null GDScript resource.
	# This is the guard test: if script_res is null, tests 2–15 will still run
	# but each calls _fail with a diagnostic and returns early.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	_assert_true(
		script_res != null,
		"GSV-UTIL-1 — load('res://scripts/asset_generation/enemy_name_utils.gd') returns non-null GDScript"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-2 through GSV-UTIL-7: Canonical family input/output table
# ---------------------------------------------------------------------------

func test_gsv_util_2_acid_spitter_animated_00() -> void:
	# GSV-UTIL-2 / GSV-UTIL-AC-3
	# Standard case: trailing int and "animated" infix both stripped.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-2", "script_res is null — cannot test")
		return
	_assert_eq(
		"acid_spitter",
		EnemyNameUtils.extract_family_name("acid_spitter_animated_00"),
		"GSV-UTIL-2 — extract_family_name('acid_spitter_animated_00') == 'acid_spitter'"
	)


func test_gsv_util_3_acid_spitter_00_no_infix() -> void:
	# GSV-UTIL-3 / GSV-UTIL-AC-4
	# Regression guard: no "animated" infix; only trailing int stripped.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-3", "script_res is null — cannot test")
		return
	_assert_eq(
		"acid_spitter",
		EnemyNameUtils.extract_family_name("acid_spitter_00"),
		"GSV-UTIL-3 — extract_family_name('acid_spitter_00') == 'acid_spitter'"
	)


func test_gsv_util_4_adhesion_bug_animated_02() -> void:
	# GSV-UTIL-4 / GSV-UTIL-AC-5
	# Canonical family: adhesion_bug with animated infix and variant 02.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-4", "script_res is null — cannot test")
		return
	_assert_eq(
		"adhesion_bug",
		EnemyNameUtils.extract_family_name("adhesion_bug_animated_02"),
		"GSV-UTIL-4 — extract_family_name('adhesion_bug_animated_02') == 'adhesion_bug'"
	)


func test_gsv_util_5_tar_slug_animated_01() -> void:
	# GSV-UTIL-5 / GSV-UTIL-AC-6
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-5", "script_res is null — cannot test")
		return
	_assert_eq(
		"tar_slug",
		EnemyNameUtils.extract_family_name("tar_slug_animated_01"),
		"GSV-UTIL-5 — extract_family_name('tar_slug_animated_01') == 'tar_slug'"
	)


func test_gsv_util_6_carapace_husk_animated_00() -> void:
	# GSV-UTIL-6 / GSV-UTIL-AC-7
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-6", "script_res is null — cannot test")
		return
	_assert_eq(
		"carapace_husk",
		EnemyNameUtils.extract_family_name("carapace_husk_animated_00"),
		"GSV-UTIL-6 — extract_family_name('carapace_husk_animated_00') == 'carapace_husk'"
	)


func test_gsv_util_7_claw_crawler_animated_01() -> void:
	# GSV-UTIL-7 / GSV-UTIL-AC-8
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-7", "script_res is null — cannot test")
		return
	_assert_eq(
		"claw_crawler",
		EnemyNameUtils.extract_family_name("claw_crawler_animated_01"),
		"GSV-UTIL-7 — extract_family_name('claw_crawler_animated_01') == 'claw_crawler'"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-8 and GSV-UTIL-8b: Passthrough cases (no int, no "animated")
# ---------------------------------------------------------------------------

func test_gsv_util_8_passthrough_no_int_no_animated() -> void:
	# GSV-UTIL-8 / GSV-UTIL-AC-9
	# Input has no trailing int and no "animated" segment — returned unchanged.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-8", "script_res is null — cannot test")
		return
	_assert_eq(
		"adhesion_bug",
		EnemyNameUtils.extract_family_name("adhesion_bug"),
		"GSV-UTIL-8 — extract_family_name('adhesion_bug') == 'adhesion_bug'"
	)


func test_gsv_util_8b_ember_imp_passthrough() -> void:
	# GSV-UTIL-8b / GSV-UTIL-AC-9b
	# ember_imp has no animated variants in M5; passthrough boundary condition.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-8b", "script_res is null — cannot test")
		return
	_assert_eq(
		"ember_imp",
		EnemyNameUtils.extract_family_name("ember_imp"),
		"GSV-UTIL-8b — extract_family_name('ember_imp') == 'ember_imp'"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-9 through GSV-UTIL-12: Edge cases derived from algorithm
# ---------------------------------------------------------------------------

func test_gsv_util_9_animated_only_with_int() -> void:
	# GSV-UTIL-9 / GSV-UTIL-AC-10
	# All segments removed (int stripped, "animated" stripped) → empty string.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-9", "script_res is null — cannot test")
		return
	_assert_eq(
		"",
		EnemyNameUtils.extract_family_name("animated_00"),
		"GSV-UTIL-9 — extract_family_name('animated_00') == ''"
	)


func test_gsv_util_10_animated_only_no_int() -> void:
	# GSV-UTIL-10 / GSV-UTIL-AC-11
	# Single segment "animated" is removed → empty string.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-10", "script_res is null — cannot test")
		return
	_assert_eq(
		"",
		EnemyNameUtils.extract_family_name("animated"),
		"GSV-UTIL-10 — extract_family_name('animated') == ''"
	)


func test_gsv_util_11_single_non_int_segment() -> void:
	# GSV-UTIL-11 / GSV-UTIL-AC-12
	# Single segment that is not an int and not "animated" — returned as-is.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-11", "script_res is null — cannot test")
		return
	_assert_eq(
		"enemy",
		EnemyNameUtils.extract_family_name("enemy"),
		"GSV-UTIL-11 — extract_family_name('enemy') == 'enemy'"
	)


func test_gsv_util_12_empty_string() -> void:
	# GSV-UTIL-12 / GSV-UTIL-AC-13
	# Empty input returns empty string.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-12", "script_res is null — cannot test")
		return
	_assert_eq(
		"",
		EnemyNameUtils.extract_family_name(""),
		"GSV-UTIL-12 — extract_family_name('') == ''"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-13: Multiple "animated" segments
# ---------------------------------------------------------------------------

func test_gsv_util_13_multiple_animated_segments() -> void:
	# GSV-UTIL-13 / GSV-UTIL-AC-14
	# All occurrences of "animated" are removed, not just the first.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-13", "script_res is null — cannot test")
		return
	_assert_eq(
		"acid_spitter",
		EnemyNameUtils.extract_family_name("acid_spitter_animated_animated_00"),
		"GSV-UTIL-13 — extract_family_name('acid_spitter_animated_animated_00') == 'acid_spitter'"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-14: Static callability without instantiation
# ---------------------------------------------------------------------------

func test_gsv_util_14_static_callable_without_instance() -> void:
	# GSV-UTIL-14 / GSV-UTIL-AC-15
	# Verifies static invocation succeeds: no .new() needed.
	# The file-scope preload has already registered the class; this call
	# exercises the static path directly and asserts on the return value.
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-14", "script_res is null — cannot test")
		return
	_assert_eq(
		"x",
		EnemyNameUtils.extract_family_name("x"),
		"GSV-UTIL-14 — EnemyNameUtils.extract_family_name('x') called without .new() returns 'x'"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-15: Source does not contain @tool or EditorScript
# ---------------------------------------------------------------------------

func test_gsv_util_15_source_has_no_tool_or_editor_script() -> void:
	# GSV-UTIL-15 / GSV-UTIL-AC-16 / GSV-NFR-AC-3
	# Checks source_code directly; verifies the file is headlessly loadable
	# (no editor-only declarations).
	var script_res: GDScript = load("res://scripts/asset_generation/enemy_name_utils.gd")
	if script_res == null:
		_fail("GSV-UTIL-15", "script_res is null — cannot test")
		return
	var source: String = script_res.source_code
	_assert_true(
		not source.contains("@tool"),
		"GSV-UTIL-15a — enemy_name_utils.gd source does not contain '@tool'"
	)
	_assert_true(
		not source.contains("EditorScript"),
		"GSV-UTIL-15b — enemy_name_utils.gd source does not contain 'EditorScript'"
	)


# ---------------------------------------------------------------------------
# GSV-UTIL-16 through GSV-UTIL-18: load_assets.gd modification verification
# ---------------------------------------------------------------------------

func test_gsv_util_16_loadmod_source_delegates_to_enemy_name_utils() -> void:
	# GSV-UTIL-16 / GSV-LOADMOD-AC-3
	# load_assets.gd source must contain the delegation call.
	# load() only — never instantiate (EditorScript.new() crashes headlessly).
	var load_assets_res: GDScript = load("res://scripts/asset_generation/load_assets.gd")
	if load_assets_res == null:
		_fail("GSV-UTIL-16", "load_assets.gd could not be loaded — cannot test")
		return
	var source: String = load_assets_res.source_code
	_assert_true(
		source.contains("EnemyNameUtils.extract_family_name"),
		"GSV-UTIL-16 — load_assets.gd source contains 'EnemyNameUtils.extract_family_name'"
	)


func test_gsv_util_17_loadmod_source_old_body_removed() -> void:
	# GSV-UTIL-17 / GSV-LOADMOD-AC-2
	# The original inline implementation must be removed.
	var load_assets_res: GDScript = load("res://scripts/asset_generation/load_assets.gd")
	if load_assets_res == null:
		_fail("GSV-UTIL-17", "load_assets.gd could not be loaded — cannot test")
		return
	var source: String = load_assets_res.source_code
	_assert_true(
		not source.contains("parts[-1].is_valid_int()"),
		"GSV-UTIL-17 — load_assets.gd source does not contain 'parts[-1].is_valid_int()' (old body removed)"
	)


func test_gsv_util_18_loadmod_source_has_preload() -> void:
	# GSV-UTIL-18 / GSV-LOADMOD-AC-5
	# The mandatory preload declaration must be present.
	var load_assets_res: GDScript = load("res://scripts/asset_generation/load_assets.gd")
	if load_assets_res == null:
		_fail("GSV-UTIL-18", "load_assets.gd could not be loaded — cannot test")
		return
	var source: String = load_assets_res.source_code
	_assert_true(
		source.contains("preload(\"res://scripts/asset_generation/enemy_name_utils.gd\")"),
		"GSV-UTIL-18 — load_assets.gd source contains preload for enemy_name_utils.gd"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_name_utils.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Guard: script load
	test_gsv_util_1_script_loads_non_null()

	# Canonical family table
	test_gsv_util_2_acid_spitter_animated_00()
	test_gsv_util_3_acid_spitter_00_no_infix()
	test_gsv_util_4_adhesion_bug_animated_02()
	test_gsv_util_5_tar_slug_animated_01()
	test_gsv_util_6_carapace_husk_animated_00()
	test_gsv_util_7_claw_crawler_animated_01()

	# Passthrough cases
	test_gsv_util_8_passthrough_no_int_no_animated()
	test_gsv_util_8b_ember_imp_passthrough()

	# Edge cases
	test_gsv_util_9_animated_only_with_int()
	test_gsv_util_10_animated_only_no_int()
	test_gsv_util_11_single_non_int_segment()
	test_gsv_util_12_empty_string()

	# Multiple animated segments
	test_gsv_util_13_multiple_animated_segments()

	# Static callability
	test_gsv_util_14_static_callable_without_instance()

	# Source inspection: enemy_name_utils.gd
	test_gsv_util_15_source_has_no_tool_or_editor_script()

	# Source inspection: load_assets.gd modification
	test_gsv_util_16_loadmod_source_delegates_to_enemy_name_utils()
	test_gsv_util_17_loadmod_source_old_body_removed()
	test_gsv_util_18_loadmod_source_has_preload()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
