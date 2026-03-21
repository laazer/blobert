# test_enemy_base.gd
#
# Primary behavioral tests for EnemyBase (scripts/enemies/enemy_base.gd).
# Verifies script load, CharacterBody3D attachment, exported vars, State enum
# integer values and member count, current_state default and transitions, and
# the load_assets.gd integration contract (root.set() pattern).
#
# Ticket: enemy_base_script
# Spec: agent_context/agents/2_spec/enemy_base_spec.md
# Stage: TEST_DESIGN (red-phase — tests will fail until enemy_base.gd is created)
#
# Instantiation pattern: load() + CharacterBody3D.new() + set_script().
# EnemyBase.new() is NOT used; class cache may not be populated before the
# test runner initializes.

extends Object


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


func _make_body(script_res: GDScript) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.set_script(script_res)
	return body


# ---------------------------------------------------------------------------
# EB-LOAD: Script loading and CharacterBody3D attachment
# ---------------------------------------------------------------------------

func test_eb_load_1_script_loads_non_null() -> void:
	# EB-LOAD-1 / AC-CLASS-1: load() returns a non-null GDScript resource.
	# Spec: EB-CLASS AC-CLASS-1
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	_assert_true(
		script_res != null,
		"EB-LOAD-1 — load('res://scripts/enemies/enemy_base.gd') returns non-null GDScript resource"
	)


func test_eb_load_2_attaches_to_character_body_3d() -> void:
	# EB-LOAD-2 / AC-CLASS-2 / AC-CLASS-3: set_script() does not crash; node
	# remains a CharacterBody3D.
	# Spec: EB-CLASS AC-CLASS-2, AC-CLASS-3
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-LOAD-2", "script_res is null — cannot test attachment")
		return

	var body := CharacterBody3D.new()
	body.set_script(script_res)
	_assert_true(
		body is CharacterBody3D,
		"EB-LOAD-2 — scripted node is instance of CharacterBody3D after set_script()"
	)
	body.free()


# ---------------------------------------------------------------------------
# EB-EXPORT: Exported String variables
# ---------------------------------------------------------------------------

func test_eb_export_1_enemy_id_default() -> void:
	# EB-EXPORT-1: enemy_id exists and defaults to "".
	# Spec: EB-EXPORT AC-EXPORT-1
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-EXPORT-1", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq("", body.get("enemy_id"), "EB-EXPORT-1 — enemy_id default is empty string")
	body.free()


func test_eb_export_2_enemy_family_default() -> void:
	# EB-EXPORT-2: enemy_family exists and defaults to "".
	# Spec: EB-EXPORT AC-EXPORT-2
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-EXPORT-2", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq("", body.get("enemy_family"), "EB-EXPORT-2 — enemy_family default is empty string")
	body.free()


func test_eb_export_3_mutation_drop_default() -> void:
	# EB-EXPORT-3: mutation_drop exists and defaults to "".
	# Spec: EB-EXPORT AC-EXPORT-3
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-EXPORT-3", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq("", body.get("mutation_drop"), "EB-EXPORT-3 — mutation_drop default is empty string")
	body.free()


func test_eb_export_4_enemy_id_settable() -> void:
	# EB-EXPORT-4: enemy_id is settable; reads back the assigned value.
	# Spec: EB-EXPORT AC-EXPORT-4
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-EXPORT-4", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set("enemy_id", "test_id")
	_assert_eq("test_id", body.get("enemy_id"), "EB-EXPORT-4 — enemy_id set to 'test_id' reads back 'test_id'")
	body.free()


func test_eb_export_5_enemy_family_settable() -> void:
	# EB-EXPORT-5: enemy_family is settable.
	# Spec: EB-EXPORT AC-EXPORT-5
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-EXPORT-5", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set("enemy_family", "acid_spitter")
	_assert_eq("acid_spitter", body.get("enemy_family"), "EB-EXPORT-5 — enemy_family set to 'acid_spitter' reads back correctly")
	body.free()


func test_eb_export_6_mutation_drop_settable() -> void:
	# EB-EXPORT-6: mutation_drop is settable.
	# Spec: EB-EXPORT AC-EXPORT-6
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-EXPORT-6", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set("mutation_drop", "acid")
	_assert_eq("acid", body.get("mutation_drop"), "EB-EXPORT-6 — mutation_drop set to 'acid' reads back correctly")
	body.free()


# ---------------------------------------------------------------------------
# EB-ENUM: State enum existence and integer values
# ---------------------------------------------------------------------------

func test_eb_enum_1_state_exists() -> void:
	# EB-ENUM-1: State enum property exists on the scripted instance (not null).
	# Spec: EB-ENUM (preamble); GDScript exposes enum as Dictionary on instance.
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-ENUM-1", "script_res is null")
		return
	var body := _make_body(script_res)
	var state_dict: Variant = body.get("State")
	_assert_true(
		state_dict != null,
		"EB-ENUM-1 — body.State is not null (enum accessible as Dictionary on instance)"
	)
	body.free()


func test_eb_enum_2_normal_equals_0() -> void:
	# EB-ENUM-2: State.NORMAL == 0.
	# Spec: EB-ENUM AC-ENUM-1
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-ENUM-2", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq(0, body.State.NORMAL, "EB-ENUM-2 — State.NORMAL == 0")
	body.free()


func test_eb_enum_3_weakened_equals_1() -> void:
	# EB-ENUM-3: State.WEAKENED == 1.
	# Spec: EB-ENUM AC-ENUM-2
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-ENUM-3", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq(1, body.State.WEAKENED, "EB-ENUM-3 — State.WEAKENED == 1")
	body.free()


func test_eb_enum_4_infected_equals_2() -> void:
	# EB-ENUM-4: State.INFECTED == 2.
	# Spec: EB-ENUM AC-ENUM-3
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-ENUM-4", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq(2, body.State.INFECTED, "EB-ENUM-4 — State.INFECTED == 2")
	body.free()


func test_eb_enum_5_state_has_exactly_3_members() -> void:
	# EB-ENUM-5: State enum has exactly 3 members (NORMAL, WEAKENED, INFECTED).
	# Spec: EB-ENUM AC-ENUM-4
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-ENUM-5", "script_res is null")
		return
	var body := _make_body(script_res)
	var key_count: int = body.State.keys().size()
	_assert_eq(3, key_count, "EB-ENUM-5 — State enum has exactly 3 members, got " + str(key_count))
	body.free()


# ---------------------------------------------------------------------------
# EB-STATE: current_state default and transitions
# ---------------------------------------------------------------------------

func test_eb_state_1_default_is_normal() -> void:
	# EB-STATE-1: current_state defaults to State.NORMAL (0) on fresh instance.
	# Spec: EB-STATE AC-STATE-1
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-STATE-1", "script_res is null")
		return
	var body := _make_body(script_res)
	_assert_eq(0, body.current_state, "EB-STATE-1 — current_state defaults to State.NORMAL (0)")
	body.free()


func test_eb_state_2_set_weakened() -> void:
	# EB-STATE-2: set_base_state(State.WEAKENED) → get_base_state() returns WEAKENED.
	# Spec: EB-STATE AC-STATE-2, AC-STATE-5
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-STATE-2", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set_base_state(body.State.WEAKENED)
	_assert_eq(1, body.current_state, "EB-STATE-2 — current_state == 1 (WEAKENED) after set_base_state(WEAKENED)")
	_assert_eq(1, body.get_base_state(), "EB-STATE-2 — get_base_state() returns 1 (WEAKENED)")
	body.free()


func test_eb_state_3_set_infected() -> void:
	# EB-STATE-3: set_base_state(State.INFECTED) → get_base_state() returns INFECTED.
	# Spec: EB-STATE AC-STATE-3, AC-STATE-5
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-STATE-3", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set_base_state(body.State.INFECTED)
	_assert_eq(2, body.current_state, "EB-STATE-3 — current_state == 2 (INFECTED) after set_base_state(INFECTED)")
	_assert_eq(2, body.get_base_state(), "EB-STATE-3 — get_base_state() returns 2 (INFECTED)")
	body.free()


func test_eb_state_4_transition_back_to_normal() -> void:
	# EB-STATE-4: set_base_state(State.NORMAL) after INFECTED → returns State.NORMAL.
	# Spec: EB-STATE AC-STATE-4, AC-STATE-5
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-STATE-4", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set_base_state(body.State.INFECTED)
	body.set_base_state(body.State.NORMAL)
	_assert_eq(0, body.current_state, "EB-STATE-4 — current_state == 0 (NORMAL) after transition back from INFECTED")
	_assert_eq(0, body.get_base_state(), "EB-STATE-4 — get_base_state() returns 0 (NORMAL) after transition back")
	body.free()


# ---------------------------------------------------------------------------
# EB-INTEGRATE: load_assets.gd integration contract via Object.set()
# ---------------------------------------------------------------------------

func test_eb_integrate_1_set_via_object_set() -> void:
	# EB-INTEGRATE-1: enemy_id, enemy_family, mutation_drop settable via
	# Object.set() — mirrors load_assets.gd root.set("enemy_id", ...) pattern.
	# Spec: EB-INTEGRATION AC-INTEGRATION-2, AC-INTEGRATION-3
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-INTEGRATE-1", "script_res is null")
		return
	var body := _make_body(script_res)
	body.set("enemy_id", "acid_spitter_00")
	body.set("enemy_family", "acid_spitter")
	body.set("mutation_drop", "acid")
	_assert_eq("acid_spitter_00", body.enemy_id, "EB-INTEGRATE-1 — enemy_id set via Object.set() reads back via dot notation")
	_assert_eq("acid_spitter", body.enemy_family, "EB-INTEGRATE-1 — enemy_family set via Object.set() reads back via dot notation")
	_assert_eq("acid", body.mutation_drop, "EB-INTEGRATE-1 — mutation_drop set via Object.set() reads back via dot notation")
	body.free()


# ---------------------------------------------------------------------------
# EB-COMPAT: No _physics_process override on the base script
# ---------------------------------------------------------------------------

func test_eb_compat_1_no_physics_process_override() -> void:
	# EB-COMPAT-1: enemy_base.gd does NOT define _physics_process.
	# Spec: EB-NFR-NOPHYSICS AC-NFR-PHYSICS-1
	# Verified by source inspection: script source must not contain the string
	# "_physics_process" as a function definition.
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		_fail("EB-COMPAT-1", "script_res is null")
		return
	var source: String = script_res.source_code
	_assert_true(
		not source.contains("_physics_process"),
		"EB-COMPAT-1 — enemy_base.gd source does not define _physics_process"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_base.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Load and attachment
	test_eb_load_1_script_loads_non_null()
	test_eb_load_2_attaches_to_character_body_3d()

	# Exported vars
	test_eb_export_1_enemy_id_default()
	test_eb_export_2_enemy_family_default()
	test_eb_export_3_mutation_drop_default()
	test_eb_export_4_enemy_id_settable()
	test_eb_export_5_enemy_family_settable()
	test_eb_export_6_mutation_drop_settable()

	# State enum
	test_eb_enum_1_state_exists()
	test_eb_enum_2_normal_equals_0()
	test_eb_enum_3_weakened_equals_1()
	test_eb_enum_4_infected_equals_2()
	test_eb_enum_5_state_has_exactly_3_members()

	# current_state and transitions
	test_eb_state_1_default_is_normal()
	test_eb_state_2_set_weakened()
	test_eb_state_3_set_infected()
	test_eb_state_4_transition_back_to_normal()

	# Integration contract
	test_eb_integrate_1_set_via_object_set()

	# Compatibility (no physics process override)
	test_eb_compat_1_no_physics_process_override()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
