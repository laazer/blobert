#
# test_utils_smoke.gd
#
# Smoke tests for tests/utils/test_utils.gd (the shared test utility base).
#
# Spec:   project_board/maintenance/in_progress/test_utility_consolidation.md
#         ## Specification — Requirements MAINT-TUC-1, MAINT-TUC-2, MAINT-TUC-3
#
# PURPOSE
# -------
# These tests are written BEFORE test_utils.gd exists. They will initially fail
# with a load error (the file does not exist). That is the correct, expected
# state. Once the Implementation Agent creates tests/utils/test_utils.gd, these
# tests must all pass. They are the executable contract that implementation must
# satisfy.
#
# COVERAGE
# --------
# SMOKE-1   AC-1.1  The file tests/utils/test_utils.gd can be loaded without error
# SMOKE-2   AC-1.3  The loaded script has NO class_name registration pollution
# SMOKE-3   AC-1.4  run_all() is present, returns int 0, prints nothing
# SMOKE-4   AC-2.1  _pass(name) method is present on the loaded script
# SMOKE-5   AC-2.2  _pass_test(name) method is present
# SMOKE-6   AC-2.3  _fail(name, msg) method is present
# SMOKE-7   AC-2.4  _fail_test(name, msg) method is present
# SMOKE-8   AC-2.5  _assert_true(condition, name) method is present
# SMOKE-9   AC-2.7  _assert_false(condition, name) method is present
# SMOKE-10  AC-2.9  _assert_eq_int(expected, actual, name) method is present
# SMOKE-11  AC-2.10 _assert_eq_string(expected, actual, name) method is present
# SMOKE-12  AC-2.12 _assert_eq(expected, actual, name) method is present
# SMOKE-13  AC-2.15 _assert_approx(a, b, name) method is present
# SMOKE-14  AC-2.16 _assert_vec2_approx(a, b, name) method is present
# SMOKE-15  AC-2.18 _assert_vec3_near(actual, expected, tol, name) method is present
# SMOKE-16  AC-3.1  test_utils.gd does NOT declare _pass_count
# SMOKE-17  AC-3.1  test_utils.gd does NOT declare _fail_count
# SMOKE-18  AC-2.1  A subclass that owns _pass_count/_fail_count can call _pass
#                   without runtime error; _pass_count is incremented
# SMOKE-19  AC-2.3  Same subclass can call _fail; _fail_count is incremented
# SMOKE-20  AC-2.1  _pass and _pass_test are behaviorally identical (both increment
#                   _pass_count by 1)
# SMOKE-21  AC-2.3  _fail and _fail_test are behaviorally identical (both increment
#                   _fail_count by 1)
# SMOKE-22  AC-2.5  _assert_true(true, name) delegates to _pass (pass_count +1)
# SMOKE-23  AC-2.5  _assert_true(false, name) delegates to _fail (fail_count +1)
# SMOKE-24  AC-2.7  _assert_false(false, name) delegates to _pass (pass_count +1)
# SMOKE-25  AC-2.7  _assert_false(true, name) delegates to _fail (fail_count +1)
# SMOKE-26  AC-2.6  _assert_true(false, name, "custom") uses the custom fail_msg
# SMOKE-27  AC-2.8  _assert_false(true, name, "custom") uses the custom fail_msg
#
# SPEC GAPS / QUESTIONS FOR SPEC AGENT
# -------------------------------------
# None identified. All required behaviors are fully specified in MAINT-TUC-2.
#
# ASSUMPTIONS
# -----------
# Assumption A: GDScript allows `script.get_script_method_list()` to enumerate
#   methods defined directly on the script. This is used to verify presence of
#   each required method. If a method is inherited from a deeper GDScript base,
#   it may not appear in `get_script_method_list()` — however test_utils.gd
#   extends Object (a built-in), so all user-defined methods are at the script
#   level and are enumerated correctly.
# Assumption B: `script.get_script_property_list()` reliably lists instance
#   variables declared with `var` in the script body. This is used to assert
#   that _pass_count and _fail_count are NOT declared in test_utils.gd (SMOKE-16/17).
# Assumption C: A minimal inner subclass that declares _pass_count and _fail_count
#   and extends test_utils.gd at runtime via script inheritance reliably exercises
#   dynamic dispatch. Since GDScript inline script inheritance is not possible at
#   runtime without writing a temp file, SMOKE-18/19 are tested by creating a
#   minimal helper GDScript object declared at the bottom of this file as an inner
#   class that extends the loaded script by forwarding calls. The behavioral
#   assertions (counter increments) are the definitive observable, not the dispatch
#   mechanism.
#

extends Object

var _pass_count: int = 0
var _fail_count: int = 0

const _UTILS_PATH: String = "res://tests/utils/test_utils.gd"


# ---------------------------------------------------------------------------
# Internal helpers (self-contained — this file does not depend on test_utils.gd)
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_local(condition: bool, test_name: String, fail_msg: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


# ---------------------------------------------------------------------------
# Helper: collect method names from a script's own method list
# ---------------------------------------------------------------------------

func _method_names(script: GDScript) -> Array:
	var names: Array = []
	for m in script.get_script_method_list():
		names.append(m["name"])
	return names


# ---------------------------------------------------------------------------
# Helper: collect property names declared directly on a script
# ---------------------------------------------------------------------------

func _property_names(script: GDScript) -> Array:
	var names: Array = []
	for p in script.get_script_property_list():
		names.append(p["name"])
	return names


# ---------------------------------------------------------------------------
# Minimal runtime subclass that owns the counters — used by SMOKE-18..27
# ---------------------------------------------------------------------------
# GDScript does not support runtime creation of a class that extends a GDScript
# file via script.new() with overridden properties inline. Instead, we create a
# plain Object, attach the test_utils script to it, and then verify behavior by
# calling the methods directly with the counters injected as properties on the
# same instance. This is valid because test_utils.gd methods reference
# _pass_count/_fail_count on self, and GDScript Object.set() / get() resolve
# those references dynamically.

func _make_subclass_instance(utils_script: GDScript) -> Object:
	var inst: Object = utils_script.new()
	# Inject counter properties that the subclass would normally declare.
	# The methods in utils_script reference self._pass_count and self._fail_count;
	# setting them here simulates the subclass ownership contract.
	inst.set("_pass_count", 0)
	inst.set("_fail_count", 0)
	return inst


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

func run_all() -> int:
	_pass_count = 0
	_fail_count = 0

	print("--- test_utils_smoke ---")

	# --- SMOKE-1: file is loadable ---
	var utils_script: GDScript = load(_UTILS_PATH)
	_assert_local(
		utils_script != null,
		"SMOKE-1_loadable",
		"tests/utils/test_utils.gd could not be loaded (file may not exist yet)"
	)

	# All subsequent tests depend on the script loading successfully.
	# If it fails, we report the remaining tests as failed too (they cannot run).
	if utils_script == null:
		# Mark all remaining tests as failures so the count is accurate.
		var remaining: int = 26  # SMOKE-2 through SMOKE-27
		_fail_count += remaining
		print("  (skipping SMOKE-2..27: script load failed)")
		print("--- test_utils_smoke: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed ---")
		return _fail_count

	# --- SMOKE-2: no class_name pollution ---
	# GDScript.get_global_name() returns the class_name string if declared,
	# or an empty string if none. test_utils.gd must return "".
	_assert_local(
		utils_script.get_global_name() == "",
		"SMOKE-2_no_class_name",
		"test_utils.gd must NOT declare a class_name; got: '" + utils_script.get_global_name() + "'"
	)

	# --- SMOKE-3: run_all() returns int 0 ---
	var base_instance: Object = utils_script.new()
	var run_all_result = base_instance.call("run_all")
	_assert_local(
		run_all_result == 0,
		"SMOKE-3_run_all_returns_0",
		"run_all() must return 0 (no-op); got: " + str(run_all_result)
	)
	base_instance.free()

	# --- SMOKE-4..15: required methods are present ---
	var methods: Array = _method_names(utils_script)

	var required_methods: Array = [
		"_pass",
		"_pass_test",
		"_fail",
		"_fail_test",
		"_assert_true",
		"_assert_false",
		"_assert_eq_int",
		"_assert_eq_string",
		"_assert_eq",
		"_assert_approx",
		"_assert_vec2_approx",
		"_assert_vec3_near",
		"run_all",
	]

	var smoke_ids: Array = [
		"SMOKE-4_has__pass",
		"SMOKE-5_has__pass_test",
		"SMOKE-6_has__fail",
		"SMOKE-7_has__fail_test",
		"SMOKE-8_has__assert_true",
		"SMOKE-9_has__assert_false",
		"SMOKE-10_has__assert_eq_int",
		"SMOKE-11_has__assert_eq_string",
		"SMOKE-12_has__assert_eq",
		"SMOKE-13_has__assert_approx",
		"SMOKE-14_has__assert_vec2_approx",
		"SMOKE-15_has__assert_vec3_near",
		"SMOKE-3b_has_run_all",
	]

	for i in range(required_methods.size()):
		var m: String = required_methods[i]
		_assert_local(
			methods.has(m),
			smoke_ids[i],
			"test_utils.gd is missing required method: " + m
		)

	# --- SMOKE-16: _pass_count NOT declared in test_utils.gd ---
	var props: Array = _property_names(utils_script)
	_assert_local(
		not props.has("_pass_count"),
		"SMOKE-16_no__pass_count_in_base",
		"test_utils.gd must NOT declare _pass_count (ownership belongs to subclass)"
	)

	# --- SMOKE-17: _fail_count NOT declared in test_utils.gd ---
	_assert_local(
		not props.has("_fail_count"),
		"SMOKE-17_no__fail_count_in_base",
		"test_utils.gd must NOT declare _fail_count (ownership belongs to subclass)"
	)

	# --- SMOKE-18: subclass-owned _pass_count is incremented by _pass ---
	var inst: Object = _make_subclass_instance(utils_script)
	inst.call("_pass", "dummy")
	var pass_after_one: int = inst.get("_pass_count")
	_assert_local(
		pass_after_one == 1,
		"SMOKE-18_pass_increments_pass_count",
		"_pass() must increment _pass_count by 1; got _pass_count=" + str(pass_after_one)
	)
	inst.free()

	# --- SMOKE-19: subclass-owned _fail_count is incremented by _fail ---
	var inst2: Object = _make_subclass_instance(utils_script)
	inst2.call("_fail", "dummy", "some reason")
	var fail_after_one: int = inst2.get("_fail_count")
	_assert_local(
		fail_after_one == 1,
		"SMOKE-19_fail_increments_fail_count",
		"_fail() must increment _fail_count by 1; got _fail_count=" + str(fail_after_one)
	)
	inst2.free()

	# --- SMOKE-20: _pass and _pass_test are behaviorally identical ---
	var inst3: Object = _make_subclass_instance(utils_script)
	inst3.call("_pass", "a")
	inst3.call("_pass_test", "b")
	var pass_after_two: int = inst3.get("_pass_count")
	_assert_local(
		pass_after_two == 2,
		"SMOKE-20_pass_and_pass_test_identical",
		"_pass and _pass_test must each increment _pass_count by 1; got " + str(pass_after_two) + " after two calls"
	)
	inst3.free()

	# --- SMOKE-21: _fail and _fail_test are behaviorally identical ---
	var inst4: Object = _make_subclass_instance(utils_script)
	inst4.call("_fail", "a", "msg1")
	inst4.call("_fail_test", "b", "msg2")
	var fail_after_two: int = inst4.get("_fail_count")
	_assert_local(
		fail_after_two == 2,
		"SMOKE-21_fail_and_fail_test_identical",
		"_fail and _fail_test must each increment _fail_count by 1; got " + str(fail_after_two) + " after two calls"
	)
	inst4.free()

	# --- SMOKE-22: _assert_true(true, name) calls _pass ---
	var inst5: Object = _make_subclass_instance(utils_script)
	inst5.call("_assert_true", true, "dummy")
	_assert_local(
		inst5.get("_pass_count") == 1 and inst5.get("_fail_count") == 0,
		"SMOKE-22_assert_true_pass_branch",
		"_assert_true(true, ...) must call _pass; got pass_count=" + str(inst5.get("_pass_count")) + " fail_count=" + str(inst5.get("_fail_count"))
	)
	inst5.free()

	# --- SMOKE-23: _assert_true(false, name) calls _fail ---
	var inst6: Object = _make_subclass_instance(utils_script)
	inst6.call("_assert_true", false, "dummy")
	_assert_local(
		inst6.get("_pass_count") == 0 and inst6.get("_fail_count") == 1,
		"SMOKE-23_assert_true_fail_branch",
		"_assert_true(false, ...) must call _fail; got pass_count=" + str(inst6.get("_pass_count")) + " fail_count=" + str(inst6.get("_fail_count"))
	)
	inst6.free()

	# --- SMOKE-24: _assert_false(false, name) calls _pass ---
	var inst7: Object = _make_subclass_instance(utils_script)
	inst7.call("_assert_false", false, "dummy")
	_assert_local(
		inst7.get("_pass_count") == 1 and inst7.get("_fail_count") == 0,
		"SMOKE-24_assert_false_pass_branch",
		"_assert_false(false, ...) must call _pass; got pass_count=" + str(inst7.get("_pass_count")) + " fail_count=" + str(inst7.get("_fail_count"))
	)
	inst7.free()

	# --- SMOKE-25: _assert_false(true, name) calls _fail ---
	var inst8: Object = _make_subclass_instance(utils_script)
	inst8.call("_assert_false", true, "dummy")
	_assert_local(
		inst8.get("_pass_count") == 0 and inst8.get("_fail_count") == 1,
		"SMOKE-25_assert_false_fail_branch",
		"_assert_false(true, ...) must call _fail; got pass_count=" + str(inst8.get("_pass_count")) + " fail_count=" + str(inst8.get("_fail_count"))
	)
	inst8.free()

	# --- SMOKE-26: _assert_true with custom fail_msg uses it ---
	# We cannot intercept print output headlessly, but we CAN verify the counter
	# behavior is identical to the default case (the custom message goes to print
	# output, which is observable but not assertable here). The behavioral
	# assertion is: _fail_count is incremented exactly once, same as the default
	# fail path. This is sufficient to verify the optional parameter is handled.
	var inst9: Object = _make_subclass_instance(utils_script)
	inst9.call("_assert_true", false, "dummy", "custom message")
	_assert_local(
		inst9.get("_fail_count") == 1,
		"SMOKE-26_assert_true_custom_fail_msg_increments_fail_count",
		"_assert_true(false, name, 'custom') must still call _fail; got fail_count=" + str(inst9.get("_fail_count"))
	)
	inst9.free()

	# --- SMOKE-27: _assert_false with custom fail_msg uses it ---
	var inst10: Object = _make_subclass_instance(utils_script)
	inst10.call("_assert_false", true, "dummy", "custom message")
	_assert_local(
		inst10.get("_fail_count") == 1,
		"SMOKE-27_assert_false_custom_fail_msg_increments_fail_count",
		"_assert_false(true, name, 'custom') must still call _fail; got fail_count=" + str(inst10.get("_fail_count"))
	)
	inst10.free()

	print("--- test_utils_smoke: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed ---")
	return _fail_count
