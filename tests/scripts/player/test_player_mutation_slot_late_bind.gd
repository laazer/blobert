#
# PlayerController3D binds MutationSlotManager from InfectionInteractionHandler on
# demand so attack (J) is not blocked when handler initializes after player _ready.

extends "res://tests/utils/test_utils.gd"

const _CONTROLLER_PATH: String = "res://scripts/player/player_controller_3d.gd"
const _HANDLER_PATH: String = "res://scripts/infection/infection_interaction_handler.gd"
const _BIND_PATH: String = "res://scripts/player/player_mutation_slot_bind.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func _build_handler_player_scene(test_label: String) -> Dictionary:
	var ctrl_script: GDScript = load(_CONTROLLER_PATH) as GDScript
	var handler_script: GDScript = load(_HANDLER_PATH) as GDScript
	if ctrl_script == null or handler_script == null:
		_fail(test_label, "could not load player or handler script")
		return {}
	var root: Node3D = Node3D.new()
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail(test_label, "no SceneTree")
		return {}
	tree.root.add_child(root)
	var handler: Node = handler_script.new() as Node
	handler.name = "InfectionInteractionHandler"
	root.add_child(handler)
	var player: CharacterBody3D = ctrl_script.new() as CharacterBody3D
	player.name = "Player3D"
	root.add_child(player)
	return {"root": root, "handler": handler, "player": player}


func _teardown(scene: Dictionary) -> void:
	var root: Variant = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


func test_try_bind_skips_until_handler_ready() -> void:
	var handler_script: GDScript = load(_HANDLER_PATH) as GDScript
	var ctrl_script: GDScript = load(_CONTROLLER_PATH) as GDScript
	if handler_script == null or ctrl_script == null:
		_fail("late_bind_scripts", "could not load handler or controller script")
		return
	var handler: Node = handler_script.new() as Node
	var player: CharacterBody3D = ctrl_script.new() as CharacterBody3D
	var bind_script: GDScript = load(_BIND_PATH) as GDScript
	if bind_script == null:
		_fail("late_bind_bind_script", "PlayerMutationSlotBind script missing")
		return
	player.set("_mutation_slot", bind_script.call("try_bind_from_handler", handler))
	_assert_true(player.get("_mutation_slot") == null, "bind_skips_before_handler_ready")
	handler._ready()
	player.set("_mutation_slot", bind_script.call("try_bind_from_handler", handler))
	var bound: Variant = player.get("_mutation_slot")
	_assert_true(bound != null, "bind_succeeds_after_handler_ready")
	if bound != null and handler.has_method("get_mutation_slot_manager"):
		_assert_true(bound == handler.call("get_mutation_slot_manager"), "bind_uses_handler_manager")


func test_ensure_mutation_slot_binding_after_handler_ready() -> void:
	var scene: Dictionary = _build_handler_player_scene("late_bind_recover")
	if scene.is_empty():
		return
	var handler: Node = scene["handler"]
	var player: CharacterBody3D = scene["player"]
	player.set("_mutation_slot", null)
	var bind_script: GDScript = load(_BIND_PATH) as GDScript
	if bind_script == null:
		_fail("late_bind_ensure_script", "PlayerMutationSlotBind script missing")
		_teardown(scene)
		return
	bind_script.call("ensure_binding", player)
	var bound: Variant = player.get("_mutation_slot")
	_assert_true(bound != null, "mutation_slot_bound_after_ensure")
	if bound != null and handler.has_method("get_mutation_slot_manager"):
		var mgr: Variant = handler.call("get_mutation_slot_manager")
		_assert_true(bound == mgr, "mutation_slot_same_manager_as_handler")
	_teardown(scene)


func test_filled_slots_do_not_force_mutate_fsm_state() -> void:
	var scene: Dictionary = _build_handler_player_scene("filled_slots_fsm")
	if scene.is_empty():
		return
	var player: CharacterBody3D = scene["player"]
	player.set("_mutation_slot", null)
	var bind_script: GDScript = load(_BIND_PATH) as GDScript
	if bind_script == null:
		_fail("late_bind_ensure_script", "PlayerMutationSlotBind script missing")
		_teardown(scene)
		return
	bind_script.call("ensure_binding", player)
	var mgr: MutationSlotManager = player.get("_mutation_slot") as MutationSlotManager
	if mgr == null:
		_fail("filled_slots_fsm_mgr", "mutation slot manager still null")
		_teardown(scene)
		return
	mgr.fill_next_available("acid")
	player.set("_fusion_active", false)
	if not player.has_method("_sync_player_state_machine"):
		_fail("filled_slots_fsm_sync", "_sync_player_state_machine missing")
		_teardown(scene)
		return
	player.call("_sync_player_state_machine")
	var psm: PlayerStateMachine = player.get("_player_state_machine") as PlayerStateMachine
	if psm == null:
		_fail("filled_slots_fsm_psm", "player state machine missing")
		_teardown(scene)
		return
	_assert_true(
		psm.get_state() != PlayerStateMachine.PlayerState.MUTATE,
		"filled_slots_stay_kinematic_not_mutate_fsm",
	)
	_teardown(scene)


func test_fusion_active_does_not_derive_mutate_or_block_attack() -> void:
	var scene: Dictionary = _build_handler_player_scene("fusion_attack_gate")
	if scene.is_empty():
		return
	var player: CharacterBody3D = scene["player"]
	player.set("_mutation_slot", null)
	var bind_script: GDScript = load(_BIND_PATH) as GDScript
	if bind_script == null:
		_fail("late_bind_ensure_script", "PlayerMutationSlotBind script missing")
		_teardown(scene)
		return
	bind_script.call("ensure_binding", player)
	var mgr: MutationSlotManager = player.get("_mutation_slot") as MutationSlotManager
	if mgr == null:
		_fail("fusion_attack_gate_mgr", "mutation slot manager still null")
		_teardown(scene)
		return
	mgr.fill_next_available("claw")
	mgr.fill_next_available("acid")
	player.call("apply_fusion_effect", 5.0, 1.5)
	player.call("_sync_player_state_machine")
	var psm: PlayerStateMachine = player.get("_player_state_machine") as PlayerStateMachine
	if psm == null:
		_fail("fusion_attack_gate_psm", "player state machine missing")
		_teardown(scene)
		return
	_assert_true(
		psm.get_state() != PlayerStateMachine.PlayerState.MUTATE,
		"fusion_does_not_force_mutate_fsm",
	)
	var policy: PlayerInputActionPolicy = player.get("_input_policy") as PlayerInputActionPolicy
	if policy == null:
		_fail("fusion_attack_gate_policy", "input policy missing")
		_teardown(scene)
		return
	_assert_true(
		policy.is_action_permitted(psm.get_state(), PlayerInputActionPolicy.ACTION_ATTACK),
		"fusion_does_not_block_attack_policy",
	)
	_teardown(scene)


func test_try_attack_fires_after_late_bind_with_claw() -> void:
	var db: Node = _get_attack_database()
	if db == null:
		_fail("late_bind_attack_db", "AttackDatabase autoload not available")
		return
	var scene: Dictionary = _build_handler_player_scene("late_bind_try_attack")
	if scene.is_empty():
		return
	var player: CharacterBody3D = scene["player"]
	player.set("_mutation_slot", null)
	var bind_script: GDScript = load(_BIND_PATH) as GDScript
	if bind_script == null:
		_fail("late_bind_ensure_script", "PlayerMutationSlotBind script missing")
		_teardown(scene)
		return
	bind_script.call("ensure_binding", player)
	var mgr: MutationSlotManager = player.get("_mutation_slot") as MutationSlotManager
	if mgr == null:
		_fail("late_bind_try_attack_mgr", "mutation slot manager still null")
		_teardown(scene)
		return
	mgr.fill_next_available("claw")
	var psm: PlayerStateMachine = player.get("_player_state_machine")
	if psm != null:
		psm._state = PlayerStateMachine.PlayerState.IDLE
	var executor: AttackExecutor = player.get("_attack_executor") as AttackExecutor
	var fired: Array = [false]
	if executor != null and executor.has_signal("attack_started"):
		executor.attack_started.connect(func(_r): fired[0] = true)
	if not player.has_method("_try_attack"):
		_fail("late_bind_try_attack_method", "_try_attack missing")
		_teardown(scene)
		return
	player.call("_try_attack")
	_assert_true(fired[0], "try_attack_fires_after_late_bind")
	_teardown(scene)


func _get_attack_database() -> Node:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null:
		return null
	return tree.root.get_node_or_null("AttackDatabase")


func run_all() -> int:
	_pass_count = 0
	_fail_count = 0
	test_try_bind_skips_until_handler_ready()
	test_ensure_mutation_slot_binding_after_handler_ready()
	test_filled_slots_do_not_force_mutate_fsm_state()
	test_fusion_active_does_not_derive_mutate_or_block_attack()
	test_try_attack_fires_after_late_bind_with_claw()
	return _fail_count
