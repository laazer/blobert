#
# test_detach_recall_fx_adversarial.gd
#
# Adversarial / edge-case tests for Detach & Recall visual feedback.
# Scope: rapid detach/recall, recall cancel (chunk destroyed), no chunk on recall,
# signal ordering stability, non-blocking under stress.
#
# Spec: agent_context/projects/blobert/specs/detach_recall_fx_spec.md
#

class_name DetachRecallFxAdversarialTests
extends Object

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


func _approx_eq(a: float, b: float) -> bool:
	return abs(a - b) < EPSILON


func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _cleanup_input() -> void:
	Input.action_release("move_left")
	Input.action_release("move_right")
	Input.action_release("jump")
	Input.action_release("detach")


func _load_main_scene() -> Node:
	var packed: PackedScene = load("res://scenes/levels/test_movement.tscn") as PackedScene
	if packed == null:
		_fail("adv_fx_scene_load", "could not load res://scenes/levels/test_movement.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("adv_fx_scene_instantiate", "instantiate() returned null")
		return null
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree != null and tree.root != null:
		tree.root.add_child(inst)
		tree.current_scene = inst
	return inst


func _get_player(root: Node) -> PlayerController:
	if root == null:
		return null
	return root.get_node_or_null("Player") as PlayerController


func _pulse_detach(controller: PlayerController, delta: float) -> void:
	_cleanup_input()
	Input.action_press("detach")
	controller._physics_process(delta)
	Input.action_release("detach")


# ---------------------------------------------------------------------------
# Rapid detach/recall — no double emissions, no crash
# ---------------------------------------------------------------------------

func test_adv_rapid_detach_press_only_emits_detach_fired_once_per_logical_detach() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("adv_rapid_player", "Player not PlayerController")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: adv_rapid_detach_press_only_emits_detach_fired_once_per_logical_detach — no valid physics space for CharacterBody2D")
		root.free()
		return
	_cleanup_input()

	if not player.has_signal("detach_fired"):
		_fail("adv_rapid_detach_signal", "detach_fired not declared")
		root.free()
		return

	var count: int = 0
	player.detach_fired.connect(func(_pp: Vector2, _cp: Vector2) -> void: count += 1)

	# Two physics frames with detach held; only first frame has logical detach (has_chunk true→false).
	Input.action_press("detach")
	player._physics_process(0.016)
	player._physics_process(0.016)
	Input.action_release("detach")

	_assert_true(count == 1, "adv_rapid_detach_emitted_once")
	root.free()


# CHECKPOINT: Spec says recall cancel (chunk destroyed before reabsorb) must not emit chunk_reabsorbed.
func test_adv_recall_cancel_chunk_destroyed_before_reabsorb_does_not_emit_chunk_reabsorbed() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("adv_cancel_player", "Player not PlayerController")
		root.free()
		return

	player._ready()
	_cleanup_input()

	if not player.has_signal("chunk_reabsorbed"):
		_fail("adv_cancel_signal", "chunk_reabsorbed not declared")
		root.free()
		return

	_pulse_detach(player, 0.016)
	if player._chunk_node == null or not is_instance_valid(player._chunk_node):
		_fail("adv_cancel_requires_chunk", "no chunk after detach")
		root.free()
		return

	var reabsorb_count: int = 0
	player.chunk_reabsorbed.connect(func(_pp: Vector2, _cp: Vector2) -> void: reabsorb_count += 1)

	# Start recall then destroy chunk before travel time completes.
	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")
	_assert_true(player._recall_in_progress, "adv_cancel_recall_started")

	player._chunk_node.queue_free()
	player._chunk_node = null

	# Advance past would-be reabsorb time.
	player._physics_process(0.5)

	_assert_true(reabsorb_count == 0, "adv_cancel_chunk_reabsorbed_not_emitted")
	root.free()


func test_adv_recall_pressed_with_no_chunk_does_not_emit_recall_started() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("adv_no_chunk_player", "Player not PlayerController")
		root.free()
		return

	player._ready()
	_cleanup_input()

	# Never detach — has_chunk stays true (or if we force has_chunk false without a chunk, recall is invalid).
	# Controller: recall_pressed = detach_just_pressed and (not prev_has_chunk) and _chunk_node != null.
	# So with no detach, pressing detach gives prev_has_chunk=true → no recall. To test "no chunk" we
	# detach once (creates chunk), free the chunk manually, then press detach again — recall_pressed
	# is false because _chunk_node is null. So recall_started should not fire.
	_pulse_detach(player, 0.016)
	if player._chunk_node != null and is_instance_valid(player._chunk_node):
		player._chunk_node.queue_free()
		player._chunk_node = null

	var recall_start_count: int = 0
	player.recall_started.connect(func(_pp: Vector2, _cp: Vector2) -> void: recall_start_count += 1)

	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")

	_assert_true(recall_start_count == 0, "adv_no_chunk_recall_started_not_emitted")
	root.free()


func test_adv_signal_ordering_preserved_over_full_cycle() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("adv_order_player", "Player not PlayerController")
		root.free()
		return

	player._ready()
	_cleanup_input()

	var order: Array[String] = []
	player.detach_fired.connect(func(_p: Vector2, _c: Vector2) -> void: order.append("detach_fired"))
	player.recall_started.connect(func(_p: Vector2, _c: Vector2) -> void: order.append("recall_started"))
	player.chunk_reabsorbed.connect(func(_p: Vector2, _c: Vector2) -> void: order.append("chunk_reabsorbed"))

	_pulse_detach(player, 0.016)
	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")
	player._recall_in_progress = true
	player._recall_timer = player._RECALL_TRAVEL_TIME - 0.016
	player._physics_process(0.016)

	var ok: bool = order.size() == 3 and order[0] == "detach_fired" and order[1] == "recall_started" and order[2] == "chunk_reabsorbed"
	_assert_true(ok, "adv_order_detach_recall_reabsorb")
	root.free()


func test_adv_non_blocking_input_processed_after_detach_and_recall_start() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("adv_nb_player", "Player not PlayerController")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: adv_non_blocking_input_processed_after_detach_and_recall_start — no valid physics space for CharacterBody2D")
		root.free()
		return
	_cleanup_input()

	Input.action_press("move_right")
	_pulse_detach(player, 0.016)
	if player._chunk_node != null and is_instance_valid(player._chunk_node):
		Input.action_press("detach")
		player._physics_process(0.016)
		Input.action_release("detach")
	var vx: float = player.velocity.x
	_assert_true(vx > 0.0, "adv_nb_velocity_positive_after_detach_and_recall_start")
	_cleanup_input()
	root.free()


func run_all() -> int:
	print("--- test_detach_recall_fx_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_rapid_detach_press_only_emits_detach_fired_once_per_logical_detach()
	test_adv_recall_cancel_chunk_destroyed_before_reabsorb_does_not_emit_chunk_reabsorbed()
	test_adv_recall_pressed_with_no_chunk_does_not_emit_recall_started()
	test_adv_signal_ordering_preserved_over_full_cycle()
	test_adv_non_blocking_input_processed_after_detach_and_recall_start()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
