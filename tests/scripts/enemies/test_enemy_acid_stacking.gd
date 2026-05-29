#
# test_enemy_acid_stacking.gd
#
# Isolated behavioral tests for the stacking acid DoT mechanism introduced
# by M12-04: EnemyEffectTracker.add_acid_stack() / get_acid_stack_count()
# and EnemyBase.apply_acid_stack() / get_acid_stack_count().
#
# These tests have NO dependency on AttackExecutor. They test the stacking
# contract in isolation at the component boundary.
#
# Spec: project_board/specs/acid_claw_fusion_attack_spec.md
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
# Traceability: AC-3 (AC-3a through AC-3m), AC-DD-3, AC-DD-4
#
# NOTE: Tests will be RED until implementation:
#   - EnemyEffectTracker._acid_stack_counter field
#   - EnemyEffectTracker.add_acid_stack(duration, dps)
#   - EnemyEffectTracker.get_acid_stack_count()
#   - EnemyBase.apply_acid_stack(duration, dps)
#   - EnemyBase.get_acid_stack_count()
#

class_name EnemyAcidStackingTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_tracker() -> Node:
	# Creates a standalone EnemyEffectTracker instance (no scene tree needed).
	var script_res: GDScript = load("res://scripts/enemies/enemy_effect_tracker.gd")
	if script_res == null:
		return null
	var node = Node.new()
	node.set_script(script_res)
	return node


func _make_enemy() -> CharacterBody3D:
	# Creates a standalone EnemyBase instance.
	# Calls _ready() explicitly to initialize _effect_tracker child.
	var script_res: GDScript = load("res://scripts/enemies/enemy_base.gd")
	if script_res == null:
		return null
	var body = CharacterBody3D.new()
	body.set_script(script_res)
	# Add to scene tree so _ready() and child nodes work correctly.
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(body)
	else:
		body._ready()
	return body


func _free_enemy(enemy: CharacterBody3D) -> void:
	if enemy != null and is_instance_valid(enemy):
		enemy.free()


func _check_add_acid_stack(tracker: Node, test_label: String) -> bool:
	if not tracker.has_method("add_acid_stack"):
		_fail_test(test_label, "add_acid_stack not yet implemented on EnemyEffectTracker")
		return false
	return true


func _check_get_acid_stack_count(tracker: Node, test_label: String) -> bool:
	if not tracker.has_method("get_acid_stack_count"):
		_fail_test(test_label, "get_acid_stack_count not yet implemented on EnemyEffectTracker")
		return false
	return true


# ---------------------------------------------------------------------------
# AC-3h: Fresh tracker has 0 stacks
# ---------------------------------------------------------------------------

func test_ac3h_fresh_tracker_returns_0_stack_count() -> void:
	# AC-3h: get_acid_stack_count() returns 0 on freshly instantiated tracker
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3h", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_get_acid_stack_count(tracker, "AC-3h"):
		tracker.free()
		return
	_assert_eq_int(0, tracker.get_acid_stack_count(), "AC-3h_0_on_fresh_tracker")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3a: Three calls → get_acid_stack_count() == 3
# ---------------------------------------------------------------------------

func test_ac3a_three_add_acid_stack_calls_gives_count_3() -> void:
	# AC-3a: after 3 calls to add_acid_stack, get_acid_stack_count() == 3
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3a", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3a") or not _check_get_acid_stack_count(tracker, "AC-3a"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	_assert_eq_int(3, tracker.get_acid_stack_count(), "AC-3a_3_stacks")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3b: Stacks stored under indexed keys acid_stack_0, _1, _2
# ---------------------------------------------------------------------------

func test_ac3b_stacks_stored_under_indexed_keys() -> void:
	# AC-3b: keys are "acid_stack_0", "acid_stack_1", "acid_stack_2"
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3b", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3b"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	_assert_true(tracker.has_active_dot("acid_stack_0"), "AC-3b_key_acid_stack_0_exists")
	_assert_true(tracker.has_active_dot("acid_stack_1"), "AC-3b_key_acid_stack_1_exists")
	_assert_true(tracker.has_active_dot("acid_stack_2"), "AC-3b_key_acid_stack_2_exists")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3c: Each stack has correct initial remaining_duration and dps
# ---------------------------------------------------------------------------

func test_ac3c_each_stack_has_correct_initial_values() -> void:
	# AC-3c: remaining_duration == 2.5, dps == 0.4 for each stack
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3c", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3c"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	for key in ["acid_stack_0", "acid_stack_1", "acid_stack_2"]:
		if tracker._active_dots.has(key):
			_assert_eq_float(2.5, tracker._active_dots[key]["remaining_duration"],
				"AC-3c_remaining_duration_" + key)
			_assert_eq_float(0.4, tracker._active_dots[key]["dps"], "AC-3c_dps_" + key)
		else:
			_fail_test("AC-3c", "key " + key + " not present in _active_dots")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3d: Stack 0 expires — other two stacks unaffected
# ---------------------------------------------------------------------------

func test_ac3d_first_stack_expiry_leaves_two_remaining() -> void:
	# AC-3d: stack_0 expires → get_acid_stack_count() == 2
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3d", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3d") or not _check_get_acid_stack_count(tracker, "AC-3d"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	# Simulate stack 0 expiring: set its remaining_duration to 0 and process
	if tracker._active_dots.has("acid_stack_0"):
		tracker._active_dots["acid_stack_0"]["remaining_duration"] = 0.0
	# Trigger one _process tick to clean up expired dots
	tracker._process(0.001)
	_assert_eq_int(2, tracker.get_acid_stack_count(), "AC-3d_2_stacks_after_expiry_of_0")
	_assert_false(tracker.has_active_dot("acid_stack_0"), "AC-3d_stack_0_expired")
	_assert_true(tracker.has_active_dot("acid_stack_1"), "AC-3d_stack_1_still_active")
	_assert_true(tracker.has_active_dot("acid_stack_2"), "AC-3d_stack_2_still_active")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3e: Three stacks tick independently (dot_tick_requested per stack per tick)
# ---------------------------------------------------------------------------

func test_ac3e_three_stacks_emit_tick_per_stack() -> void:
	# AC-3e: 3 stacks → dot_tick_requested emitted 3 times per tick interval
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3e", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3e"):
		tracker.free()
		return
	var ticks: Array = []
	tracker.dot_tick_requested.connect(func(name, dmg): ticks.append({"name": name, "dmg": dmg}))
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	# Advance by exactly DOT_TICK_INTERVAL to trigger one tick per stack
	tracker._process(EnemyEffectTracker.DOT_TICK_INTERVAL)
	_assert_eq_int(3, ticks.size(), "AC-3e_3_ticks_per_interval")
	# Each tick should carry the correct key name
	var tick_names: Array = []
	for t in ticks:
		tick_names.append(t["name"])
	_assert_true(tick_names.has("acid_stack_0"), "AC-3e_tick_for_stack_0")
	_assert_true(tick_names.has("acid_stack_1"), "AC-3e_tick_for_stack_1")
	_assert_true(tick_names.has("acid_stack_2"), "AC-3e_tick_for_stack_2")
	tracker.free()


func test_ac3e_tick_damage_equals_dps_times_interval() -> void:
	# AC-3e: tick_damage == dps * DOT_TICK_INTERVAL == 0.4 * 0.5 = 0.2
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3e_dmg", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3e_dmg"):
		tracker.free()
		return
	var ticks: Array = []
	tracker.dot_tick_requested.connect(func(name, dmg): ticks.append({"name": name, "dmg": dmg}))
	tracker.add_acid_stack(2.5, 0.4)
	tracker._process(EnemyEffectTracker.DOT_TICK_INTERVAL)
	if ticks.size() > 0:
		_assert_eq_float(0.4 * EnemyEffectTracker.DOT_TICK_INTERVAL, ticks[0]["dmg"],
			"AC-3e_tick_damage_correct")
	else:
		_fail_test("AC-3e_dmg", "no tick emitted after DOT_TICK_INTERVAL")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3f: Counter monotonicity — 4th add after stack 0 expires uses key acid_stack_3
# ---------------------------------------------------------------------------

func test_ac3f_counter_monotonic_after_first_stack_expires() -> void:
	# AC-3f: after stack_0 expires, next add uses key "acid_stack_3" (not "acid_stack_0")
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3f", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3f") or not _check_get_acid_stack_count(tracker, "AC-3f"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)  # acid_stack_0
	tracker.add_acid_stack(2.5, 0.4)  # acid_stack_1
	tracker.add_acid_stack(2.5, 0.4)  # acid_stack_2
	# Expire stack 0
	if tracker._active_dots.has("acid_stack_0"):
		tracker._active_dots["acid_stack_0"]["remaining_duration"] = 0.0
	tracker._process(0.001)
	_assert_false(tracker.has_active_dot("acid_stack_0"), "AC-3f_stack_0_expired")
	# Add a 4th stack — counter was at 3, so key should be "acid_stack_3"
	tracker.add_acid_stack(2.5, 0.4)
	_assert_true(tracker.has_active_dot("acid_stack_3"), "AC-3f_4th_stack_key_is_stack_3")
	_assert_false(tracker.has_active_dot("acid_stack_0"), "AC-3f_stack_0_not_reused")
	_assert_eq_int(3, tracker.get_acid_stack_count(), "AC-3f_count_is_3_after_4th_add")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3g: apply_acid (non-stacking) does not affect acid_stack_* entries
# ---------------------------------------------------------------------------

func test_ac3g_base_apply_acid_coexists_without_affecting_stack_count() -> void:
	# AC-3g: apply_acid() stores at key "acid" — does NOT affect acid_stack_* count
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3g", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3g") or not _check_get_acid_stack_count(tracker, "AC-3g"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_dot("acid", 3.0, 1.0)  # existing non-stacking acid call
	_assert_eq_int(1, tracker.get_acid_stack_count(), "AC-3g_stack_count_unaffected_by_base_acid")
	_assert_true(tracker.has_active_dot("acid"), "AC-3g_base_acid_key_exists")
	_assert_true(tracker.has_active_dot("acid_stack_0"), "AC-3g_acid_stack_0_still_present")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3j: stop_all_effects clears all stacks
# ---------------------------------------------------------------------------

func test_ac3j_stop_all_effects_clears_all_stacks() -> void:
	# AC-3j: stop_all_effects() → get_acid_stack_count() == 0
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3j", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3j") or not _check_get_acid_stack_count(tracker, "AC-3j"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.add_acid_stack(2.5, 0.4)
	tracker.stop_all_effects()
	_assert_eq_int(0, tracker.get_acid_stack_count(), "AC-3j_0_stacks_after_stop_all")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3k: _acid_stack_counter persists across stop_all_effects
# ---------------------------------------------------------------------------

func test_ac3k_counter_persists_across_stop_all_effects() -> void:
	# AC-3k: counter does NOT reset on stop_all_effects; next add after stop uses next counter value
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("AC-3k", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "AC-3k") or not _check_get_acid_stack_count(tracker, "AC-3k"):
		tracker.free()
		return
	tracker.add_acid_stack(2.5, 0.4)  # acid_stack_0
	tracker.add_acid_stack(2.5, 0.4)  # acid_stack_1
	tracker.add_acid_stack(2.5, 0.4)  # acid_stack_2
	tracker.stop_all_effects()
	_assert_eq_int(0, tracker.get_acid_stack_count(), "AC-3k_0_after_stop")
	# Next add must use acid_stack_3 (not 0)
	tracker.add_acid_stack(2.5, 0.4)
	_assert_true(tracker.has_active_dot("acid_stack_3"), "AC-3k_next_key_is_stack_3")
	_assert_false(tracker.has_active_dot("acid_stack_0"), "AC-3k_stack_0_not_reused_after_stop")
	_assert_eq_int(1, tracker.get_acid_stack_count(), "AC-3k_count_1_after_single_add_post_stop")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-3i: apply_acid_stack on dead EnemyBase — no stack added
# ---------------------------------------------------------------------------

func test_ac3i_apply_acid_stack_on_dead_enemy_no_effect() -> void:
	# AC-3i: apply_acid_stack() on _is_dead==true enemy returns without adding stack
	var enemy = _make_enemy()
	if enemy == null:
		_fail_test("AC-3i", "enemy_base.gd not loadable")
		return
	if not enemy.has_method("apply_acid_stack"):
		_fail_test("AC-3i", "apply_acid_stack not yet implemented on EnemyBase")
		_free_enemy(enemy)
		return
	if not enemy.has_method("get_acid_stack_count"):
		_fail_test("AC-3i", "get_acid_stack_count not yet implemented on EnemyBase")
		_free_enemy(enemy)
		return
	enemy._is_dead = true
	enemy.apply_acid_stack(2.5, 0.4)
	_assert_eq_int(0, enemy.get_acid_stack_count(), "AC-3i_no_stack_on_dead")
	_free_enemy(enemy)


# ---------------------------------------------------------------------------
# AC-3l: EnemyBase.apply_acid_stack method exists (has_method check)
# ---------------------------------------------------------------------------

func test_ac3l_enemy_base_has_apply_acid_stack_method() -> void:
	# AC-3l: EnemyBase exposes apply_acid_stack as public method
	var enemy = _make_enemy()
	if enemy == null:
		_fail_test("AC-3l", "enemy_base.gd not loadable")
		return
	_assert_true(enemy.has_method("apply_acid_stack"), "AC-3l_has_method_apply_acid_stack")
	_free_enemy(enemy)


# ---------------------------------------------------------------------------
# AC-3m: EnemyBase.get_acid_stack_count delegates to tracker
# ---------------------------------------------------------------------------

func test_ac3m_enemy_base_get_acid_stack_count_delegates() -> void:
	# AC-3m: enemy.get_acid_stack_count() delegates to _effect_tracker.get_acid_stack_count()
	var enemy = _make_enemy()
	if enemy == null:
		_fail_test("AC-3m", "enemy_base.gd not loadable")
		return
	if not enemy.has_method("apply_acid_stack"):
		_fail_test("AC-3m", "apply_acid_stack not yet implemented")
		_free_enemy(enemy)
		return
	if not enemy.has_method("get_acid_stack_count"):
		_fail_test("AC-3m", "get_acid_stack_count not yet implemented on EnemyBase")
		_free_enemy(enemy)
		return
	_assert_eq_int(0, enemy.get_acid_stack_count(), "AC-3m_initial_0_via_enemy")
	enemy.apply_acid_stack(2.5, 0.4)
	enemy.apply_acid_stack(2.5, 0.4)
	enemy.apply_acid_stack(2.5, 0.4)
	_assert_eq_int(3, enemy.get_acid_stack_count(), "AC-3m_3_via_enemy")
	_free_enemy(enemy)


# ---------------------------------------------------------------------------
# Two stacks decay independently (timing isolation)
# ---------------------------------------------------------------------------

func test_two_stacks_decay_independently() -> void:
	# Two stacks with different durations — shorter one expires, longer persists
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("TWO_STACKS_DECAY", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "TWO_STACKS_DECAY") or not _check_get_acid_stack_count(tracker, "TWO_STACKS_DECAY"):
		tracker.free()
		return
	tracker.add_acid_stack(0.3, 0.4)  # acid_stack_0 — short
	tracker.add_acid_stack(5.0, 0.4)  # acid_stack_1 — long
	_assert_eq_int(2, tracker.get_acid_stack_count(), "TWO_STACKS_DECAY_initial_2")
	# Process enough time to expire stack_0 but not stack_1
	tracker._process(0.35)
	_assert_false(tracker.has_active_dot("acid_stack_0"), "TWO_STACKS_DECAY_stack0_expired")
	_assert_true(tracker.has_active_dot("acid_stack_1"), "TWO_STACKS_DECAY_stack1_still_active")
	_assert_eq_int(1, tracker.get_acid_stack_count(), "TWO_STACKS_DECAY_count_1_after_expiry")
	tracker.free()


# ---------------------------------------------------------------------------
# Three stacks: correct count before/during/after decay
# ---------------------------------------------------------------------------

func test_three_stacks_count_before_during_after_decay() -> void:
	# Full lifecycle: add 3 stacks, let them expire one by one, verify count at each stage
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("THREE_DECAY", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "THREE_DECAY") or not _check_get_acid_stack_count(tracker, "THREE_DECAY"):
		tracker.free()
		return
	tracker.add_acid_stack(0.2, 0.4)  # acid_stack_0 — expires first
	tracker.add_acid_stack(0.5, 0.4)  # acid_stack_1 — expires second
	tracker.add_acid_stack(1.0, 0.4)  # acid_stack_2 — expires last
	# Before: all 3 active
	_assert_eq_int(3, tracker.get_acid_stack_count(), "THREE_DECAY_before_3")
	# After 0.25s: stack_0 expired
	tracker._process(0.25)
	_assert_eq_int(2, tracker.get_acid_stack_count(), "THREE_DECAY_after_0_25s_count_2")
	# After another 0.3s (total 0.55s): stack_1 expired
	tracker._process(0.3)
	_assert_eq_int(1, tracker.get_acid_stack_count(), "THREE_DECAY_after_0_55s_count_1")
	# After another 0.5s (total 1.05s): stack_2 expired
	tracker._process(0.5)
	_assert_eq_int(0, tracker.get_acid_stack_count(), "THREE_DECAY_after_1_05s_count_0")
	tracker.free()


# ---------------------------------------------------------------------------
# AC-EC-9: add_acid_stack with duration=0.0 — not stored, counter not advanced
# ---------------------------------------------------------------------------

func test_zero_duration_stack_not_stored_counter_not_advanced() -> void:
	# AC-EC-9: duration=0.0 → no-op, counter not incremented
	var tracker = _make_tracker()
	if tracker == null:
		_fail_test("EC9_TRACKER", "enemy_effect_tracker.gd not loadable")
		return
	if not _check_add_acid_stack(tracker, "EC9_TRACKER") or not _check_get_acid_stack_count(tracker, "EC9_TRACKER"):
		tracker.free()
		return
	tracker.add_acid_stack(0.0, 0.4)  # should be no-op
	_assert_eq_int(0, tracker.get_acid_stack_count(), "EC9_0_stored_for_zero_dur")
	_assert_false(tracker.has_active_dot("acid_stack_0"), "EC9_key_acid_stack_0_not_created")
	# Counter must not have advanced — next valid add uses "acid_stack_0"
	tracker.add_acid_stack(2.5, 0.4)
	_assert_true(tracker.has_active_dot("acid_stack_0"), "EC9_next_valid_add_uses_stack_0")
	tracker.free()


# ---------------------------------------------------------------------------
# Counter per-instance isolation
# ---------------------------------------------------------------------------

func test_counters_are_per_instance_not_shared() -> void:
	# Two separate EnemyEffectTracker instances have independent counters
	var tracker1 = _make_tracker()
	var tracker2 = _make_tracker()
	if tracker1 == null or tracker2 == null:
		_fail_test("COUNTER_ISOLATION", "enemy_effect_tracker.gd not loadable")
		if tracker1 != null:
			tracker1.free()
		if tracker2 != null:
			tracker2.free()
		return
	if not _check_add_acid_stack(tracker1, "COUNTER_ISOLATION") or not _check_add_acid_stack(tracker2, "COUNTER_ISOLATION"):
		tracker1.free()
		tracker2.free()
		return
	tracker1.add_acid_stack(2.5, 0.4)
	tracker1.add_acid_stack(2.5, 0.4)
	# tracker2 should still start at counter 0 regardless of tracker1 state
	tracker2.add_acid_stack(2.5, 0.4)
	if tracker2.has_method("get_acid_stack_count"):
		_assert_eq_int(1, tracker2.get_acid_stack_count(), "COUNTER_ISOLATION_tracker2_count_1")
	_assert_true(tracker2.has_active_dot("acid_stack_0"), "COUNTER_ISOLATION_tracker2_starts_at_0")
	tracker1.free()
	tracker2.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== EnemyAcidStackingTests ===")

	# Fresh state
	test_ac3h_fresh_tracker_returns_0_stack_count()

	# Core stacking behavior
	test_ac3a_three_add_acid_stack_calls_gives_count_3()
	test_ac3b_stacks_stored_under_indexed_keys()
	test_ac3c_each_stack_has_correct_initial_values()

	# Decay independence
	test_ac3d_first_stack_expiry_leaves_two_remaining()
	test_ac3e_three_stacks_emit_tick_per_stack()
	test_ac3e_tick_damage_equals_dps_times_interval()

	# Counter monotonicity
	test_ac3f_counter_monotonic_after_first_stack_expires()
	test_ac3k_counter_persists_across_stop_all_effects()

	# Coexistence with base acid
	test_ac3g_base_apply_acid_coexists_without_affecting_stack_count()

	# stop_all_effects
	test_ac3j_stop_all_effects_clears_all_stacks()

	# EnemyBase delegation
	test_ac3i_apply_acid_stack_on_dead_enemy_no_effect()
	test_ac3l_enemy_base_has_apply_acid_stack_method()
	test_ac3m_enemy_base_get_acid_stack_count_delegates()

	# Decay lifecycle
	test_two_stacks_decay_independently()
	test_three_stacks_count_before_during_after_decay()

	# Edge cases
	test_zero_duration_stack_not_stored_counter_not_advanced()
	test_counters_are_per_instance_not_shared()

	print("EnemyAcidStackingTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
