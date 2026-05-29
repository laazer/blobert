#
# test_fused_combo_matrix_adversarial.gd
#
# Adversarial tests for the fused attack dispatch system.
# Spec: project_board/specs/fused_attack_database_integration_spec.md
# Ticket: M12-01
#   project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md
#
# Requirements targeted:
#   FADI-EC-1..EC-7, FADI-3b/3c/3d, FADI-5b/5c, FADI-7a, FADI-NF-1/NF-4/NF-5,
#   FADI-1c: last-write-wins overwrite, FADI-DD-1/DD-2
#   Additional: order stress, cooldown decay, combinatorial invalid sequence.
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _CONTROLLER_PATH := "res://scripts/player/player_controller_3d.gd"
const _DB_PATH := "res://scripts/attacks/attack_database.gd"


func _make_resource(overrides: Dictionary = {}) -> Resource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _make_db(label: String) -> Node:
	var script = load(_DB_PATH) as GDScript
	if script == null:
		_fail_test(label, _DB_PATH + " not loadable")
		return null
	return script.new()


func _get_autoload_db() -> Node:
	var tree = Engine.get_main_loop() as SceneTree
	return tree.root.get_node_or_null("AttackDatabase") if tree else null


# Builds a controller pipeline in the scene tree. slot_ids is an Array of String;
# each element fills the next available slot. Returns {"root","controller","executor"}
# or empty dict on failure. Caller must call _free_adv_pipeline() when done.
func _build_adv_pipeline(label: String, slot_ids: Array) -> Dictionary:
	var ctrl_script = load(_CONTROLLER_PATH) as GDScript
	if ctrl_script == null:
		_fail_test(label, _CONTROLLER_PATH + " not loadable")
		return {}
	var controller = ctrl_script.new()
	if controller == null:
		_fail_test(label, "controller instantiation returned null")
		return {}
	var scene_root = Node3D.new()
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(scene_root)
	scene_root.add_child(controller)
	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test(label, "_player_state_machine not found")
		scene_root.free()
		return {}
	psm._state = PlayerStateMachine.PlayerState.IDLE
	var msm = MutationSlotManager.new()
	for sid in slot_ids:
		msm.fill_next_available(sid)
	controller.set("_mutation_slot", msm)
	var executor = controller.get("_attack_executor")
	return {"root": scene_root, "controller": controller, "executor": executor}


func _free_adv_pipeline(pipeline: Dictionary) -> void:
	var root = pipeline.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


func _composite_key(a: String, b: String) -> String:
	var pair: Array = [a, b]
	pair.sort()
	return "%s_%s" % [pair[0], pair[1]]


# ---------------------------------------------------------------------------
# FADI-EC-1: Self-fusion — same mutation in both slots
# Catches: missing slot_a == slot_b guard in registration or stale key collision.
# ---------------------------------------------------------------------------

func test_ec1_self_fusion_registration_rejected() -> void:
	# FADI-EC-1, FADI-NF-4: register("claw","claw") must not store.
	var label := "FADI-EC-1_self_fusion_register"
	var db = _make_db(label)
	if db == null:
		return
	db.register_fused_attack("claw", "claw", _make_resource({"attack_id": 9001}))
	_assert_true(db.get_fused_attack("claw", "claw") == null, label)
	db.free()


func test_ec1_self_fusion_lookup_returns_null_without_registration() -> void:
	# FADI-EC-1: lookup("X","X") returns null even without prior registration attempt.
	var label := "FADI-EC-1_self_fusion_lookup_no_reg"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_fused_attack("acid", "acid") == null, label)
	db.free()


func test_ec1_self_fusion_player_dispatch_falls_back_to_base() -> void:
	# FADI-EC-1: Both slots filled with same ID → fused null → fallback to base.
	var label := "FADI-EC-1_self_fusion_dispatch_fallback"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns := "ec1_selffuse_claw"
	var base_res = _make_resource({"attack_id": 9010, "cooldown": 0.3, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns, base_res)
	var pipeline = _build_adv_pipeline(label, [ns, ns])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	# CHECKPOINT: FADI-EC-1 — self-fusion not registered → fallback to slot A's base.
	# Assumption: get_fused_attack returns null for same-ID pair → else branch fires base.
	# Confidence: High — code lines 467-474 confirm path.
	_assert_true(fired[0] == base_res, label + "_base_fires")  # CHECKPOINT
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-EC-2 / FADI-3c: Composite cooldown active blocks fire.
# Catches: gate reads wrong key (individual slot key instead of composite).
# ---------------------------------------------------------------------------

func test_ec2_fused_cooldown_active_blocks_fire() -> void:
	# FADI-EC-2, FADI-3c: composite key > 0 → no fire; individual keys are 0.
	var label := "FADI-EC-2_fused_cd_blocks"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "ec2_acid"
	var ns_b := "ec2_claw"
	var ns_key := _composite_key(ns_a, ns_b)
	db.register_fused_attack(ns_a, ns_b, _make_resource({"attack_id": 9020, "cooldown": 2.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9021, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9022, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	cd[ns_key] = 2.0  # Composite cooldown active; individual keys at 0.
	var executor = pipeline.get("executor")
	var fired_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired_count[0] += 1)
	controller.call("_try_attack")
	_assert_eq_int(0, fired_count[0], label + "_no_fire")
	_assert_eq_float(0.0, cd.get(ns_a, 0.0), label + "_slot_a_zero")
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_zero")
	_free_adv_pipeline(pipeline)


func test_ec2_fused_cooldown_refire_after_expiry() -> void:
	# FADI-3d: After composite cooldown expires, fused can fire again.
	var label := "FADI-3d_fused_refire"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "3d_acid"
	var ns_b := "3d_claw"
	var ns_key := _composite_key(ns_a, ns_b)
	var fused = _make_resource({"attack_id": 9030, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	db.register_fused_attack(ns_a, ns_b, fused)
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9031, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9032, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack") or not controller.has_method("_tick_controller_timers"):
		_fail_test(label, "_try_attack or _tick_controller_timers not found")
		_free_adv_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = []
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired.append(r))
	controller.call("_try_attack")
	_assert_eq_int(1, fired.size(), label + "_first_fire")
	controller.call("_try_attack")
	_assert_eq_int(1, fired.size(), label + "_blocked_during_cd")
	controller.call("_tick_controller_timers", 1.0, false)
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_eq_float(0.0, cd.get(ns_key, -1.0), label + "_cd_expired")
	controller.call("_try_attack")
	_assert_eq_int(2, fired.size(), label + "_second_fire")
	_assert_true(fired[1] == fused, label + "_second_fire_correct_resource")
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-EC-3 / FADI-3b: Composite key independent of individual slot keys.
# Catches: fused path sets individual cooldowns as side effect.
# ---------------------------------------------------------------------------

func test_ec3_fused_fire_does_not_set_individual_slot_cooldowns() -> void:
	# FADI-EC-3, FADI-3b, FADI-DD-1: after fused fires, individual keys stay 0.
	var label := "FADI-EC-3_composite_independence"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "ec3_acid"
	var ns_b := "ec3_claw"
	var ns_key := _composite_key(ns_a, ns_b)
	db.register_fused_attack(ns_a, ns_b, _make_resource({"attack_id": 9040, "cooldown": 3.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9041, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9042, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	_assert_true(cd.get(ns_key, 0.0) > 0.0, label + "_composite_set")
	_assert_eq_float(0.0, cd.get(ns_a, 0.0), label + "_slot_a_unset")
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_unset")
	_free_adv_pipeline(pipeline)


func test_ec3_individual_cooldown_active_does_not_block_fused_fire() -> void:
	# FADI-EC-3: Individual slot cds active + composite at 0 → fused still fires.
	# CHECKPOINT: FADI-EC-3 states individual and composite cooldowns are independent.
	# Assumption: gate at _try_attack line 479 reads only the resolved cooldown_key
	# (composite for fused path). Individual slot keys do not gate fused.
	# Confidence: High — code at lines 467-479 confirms composite key is the gate.
	var label := "FADI-EC-3_individual_cd_no_block_fused"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "ec3b_acid"
	var ns_b := "ec3b_claw"
	var fused = _make_resource({"attack_id": 9050, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"})
	db.register_fused_attack(ns_a, ns_b, fused)
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9051, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9052, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	cd[ns_a] = 5.0  # Individual slot A cooldown active
	cd[ns_b] = 5.0  # Individual slot B cooldown active
	# Composite key is NOT set → fused should fire.
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	_assert_true(fired[0] == fused, label + "_fused_fires")  # CHECKPOINT
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-EC-4: Empty string arguments to register/get
# ---------------------------------------------------------------------------

func test_ec4_empty_args() -> void:
	# FADI-EC-4, FADI-1d, FADI-1e, FADI-2d: all empty-arg paths.
	var label := "FADI-EC-4_empty_args"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 9060})
	db.register_fused_attack("", "acid", res)
	_assert_true(db.get_fused_attack("", "acid") == null, label + "_empty_a_reg")
	db.register_fused_attack("acid", "", res)
	_assert_true(db.get_fused_attack("acid", "") == null, label + "_empty_b_reg")
	db.register_fused_attack("claw", "acid", res)
	_assert_true(db.get_fused_attack("", "acid") == null, label + "_empty_a_lookup")
	_assert_true(db.get_fused_attack("", "") == null, label + "_both_empty_lookup")
	db.free()


# ---------------------------------------------------------------------------
# FADI-EC-5: One slot unfilled routes to single-slot base attack, not fused.
# Catches: fused path entered when only one slot filled.
# ---------------------------------------------------------------------------

func test_ec5_single_slot_routes_to_base_not_fused() -> void:
	# FADI-EC-5, FADI-4c: single slot filled → base attack fires, not fused.
	var label := "FADI-EC-5_single_slot_no_fused"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "ec5_claw"
	var ns_b := "ec5_acid"
	var base_a = _make_resource({"attack_id": 9070, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	var fused = _make_resource({"attack_id": 9075, "cooldown": 2.0, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	db.register_fused_attack(ns_a, ns_b, fused)
	# Only slot A filled (pass only one slot id).
	var pipeline = _build_adv_pipeline(label, [ns_a])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	_assert_true(fired[0] == base_a, label + "_base_a_fires")
	_assert_true(fired[0] != fused, label + "_fused_not_fired")
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-EC-6: Individual slot timers isolated after fused fire.
# Same invariant as EC-3 but from the post-fire angle: neither slot key is > 0.
# ---------------------------------------------------------------------------

func test_ec6_individual_slot_timers_isolated() -> void:
	# FADI-EC-6, FADI-DD-1
	var label := "FADI-EC-6_slot_timers_isolated"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "ec6_carapace"
	var ns_b := "ec6_adhesion"
	var ns_key := _composite_key(ns_a, ns_b)
	db.register_fused_attack(ns_a, ns_b, _make_resource({"attack_id": 9080, "cooldown": 4.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9081, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9082, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	_assert_true(cd.get(ns_key, 0.0) > 0.0, label + "_composite_set")
	_assert_eq_float(0.0, cd.get(ns_a, 0.0), label + "_slot_a_zero")
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_zero")
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-EC-7: Key collision analysis
# _make_fused_key("ab","c") != _make_fused_key("a","bc")
# ---------------------------------------------------------------------------

func test_ec7_no_adjacent_concat_collision() -> void:
	# FADI-EC-7: "ab"+"c" → "ab_c" vs "a"+"bc" → "a_bc" — no collision.
	var label := "FADI-EC-7_no_adj_concat_collision"
	var db = _make_db(label)
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 9090, "attack_name": "R1"})
	var r2 = _make_resource({"attack_id": 9091, "attack_name": "R2"})
	db.register_fused_attack("ab", "c", r1)
	db.register_fused_attack("a", "bc", r2)
	_assert_true(db.get_fused_attack("ab", "c") == r1, label + "_ab_c")
	_assert_true(db.get_fused_attack("a", "bc") == r2, label + "_a_bc")
	_assert_true(db.get_fused_attack("ab", "c") != r2, label + "_no_cross_1")
	_assert_true(db.get_fused_attack("a", "bc") != r1, label + "_no_cross_2")
	db.free()


func test_ec7_canonical_4_mutation_keys_no_collision() -> void:
	# FADI-EC-7: All 6 canonical sorted keys are distinct; each returns correct resource.
	var label := "FADI-EC-7_canonical_6_keys_distinct"
	var db = _make_db(label)
	if db == null:
		return
	var ids := ["claw", "acid", "carapace", "adhesion"]
	var registered: Dictionary = {}
	var all_distinct := true
	for i in range(ids.size()):
		for j in range(i + 1, ids.size()):
			var r = _make_resource({"attack_id": 9100 + i * 10 + j})
			db.register_fused_attack(ids[i], ids[j], r)
			var key = _composite_key(ids[i], ids[j])
			if key in registered:
				all_distinct = false
			registered[key] = r
	_assert_true(all_distinct, label + "_distinct")
	_assert_eq_int(6, registered.size(), label + "_6_keys")
	var all_correct := true
	for i in range(ids.size()):
		for j in range(i + 1, ids.size()):
			var result = db.get_fused_attack(ids[i], ids[j])
			if result != registered[_composite_key(ids[i], ids[j])]:
				all_correct = false
				break
	_assert_true(all_correct, label + "_each_correct")
	db.free()


# ---------------------------------------------------------------------------
# FADI-5c / FADI-5b / FADI-DD-2: Fallback does NOT set slot B cooldown.
# Catches: fallback path writes _mutation_cooldowns[b_id].
# ---------------------------------------------------------------------------

func test_fadi5c_fallback_does_not_set_slot_b_cooldown() -> void:
	# FADI-5c: after fallback (no fused), slot B cooldown must remain 0.
	var label := "FADI-5c_slot_b_untouched"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "5c_claw"
	var ns_b := "5c_acid"
	var base_a = _make_resource({"attack_id": 9110, "cooldown": 1.5, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9111, "cooldown": 1.5, "effect_type": "MELEE_SWIPE"}))
	# No fused registered for (ns_a, ns_b).
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)
	controller.call("_try_attack")
	_assert_true(fired[0] == base_a, label + "_slot_a_fires")  # FADI-5a
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	_assert_true(cd.get(ns_a, 0.0) > 0.0, label + "_slot_a_cd_set")  # FADI-5b
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_cd_zero")  # FADI-5c
	_free_adv_pipeline(pipeline)


func test_fadi5b_fallback_slot_a_cooldown_exact_value() -> void:
	# FADI-5b: slot A cooldown equals base_a.cooldown exactly (no scaling).
	var label := "FADI-5b_slot_a_cd_exact"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "5b_carapace"
	var ns_b := "5b_adhesion"
	var base_a = _make_resource({"attack_id": 9120, "cooldown": 2.75, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9121, "cooldown": 1.25, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	_assert_eq_float(2.75, cd.get(ns_a, 0.0), label + "_exact_value")
	_assert_eq_float(0.0, cd.get(ns_b, 0.0), label + "_slot_b_zero")
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-7a: State-machine gate blocks fused attack in non-permit state.
# Catches: fused path entered before state-machine check.
# ---------------------------------------------------------------------------

func test_fadi7a_dead_state_blocks_fused_attack() -> void:
	# FADI-7a: DEAD state must block fused dispatch.
	var label := "FADI-7a_dead_blocks_fused"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "7a_acid"
	var ns_b := "7a_claw"
	var ns_key := _composite_key(ns_a, ns_b)
	db.register_fused_attack(ns_a, ns_b, _make_resource({"attack_id": 9130, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9131, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9132, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test(label, "_player_state_machine not found")
		_free_adv_pipeline(pipeline)
		return
	psm._state = PlayerStateMachine.PlayerState.DEAD
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired_count[0] += 1)
	controller.call("_try_attack")
	_assert_eq_int(0, fired_count[0], label + "_no_fire")
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_eq_float(0.0, cd.get(ns_key, 0.0), label + "_cd_untouched")
	_free_adv_pipeline(pipeline)


func test_fadi7a_hurt_state_blocks_fused_attack() -> void:
	# FADI-7a: HURT state also blocks fused dispatch.
	var label := "FADI-7a_hurt_blocks_fused"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "7ah_carapace"
	var ns_b := "7ah_adhesion"
	db.register_fused_attack(ns_a, ns_b, _make_resource({"attack_id": 9140, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9141, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9142, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	var psm = controller.get("_player_state_machine")
	if psm == null:
		_fail_test(label, "_player_state_machine not found")
		_free_adv_pipeline(pipeline)
		return
	psm._state = PlayerStateMachine.PlayerState.HURT
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found")
		_free_adv_pipeline(pipeline)
		return
	var executor = pipeline.get("executor")
	var fired_count = [0]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(_r): fired_count[0] += 1)
	controller.call("_try_attack")
	_assert_eq_int(0, fired_count[0], label + "_no_fire")
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# Null resource and overwrite semantics
# ---------------------------------------------------------------------------

func test_null_resource_not_registered() -> void:
	# FADI-1g, FADI-NF-5: null resource rejected; subsequent lookup returns null.
	var label := "FADI-1g_null_resource"
	var db = _make_db(label)
	if db == null:
		return
	db.register_fused_attack("claw", "acid", null)
	_assert_true(db.get_fused_attack("claw", "acid") == null, label + "_rejected")
	var res = _make_resource({"attack_id": 9150})
	db.register_fused_attack("claw", "acid", res)
	db.register_fused_attack("claw", "acid", null)
	_assert_true(db.get_fused_attack("claw", "acid") == res, label + "_no_overwrite")
	db.free()


func test_overwrite_reverse_registration_last_wins() -> void:
	# FADI-1c: register("claw","acid",r1) then register("acid","claw",r2) → r2 wins.
	var label := "FADI-1c_reverse_overwrite"
	var db = _make_db(label)
	if db == null:
		return
	var r1 = _make_resource({"attack_id": 9160})
	var r2 = _make_resource({"attack_id": 9161})
	db.register_fused_attack("claw", "acid", r1)
	db.register_fused_attack("acid", "claw", r2)
	_assert_true(db.get_fused_attack("claw", "acid") == r2, label + "_fwd_r2")
	_assert_true(db.get_fused_attack("acid", "claw") == r2, label + "_rev_r2")
	db.free()


# ---------------------------------------------------------------------------
# Order stress: 3 combos, no cross-contamination
# ---------------------------------------------------------------------------

func test_order_stress_3_combos_no_cross_contamination() -> void:
	# 3 combos registered in order; each independently retrievable.
	var label := "order_stress_3_combos"
	var db = _make_db(label)
	if db == null:
		return
	var r_ac = _make_resource({"attack_id": 9170})
	var r_ap = _make_resource({"attack_id": 9171})
	var r_ah = _make_resource({"attack_id": 9172})
	db.register_fused_attack("claw", "acid", r_ac)
	db.register_fused_attack("acid", "carapace", r_ap)
	db.register_fused_attack("adhesion", "acid", r_ah)
	_assert_true(db.get_fused_attack("claw", "acid") == r_ac, label + "_ac")
	_assert_true(db.get_fused_attack("acid", "claw") == r_ac, label + "_ac_rev")
	_assert_true(db.get_fused_attack("acid", "carapace") == r_ap, label + "_ap")
	_assert_true(db.get_fused_attack("carapace", "acid") == r_ap, label + "_ap_rev")
	_assert_true(db.get_fused_attack("adhesion", "acid") == r_ah, label + "_ah")
	_assert_true(db.get_fused_attack("acid", "adhesion") == r_ah, label + "_ah_rev")
	db.free()


# ---------------------------------------------------------------------------
# Cooldown decay: composite key decrements via _tick_controller_timers
# Catches: composite key skipped in decrement loop (treated as non-standard key).
# ---------------------------------------------------------------------------

func test_composite_cooldown_key_decrements_via_tick() -> void:
	var label := "composite_cd_decrements"
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return
	var ns_a := "decay_acid"
	var ns_b := "decay_claw"
	var ns_key := _composite_key(ns_a, ns_b)
	db.register_fused_attack(ns_a, ns_b, _make_resource({"attack_id": 9180, "cooldown": 2.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_a, _make_resource({"attack_id": 9181, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	db.register_base_attack(ns_b, _make_resource({"attack_id": 9182, "cooldown": 1.0, "effect_type": "MELEE_SWIPE"}))
	var pipeline = _build_adv_pipeline(label, [ns_a, ns_b])
	if pipeline.is_empty():
		return
	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack") or not controller.has_method("_tick_controller_timers"):
		_fail_test(label, "_try_attack or _tick_controller_timers not found")
		_free_adv_pipeline(pipeline)
		return
	controller.call("_try_attack")
	var cd = controller.get("_mutation_cooldowns")
	if cd == null:
		_fail_test(label, "_mutation_cooldowns not found")
		_free_adv_pipeline(pipeline)
		return
	var initial: float = cd.get(ns_key, 0.0)
	_assert_true(initial > 0.0, label + "_initial_set")
	controller.call("_tick_controller_timers", 0.5, false)
	var after_tick: float = cd.get(ns_key, -1.0)
	_assert_true(after_tick < initial, label + "_decremented")
	_assert_true(after_tick >= 0.0, label + "_non_negative")
	_free_adv_pipeline(pipeline)


# ---------------------------------------------------------------------------
# FADI-NF-1: Fresh db instance has zero fused attacks after _ready().
# Catches: _register_defaults() accidentally registering fused attacks.
# ---------------------------------------------------------------------------

func test_nf1_fresh_db_has_zero_fused_attacks() -> void:
	# FADI-NF-1
	var label := "FADI-NF-1_fresh_zero_fused"
	var db = _make_db(label)
	if db == null:
		return
	_assert_eq_int(0, db.get_fused_attack_count(), label)
	db.free()


# ---------------------------------------------------------------------------
# Combinatorial: invalid ops sequence must not corrupt state for valid op after.
# ---------------------------------------------------------------------------

func test_combinatorial_invalid_ops_do_not_corrupt_state() -> void:
	var label := "combo_invalid_no_corruption"
	var db = _make_db(label)
	if db == null:
		return
	var valid = _make_resource({"attack_id": 9200})
	db.register_fused_attack("", "b", valid)
	db.register_fused_attack("a", "", valid)
	db.register_fused_attack("a", "a", valid)
	db.register_fused_attack("a", "b", null)
	_assert_true(db.get_fused_attack("", "b") == null, label + "_empty_a")
	_assert_true(db.get_fused_attack("a", "") == null, label + "_empty_b")
	_assert_true(db.get_fused_attack("a", "a") == null, label + "_self")
	_assert_true(db.get_fused_attack("a", "b") == null, label + "_null_res")
	db.register_fused_attack("a", "b", valid)
	_assert_true(db.get_fused_attack("a", "b") == valid, label + "_valid_after")
	db.free()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusedComboMatrixAdversarialTests ===")

	test_ec1_self_fusion_registration_rejected()
	test_ec1_self_fusion_lookup_returns_null_without_registration()
	test_ec1_self_fusion_player_dispatch_falls_back_to_base()

	test_ec2_fused_cooldown_active_blocks_fire()
	test_ec2_fused_cooldown_refire_after_expiry()

	test_ec3_fused_fire_does_not_set_individual_slot_cooldowns()
	test_ec3_individual_cooldown_active_does_not_block_fused_fire()

	test_ec4_empty_args()

	test_ec5_single_slot_routes_to_base_not_fused()

	test_ec6_individual_slot_timers_isolated()

	test_ec7_no_adjacent_concat_collision()
	test_ec7_canonical_4_mutation_keys_no_collision()

	test_fadi5c_fallback_does_not_set_slot_b_cooldown()
	test_fadi5b_fallback_slot_a_cooldown_exact_value()

	test_fadi7a_dead_state_blocks_fused_attack()
	test_fadi7a_hurt_state_blocks_fused_attack()

	test_null_resource_not_registered()
	test_overwrite_reverse_registration_last_wins()

	test_order_stress_3_combos_no_cross_contamination()
	test_composite_cooldown_key_decrements_via_tick()
	test_nf1_fresh_db_has_zero_fused_attacks()
	test_combinatorial_invalid_ops_do_not_corrupt_state()

	print(
		"FusedComboMatrixAdversarialTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
