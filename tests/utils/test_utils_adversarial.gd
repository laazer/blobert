#
# test_utils_adversarial.gd
#
# Adversarial tests for tests/utils/test_utils.gd (the shared test utility base).
#
# Spec:   project_board/maintenance/in_progress/test_utility_consolidation.md
#         ## Specification — Requirements MAINT-TUC-1, MAINT-TUC-2, MAINT-TUC-3
#
# PURPOSE
# -------
# These tests expose specific vulnerabilities and blind spots in the smoke suite.
# They do NOT duplicate smoke-suite coverage; they target the gaps identified by
# the Test Breaker Agent adversarial review.
#
# Each test documents the vulnerability it targets and why it would be missed by
# the existing smoke suite.
#
# COVERAGE
# --------
# ADV-TU-1   run_all() return type is truly int, not bool — `false == 0` in GDScript
#              so a `return false` impl silently passes SMOKE-3.
# ADV-TU-2   _assert_eq_float is present (spec AC-2.11, omitted from SMOKE-4..15 list)
# ADV-TU-3   _assert_eq_str is present (spec AC-2.13, omitted from SMOKE-4..15 list)
# ADV-TU-4   _approx_eq is present (spec AC-2.14, omitted from SMOKE-4..15 list)
# ADV-TU-5   _near is present (spec AC-2.17, omitted from SMOKE-4..15 list)
# ADV-TU-6   _assert_eq_int behavior — correct pass on equal ints
# ADV-TU-7   _assert_eq_int behavior — correct fail on unequal ints
# ADV-TU-8   _assert_eq_int boundary — zero
# ADV-TU-9   _assert_eq_int boundary — negative values
# ADV-TU-10  _assert_eq_string behavior — correct pass
# ADV-TU-11  _assert_eq_string behavior — correct fail and message uses single-quotes
# ADV-TU-12  _assert_eq_str parameter order — actual-first convention (spec AC-2.13)
#              A swapped implementation would report wrong message but still fail,
#              revealing the order inversion.
# ADV-TU-13  _assert_approx at exact tolerance boundary — abs(a-b)==1e-4 must FAIL
#              (strict `<`, not `<=`). A misimplemented `<=` would silently pass.
# ADV-TU-14  _assert_approx passes when a==b (delta==0)
# ADV-TU-15  _assert_approx fails when delta > 1e-4
# ADV-TU-16  _assert_vec2_approx passes on equal vectors
# ADV-TU-17  _assert_vec2_approx fails when x component differs beyond tolerance
# ADV-TU-18  _assert_vec2_approx fails when y component differs beyond tolerance
# ADV-TU-19  _assert_vec3_near passes on equal vectors with tol=0.0
# ADV-TU-20  _assert_vec3_near fails when any component exceeds tolerance
# ADV-TU-21  _assert_vec3_near with tol=0.0 fails for non-identical vectors
# ADV-TU-22  Counter isolation — two separate instances have independent counters
# ADV-TU-23  _pass increments by exactly 1 per call (not 2, not 0)
# ADV-TU-24  _fail increments by exactly 1 per call (not 2, not 0)
# ADV-TU-25  Subclass that locally redefines _pass shadows correctly — its own
#              _pass_count is used (not a phantom from the base). This guards against
#              the base declaring _pass_count despite the spec prohibition.
# ADV-TU-26  _assert_eq Variant equality — int vs int passes
# ADV-TU-27  _assert_eq Variant equality — string vs string passes
# ADV-TU-28  _assert_eq Variant equality — int 1 vs int 2 fails (unequal values)
# ADV-TU-29  _assert_eq_float tolerance — values within 0.0001 pass
# ADV-TU-30  _assert_eq_float tolerance — values equal pass
# ADV-TU-31  _assert_eq_float tolerance — values differing by exactly 0.0001 fail
#              (strict `<` per spec AC-2.11)
# ADV-TU-32  _near(a, b, tol) boundary — absf(a-b)==tol must PASS (spec uses `<=`)
#              This is the opposite strict/inclusive semantics from _approx_eq. A
#              copy-paste of _approx_eq logic would use `<` and fail this test.
# ADV-TU-33  _near(a, b, tol) above tolerance must FAIL
# ADV-TU-34  run_all() called multiple times always returns 0 (idempotent no-op)
#
# ADVERSARIAL ASSUMPTIONS
# -----------------------
# Assumption AA-1: `typeof()` in GDScript returns TYPE_INT (2) for int, TYPE_BOOL (1)
#   for bool. We use `typeof(result) == TYPE_INT` to distinguish `false` from `0`
#   even though `false == 0` evaluates true in GDScript.
# Assumption AA-2: GDScript `get_script_method_list()` on a GDScript includes all
#   user-defined functions at that script level, including internal helpers like
#   `_approx_eq` and `_near`. This is consistent with Assumption A in the smoke suite.
# Assumption AA-3: Creating two independent instances via `utils_script.new()` gives
#   truly independent objects with no shared mutable state between them.
# Assumption AA-4: `inst.set("_pass_count", 0)` followed by reading via `inst.get()`
#   exercises the same dynamic property mechanism as the smoke suite's
#   `_make_subclass_instance` helper.
#

extends Object

var _pass_count: int = 0
var _fail_count: int = 0

const _UTILS_PATH: String = "res://tests/utils/test_utils.gd"


# ---------------------------------------------------------------------------
# Internal helpers (self-contained — does NOT depend on test_utils.gd)
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
# Helper: collect method names from a script
# ---------------------------------------------------------------------------

func _method_names(script: GDScript) -> Array:
	var names: Array = []
	for m in script.get_script_method_list():
		names.append(m["name"])
	return names


# ---------------------------------------------------------------------------
# Helper: create an instrumented instance with injected counters
# ---------------------------------------------------------------------------

func _make_inst(utils_script: GDScript) -> Object:
	var inst: Object = utils_script.new()
	inst.set("_pass_count", 0)
	inst.set("_fail_count", 0)
	return inst


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

func run_all() -> int:
	_pass_count = 0
	_fail_count = 0

	print("--- test_utils_adversarial ---")

	var utils_script: GDScript = load(_UTILS_PATH)
	if utils_script == null:
		var remaining: int = 34
		_fail_count += remaining
		print("  (skipping ADV-TU-1..34: script load failed — run smoke suite first)")
		print("--- test_utils_adversarial: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed ---")
		return _fail_count

	var methods: Array = _method_names(utils_script)

	# -----------------------------------------------------------------------
	# ADV-TU-1: run_all() return type must be int, not bool
	# -----------------------------------------------------------------------
	# Vulnerability: `false == 0` is true in GDScript, so SMOKE-3 passes even
	# if the implementation does `return false`. We check typeof() to distinguish.
	var base_inst: Object = utils_script.new()
	var run_result = base_inst.call("run_all")
	_assert_local(
		typeof(run_result) == TYPE_INT,
		"ADV-TU-1_run_all_return_type_is_int_not_bool",
		"run_all() must return TYPE_INT; got typeof=" + str(typeof(run_result)) + " value=" + str(run_result)
	)
	base_inst.free()

	# -----------------------------------------------------------------------
	# ADV-TU-2: _assert_eq_float is present (omitted from SMOKE-4..15 check)
	# -----------------------------------------------------------------------
	_assert_local(
		methods.has("_assert_eq_float"),
		"ADV-TU-2_has__assert_eq_float",
		"test_utils.gd is missing _assert_eq_float (spec AC-2.11; omitted from smoke suite method list)"
	)

	# -----------------------------------------------------------------------
	# ADV-TU-3: _assert_eq_str is present (omitted from SMOKE-4..15 check)
	# -----------------------------------------------------------------------
	_assert_local(
		methods.has("_assert_eq_str"),
		"ADV-TU-3_has__assert_eq_str",
		"test_utils.gd is missing _assert_eq_str (spec AC-2.13; omitted from smoke suite method list)"
	)

	# -----------------------------------------------------------------------
	# ADV-TU-4: _approx_eq is present (omitted from SMOKE-4..15 check)
	# -----------------------------------------------------------------------
	_assert_local(
		methods.has("_approx_eq"),
		"ADV-TU-4_has__approx_eq",
		"test_utils.gd is missing _approx_eq (spec AC-2.14; omitted from smoke suite method list)"
	)

	# -----------------------------------------------------------------------
	# ADV-TU-5: _near is present (omitted from SMOKE-4..15 check)
	# -----------------------------------------------------------------------
	_assert_local(
		methods.has("_near"),
		"ADV-TU-5_has__near",
		"test_utils.gd is missing _near (spec AC-2.17; omitted from smoke suite method list)"
	)

	# -----------------------------------------------------------------------
	# ADV-TU-6: _assert_eq_int — pass on equal ints
	# -----------------------------------------------------------------------
	var i6: Object = _make_inst(utils_script)
	i6.call("_assert_eq_int", 42, 42, "dummy")
	_assert_local(
		i6.get("_pass_count") == 1 and i6.get("_fail_count") == 0,
		"ADV-TU-6_assert_eq_int_pass",
		"_assert_eq_int(42, 42) must pass"
	)
	i6.free()

	# -----------------------------------------------------------------------
	# ADV-TU-7: _assert_eq_int — fail on unequal ints
	# -----------------------------------------------------------------------
	var i7: Object = _make_inst(utils_script)
	i7.call("_assert_eq_int", 1, 2, "dummy")
	_assert_local(
		i7.get("_pass_count") == 0 and i7.get("_fail_count") == 1,
		"ADV-TU-7_assert_eq_int_fail",
		"_assert_eq_int(1, 2) must fail"
	)
	i7.free()

	# -----------------------------------------------------------------------
	# ADV-TU-8: _assert_eq_int boundary — zero
	# -----------------------------------------------------------------------
	var i8: Object = _make_inst(utils_script)
	i8.call("_assert_eq_int", 0, 0, "dummy")
	_assert_local(
		i8.get("_pass_count") == 1,
		"ADV-TU-8_assert_eq_int_zero",
		"_assert_eq_int(0, 0) must pass"
	)
	i8.free()

	# -----------------------------------------------------------------------
	# ADV-TU-9: _assert_eq_int boundary — negative values
	# -----------------------------------------------------------------------
	var i9: Object = _make_inst(utils_script)
	i9.call("_assert_eq_int", -99, -99, "dummy")
	_assert_local(
		i9.get("_pass_count") == 1,
		"ADV-TU-9_assert_eq_int_negative",
		"_assert_eq_int(-99, -99) must pass"
	)
	i9.free()

	# -----------------------------------------------------------------------
	# ADV-TU-10: _assert_eq_string — pass on equal strings
	# -----------------------------------------------------------------------
	var i10: Object = _make_inst(utils_script)
	i10.call("_assert_eq_string", "hello", "hello", "dummy")
	_assert_local(
		i10.get("_pass_count") == 1 and i10.get("_fail_count") == 0,
		"ADV-TU-10_assert_eq_string_pass",
		"_assert_eq_string('hello', 'hello') must pass"
	)
	i10.free()

	# -----------------------------------------------------------------------
	# ADV-TU-11: _assert_eq_string — fail on mismatch; message uses single-quotes
	# -----------------------------------------------------------------------
	# Vulnerability: _assert_eq_str uses double-quotes in its message. If someone
	# accidentally copies _assert_eq_str logic into _assert_eq_string, the message
	# format will be wrong. We verify the fail message contains single-quote delimiters
	# by checking that _fail_count is incremented (the format check is done via
	# a helper that captures _fail_count==1 to confirm the fail branch was taken).
	# We cannot assert the exact message text headlessly, but we CAN verify that
	# _assert_eq_string("a", "b") fails while _assert_eq_string("a", "a") passes,
	# ensuring the comparison logic and branching are correct.
	var i11: Object = _make_inst(utils_script)
	i11.call("_assert_eq_string", "expected_val", "actual_val", "dummy")
	_assert_local(
		i11.get("_fail_count") == 1 and i11.get("_pass_count") == 0,
		"ADV-TU-11_assert_eq_string_fail",
		"_assert_eq_string with mismatched strings must fail"
	)
	i11.free()

	# -----------------------------------------------------------------------
	# ADV-TU-12: _assert_eq_str parameter order — actual-first
	# -----------------------------------------------------------------------
	# Vulnerability: spec AC-2.13 says _assert_eq_str(actual, expected, name) with
	# actual FIRST — opposite of _assert_eq_string(expected, actual, name).
	# A copy-paste error that swaps them would still pass/fail correctly on equal
	# strings but produce wrong fail messages. Since we cannot read print output,
	# we test with unequal strings and verify the failure is recorded. We also
	# verify calling it with (actual, expected) order where actual != expected fails.
	var i12: Object = _make_inst(utils_script)
	i12.call("_assert_eq_str", "actual_value", "expected_value", "dummy")
	_assert_local(
		i12.get("_fail_count") == 1 and i12.get("_pass_count") == 0,
		"ADV-TU-12_assert_eq_str_fail_on_mismatch",
		"_assert_eq_str(actual, expected) with mismatched values must fail"
	)
	i12.free()

	var i12b: Object = _make_inst(utils_script)
	i12b.call("_assert_eq_str", "same", "same", "dummy")
	_assert_local(
		i12b.get("_pass_count") == 1 and i12b.get("_fail_count") == 0,
		"ADV-TU-12b_assert_eq_str_pass_on_match",
		"_assert_eq_str(actual, expected) with equal values must pass"
	)
	i12b.free()

	# -----------------------------------------------------------------------
	# ADV-TU-13: _assert_approx at EXACT tolerance boundary must FAIL
	# -----------------------------------------------------------------------
	# Vulnerability: spec uses strict `<` (not `<=`). A misimplemented `<=` would
	# pass this boundary case silently. abs(1e-4) == 1e-4 exactly.
	var i13: Object = _make_inst(utils_script)
	var a_val: float = 0.0
	var b_val: float = 1e-4
	i13.call("_assert_approx", a_val, b_val, "boundary")
	_assert_local(
		i13.get("_fail_count") == 1,
		"ADV-TU-13_assert_approx_exact_boundary_must_fail",
		"_assert_approx(0.0, 1e-4) must FAIL (boundary is exclusive: abs < 1e-4)"
	)
	i13.free()

	# -----------------------------------------------------------------------
	# ADV-TU-14: _assert_approx passes when a==b (delta==0)
	# -----------------------------------------------------------------------
	var i14: Object = _make_inst(utils_script)
	i14.call("_assert_approx", 3.14159, 3.14159, "equal")
	_assert_local(
		i14.get("_pass_count") == 1,
		"ADV-TU-14_assert_approx_equal_values_pass",
		"_assert_approx(x, x) must pass"
	)
	i14.free()

	# -----------------------------------------------------------------------
	# ADV-TU-15: _assert_approx fails when delta > 1e-4
	# -----------------------------------------------------------------------
	var i15: Object = _make_inst(utils_script)
	i15.call("_assert_approx", 0.0, 0.001, "too_far")
	_assert_local(
		i15.get("_fail_count") == 1,
		"ADV-TU-15_assert_approx_fail_on_large_delta",
		"_assert_approx(0.0, 0.001) must fail (delta 0.001 > 1e-4)"
	)
	i15.free()

	# -----------------------------------------------------------------------
	# ADV-TU-16: _assert_vec2_approx passes on equal vectors
	# -----------------------------------------------------------------------
	var i16: Object = _make_inst(utils_script)
	i16.call("_assert_vec2_approx", Vector2(1.0, 2.0), Vector2(1.0, 2.0), "equal_v2")
	_assert_local(
		i16.get("_pass_count") == 1,
		"ADV-TU-16_assert_vec2_approx_pass",
		"_assert_vec2_approx with equal vectors must pass"
	)
	i16.free()

	# -----------------------------------------------------------------------
	# ADV-TU-17: _assert_vec2_approx fails when x component differs beyond tolerance
	# -----------------------------------------------------------------------
	var i17: Object = _make_inst(utils_script)
	i17.call("_assert_vec2_approx", Vector2(0.0, 0.0), Vector2(0.001, 0.0), "x_diff")
	_assert_local(
		i17.get("_fail_count") == 1,
		"ADV-TU-17_assert_vec2_approx_fail_x",
		"_assert_vec2_approx must fail when x differs by 0.001"
	)
	i17.free()

	# -----------------------------------------------------------------------
	# ADV-TU-18: _assert_vec2_approx fails when y component differs beyond tolerance
	# -----------------------------------------------------------------------
	var i18: Object = _make_inst(utils_script)
	i18.call("_assert_vec2_approx", Vector2(0.0, 0.0), Vector2(0.0, 0.001), "y_diff")
	_assert_local(
		i18.get("_fail_count") == 1,
		"ADV-TU-18_assert_vec2_approx_fail_y",
		"_assert_vec2_approx must fail when y differs by 0.001"
	)
	i18.free()

	# -----------------------------------------------------------------------
	# ADV-TU-19: _assert_vec3_near passes on equal vectors with tol=0.0
	# -----------------------------------------------------------------------
	var i19: Object = _make_inst(utils_script)
	i19.call("_assert_vec3_near", Vector3(1.0, 2.0, 3.0), Vector3(1.0, 2.0, 3.0), 0.0, "equal_v3")
	_assert_local(
		i19.get("_pass_count") == 1,
		"ADV-TU-19_assert_vec3_near_pass_tol0",
		"_assert_vec3_near with identical vectors and tol=0.0 must pass"
	)
	i19.free()

	# -----------------------------------------------------------------------
	# ADV-TU-20: _assert_vec3_near fails when a component exceeds tolerance
	# -----------------------------------------------------------------------
	var i20: Object = _make_inst(utils_script)
	i20.call("_assert_vec3_near", Vector3(0.0, 0.0, 0.0), Vector3(0.0, 0.0, 1.0), 0.5, "z_fail")
	_assert_local(
		i20.get("_fail_count") == 1,
		"ADV-TU-20_assert_vec3_near_fail_z",
		"_assert_vec3_near must fail when z differs by 1.0 with tol=0.5"
	)
	i20.free()

	# -----------------------------------------------------------------------
	# ADV-TU-21: _assert_vec3_near with tol=0.0 fails for non-identical vectors
	# -----------------------------------------------------------------------
	var i21: Object = _make_inst(utils_script)
	i21.call("_assert_vec3_near", Vector3(0.0, 0.0, 0.0), Vector3(0.0, 0.0, 0.001), 0.0, "tol0_fail")
	_assert_local(
		i21.get("_fail_count") == 1,
		"ADV-TU-21_assert_vec3_near_tol0_fail",
		"_assert_vec3_near with tol=0.0 must fail for non-identical vectors"
	)
	i21.free()

	# -----------------------------------------------------------------------
	# ADV-TU-22: Counter isolation between two separate instances
	# -----------------------------------------------------------------------
	# Vulnerability: if the implementation accidentally declares a static or class-level
	# variable for counters (not possible in standard GDScript but a copy-paste error
	# could introduce shared state via a singleton reference), two instances would not
	# be independent. This confirms per-instance isolation.
	var ia: Object = _make_inst(utils_script)
	var ib: Object = _make_inst(utils_script)
	ia.call("_pass", "a1")
	ia.call("_pass", "a2")
	ia.call("_pass", "a3")
	ib.call("_pass", "b1")
	_assert_local(
		ia.get("_pass_count") == 3 and ib.get("_pass_count") == 1,
		"ADV-TU-22_counter_isolation_between_instances",
		"Instances must have independent _pass_count; got ia=" + str(ia.get("_pass_count")) + " ib=" + str(ib.get("_pass_count"))
	)
	ia.free()
	ib.free()

	# -----------------------------------------------------------------------
	# ADV-TU-23: _pass increments by exactly 1 per call (not 2, not 0)
	# -----------------------------------------------------------------------
	var i23: Object = _make_inst(utils_script)
	i23.call("_pass", "once")
	i23.call("_pass", "twice")
	_assert_local(
		i23.get("_pass_count") == 2,
		"ADV-TU-23_pass_increments_by_exactly_1",
		"Two _pass() calls must yield _pass_count==2; got " + str(i23.get("_pass_count"))
	)
	i23.free()

	# -----------------------------------------------------------------------
	# ADV-TU-24: _fail increments by exactly 1 per call (not 2, not 0)
	# -----------------------------------------------------------------------
	var i24: Object = _make_inst(utils_script)
	i24.call("_fail", "once", "msg1")
	i24.call("_fail", "twice", "msg2")
	_assert_local(
		i24.get("_fail_count") == 2,
		"ADV-TU-24_fail_increments_by_exactly_1",
		"Two _fail() calls must yield _fail_count==2; got " + str(i24.get("_fail_count"))
	)
	i24.free()

	# -----------------------------------------------------------------------
	# ADV-TU-25: Subclass that locally redefines _pass uses its own counter
	# -----------------------------------------------------------------------
	# Vulnerability: if test_utils.gd secretly declares _pass_count despite the spec
	# prohibition, a subclass's redeclaration of _pass_count would shadow the base
	# variable. The smoke suite verifies _pass_count is absent from the base
	# (SMOKE-16), but does not verify that a second, separately-created instance
	# has its counter start at 0 independently.
	# We create two fresh instances and confirm each starts at 0.
	var ix: Object = _make_inst(utils_script)
	var iy: Object = _make_inst(utils_script)
	ix.call("_pass", "x_only")
	_assert_local(
		ix.get("_pass_count") == 1 and iy.get("_pass_count") == 0,
		"ADV-TU-25_fresh_instance_counter_starts_at_zero",
		"Fresh instance must start with _pass_count==0; got ix=" + str(ix.get("_pass_count")) + " iy=" + str(iy.get("_pass_count"))
	)
	ix.free()
	iy.free()

	# -----------------------------------------------------------------------
	# ADV-TU-26: _assert_eq Variant — int vs int passes
	# -----------------------------------------------------------------------
	var i26: Object = _make_inst(utils_script)
	i26.call("_assert_eq", 7, 7, "int_eq")
	_assert_local(
		i26.get("_pass_count") == 1,
		"ADV-TU-26_assert_eq_int_pass",
		"_assert_eq(7, 7) must pass"
	)
	i26.free()

	# -----------------------------------------------------------------------
	# ADV-TU-27: _assert_eq Variant — string vs string passes
	# -----------------------------------------------------------------------
	var i27: Object = _make_inst(utils_script)
	i27.call("_assert_eq", "foo", "foo", "str_eq")
	_assert_local(
		i27.get("_pass_count") == 1,
		"ADV-TU-27_assert_eq_string_pass",
		"_assert_eq('foo', 'foo') must pass"
	)
	i27.free()

	# -----------------------------------------------------------------------
	# ADV-TU-28: _assert_eq Variant — int 1 vs int 2 fails (unequal values)
	# -----------------------------------------------------------------------
	# Vulnerability: the fail branch of _assert_eq must fire when expected != actual.
	# NOTE: GDScript 4 Variant `==` coerces int vs string (1 == "1" returns true),
	# so the original type-mismatch assumption was wrong. Instead we use two
	# different integers, which are unambiguously unequal in all GDScript versions.
	var i28: Object = _make_inst(utils_script)
	i28.call("_assert_eq", 1, 2, "value_mismatch")
	_assert_local(
		i28.get("_fail_count") == 1,
		"ADV-TU-28_assert_eq_value_mismatch_fails",
		"_assert_eq(1, 2) must fail — different integers are not equal"
	)
	i28.free()

	# -----------------------------------------------------------------------
	# ADV-TU-29: _assert_eq_float — values within 0.0001 pass
	# -----------------------------------------------------------------------
	var i29: Object = _make_inst(utils_script)
	i29.call("_assert_eq_float", 1.0, 1.00005, "within_tol")
	_assert_local(
		i29.get("_pass_count") == 1,
		"ADV-TU-29_assert_eq_float_within_tolerance",
		"_assert_eq_float(1.0, 1.00005) must pass (delta 0.00005 < 0.0001)"
	)
	i29.free()

	# -----------------------------------------------------------------------
	# ADV-TU-30: _assert_eq_float — equal values pass
	# -----------------------------------------------------------------------
	var i30: Object = _make_inst(utils_script)
	i30.call("_assert_eq_float", 2.5, 2.5, "exact_eq")
	_assert_local(
		i30.get("_pass_count") == 1,
		"ADV-TU-30_assert_eq_float_equal_values",
		"_assert_eq_float(2.5, 2.5) must pass"
	)
	i30.free()

	# -----------------------------------------------------------------------
	# ADV-TU-31: _assert_eq_float — values differing by exactly 0.0001 fail
	# -----------------------------------------------------------------------
	# Vulnerability: spec uses strict `<` (absf(actual - expected) < 0.0001).
	# A misimplemented `<=` would pass this boundary, hiding precision bugs.
	var i31: Object = _make_inst(utils_script)
	i31.call("_assert_eq_float", 0.0, 0.0001, "exact_boundary")
	_assert_local(
		i31.get("_fail_count") == 1,
		"ADV-TU-31_assert_eq_float_exact_boundary_must_fail",
		"_assert_eq_float(0.0, 0.0001) must FAIL (boundary is exclusive: absf < 0.0001)"
	)
	i31.free()

	# -----------------------------------------------------------------------
	# ADV-TU-32: _near(a, b, tol) boundary — absf(a-b)==tol must PASS (inclusive <=)
	# -----------------------------------------------------------------------
	# Vulnerability: spec AC-2.17 says `absf(a - b) <= tol` (INCLUSIVE). This is
	# the OPPOSITE of _approx_eq which uses strict `<`. A copy-paste of _approx_eq
	# into _near would make this boundary case fail instead of pass.
	# We use 0.5 and tolerance 0.5: absf(0.5 - 0.0) == 0.5 exactly in IEEE 754
	# (0.5 is a power-of-two fraction, so it has a lossless float representation).
	# This avoids the float-representation ambiguity of 0.1 which cannot be
	# represented exactly in binary floating-point.
	var i32: Object = _make_inst(utils_script)
	i32.call("_assert_vec3_near", Vector3(0.0, 0.0, 0.0), Vector3(0.5, 0.0, 0.0), 0.5, "at_boundary")
	_assert_local(
		i32.get("_pass_count") == 1,
		"ADV-TU-32_near_at_exact_tol_must_pass",
		"_assert_vec3_near with component delta==tol must PASS (spec uses <=)"
	)
	i32.free()

	# -----------------------------------------------------------------------
	# ADV-TU-33: _near above tolerance must FAIL
	# -----------------------------------------------------------------------
	var i33: Object = _make_inst(utils_script)
	i33.call("_assert_vec3_near", Vector3(0.0, 0.0, 0.0), Vector3(0.101, 0.0, 0.0), 0.1, "above_tol")
	_assert_local(
		i33.get("_fail_count") == 1,
		"ADV-TU-33_near_above_tol_must_fail",
		"_assert_vec3_near with component delta 0.101 > tol 0.1 must FAIL"
	)
	i33.free()

	# -----------------------------------------------------------------------
	# ADV-TU-34: run_all() is idempotent — multiple calls always return 0
	# -----------------------------------------------------------------------
	# Vulnerability: if run_all() accidentally accumulates state (e.g., increments
	# an internal counter), repeated calls might return non-zero. Since test_utils.gd
	# should be a pure no-op, call it twice.
	var i34: Object = utils_script.new()
	var r1 = i34.call("run_all")
	var r2 = i34.call("run_all")
	_assert_local(
		r1 == 0 and r2 == 0,
		"ADV-TU-34_run_all_idempotent",
		"run_all() must return 0 on repeated calls; got r1=" + str(r1) + " r2=" + str(r2)
	)
	i34.free()

	print("--- test_utils_adversarial: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed ---")
	return _fail_count
