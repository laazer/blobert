#
# test_fusion_attack_routing.gd
#
# Behavioral regression tests for the fusion attack dispatch routing layer.
# Traceability: M12-03, FAF spec (project_board/specs/fusion_attack_framework_spec.md)
#
# Coverage: 14 behavioral tests.
#   FAF-1a/1b  — fused route fires when both slots filled and combo registered
#   FAF-1d/2a  — base route fires when only slot A filled
#   FAF-1e/2b  — base route fires when only slot B filled
#   FAF-1f     — no attack when neither slot filled
#   FAF-3a/3b/3c — fused cooldown key is composite; individual keys unset
#   FAF-3d     — composite cooldown blocks repeat fused fire
#   FAF-4c/4d  — no attack during speed-boost window (is_fusion_active true, slots empty)
#   FAF-5a     — attack blocked in ABSORB state
#   FAF-5b     — attack blocked in MUTATE state
#   FAF-5c     — attack blocked in HURT state
#   FAF-5d     — attack blocked in DEAD state
#   FAF-5e     — attack permitted in IDLE state
#   FAF-2c/FADI-EC-3 — composite cooldown does not block single-slot base attack on independent key
#   FAF-1g/FADI-5a/5c — fallback to slot A base when no fused combo registered
#

class_name FusionAttackRoutingTests
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


# Build a full controller + MutationSlotManager pipeline in the scene tree.
# slot_a_id: String or "" (empty string = slot A unfilled)
# slot_b_id: String or "" (empty string = slot B unfilled)
# state: PlayerStateMachine.PlayerState integer
# cooldowns: Dictionary of String -> float to pre-populate _mutation_cooldowns
# Returns {"root", "controller", "executor"} or {} on failure.
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
	return {"root": scene_root, "controller": controller, "executor": executor}


func _free_pipeline(pipeline: Dictionary) -> void:
	var root = pipeline.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


func _composite_key(a: String, b: String) -> String:
	var pair: Array = [a, b]
	pair.sort()
	return "%s_%s" % [pair[0], pair[1]]


# ---------------------------------------------------------------------------
# Test 1: FAF-1a, FAF-1b
# Both slots filled, combo registered → fused resource fires via attack_started
# ---------------------------------------------------------------------------

func test_fused_route_fires_when_both_slots_filled() -> void:
	# FAF-1a, FAF-1b: both slots filled, fused registered → fused resource fires
	var label := "FAF-1_fused_route_fires_both_slots"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "frf_acid"
	var ns_b := "frf_claw"
	var base_a := _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	var base_b := _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	var fused := _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE", "damage": 10.0})
	db.register_base_attack(ns_a, base_a)
	db.register_base_attack(ns_b, base_b)
	db.register_fused_attack(ns_a, ns_b, fused)

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, ns_b)
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
	_assert_true(fired[0] == fused, label + "_fused_resource_fired")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 2: FAF-1d, FAF-2a
# Only slot A filled → slot A's base attack fires (no fused path entered)
# ---------------------------------------------------------------------------

func test_base_route_fires_when_only_slot_a_filled() -> void:
	# FAF-1d, FAF-2a: slot A filled, slot B unfilled → base A fires, not fused
	var label := "FAF-2_base_route_only_slot_a"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "far_slota_acid"
	var base_a := _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)

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
	_assert_true(fired[0] == base_a, label + "_base_a_fires")
	# Verify cooldown key is slot A's mutation id (not composite)
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_true(cd.get(ns_a, 0.0) > 0.0, label + "_slot_a_cooldown_set")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 3: FAF-1e, FAF-2b
# Only slot B filled → slot B's base attack fires
# ---------------------------------------------------------------------------

func test_base_route_fires_when_only_slot_b_filled() -> void:
	# FAF-1e, FAF-2b: slot A unfilled, slot B filled → slot B's base fires.
	# MutationSlotManager has no fill_at_index; we call get_slot(1).set_active_mutation_id()
	# directly (MutationSlot API) to place a mutation in slot 1 only.
	var label := "FAF-3_base_route_only_slot_b"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_b := "far_slotb_claw"
	var base_b := _make_resource({"cooldown": 0.8, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_b, base_b)

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
	if psm == null:
		_fail_test(label, "_player_state_machine not found")
		scene_root.free()
		return
	psm._state = PlayerStateMachine.PlayerState.IDLE

	# Build MSM: leave slot 0 empty, fill slot 1 with ns_b via direct API
	var msm := MutationSlotManager.new()
	var slot_1 = msm.get_slot(1)
	if slot_1 == null or not slot_1.has_method("set_active_mutation_id"):
		_fail_test(label, "MutationSlot slot 1 missing set_active_mutation_id")
		scene_root.free()
		return
	slot_1.set_active_mutation_id(ns_b)
	controller.set("_mutation_slot", msm)

	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		scene_root.free()
		return

	var executor = controller.get("_attack_executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)

	controller.call("_try_attack")
	_assert_true(fired[0] == base_b, label + "_base_b_fires")
	# Cooldown key must be ns_b (slot B's id), not composite
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_true(cd.get(ns_b, 0.0) > 0.0, label + "_slot_b_cooldown_set")
	scene_root.free()


# ---------------------------------------------------------------------------
# Test 4: FAF-1f
# Neither slot filled → no attack fires
# ---------------------------------------------------------------------------

func test_no_attack_when_no_slots_filled() -> void:
	# FAF-1f: neither slot filled → _try_attack returns early, no attack
	var label := "FAF-4_no_attack_no_slots"
	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, "", "")
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
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_no_attack_fired")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 5: FAF-3a, FAF-3b, FAF-3c
# After fused fires: composite key set, individual slot keys NOT set
# ---------------------------------------------------------------------------

func test_fused_cooldown_key_is_composite_not_individual() -> void:
	# FAF-3a/3b/3c: fused fire → composite key set; a_id and b_id keys absent
	var label := "FAF-5_fused_cd_composite_only"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fcd_acid"
	var ns_b := "fcd_claw"
	var composite := _composite_key(ns_a, ns_b)
	var fused := _make_resource({"cooldown": 2.0, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, fused)

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, ns_b)
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not accessible")
		_free_pipeline(pipeline)
		return
	_assert_true(cd.get(composite, 0.0) == fused.cooldown, label + "_composite_key_set_to_resource_cooldown")
	_assert_eq_float(0.0, cd.get(ns_a, 0.0), label + "_slot_a_individual_key_unset")
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_individual_key_unset")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 6: FAF-3d
# While composite cooldown > 0, second _try_attack call fires nothing
# ---------------------------------------------------------------------------

func test_fused_cooldown_blocks_repeat_fire() -> void:
	# FAF-3d: composite cooldown active → second call to _try_attack fires nothing
	var label := "FAF-6_fused_cd_blocks_repeat"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fcb_acid"
	var ns_b := "fcb_claw"
	var composite := _composite_key(ns_a, ns_b)
	var fused := _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, fused)

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, ns_b)
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fire_count := [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fire_count[0] += 1)

	# First call: should fire
	controller.call("_try_attack")
	_assert_eq_int(1, fire_count[0], label + "_first_call_fires")

	# Verify composite cooldown is set
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not accessible")
		_free_pipeline(pipeline)
		return
	_assert_true(cd.get(composite, 0.0) > 0.0, label + "_composite_cd_set_after_first_fire")

	# Second call while cooldown active: should NOT fire
	controller.call("_try_attack")
	_assert_eq_int(1, fire_count[0], label + "_second_call_blocked_by_cd")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 7: FAF-4c, FAF-4d
# is_fusion_active() == true (speed-boost window, both slots empty) → no attack
# ---------------------------------------------------------------------------

func test_no_attack_during_speed_boost_window() -> void:
	# FAF-4c/4d: _fusion_active=true, both slots empty → _try_attack fires nothing.
	# Validates temporal separation: speed-boost window != "slots are filled".
	var label := "FAF-7_no_attack_speed_boost_window"
	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, "", "")
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	# Set _fusion_active=true directly to simulate post-resolve_fusion() state
	controller.set("_fusion_active", true)
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return
	# Verify is_fusion_active() returns true (speed-boost timer is running)
	if controller.has_method("is_fusion_active"):
		_assert_true(controller.call("is_fusion_active"), label + "_is_fusion_active_returns_true")
	var executor = pipeline.get("executor")
	var fired := [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired[0] = true)
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_no_attack_fires_in_speed_boost_window")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 8: FAF-5a
# Both slots filled, fused registered, state=ABSORB → no attack
# ---------------------------------------------------------------------------

func test_attack_blocked_in_absorb_state() -> void:
	# FAF-5a: ABSORB state blocks fused attack dispatch
	var label := "FAF-8_blocked_absorb"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "abs_acid"
	var ns_b := "abs_claw"
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.ABSORB, ns_a, ns_b)
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
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_attack_blocked_in_absorb")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 9: FAF-5b
# Both slots filled, fused registered, state=MUTATE → no attack
# ---------------------------------------------------------------------------

func test_attack_blocked_in_mutate_state() -> void:
	# FAF-5b: MUTATE state blocks fused attack dispatch
	var label := "FAF-9_blocked_mutate"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "mut_acid"
	var ns_b := "mut_claw"
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.MUTATE, ns_a, ns_b)
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
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_attack_blocked_in_mutate")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 10: FAF-5c
# Both slots filled, fused registered, state=HURT → no attack
# ---------------------------------------------------------------------------

func test_attack_blocked_in_hurt_state() -> void:
	# FAF-5c: HURT state blocks fused attack dispatch
	var label := "FAF-10_blocked_hurt"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "hrt_acid"
	var ns_b := "hrt_claw"
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.HURT, ns_a, ns_b)
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
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_attack_blocked_in_hurt")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 11: FAF-5d
# Both slots filled, fused registered, state=DEAD → no attack
# ---------------------------------------------------------------------------

func test_attack_blocked_in_dead_state() -> void:
	# FAF-5d: DEAD state blocks fused attack dispatch
	var label := "FAF-11_blocked_dead"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "ded_acid"
	var ns_b := "ded_claw"
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.DEAD, ns_a, ns_b)
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
	controller.call("_try_attack")
	_assert_false(fired[0], label + "_attack_blocked_in_dead")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 12: FAF-5e
# Both slots filled, fused registered, state=IDLE → fused attack fires normally
# ---------------------------------------------------------------------------

func test_attack_permitted_in_idle_state() -> void:
	# FAF-5e: IDLE state permits fused attack dispatch
	var label := "FAF-12_permitted_idle"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "idl_acid"
	var ns_b := "idl_claw"
	var fused := _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE", "damage": 8.0})
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, fused)

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, ns_b)
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
	_assert_true(fired[0] == fused, label + "_fused_fires_in_idle")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 13: FAF-2c, FADI-EC-3
# Composite cooldown active; player enters single-slot state → base fires freely
# (individual slot cooldown keys are independent of composite key)
# ---------------------------------------------------------------------------

func test_base_route_not_disrupted_by_fused_cooldown_on_different_key() -> void:
	# FAF-2c, FADI-EC-3: composite key on cooldown; single-slot base fires on own key
	var label := "FAF-13_base_independent_of_fused_cd"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "bcd_acid"
	var ns_b := "bcd_claw"
	var composite := _composite_key(ns_a, ns_b)
	var base_a := _make_resource({"cooldown": 0.8, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 3.0, "effect_type": "MELEE_SWIPE"}))

	# Pre-populate composite cooldown (simulate: fused just fired)
	var pipeline := _make_pipeline(
		label, PlayerStateMachine.PlayerState.IDLE, ns_a, "",
		{composite: 3.0}
	)
	if pipeline.is_empty():
		return
	# Pipeline has only slot A filled (single-slot state), composite cd active
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
	# Slot A filled only → single-slot path; cooldown key is ns_a (not composite)
	# composite cd is irrelevant to this path → base_a should fire
	_assert_true(fired[0] == base_a, label + "_base_a_fires_despite_composite_cd")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Test 14: FAF-1g, FADI-5a, FADI-5c
# Both slots filled, no fused combo registered → falls back to slot A's base attack
# ---------------------------------------------------------------------------

func test_fallback_to_slot_a_when_no_fused_registered() -> void:
	# FAF-1g, FADI-5a/5c: both slots filled, no fused registered → slot A base fires;
	# slot B's individual cooldown remains unset
	var label := "FAF-14_fallback_slot_a_no_fused"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fb_acid"
	var ns_b := "fb_no_fused_partner"
	var base_a := _make_resource({"cooldown": 0.8, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	# ns_b has no fused combo with ns_a registered → get_fused_attack returns null

	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, ns_b)
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
	_assert_true(fired[0] == base_a, label + "_slot_a_base_fires_on_fallback")
	# Slot B's individual cooldown must not be set
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_cooldown_unset_on_fallback")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusionAttackRoutingTests ===")

	test_fused_route_fires_when_both_slots_filled()
	test_base_route_fires_when_only_slot_a_filled()
	test_base_route_fires_when_only_slot_b_filled()
	test_no_attack_when_no_slots_filled()
	test_fused_cooldown_key_is_composite_not_individual()
	test_fused_cooldown_blocks_repeat_fire()
	test_no_attack_during_speed_boost_window()
	test_attack_blocked_in_absorb_state()
	test_attack_blocked_in_mutate_state()
	test_attack_blocked_in_hurt_state()
	test_attack_blocked_in_dead_state()
	test_attack_permitted_in_idle_state()
	test_base_route_not_disrupted_by_fused_cooldown_on_different_key()
	test_fallback_to_slot_a_when_no_fused_registered()

	print(
		"FusionAttackRoutingTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
