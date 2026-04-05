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
# Test IDs: EAPD-P1..P22 — script load, class_name, canonical path, Node identity,
# wiring API, defaults, adversarial wiring/stress, shared state→clip mapping contract.
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
	_test_setup_null_and_reassign_order()
	_test_notify_root_animation_wired_orphan_no_crash()
	_test_per_instance_export_independence()
	_test_stress_many_instantiations_same_script()
	_test_early_lifecycle_methods_no_crash_without_ready_ok()
	_test_internal_resolve_clip_contract()
	_test_internal_resolve_speed_contract()
	_test_private_resolver_methods_present()
	_test_wrong_script_path_does_not_satisfy_policy()
	_test_export_boundary_mutation_values_persist()
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


func _test_setup_null_and_reassign_order() -> void:
	# CHECKPOINT: Per-instance export tuning without identity branching is not material
	# divergence; setup(null) must remain valid for deferred / pre-M15 wiring (shared policy).
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P8 setup(null)", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	inst.setup(null)
	_assert_true(inst.state_machine == null, "EAPD-P8 setup(null) leaves state_machine null")
	inst.setup(inst)
	_assert_true(inst.state_machine == inst, "EAPD-P8b setup(non-null) assigns state_machine")
	inst.setup(null)
	_assert_true(inst.state_machine == null, "EAPD-P8c setup(null) after non-null clears")


func _test_notify_root_animation_wired_orphan_no_crash() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P9 orphan notify_root_animation_wired", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	inst.notify_root_animation_wired()
	_assert_true(is_instance_valid(inst), "EAPD-P9 orphan notify_root_animation_wired survives")


func _test_per_instance_export_independence() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P10 independent blend_time", "prerequisite: script not loaded")
		_fail("EAPD-P10b independent move_threshold", "prerequisite: script not loaded")
		return
	var a: Variant = s.new()
	var b: Variant = s.new()
	a.blend_time = 0.99
	b.blend_time = 0.01
	a.move_threshold = 0.05
	b.move_threshold = 2.0
	_assert_approx(float(a.blend_time), 0.99, "EAPD-P10 independent blend_time A")
	_assert_approx(float(b.blend_time), 0.01, "EAPD-P10 independent blend_time B")
	_assert_approx(float(a.move_threshold), 0.05, "EAPD-P10b independent move_threshold A")
	_assert_approx(float(b.move_threshold), 2.0, "EAPD-P10b independent move_threshold B")


func _test_stress_many_instantiations_same_script() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P11 stress instantiate", "prerequisite: script not loaded")
		return
	const N: int = 64
	for i in N:
		var n: Node = s.new() as Node
		var scr: Variant = n.get_script()
		_assert_eq(scr, s, "EAPD-P11 stress instance " + str(i) + " uses canonical script")
		n.free()


func _test_early_lifecycle_methods_no_crash_without_ready_ok() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P12 trigger_hit before ready_ok", "prerequisite: script not loaded")
		_fail("EAPD-P13 _physics_process before ready_ok", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	inst.trigger_hit_animation()
	_assert_true(is_instance_valid(inst), "EAPD-P12 trigger_hit before ready_ok survives")
	inst.call("_physics_process", 0.0)
	_assert_true(is_instance_valid(inst), "EAPD-P13 _physics_process before ready_ok survives")


func _test_internal_resolve_clip_contract() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P14 resolve_clip mapping", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	var clip_dead: Variant = inst.call("_resolve_clip_name", "dead", 0.0)
	var clip_unknown: Variant = inst.call("_resolve_clip_name", "nonexistent_state_xyz", 0.0)
	var clip_idle_low: Variant = inst.call("_resolve_clip_name", "idle", 0.0)
	var clip_idle_high: Variant = inst.call("_resolve_clip_name", "active", 1.0)
	var clip_empty: Variant = inst.call("_resolve_clip_name", "", 0.0)
	_assert_eq_string("Death", str(clip_dead), "EAPD-P14a dead -> Death")
	_assert_eq_string("Idle", str(clip_unknown), "EAPD-P14b unknown state -> Idle fallback")
	_assert_eq_string("Idle", str(clip_idle_low), "EAPD-P14c idle below threshold -> Idle")
	_assert_eq_string("Walk", str(clip_idle_high), "EAPD-P14d active above threshold -> Walk")
	_assert_eq_string("Idle", str(clip_empty), "EAPD-P14e empty state -> Idle fallback")


func _test_internal_resolve_speed_contract() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P15 resolve_speed mapping", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	_assert_approx(float(inst.call("_resolve_speed", "dead")), 1.0, "EAPD-P15a dead speed")
	_assert_approx(float(inst.call("_resolve_speed", "infected")), 0.0, "EAPD-P15b infected speed")
	_assert_approx(float(inst.call("_resolve_speed", "weakened")), 0.5, "EAPD-P15c weakened speed")
	_assert_approx(float(inst.call("_resolve_speed", "idle")), 1.0, "EAPD-P15d idle speed default")
	_assert_approx(float(inst.call("_resolve_speed", "active")), 1.0, "EAPD-P15e active speed default")


func _test_private_resolver_methods_present() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P16 resolver methods exist", "prerequisite: script not loaded")
		return
	var inst: Object = s.new()
	_assert_true(inst.has_method("_resolve_clip_name"), "EAPD-P16 _resolve_clip_name present")
	_assert_true(inst.has_method("_resolve_speed"), "EAPD-P16b _resolve_speed present")


func _test_wrong_script_path_does_not_satisfy_policy() -> void:
	var bogus: Variant = load("res://scripts/enemies/enemy_animation_controller.gd.bogus_do_not_create")
	_assert_true(bogus == null, "EAPD-P17 bogus path does not load")
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P17b canonical still loads", "prerequisite: script not loaded")
		return
	_assert_true(s is GDScript, "EAPD-P17b canonical controller path loads GDScript")


func _test_export_boundary_mutation_values_persist() -> void:
	var s: GDScript = _controller_script()
	if s == null:
		_fail("EAPD-P18 negative move_threshold persists", "prerequisite: script not loaded")
		_fail("EAPD-P19 huge blend_time persists", "prerequisite: script not loaded")
		_fail("EAPD-P20 zero blend_time persists", "prerequisite: script not loaded")
		return
	var inst: Variant = s.new()
	inst.move_threshold = -1.0
	_assert_approx(float(inst.move_threshold), -1.0, "EAPD-P18 negative move_threshold persists")
	inst.blend_time = 1.0e9
	_assert_approx(float(inst.blend_time), 1.0e9, "EAPD-P19 huge blend_time persists")
	inst.blend_time = 0.0
	_assert_approx(float(inst.blend_time), 0.0, "EAPD-P20 zero blend_time persists")
	# Boundary combinator: negative threshold makes any non-negative vel_len "above" threshold.
	var walk_clip: Variant = inst.call("_resolve_clip_name", "idle", 0.0)
	_assert_eq_string("Walk", str(walk_clip), "EAPD-P21 idle vel 0 with negative threshold -> Walk")
	# vel_len must be strictly below move_threshold (-1.0) to stay Idle, e.g. -2.0 < -1.0
	var idle_clip: Variant = inst.call("_resolve_clip_name", "idle", -2.0)
	_assert_eq_string("Idle", str(idle_clip), "EAPD-P22 idle vel below negative threshold -> Idle")
