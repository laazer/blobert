#
# test_fusion_attack_routing_adversarial2.gd
#
# Second adversarial test file for fusion attack dispatch routing.
# Traceability: M12-03, FAF spec (project_board/specs/fusion_attack_framework_spec.md)
#
# Gaps targeted (not covered by test_fusion_attack_routing_adversarial.gd):
#
#   GAP-1  FAF-FM-3    executor _is_active=true at call time — cooldown must NOT be set
#                      (spec: "cooldown not set on executor-blocked dispatch")
#   GAP-2  FAF-FM-6    slot clear between fused fire and second call — single-slot fallback fires
#   GAP-3  FAF-3d seq  sequential fused attacks after composite cooldown expires — second fires OK
#   GAP-4  FAF-1a id   near-identical fused IDs — correct resource fires (not wrong resource)
#   GAP-5  FAF-3a stress rapid _try_attack() calls — exactly 1 fire; no duplicate cooldown keys
#   GAP-6  FAF-3a mag  cooldown value stored equals attack_resource.cooldown exactly (no offset)
#   GAP-7  FAF-3 key   after fused fires, _mutation_cooldowns has exactly 1 new key (composite only)
#   GAP-8  FAF-2d      single-slot dispatch leaves composite key unset
#   GAP-9  FAF-NF-1    routing determinism — identical state produces identical result across runs
#

class_name FusionAttackRoutingAdversarial2Tests
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


# Build a full controller + MutationSlotManager pipeline in the scene tree.
# slot_a_id: String or "" (empty string = slot A unfilled)
# slot_b_id: String or "" (empty string = slot B unfilled)
# state: PlayerStateMachine.PlayerState integer
# cooldowns: Dictionary of String -> float to pre-populate _mutation_cooldowns
# Returns {"root", "controller", "executor", "msm"} or {} on failure.
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
# GAP-1: FAF-FM-3
# When executor _is_active=true, execute_attack() is blocked.
# Spec: cooldown must NOT be set on executor-blocked dispatch.
# Risk: _try_attack() calls execute_attack() then unconditionally writes
#       _mutation_cooldowns[cooldown_key] — no check on whether executor accepted.
# This test exposes whether the implementation satisfies FAF-FM-3.
# CHECKPOINT: Spec says cooldown NOT set; code at line 481-482 sets it unconditionally.
#             This test may RED if the implementation does not check executor return.
# ---------------------------------------------------------------------------

func test_executor_active_blocks_cooldown_write() -> void:
	# FAF-FM-3: when executor is already _is_active=true, it rejects execute_attack()
	# silently. The spec requires that _mutation_cooldowns is NOT updated in this case.
	# The test captures the pre-call cooldown dict state and compares post-call.
	var label := "FAF-ADV2-1_executor_active_blocks_cooldown_write"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_1_acid"
	var ns_b := "fadv2_1_claw"
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

	var executor = pipeline.get("executor")
	if executor == null:
		_fail_test(label, "_attack_executor not found")
		_free_pipeline(pipeline)
		return

	# Force executor into active state before calling _try_attack
	executor.set("_is_active", true)

	var fired_count := [0]
	if executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired_count[0] += 1)

	# Capture cooldown state BEFORE call
	var cd = controller.get("_mutation_cooldowns")
	var pre_composite_cd: float = 0.0
	if cd != null:
		pre_composite_cd = cd.get(composite, 0.0)

	controller.call("_try_attack")

	# Attack must NOT have fired (executor rejected it)
	_assert_eq_int(0, fired_count[0], label + "_no_attack_when_executor_active")

	# Spec FAF-FM-3: cooldown must NOT be set when executor rejects the dispatch
	var post_composite_cd: float = 0.0
	if cd != null:
		post_composite_cd = cd.get(composite, 0.0)
	# CHECKPOINT: This assertion will FAIL if _try_attack sets cooldown unconditionally
	# (current code at line 482 does exactly that). Marking spec gap.
	_assert_eq_float(
		pre_composite_cd, post_composite_cd,
		label + "_cooldown_not_set_when_executor_blocked"
	)
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-2: FAF-FM-6
# Slot clear between fused fire and second tick.
# After fused fires (composite CD active), player's slot A is cleared.
# Next _try_attack: only slot B is filled → single-slot path fires slot B's base.
# The composite cooldown key must not interfere.
# ---------------------------------------------------------------------------

func test_slot_cleared_after_fused_routes_to_single_slot() -> void:
	# FAF-FM-6: composite cd active; player clears slot A, retains slot B.
	# Single-slot path with slot B fires base_b (independent of composite key).
	var label := "FAF-ADV2-2_slot_clear_after_fused_routes_single"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_2_acid"
	var ns_b := "fadv2_2_claw"
	var composite := _composite_key(ns_a, ns_b)
	var base_b := _make_resource({"cooldown": 0.8, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, base_b)
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 3.0, "effect_type": "MELEE_SWIPE"}))

	# Start with both slots filled; fire fused attack
	var pipeline := _make_pipeline(label, PlayerStateMachine.PlayerState.IDLE, ns_a, ns_b)
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_pipeline(pipeline)
		return

	# Fire fused attack (sets composite cooldown)
	controller.call("_try_attack")

	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not accessible")
		_free_pipeline(pipeline)
		return

	# Confirm composite CD is active
	_assert_true(cd.get(composite, 0.0) > 0.0, label + "_composite_cd_active_after_fused_fire")

	# Now simulate slot A being cleared (interruption scenario)
	var msm = pipeline.get("msm")
	if msm == null or not msm.has_method("clear_slot"):
		_fail_test(label, "MutationSlotManager.clear_slot not available")
		_free_pipeline(pipeline)
		return
	msm.clear_slot(0)  # Clear slot A; slot B (ns_b) remains

	# Fire again: only slot B filled → single-slot path, cooldown key = ns_b
	var fired: Array = [null]
	var executor = pipeline.get("executor")
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")

	# Must fire slot B's base attack (not blocked by composite cd on different key)
	_assert_true(fired[0] == base_b, label + "_base_b_fires_after_slot_a_cleared")
	# Slot B individual cooldown must now be set
	_assert_true(cd.get(ns_b, 0.0) > 0.0, label + "_slot_b_cooldown_set")
	# Composite cooldown must still be unchanged (single-slot path does not touch it)
	_assert_true(cd.get(composite, 0.0) > 0.0, label + "_composite_cd_unchanged")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-3: FAF-3d sequential
# After composite cooldown expires (manually zeroed), a second fused fire works.
# Tests: the second fire re-populates the composite cooldown correctly.
# ---------------------------------------------------------------------------

func test_sequential_fused_fires_after_cooldown_expires() -> void:
	# FAF-3d sequential: fire fused, manually expire cooldown, fire again.
	# Second fire must: emit attack_started with fused resource, set composite cd.
	var label := "FAF-ADV2-3_sequential_fused_after_cd_expires"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_3_acid"
	var ns_b := "fadv2_3_claw"
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
	var last_fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fire_count[0] += 1; last_fired[0] = r)

	# First fused fire
	controller.call("_try_attack")
	_assert_eq_int(1, fire_count[0], label + "_first_fire_succeeds")

	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not accessible")
		_free_pipeline(pipeline)
		return

	# Manually expire the composite cooldown (simulate delta-time passing)
	cd[composite] = 0.0

	# Second fused fire (cooldown now expired)
	controller.call("_try_attack")
	_assert_eq_int(2, fire_count[0], label + "_second_fire_after_cd_expires")
	_assert_true(last_fired[0] == fused, label + "_second_fire_returns_correct_fused_resource")
	# Composite cd re-set to fused.cooldown
	_assert_eq_float(fused.cooldown, cd.get(composite, 0.0), label + "_composite_cd_reset_after_second_fire")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-4: FAF-1a identity
# Near-identical fused IDs: two different fused combos registered.
# Verify that each combo fires its own distinct resource (no cross-contamination).
# Risk: if composite key collision or registry lookup error, wrong resource fires.
# ---------------------------------------------------------------------------

func test_near_identical_fused_ids_fire_correct_resource() -> void:
	# Two registered fused combos: (fadv2_4a_acid, fadv2_4a_claw) and
	# (fadv2_4b_acid, fadv2_4b_claw). Each must fire only its own fused resource.
	var label := "FAF-ADV2-4_near_identical_fused_ids"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a1 := "fadv2_4a_acid"
	var ns_b1 := "fadv2_4a_claw"
	var ns_a2 := "fadv2_4b_acid"
	var ns_b2 := "fadv2_4b_claw"
	var fused_1 := _make_resource({"cooldown": 1.2, "effect_type": "MELEE_SWIPE", "damage": 11.0})
	var fused_2 := _make_resource({"cooldown": 1.3, "effect_type": "MELEE_SWIPE", "damage": 22.0})
	db.register_base_attack(ns_a1, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b1, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a2, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b2, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a1, ns_b1, fused_1)
	db.register_fused_attack(ns_a2, ns_b2, fused_2)

	# Test combo 1
	var pipeline_1 := _make_pipeline(label + "_combo1", PlayerStateMachine.PlayerState.IDLE, ns_a1, ns_b1)
	if not pipeline_1.is_empty():
		var ctrl_1 = pipeline_1["controller"]
		if ctrl_1.has_method("_try_attack"):
			var executor_1 = pipeline_1.get("executor")
			var fired_1: Array = [null]
			if executor_1 != null and executor_1.has_signal("attack_started"):
				executor_1.connect("attack_started", func(r): fired_1[0] = r)
			ctrl_1.call("_try_attack")
			_assert_true(fired_1[0] == fused_1, label + "_combo1_fires_correct_fused_resource")
			_assert_true(fired_1[0] != fused_2, label + "_combo1_does_not_fire_wrong_resource")
		_free_pipeline(pipeline_1)

	# Test combo 2
	var pipeline_2 := _make_pipeline(label + "_combo2", PlayerStateMachine.PlayerState.IDLE, ns_a2, ns_b2)
	if not pipeline_2.is_empty():
		var ctrl_2 = pipeline_2["controller"]
		if ctrl_2.has_method("_try_attack"):
			var executor_2 = pipeline_2.get("executor")
			var fired_2: Array = [null]
			if executor_2 != null and executor_2.has_signal("attack_started"):
				executor_2.connect("attack_started", func(r): fired_2[0] = r)
			ctrl_2.call("_try_attack")
			_assert_true(fired_2[0] == fused_2, label + "_combo2_fires_correct_fused_resource")
			_assert_true(fired_2[0] != fused_1, label + "_combo2_does_not_fire_wrong_resource")
		_free_pipeline(pipeline_2)


# ---------------------------------------------------------------------------
# GAP-5: Stress — 10 rapid _try_attack() calls
# Only 1 attack fires; cooldown dict has exactly 1 composite key (no duplication).
# Risk: buggy path might fire multiple times or create duplicate entries.
# ---------------------------------------------------------------------------

func test_rapid_calls_produce_single_fire_and_single_cooldown_key() -> void:
	# FAF-3a stress: 10 immediate _try_attack() calls. Exactly one fires; composite
	# cooldown key is set exactly once (second and subsequent calls are blocked by cd).
	var label := "FAF-ADV2-5_rapid_calls_single_fire"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_5_acid"
	var ns_b := "fadv2_5_claw"
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

	var executor = pipeline.get("executor")
	var fire_count := [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fire_count[0] += 1)

	# 10 rapid calls
	for _i in range(10):
		controller.call("_try_attack")

	# Only the first should have fired
	_assert_eq_int(1, fire_count[0], label + "_only_one_fire_in_10_rapid_calls")

	# The cooldown dict must have exactly the composite key (no extra individual keys)
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not accessible")
		_free_pipeline(pipeline)
		return
	_assert_true(cd.has(composite), label + "_composite_key_present_after_rapid_calls")
	_assert_eq_float(0.0, cd.get(ns_a, 0.0), label + "_no_individual_a_key_after_rapid_calls")
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_no_individual_b_key_after_rapid_calls")
	# The composite key value should be fused.cooldown (not doubled or accumulated)
	_assert_eq_float(fused.cooldown, cd.get(composite, 0.0), label + "_cooldown_value_correct_after_rapid_calls")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-6: Cooldown value magnitude
# After fused fires, _mutation_cooldowns[composite] equals resource.cooldown exactly.
# No scaling, no additive offset (FAF-3f).
# Tests with an unusual cooldown value to catch off-by-one or multiplication bugs.
# ---------------------------------------------------------------------------

func test_large_cooldown_stored_exactly() -> void:
	# FAF-3f: cooldown stored is attack_resource.cooldown exactly.
	# Use an unusual value (e.g. 99.9) to detect any multiplication/offset.
	var label := "FAF-ADV2-6_large_cooldown_stored_exactly"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_6_acid"
	var ns_b := "fadv2_6_claw"
	var composite := _composite_key(ns_a, ns_b)
	var large_cd := 99.9
	var fused := _make_resource({"cooldown": large_cd, "effect_type": "MELEE_SWIPE"})
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
	_assert_eq_float(large_cd, cd.get(composite, 0.0), label + "_large_cooldown_stored_exactly")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-7: Cooldown key count after fused fire
# After fused fires for (ns_a, ns_b) with a fresh (empty) cooldown dict,
# exactly ONE key is added: the composite key. No spurious individual keys.
# ---------------------------------------------------------------------------

func test_fused_fire_adds_exactly_one_cooldown_key() -> void:
	# FAF-3a/3b/3c extended: start with empty cooldown dict, fire fused once.
	# Exactly 1 key must be present: the composite. a_id and b_id must be absent.
	var label := "FAF-ADV2-7_fused_adds_exactly_one_cd_key"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_7_acid"
	var ns_b := "fadv2_7_claw"
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

	# Capture key count before
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not accessible")
		_free_pipeline(pipeline)
		return
	var pre_key_count: int = cd.size()

	controller.call("_try_attack")

	var post_key_count: int = cd.size()
	# Must have added exactly 1 new key
	_assert_eq_int(pre_key_count + 1, post_key_count, label + "_exactly_one_new_key_added")
	# That key must be the composite key
	_assert_true(cd.has(composite), label + "_new_key_is_composite")
	# Individual keys must remain absent
	_assert_false(cd.has(ns_a), label + "_individual_a_key_absent")
	_assert_false(cd.has(ns_b), label + "_individual_b_key_absent")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-8: FAF-2d
# Single-slot dispatch (only slot A filled) does NOT write a composite key.
# The composite key remains absent from _mutation_cooldowns after base fires.
# ---------------------------------------------------------------------------

func test_single_slot_dispatch_leaves_composite_key_unset() -> void:
	# FAF-2d: single-slot base fire must not create a composite key in _mutation_cooldowns.
	var label := "FAF-ADV2-8_single_slot_no_composite_key"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_8_acid"
	var ns_b := "fadv2_8_claw"
	var composite := _composite_key(ns_a, ns_b)
	var base_a := _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	# Register ns_b and a fused combo too (to ensure the combo lookup path is exercised
	# and does NOT write composite key in the single-slot scenario)
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, _make_resource({"cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))

	# Only slot A filled
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
	# Base A fires
	_assert_true(fired[0] == base_a, label + "_base_a_fires_single_slot")
	# Composite key must NOT be present
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_false(cd.has(composite), label + "_composite_key_absent_in_single_slot")
	_free_pipeline(pipeline)


# ---------------------------------------------------------------------------
# GAP-9: FAF-NF-1 determinism
# Identical slot/state/cooldown setup produces identical routing outcome on 3
# separate pipeline instances. Tests that no global mutable side-effect influences
# routing across calls.
# ---------------------------------------------------------------------------

func test_routing_is_deterministic_across_identical_pipelines() -> void:
	# FAF-NF-1: Create 3 independent fresh pipelines with identical state.
	# Each must produce the same fired resource and same cooldown key.
	var label := "FAF-ADV2-9_routing_deterministic"
	var db := _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	var ns_a := "fadv2_9_acid"
	var ns_b := "fadv2_9_claw"
	var composite := _composite_key(ns_a, ns_b)
	var fused := _make_resource({"cooldown": 1.8, "effect_type": "MELEE_SWIPE", "damage": 7.0})
	db.register_base_attack(ns_a, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_fused_attack(ns_a, ns_b, fused)

	var results: Array = []
	for i in range(3):
		var pipeline := _make_pipeline(
			label + "_run_" + str(i),
			PlayerStateMachine.PlayerState.IDLE,
			ns_a, ns_b
		)
		if pipeline.is_empty():
			continue
		var controller = pipeline["controller"]
		if not controller.has_method("_try_attack"):
			_fail_test(label, "_try_attack not found in run " + str(i))
			_free_pipeline(pipeline)
			continue
		var executor = pipeline.get("executor")
		var fired: Array = [null]
		if executor != null and executor.has_signal("attack_started"):
			executor.connect("attack_started", func(r): fired[0] = r)
		controller.call("_try_attack")
		var cd = controller.get("_mutation_cooldowns")
		results.append({
			"fired": fired[0],
			"composite_cd": cd.get(composite, -1.0) if cd else -1.0
		})
		_free_pipeline(pipeline)

	# All 3 runs must produce the same results
	if results.size() == 3:
		_assert_true(
			results[0]["fired"] == fused and results[1]["fired"] == fused and results[2]["fired"] == fused,
			label + "_all_three_runs_fire_same_resource"
		)
		_assert_true(
			absf(results[0]["composite_cd"] - fused.cooldown) < 0.0001
			and absf(results[1]["composite_cd"] - fused.cooldown) < 0.0001
			and absf(results[2]["composite_cd"] - fused.cooldown) < 0.0001,
			label + "_all_three_runs_set_same_cooldown_value"
		)
	else:
		_fail_test(label, "Not all 3 pipeline runs completed (got " + str(results.size()) + ")")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusionAttackRoutingAdversarial2Tests ===")

	test_executor_active_blocks_cooldown_write()
	test_slot_cleared_after_fused_routes_to_single_slot()
	test_sequential_fused_fires_after_cooldown_expires()
	test_near_identical_fused_ids_fire_correct_resource()
	test_rapid_calls_produce_single_fire_and_single_cooldown_key()
	test_large_cooldown_stored_exactly()
	test_fused_fire_adds_exactly_one_cooldown_key()
	test_single_slot_dispatch_leaves_composite_key_unset()
	test_routing_is_deterministic_across_identical_pipelines()

	print(
		"FusionAttackRoutingAdversarial2Tests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
