#
# test_maint_eapd_shared_enemy_animation_policy.gd
#
# Policy invariant tests for MAINT-EAPD (enemy_animation_per_type_policies_deferred).
# AC-1 / MAINT-EAPD-S1: shared EnemyAnimationController remains the canonical
# state-driven dispatcher; no per-type policy injection is asserted here (AC-2 future).
#
# Ticket: project_board/maintenance/in_progress/enemy_animation_per_type_policies_deferred.md
# Requirements: MAINT-EAPD-S1 (shared controller; defer split until material divergence)
#
# Test IDs: EAPD-P1..P7 — script load, class_name on GDScript, canonical res:// path,
# Node + canonical script, wiring API, default exports.
#

extends "res://tests/utils/test_utils.gd"

const _CONTROLLER_PATH: String = "res://scripts/enemies/enemy_animation_controller.gd"
const _CLASS_NAME: String = "EnemyAnimationController"

var _pass_count: int = 0
var _fail_count: int = 0


func run_all() -> int:
	print("=== MAINT-EAPD shared enemy animation policy (invariants) ===")
	_test_script_loads()
	_test_global_class_name_on_script()
	_test_canonical_resource_path()
	_test_instantiate_is_node_with_canonical_script()
	_test_wiring_api_surface()
	_test_default_export_tuning_semantics()
	print("  (" + str(_pass_count) + " passed, " + str(_fail_count) + " failed)")
	return _fail_count


func _controller_script() -> GDScript:
	var s: Variant = load(_CONTROLLER_PATH)
	return s as GDScript


func _test_script_loads() -> void:
	var s: GDScript = _controller_script()
	_assert_true(s != null, "EAPD-P1 script resource loads", "load returned null for " + _CONTROLLER_PATH)
	_assert_true(s.can_instantiate(), "EAPD-P1b script instantiable", "can_instantiate() false")


func _test_global_class_name_on_script() -> void:
	# GDScript global classes are not always visible via ClassDB in headless runs;
	# Script.get_global_name() is the stable contract for `class_name EnemyAnimationController`.
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P2 class_name on script", "prerequisite: script not loaded")
		return
	var gn: StringName = s.get_global_name()
	_assert_eq_string(_CLASS_NAME, str(gn), "EAPD-P2 class_name matches EnemyAnimationController")


func _test_canonical_resource_path() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P7 canonical resource_path", "prerequisite: script not loaded")
		return
	_assert_eq_string(_CONTROLLER_PATH, str(s.resource_path), "EAPD-P7 script resource_path is canonical shared controller path")


func _test_instantiate_is_node_with_canonical_script() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P3 extends Node", "prerequisite: script not loaded")
		_fail("EAPD-P3b canonical script on instance", "prerequisite: script not loaded")
		return
	var inst: Variant = s.new()
	_assert_true(inst is Node, "EAPD-P3 extends Node", "instance is not Node")
	var scr: Variant = (inst as Object).get_script()
	_assert_eq(scr, s, "EAPD-P3b instance uses canonical script resource")


func _test_wiring_api_surface() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P4 setup()", "prerequisite: script not loaded")
		_fail("EAPD-P5 notify_root_animation_wired()", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	_assert_true(inst.has_method("setup"), "EAPD-P4 setup() present", "missing setup")
	_assert_true(inst.has_method("notify_root_animation_wired"), "EAPD-P5 notify_root_animation_wired() present", "missing notify_root_animation_wired")


func _test_default_export_tuning_semantics() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P6 move_threshold default", "prerequisite: script not loaded")
		_fail("EAPD-P6 blend_time default", "prerequisite: script not loaded")
		return
	var inst: Variant = s.new()
	_assert_approx(float(inst.move_threshold), 0.1, "EAPD-P6 move_threshold default 0.1")
	_assert_approx(float(inst.blend_time), 0.15, "EAPD-P6 blend_time default 0.15")
