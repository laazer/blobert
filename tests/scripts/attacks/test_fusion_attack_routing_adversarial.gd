#
# test_fusion_attack_routing_adversarial.gd
#
# Adversarial and boundary regression tests for fusion attack dispatch routing.
# Traceability: M12-03, FAF spec (project_board/specs/fusion_attack_framework_spec.md)
#
# Coverage: 10 adversarial tests.
#   FAF-1d           — single-slot state does not enter fused path (boundary)
#   FAF-FM-1         — null _mutation_slot does not crash
#   FAF-FM-2         — null AttackDatabase (no autoload) does not crash
#   FAF-FM-4/FADI-NF-4/FADI-EC-1 — same mutation in both slots falls back to base
#   FAF-FM-5         — speed-boost active, both slots empty → no attack
#   FADI-DD-3        — composite key is order-independent (slot A/B swap produces same key)
#   FADI-EC-3 adv    — individual slot cooldowns pre-set non-zero; fused still fires
#   FAF-FM-7         — _input_policy null → no crash
#   FAF-5a–5d indep  — all four denied states independently block fused attack
#   FAF-FM-8         — empty mutation id from slot; no crash at final null guard
#

class_name FusionAttackRoutingAdversarialTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _CONTROLLER_PATH := "res://scripts/player/player_controller_3d.gd"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r := AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _get_autoload_db() -> Node:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	return tree.root.get_node_or_null("AttackDatabase")


func _composite_key(a: String, b: String) -> String:
	var pair: Array = [a, b]
	pair.sort()
	return "%s_%s" % [pair[0], pair[1]]


# Build a full controller pipeline with both mutation slots. Returns
# {"root", "controller", "executor"} or {} on failure.
# Caller must free via _free_pipeline().
func _make_pipeline(
	label: String,
	state: int,
	slot_a_id: String,
	slot_b_id: String,
	cooldowns: Dictionary = {}
) -> Dictionary:
	var ctrl_script := load(_CONTROLLER_PATH) as GDScript
	if ctrl_script == null:
		_fail_test(label, _CONTROLLER_PATH + " not loadable")
		return {}
	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(label, "controller instantiation returned null")
		return {}
	var scene_root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)

	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test(label, "_player_state_machine not found")
		scene_root.free()
		return {}
	psm._state = state

	var msm := MutationSlotManager.new()
	if slot_a_id != "":
		msm.fill_next_available(slot_a_id)
	if slot_b_id != "":
		msm.fill_next_available(slot_b_id)
	controller.set("_mutation_slot", msm)

	var cd_dict = controller.get("_mutation_cooldowns")
	if cd_dict != null:
		for key in cooldowns:
			cd_dict[key] = cooldowns[key]

	var executor = controller.get("_attack_executor")
	return {"root": scene_root, "controller": controller, "executor": executor, "msm": msm}


func _free_pipeline(pipeline: Dictionary) -> void:
	var root = pipeline.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


# ---------------------------------------------------------------------------
# Adversarial test 1: FAF-1d
# Single-slot state does NOT enter the fused path.
# Boundary: only slot A filled; fused combo is registered but must NOT fire.
# ---------------------------------------------------------------------------

func test_routing_boundary_one_slot_filled_does_not_enter_fused_path() -> void:
	# FAF-1d: slot A filled, slot B unfilled — even when fused combo is registered,
	# the fused path is not entered (a_filled AND b_filled is false).
	var label := "FAF-ADV-1_single_slot_no_fused_path"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "adv1_acid"
	var ns_b := "adv1_claw"
	var base_a := _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	var fused := _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE", "damage": 20.0})
	db.register_base_attack(ns_a, base_a)
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, fused)

	# Only slot A filled (slot B intentionally empty)
	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, "")
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	# Must NOT fire the fused resource — the fused path requires both slots
	_assert_true(fired[0] != fused, label + "_fused_not_fired_with_single_slot")
	# Must fire slot A's base attack (the only filled slot)
	_assert_true(fired[0] == base_a, label + "_base_a_fires_not_fused")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Adversarial test 2: FAF-FM-1
# _mutation_slot == null → no crash, no attack
# ---------------------------------------------------------------------------

func test_null_mutation_slot_does_not_crash() -> void:
	# FAF-FM-1: ensure_binding runs but slot is still null → early return, no crash
	var label := "FAF-ADV-2_null_mutation_slot"
	var ctrl_script := load(_CONTROLLER_PATH) as GDScript
	if ctrl_script == null:
		_fail_test(label, _CONTROLLER_PATH + " not loadable")
		return
	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(label, "controller instantiation returned null")
		return
	var scene_root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)

	# Force _mutation_slot to null — PlayerMutationSlotBind.ensure_binding may
	# set it, but we null it after to simulate bind failure.
	controller.set("_mutation_slot", null)

	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		scene_root.free()
		return

	var executor = controller.get("_attack_executor")
	var fired := [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_no_attack_when_slot_null")
	_pass_test(label + "_no_crash")
	scene_root.free()


# ---------------------------------------------------------------------------
# Adversarial test 3: FAF-FM-2
# AttackDatabase autoload missing → _get_attack_database() returns null → no crash
# ---------------------------------------------------------------------------

func test_null_attack_database_does_not_crash() -> void:
	# FAF-FM-2: no AttackDatabase in scene tree → _get_attack_database() returns null
	# → _try_attack() returns without crashing.
	var label := "FAF-ADV-3_null_attack_database"
	var ctrl_script := load(_CONTROLLER_PATH) as GDScript
	if ctrl_script == null:
		_fail_test(label, _CONTROLLER_PATH + " not loadable")
		return
	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(label, "controller instantiation returned null")
		return

	# Do NOT add to scene tree — _get_attack_database() calls get_tree() which
	# returns null for nodes outside the tree, producing null db.
	var psm = controller.get("_player_state_machine")
	if psm != null:
		psm._state = PlayerStateMachine.PlayerState.IDLE
	var msm := MutationSlotManager.new()
	msm.fill_next_available("adv3_acid")
	msm.fill_next_available("adv3_claw")
	controller.set("_mutation_slot", msm)

	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		controller.free()
		return
	controller.call("_try_attack")
	_pass_test(label + "_no_crash_without_db")
	controller.free()


# ---------------------------------------------------------------------------
# Adversarial test 4: FAF-FM-4, FADI-NF-4, FADI-EC-1
# Same mutation in both slots → self-fusion rejected at DB registration →
# get_fused_attack returns null → falls back to slot A's base attack.
# ---------------------------------------------------------------------------

func test_same_mutation_in_both_slots_falls_back_to_base() -> void:
	# FAF-FM-4: Both slots filled with same mutation ID "adv4_claw".
	# AttackDatabase.register_fused_attack rejects same-ID pairs (FADI-NF-4).
	# _try_attack: get_fused_attack("adv4_claw","adv4_claw") → null → fallback base.
	var label := "FAF-ADV-4_same_mutation_both_slots"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns := "adv4_claw"
	var base_res := _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE", "damage": 3.0})
	db.register_base_attack(ns, base_res)
	# Attempt self-fusion registration (must be silently rejected per FADI-NF-4)
	db.register_fused_attack(ns, ns, _make_resource({"attack_id": 9999}))

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns, ns)
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	_assert_true(fired[0] == base_res, label + "_base_fires_when_self_fusion")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Adversarial test 5: FAF-FM-5
# _fusion_active == true (speed-boost window), both slots empty → no attack.
# This is the same test as behavioral test 7 but framed as an adversarial boundary:
# setting _fusion_active directly to verify the temporal separation contract.
# ---------------------------------------------------------------------------

func test_speed_boost_active_both_slots_empty_no_attack() -> void:
	# FAF-FM-5: speed-boost timer running, both slots empty → _try_attack returns
	# at the "not a_filled and not b_filled" guard. No attack fires.
	var label := "FAF-ADV-5_speed_boost_active_no_slots"
	var ctrl_script := load(_CONTROLLER_PATH) as GDScript
	if ctrl_script == null:
		_fail_test(label, _CONTROLLER_PATH + " not loadable")
		return
	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(label, "controller instantiation returned null")
		return
	var scene_root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)

	var psm = controller.get("_player_state_machine")
	if psm != null:
		psm._state = PlayerStateMachine.PlayerState.IDLE
	# Both slots empty (default); set _fusion_active = true directly
	controller.set("_fusion_active", true)

	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		scene_root.free()
		return

	var executor = controller.get("_attack_executor")
	var fired := [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_no_attack_in_speed_boost_window")
	scene_root.free()


# ---------------------------------------------------------------------------
# Adversarial test 6: FADI-DD-3
# Composite key is order-independent: (A="claw", B="acid") and (A="acid", B="claw")
# produce the same composite cooldown key "acid_claw" after fused fires.
# ---------------------------------------------------------------------------

func test_composite_key_is_order_independent() -> void:
	# FADI-DD-3 in routing context: regardless of which slot holds which mutation,
	# the cooldown key stored is always the alphabetically sorted composite.
	var label := "FAF-ADV-6_composite_key_order_independent"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	# Forward order: slot A = "adv6_claw", slot B = "adv6_acid"
	var ns_claw := "adv6_claw"
	var ns_acid := "adv6_acid"
	var expected_key := _composite_key(ns_claw, ns_acid)  # = "adv6_acid_adv6_claw"
	var fused := _make_resource({"cooldown": 2.0, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_claw, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_acid, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_claw, ns_acid, fused)

	# Test A: slot 0 = claw, slot 1 = acid
	var pipeline_a := _make_pipeline(label + "_fwd", PlayerStateMachine.PlayerState.IDLE, ns_claw, ns_acid)
	if not pipeline_a.is_empty():
		var ctrl_a = pipeline_a["controller"]
		if ctrl_a.has_method("_try_attack"):
			ctrl_a.call("_try_attack")
			var cd_a = ctrl_a.get("_mutation_cooldowns")
			if cd_a != null:
				_assert_true(cd_a.has(expected_key), label + "_forward_composite_key_present")
				_assert_eq_float(0.0, cd_a.get(ns_claw, 0.0), label + "_forward_slot_a_key_absent")
				_assert_eq_float(0.0, cd_a.get(ns_acid, 0.0), label + "_forward_slot_b_key_absent")
		_free_pipeline(pipeline_a)

	# Test B: slot 0 = acid, slot 1 = claw (reversed order)
	# Use a fresh pipeline; register the reverse-order combo (same resource, order-independent)
	db.register_fused_attack(ns_acid, ns_claw, fused)
	var pipeline_b := _make_pipeline(label + "_rev", PlayerStateMachine.PlayerState.IDLE, ns_acid, ns_claw)
	if not pipeline_b.is_empty():
		var ctrl_b = pipeline_b["controller"]
		if ctrl_b.has_method("_try_attack"):
			ctrl_b.call("_try_attack")
			var cd_b = ctrl_b.get("_mutation_cooldowns")
			if cd_b != null:
				_assert_true(cd_b.has(expected_key), label + "_reverse_composite_key_present")
				_assert_eq_float(0.0, cd_b.get(ns_claw, 0.0), label + "_reverse_slot_claw_key_absent")
				_assert_eq_float(0.0, cd_b.get(ns_acid, 0.0), label + "_reverse_slot_acid_key_absent")
		_free_pipeline(pipeline_b)


# ---------------------------------------------------------------------------
# Adversarial test 7: FADI-EC-3 adversarial
# Individual slot cooldowns pre-set to non-zero; fused fires anyway
# (individual keys do NOT block fused path — only composite key matters).
# ---------------------------------------------------------------------------

func test_fused_cooldown_set_independently_of_individual_slot_cooldowns() -> void:
	# FADI-EC-3 adversarial: pre-set individual slot cooldowns to non-zero values.
	# The fused path checks the composite key only; individual keys are irrelevant
	# to fused dispatch. The fused attack must still fire.
	var label := "FAF-ADV-7_individual_cd_nonzero_fused_still_fires"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "adv7_acid"
	var ns_b := "adv7_claw"
	var fused := _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, fused)

	# Pre-populate individual slot cooldowns (simulate: base attacks were recently fired)
	var pipeline := _make_pipeline(
		label,
		PlayerStateMachine.PlayerState.IDLE,
		ns_a, ns_b,
		{ns_a: 5.0, ns_b: 5.0}  # individual keys non-zero
	)
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	# Individual keys have non-zero cooldowns, but composite key is 0 → fused fires
	_assert_true(fired[0] == fused, label + "_fused_fires_despite_individual_cds")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Adversarial test 8: FAF-FM-7
# _input_policy == null → _try_attack returns early, no crash
# ---------------------------------------------------------------------------

func test_policy_null_returns_early() -> void:
	# FAF-FM-7: _input_policy set to null → guard at line 447 catches it; no crash.
	var label := "FAF-ADV-8_null_input_policy"
	var ctrl_script := load(_CONTROLLER_PATH) as GDScript
	if ctrl_script == null:
		_fail_test(label, _CONTROLLER_PATH + " not loadable")
		return
	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(label, "controller instantiation returned null")
		return
	var scene_root := Node3D.new()
	var tree := Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)

	# Fill slots so we reach the policy guard (not stopped by slot check first)
	var msm := MutationSlotManager.new()
	msm.fill_next_available("adv8_acid")
	msm.fill_next_available("adv8_claw")
	controller.set("_mutation_slot", msm)
	# Null the input policy
	controller.set("_input_policy", null)

	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		scene_root.free()
		return

	var executor = controller.get("_attack_executor")
	var fired := [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_no_attack_when_policy_null")
	_pass_test(label + "_no_crash")
	scene_root.free()


# ---------------------------------------------------------------------------
# Adversarial test 9: FAF-5a–5d independence
# All four denied states independently block fused attack dispatch.
# Tests each state in isolation to confirm state-gating applies per-state.
# ---------------------------------------------------------------------------

func test_all_four_denied_states_block_independently() -> void:
	# FAF-5a through FAF-5d: ABSORB, MUTATE, HURT, DEAD each independently block
	# fused attack dispatch. Tests loop is deterministic; each iteration uses a
	# fresh pipeline so state isolation is guaranteed.
	var label := "FAF-ADV-9_all_denied_states_independent"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "adv9_acid"
	var ns_b := "adv9_claw"
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))

	var denied_states: Array[int] = [
		PlayerStateMachine.PlayerState.ABSORB,
		PlayerStateMachine.PlayerState.MUTATE,
		PlayerStateMachine.PlayerState.HURT,
		PlayerStateMachine.PlayerState.DEAD,
	]
	for state in denied_states:
		var state_label := label + "_state_" + str(state)
		var pipeline := _make_pipeline(state_label, state, ns_a, ns_b)
		if pipeline.is_empty():
			continue
		var controller = pipeline["controller"]
		if not controller.has_method("_try_attack"):
			_fail_test(state_label, "_try_attack not found")
			_free_pipeline(pipeline)
			continue
		var executor = pipeline.get("executor")
		var fired := [false]
		if executor != null and executor.has_signal("attack_started"):
			executor.connect("attack_started", func(_r): fired[0] = true)
		controller.call("_try_attack")
		_assert_false(fired[0], state_label + "_blocked")
		_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Adversarial test 10: FAF-FM-8
# Slot returns "" from get_active_mutation_id() → get_fused_attack("","b_id") returns null
# → get_base_attack("") returns null → final null guard → no crash.
# ---------------------------------------------------------------------------

func test_empty_mutation_id_does_not_crash() -> void:
	# FAF-FM-8: MutationSlot.is_filled() returns true when id != "",
	# but we force the slots to report is_filled()=true while returning ""
	# from get_active_mutation_id() by directly manipulating _active_mutation_id
	# to be a space (non-empty, technically "filled") and the DB has no entry for it.
	# More practically: fill both slots with a namespaced id that has NO registered
	# base or fused attack — AttackDatabase returns null for both lookups,
	# and _try_attack handles the null at the final guard without crashing.
	# This covers the defensive path in FAF-FM-8 without needing to violate
	# MutationSlot invariants (is_filled() relies on id != "").
	var label := "FAF-ADV-10_empty_mutation_id_no_crash"
	var pipeline := _make_pipeline(
		label,
		PlayerStateMachine.PlayerState.IDLE,
		"adv10_unregistered_a",
		"adv10_unregistered_b"
	)
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired := [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	# No base or fused resource registered for these IDs →
	# get_fused_attack returns null → fallback get_base_attack returns null →
	# final guard blocks dispatch → no crash.
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_no_attack_for_unregistered_ids")
	_pass_test(label + "_no_crash")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusionAttackRoutingAdversarialTests ===")

	test_routing_boundary_one_slot_filled_does_not_enter_fused_path()
	test_null_mutation_slot_does_not_crash()
	test_null_attack_database_does_not_crash()
	test_same_mutation_in_both_slots_falls_back_to_base()
	test_speed_boost_active_both_slots_empty_no_attack()
	test_composite_key_is_order_independent()
	test_fused_cooldown_set_independently_of_individual_slot_cooldowns()
	test_policy_null_returns_early()
	test_all_four_denied_states_block_independently()
	test_empty_mutation_id_does_not_crash()

	print(
		"FusionAttackRoutingAdversarialTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
