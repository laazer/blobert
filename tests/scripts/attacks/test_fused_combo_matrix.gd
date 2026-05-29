#
# test_fused_combo_matrix.gd
#
# Combo matrix tests for the fused attack system: all 6 unordered canonical pairs,
# forward lookups, reverse lookups, and player-dispatch paths through _try_attack().
#
# Spec: project_board/specs/fused_attack_database_integration_spec.md
# Requirements: FADI-6 (FADI-6-1a through FADI-6-6c), FADI-DD-3, FADI-DD-4
# Ticket: M12-01
#   project_board/12_milestone_12_fused_mutation_attacks/backlog/01_fused_attack_database_integration.md
#
# Coverage: 18 tests
#   6 forward-lookup tests (FADI-6-1a, 2a, 3a, 4a, 5a, 6a)
#   6 reverse-lookup tests (FADI-6-1b, 2b, 3b, 4b, 5b, 6b)
#   6 player-dispatch tests (FADI-6-1c, 2c, 3c, 4c, 5c, 6c)
#
# Design: forward/reverse lookup tests use a private AttackDatabaseNode instance
# (not the autoload) for isolation. Player-dispatch tests use the autoload database
# because _try_attack() resolves the "AttackDatabase" scene-tree node via
# _get_attack_database(). All resources are synthetic (no .tres files).
#

class_name FusedComboMatrixTests
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


# Builds a full two-slot attack pipeline: controller in scene tree, state set,
# both mutation slots filled with ns_a / ns_b, cooldowns empty, executor wired.
# Returns {"root", "controller", "executor"} or empty dict on failure.
# This is a combined single-function setup distinct from _build_controller_scene
# + _setup_attack_pipeline used in the integration test.
func _make_fused_pipeline(label: String, ns_a: String, ns_b: String) -> Dictionary:
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
	msm.fill_next_available(ns_a)
	msm.fill_next_available(ns_b)
	controller.set("_mutation_slot", msm)

	var executor = controller.get("_attack_executor")
	return {"root": scene_root, "controller": controller, "executor": executor}


func _free_pipeline(pipeline: Dictionary) -> void:
	var root = pipeline.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


# ---------------------------------------------------------------------------
# Forward lookup tests — FADI-6-Na (N = 1..6)
#
# register_fused_attack(first, second, res), then get_fused_attack(first, second)
# must return res. Uses a private db instance per FADI-6 isolation note.
# ---------------------------------------------------------------------------

func test_fused_forward_acid_claw() -> void:
	# FADI-6-1a: claw + acid — sorted key "acid_claw", forward lookup
	var label := "FADI-6-1a_forward_acid_claw"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 601, "attack_name": "Acid+Claw"})
	db.register_fused_attack("claw", "acid", res)
	_assert_true(db.get_fused_attack("claw", "acid") == res, label)
	db.free()


func test_fused_forward_carapace_claw() -> void:
	# FADI-6-2a: claw + carapace — sorted key "carapace_claw", forward lookup
	var label := "FADI-6-2a_forward_carapace_claw"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 602, "attack_name": "Carapace+Claw"})
	db.register_fused_attack("claw", "carapace", res)
	_assert_true(db.get_fused_attack("claw", "carapace") == res, label)
	db.free()


func test_fused_forward_adhesion_claw() -> void:
	# FADI-6-3a: claw + adhesion — sorted key "adhesion_claw", forward lookup
	var label := "FADI-6-3a_forward_adhesion_claw"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 603, "attack_name": "Adhesion+Claw"})
	db.register_fused_attack("claw", "adhesion", res)
	_assert_true(db.get_fused_attack("claw", "adhesion") == res, label)
	db.free()


func test_fused_forward_acid_carapace() -> void:
	# FADI-6-4a: acid + carapace — sorted key "acid_carapace", forward lookup
	var label := "FADI-6-4a_forward_acid_carapace"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 604, "attack_name": "Acid+Carapace"})
	db.register_fused_attack("acid", "carapace", res)
	_assert_true(db.get_fused_attack("acid", "carapace") == res, label)
	db.free()


func test_fused_forward_acid_adhesion() -> void:
	# FADI-6-5a: acid + adhesion — sorted key "acid_adhesion", forward lookup
	var label := "FADI-6-5a_forward_acid_adhesion"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 605, "attack_name": "Acid+Adhesion"})
	db.register_fused_attack("acid", "adhesion", res)
	_assert_true(db.get_fused_attack("acid", "adhesion") == res, label)
	db.free()


func test_fused_forward_adhesion_carapace() -> void:
	# FADI-6-6a: carapace + adhesion — sorted key "adhesion_carapace", forward lookup
	var label := "FADI-6-6a_forward_adhesion_carapace"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 606, "attack_name": "Adhesion+Carapace"})
	db.register_fused_attack("carapace", "adhesion", res)
	_assert_true(db.get_fused_attack("carapace", "adhesion") == res, label)
	db.free()


# ---------------------------------------------------------------------------
# Reverse lookup tests — FADI-6-Nb (N = 1..6)
#
# register_fused_attack(first, second, res), then get_fused_attack(second, first)
# must return the same resource. Validates FADI-DD-3 order-independence.
# ---------------------------------------------------------------------------

func test_fused_reverse_acid_claw() -> void:
	# FADI-6-1b: register (claw, acid), lookup (acid, claw) — same resource
	var label := "FADI-6-1b_reverse_acid_claw"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 611, "attack_name": "Acid+Claw reverse"})
	db.register_fused_attack("claw", "acid", res)
	_assert_true(db.get_fused_attack("acid", "claw") == res, label)
	db.free()


func test_fused_reverse_carapace_claw() -> void:
	# FADI-6-2b: register (claw, carapace), lookup (carapace, claw) — same resource
	var label := "FADI-6-2b_reverse_carapace_claw"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 612, "attack_name": "Carapace+Claw reverse"})
	db.register_fused_attack("claw", "carapace", res)
	_assert_true(db.get_fused_attack("carapace", "claw") == res, label)
	db.free()


func test_fused_reverse_adhesion_claw() -> void:
	# FADI-6-3b: register (claw, adhesion), lookup (adhesion, claw) — same resource
	var label := "FADI-6-3b_reverse_adhesion_claw"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 613, "attack_name": "Adhesion+Claw reverse"})
	db.register_fused_attack("claw", "adhesion", res)
	_assert_true(db.get_fused_attack("adhesion", "claw") == res, label)
	db.free()


func test_fused_reverse_acid_carapace() -> void:
	# FADI-6-4b: register (acid, carapace), lookup (carapace, acid) — same resource
	var label := "FADI-6-4b_reverse_acid_carapace"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 614, "attack_name": "Acid+Carapace reverse"})
	db.register_fused_attack("acid", "carapace", res)
	_assert_true(db.get_fused_attack("carapace", "acid") == res, label)
	db.free()


func test_fused_reverse_acid_adhesion() -> void:
	# FADI-6-5b: register (acid, adhesion), lookup (adhesion, acid) — same resource
	var label := "FADI-6-5b_reverse_acid_adhesion"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 615, "attack_name": "Acid+Adhesion reverse"})
	db.register_fused_attack("acid", "adhesion", res)
	_assert_true(db.get_fused_attack("adhesion", "acid") == res, label)
	db.free()


func test_fused_reverse_adhesion_carapace() -> void:
	# FADI-6-6b: register (carapace, adhesion), lookup (adhesion, carapace) — same resource
	var label := "FADI-6-6b_reverse_adhesion_carapace"
	var db = _make_db(label)
	if db == null:
		return
	var res = _make_resource({"attack_id": 616, "attack_name": "Adhesion+Carapace reverse"})
	db.register_fused_attack("carapace", "adhesion", res)
	_assert_true(db.get_fused_attack("adhesion", "carapace") == res, label)
	db.free()


# ---------------------------------------------------------------------------
# Player dispatch tests — FADI-6-Nc (N = 1..6)
#
# For each combo: fill both slots with the two mutation IDs, register the
# fused resource on the autoload database, invoke _try_attack(), and assert:
#   (1) the fused resource was fired via attack_started signal (FADI-4a)
#   (2) the composite cooldown key is set (FADI-DD-1, FADI-3a)
#   (3) individual slot-ID cooldowns remain unset (FADI-3b / FADI-DD-1)
#
# Namespaced IDs (prefix "fcm_") prevent contamination of the autoload database.
# The autoload is used because _try_attack() -> _get_attack_database() resolves
# only the "AttackDatabase" scene-tree node.
# ---------------------------------------------------------------------------

func _run_player_dispatch_test(label: String, raw_a: String, raw_b: String) -> void:
	var db = _get_autoload_db()
	if db == null:
		_fail_test(label, "AttackDatabase autoload not available")
		return

	# Namespace to avoid contaminating the shared autoload database state
	var ns_a := "fcm_" + raw_a
	var ns_b := "fcm_" + raw_b

	# Composite key: alphabetical sort of slot IDs joined by "_" (same logic
	# as _try_attack() lines 469-471 in player_controller_3d.gd)
	var ns_pair: Array = [ns_a, ns_b]
	ns_pair.sort()
	var ns_key: String = "%s_%s" % [ns_pair[0], ns_pair[1]]

	var base_a = _make_resource({"attack_id": 700, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	var base_b = _make_resource({"attack_id": 701, "cooldown": 0.5, "effect_type": "MELEE_SWIPE"})
	db.register_base_attack(ns_a, base_a)
	db.register_base_attack(ns_b, base_b)

	var fused = _make_resource(
		{"attack_id": 750, "cooldown": 2.0, "effect_type": "MELEE_SWIPE", "damage": 15.0}
	)
	db.register_fused_attack(ns_a, ns_b, fused)

	var pipeline = _make_fused_pipeline(label, ns_a, ns_b)
	if pipeline.is_empty():
		return

	var controller = pipeline["controller"]
	if not controller.has_method("_try_attack"):
		_fail_test(label, "_try_attack not found on controller")
		_free_pipeline(pipeline)
		return

	var executor = pipeline.get("executor")
	var fired: Array = [null]
	if executor != null and executor.has_signal("attack_started"):
		executor.connect("attack_started", func(r): fired[0] = r)

	controller.call("_try_attack")

	# (1) fused resource was fired — not a base resource (FADI-4a, FADI-6-Nc)
	_assert_true(fired[0] == fused, label + "_fused_resource_fired")

	# (2) composite cooldown key is set (FADI-3a, FADI-DD-1)
	var cd = controller.get("_mutation_cooldowns")
	if cd != null:
		_assert_true(cd.get(ns_key, 0.0) > 0.0, label + "_composite_cooldown_set")
		# (3) individual slot cooldowns are NOT set (FADI-3b, FADI-DD-1)
		_assert_true(cd.get(ns_a, 0.0) == 0.0, label + "_slot_a_individual_unset")
		_assert_true(cd.get(ns_b, 0.0) == 0.0, label + "_slot_b_individual_unset")
	else:
		_fail_test(label, "_mutation_cooldowns not accessible")

	_free_pipeline(pipeline)


func test_fused_dispatch_acid_claw() -> void:
	# FADI-6-1c: player fires fused acid+claw combo
	_run_player_dispatch_test("FADI-6-1c_dispatch_acid_claw", "claw", "acid")


func test_fused_dispatch_carapace_claw() -> void:
	# FADI-6-2c: player fires fused carapace+claw combo
	_run_player_dispatch_test("FADI-6-2c_dispatch_carapace_claw", "claw", "carapace")


func test_fused_dispatch_adhesion_claw() -> void:
	# FADI-6-3c: player fires fused adhesion+claw combo
	_run_player_dispatch_test("FADI-6-3c_dispatch_adhesion_claw", "claw", "adhesion")


func test_fused_dispatch_acid_carapace() -> void:
	# FADI-6-4c: player fires fused acid+carapace combo
	_run_player_dispatch_test("FADI-6-4c_dispatch_acid_carapace", "acid", "carapace")


func test_fused_dispatch_acid_adhesion() -> void:
	# FADI-6-5c: player fires fused acid+adhesion combo
	_run_player_dispatch_test("FADI-6-5c_dispatch_acid_adhesion", "acid", "adhesion")


func test_fused_dispatch_adhesion_carapace() -> void:
	# FADI-6-6c: player fires fused adhesion+carapace combo
	_run_player_dispatch_test("FADI-6-6c_dispatch_adhesion_carapace", "carapace", "adhesion")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusedComboMatrixTests ===")

	# Forward lookups (FADI-6-1a through FADI-6-6a)
	test_fused_forward_acid_claw()
	test_fused_forward_carapace_claw()
	test_fused_forward_adhesion_claw()
	test_fused_forward_acid_carapace()
	test_fused_forward_acid_adhesion()
	test_fused_forward_adhesion_carapace()

	# Reverse lookups (FADI-6-1b through FADI-6-6b)
	test_fused_reverse_acid_claw()
	test_fused_reverse_carapace_claw()
	test_fused_reverse_adhesion_claw()
	test_fused_reverse_acid_carapace()
	test_fused_reverse_acid_adhesion()
	test_fused_reverse_adhesion_carapace()

	# Player dispatch (FADI-6-1c through FADI-6-6c)
	test_fused_dispatch_acid_claw()
	test_fused_dispatch_carapace_claw()
	test_fused_dispatch_adhesion_claw()
	test_fused_dispatch_acid_carapace()
	test_fused_dispatch_acid_adhesion()
	test_fused_dispatch_adhesion_carapace()

	print(
		"FusedComboMatrixTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
