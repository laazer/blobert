# test_enemy_base_adversarial.gd
#
# Adversarial behavioral tests for EnemyBase (scripts/enemies/enemy_base.gd).
# Exercises boundary conditions, invalid inputs, multi-instance isolation,
# and the load_assets.gd contract edge cases not covered by the primary suite.
#
# Ticket: enemy_base_script
# Spec: agent_context/agents/2_spec/enemy_base_spec.md (Adversarial Behavior section)
# Stage: TEST_DESIGN (red-phase — tests will fail until enemy_base.gd is created)
#
# ADV-EB-01 behavior (out-of-range cast): GDScript stores the integer as-is.
# No clamping or crash. Documented in spec EB-STATE risk analysis.

extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


func _make_body(script_res: GDScript) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.set_script(script_res)
	return body


# ---------------------------------------------------------------------------
# ADV-EB-01: Out-of-range integer cast to State
# ---------------------------------------------------------------------------

func test_adv_eb_01_out_of_range_state_no_crash() -> void:
	# ADV-EB-01: set_base_state with an integer outside the enum range (99).
	# Must not crash. GDScript stores the value as-is (pass-through).
	# Spec: EB-STATE risk analysis, Adversarial Behavior ADV-EB-01
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-01", "script_res is null")
		return
	var body := _make_body(script_res)
	# Cast 99 to the State enum type as GDScript allows runtime int-to-enum cast.
	body.set_base_state(99 as int)
	_assert_eq(99, body.get_base_state(), "ADV-EB-01 — set_base_state(99) stores 99 as-is, no crash, get_base_state() returns 99")
	body.free()


# ---------------------------------------------------------------------------
# ADV-EB-02: Empty string enemy_id — no crash, stays ""
# ---------------------------------------------------------------------------

func test_adv_eb_02_enemy_id_empty_string() -> void:
	# ADV-EB-02: Setting enemy_id to "" via Object.set() must not crash and
	# must return "" (not null, not a missing-key error).
	# Spec: EB-EXPORT AC-EXPORT-7, Adversarial Behavior ADV-EB-08
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-02", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set("enemy_id", "")
	var result: Variant = body.get("enemy_id")
	_assert_true(result != null, "ADV-EB-02 — enemy_id after set('') is not null")
	_assert_eq("", result, "ADV-EB-02 — enemy_id after set('') returns empty string")
	body.free()


# ---------------------------------------------------------------------------
# ADV-EB-03: Very long enemy_id string (200 chars)
# ---------------------------------------------------------------------------

func test_adv_eb_03_long_enemy_id_string() -> void:
	# ADV-EB-03: enemy_id must store a 200-character string without crash or
	# truncation. GDScript String has no practical size limit in Godot 4.
	# Spec: Adversarial Behavior ADV-EB-03
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-03", "script_res is null")
		return
	var body := _make_body(script_res)
	var long_str: String = "x".repeat(200)
	body.set("enemy_id", long_str)
	var result: Variant = body.get("enemy_id")
	_assert_eq(200, (result as String).length(), "ADV-EB-03 — enemy_id stores 200-char string without truncation, length == 200")
	_assert_eq(long_str, result, "ADV-EB-03 — enemy_id 200-char value reads back correctly")
	body.free()


# ---------------------------------------------------------------------------
# ADV-EB-04: Two instances have independent state
# ---------------------------------------------------------------------------

func test_adv_eb_04_two_instances_independent_state() -> void:
	# ADV-EB-04: Mutating current_state on one instance does not affect another.
	# Spec: EB-STATE AC-STATE-6, Adversarial Behavior ADV-EB-05
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-04", "script_res is null")
		return
	var body_a := _make_body(script_res)
	var body_b := _make_body(script_res)

	body_a.set_base_state(body_a.State.INFECTED)

	_assert_eq(2, body_a.current_state, "ADV-EB-04 — instance A current_state == INFECTED (2)")
	_assert_eq(0, body_b.current_state, "ADV-EB-04 — instance B current_state remains NORMAL (0) after A was mutated")

	body_a.free()
	body_b.free()


# ---------------------------------------------------------------------------
# ADV-EB-05: get_base_state() returns int type (not String, not null)
# ---------------------------------------------------------------------------

func test_adv_eb_05_get_base_state_returns_int() -> void:
	# ADV-EB-05: get_base_state() must return an integer, not a String or null.
	# Spec: EB-STATE AC-STATE-5, Adversarial Behavior ADV-EB-07
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-05", "script_res is null")
		return
	var body := _make_body(script_res)
	var result: Variant = body.get_base_state()
	_assert_true(result != null, "ADV-EB-05 — get_base_state() is not null on fresh instance")
	_assert_true(typeof(result) == TYPE_INT, "ADV-EB-05 — get_base_state() returns TYPE_INT, got type " + str(typeof(result)))
	_assert_eq(0, result, "ADV-EB-05 — get_base_state() returns 0 (NORMAL) on fresh instance")
	body.free()


# ---------------------------------------------------------------------------
# ADV-EB-06: State.keys() returns Array (not null)
# ---------------------------------------------------------------------------

func test_adv_eb_06_state_keys_returns_array() -> void:
	# ADV-EB-06: body.State.keys() must return a non-null Array.
	# GDScript exposes script-level enums as Dictionary on the instance.
	# Spec: EB-ENUM preamble and AC-ENUM-4
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-06", "script_res is null")
		return
	var body := _make_body(script_res)
	var keys: Variant = body.State.keys()
	_assert_true(keys != null, "ADV-EB-06 — State.keys() is not null")
	_assert_true(keys is Array, "ADV-EB-06 — State.keys() returns an Array")
	body.free()


# ---------------------------------------------------------------------------
# ADV-EB-07: Source does NOT contain "extends Node" (must extend CharacterBody3D)
# ---------------------------------------------------------------------------

func test_adv_eb_07_extends_character_body_3d_not_node() -> void:
	# ADV-EB-07: The script source must not say "extends Node". It must extend
	# CharacterBody3D directly.
	# Spec: EB-CLASS AC-CLASS-4; EB-NFR-NOPHYSICS (must not extend BasePhysicsEntity3D)
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-07", "script_res is null")
		return
	var source: String = script_res.source_code
	_assert_true(
		source.contains("extends CharacterBody3D"),
		"ADV-EB-07 — source contains 'extends CharacterBody3D'"
	)
	_assert_true(
		not source.contains("extends Node\n") and not source.contains("extends Node "),
		"ADV-EB-07 — source does not 'extends Node' (bare Node, not CharacterBody3D)"
	)


# ---------------------------------------------------------------------------
# ADV-EB-08: class_name is "EnemyBase" (source contains class_name EnemyBase)
# ---------------------------------------------------------------------------

func test_adv_eb_08_class_name_is_enemy_base() -> void:
	# ADV-EB-08: The script must declare class_name EnemyBase.
	# Verified via source_code inspection (resource_path approach is fragile in
	# headless mode; source_code is more direct).
	# Spec: EB-CLASS AC-CLASS-4, EB-STYLE AC-STYLE-2
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("ADV-EB-08", "script_res is null")
		return
	var source: String = script_res.source_code
	_assert_true(
		source.contains("class_name EnemyBase"),
		"ADV-EB-08 — source contains 'class_name EnemyBase'"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_base_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_eb_01_out_of_range_state_no_crash()
	test_adv_eb_02_enemy_id_empty_string()
	test_adv_eb_03_long_enemy_id_string()
	test_adv_eb_04_two_instances_independent_state()
	test_adv_eb_05_get_base_state_returns_int()
	test_adv_eb_06_state_keys_returns_array()
	test_adv_eb_07_extends_character_body_3d_not_node()
	test_adv_eb_08_class_name_is_enemy_base()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
