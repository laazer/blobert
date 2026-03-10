#
# test_detach_recall_fx.gd
#
# Primary deterministic behavioral tests for Detach & Recall visual feedback.
# Focus:
#   - DRF-4: PlayerController signal contract (names, signatures, emit points, ordering).
#   - DRF-1/2/3: Presentation layer reacts in a headless-verifiable way via a
#     small "test state" hook (see CHECKPOINTS.md [detach_recall_fx]).
#   - DRF-NF1: Non-blocking: movement/input continue to behave during these cues.
#
# Spec: agent_context/projects/blobert/specs/detach_recall_fx_spec.md
#

class_name DetachRecallFxTests
extends Object

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _approx_eq(a: float, b: float) -> bool:
	return abs(a - b) < EPSILON


func _vec2_approx_eq(a: Vector2, b: Vector2) -> bool:
	return _approx_eq(a.x, b.x) and _approx_eq(a.y, b.y)


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


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_vec2_approx(a: Vector2, b: Vector2, test_name: String) -> void:
	if _vec2_approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


func _cleanup_input() -> void:
	Input.action_release("move_left")
	Input.action_release("move_right")
	Input.action_release("jump")
	Input.action_release("detach")


func _load_main_scene() -> Node:
	var packed: PackedScene = load("res://scenes/levels/test_movement.tscn") as PackedScene
	if packed == null:
		_fail("fx_scene_load_main", "could not load res://scenes/levels/test_movement.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("fx_scene_instantiate_main", "instantiate() returned null for test_movement.tscn")
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


func _find_fx_presenter(root: Node) -> Node:
	# Spec requires presentation to be testable. We enforce a minimal hook:
	# a node implementing get_detach_recall_fx_test_state() -> Dictionary.
	if root == null:
		return null
	for node in root.find_children("*", "", true, false):
		var n := node as Node
		if n != null and n.has_method("get_detach_recall_fx_test_state"):
			return n
	return null


func _get_fx_state(presenter: Node) -> Dictionary:
	if presenter == null:
		return {}
	var raw: Variant = presenter.call("get_detach_recall_fx_test_state")
	if raw is Dictionary:
		return raw as Dictionary
	return {}


func _signal_args_for(target: Object, signal_name: String) -> Array:
	for d in target.get_signal_list():
		if d.has("name") and d["name"] == signal_name:
			if d.has("args") and d["args"] is Array:
				return d["args"]
			return []
	return []


# ---------------------------------------------------------------------------
# DRF-4 — Signal contract: declaration and signature
# ---------------------------------------------------------------------------

func test_drf4_signals_declared_with_vector2_vector2_signatures() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf4_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var expected_signals: Array[String] = ["detach_fired", "recall_started", "chunk_reabsorbed"]
	var all_present: bool = true
	for s in expected_signals:
		if not player.has_signal(s):
			all_present = false
			_fail("drf4_signal_declared_" + s, "PlayerController must declare signal '" + s + "'")
			continue

		var args: Array = _signal_args_for(player, s)
		_assert_true(args.size() == 2, "drf4_signal_arg_count_" + s + " — expected 2 args (player_position, chunk_position)")
		if args.size() == 2:
			var a0: Dictionary = args[0]
			var a1: Dictionary = args[1]
			var t0_ok: bool = a0.has("type") and int(a0["type"]) == TYPE_VECTOR2
			var t1_ok: bool = a1.has("type") and int(a1["type"]) == TYPE_VECTOR2
			_assert_true(t0_ok and t1_ok, "drf4_signal_arg_types_" + s + " — both args are Vector2")

	_assert_true(all_present, "drf4_all_three_signals_present")
	root.free()


# ---------------------------------------------------------------------------
# DRF-4 — Emit points and argument semantics
# ---------------------------------------------------------------------------

func test_drf4_detach_fired_emitted_once_on_successful_detach_and_positions_equal() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf4_detach_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: drf4_detach_fired_emitted_once_on_successful_detach_and_positions_equal — no valid physics space for CharacterBody2D")
		root.free()
		return
	_cleanup_input()

	if not player.has_signal("detach_fired"):
		_fail("drf4_detach_signal_missing", "PlayerController must declare signal detach_fired(Vector2, Vector2)")
		root.free()
		return

	var count: int = 0
	var got_player_pos: Vector2 = Vector2.INF
	var got_chunk_pos: Vector2 = Vector2.INF

	player.detach_fired.connect(func(pp: Vector2, cp: Vector2) -> void:
		count += 1
		got_player_pos = pp
		got_chunk_pos = cp
	)

	_pulse_detach(player, 0.016)

	_assert_true(count == 1, "drf4_detach_emitted_once_per_detach")
	_assert_true(player._chunk_node != null and is_instance_valid(player._chunk_node),
		"drf4_detach_chunk_spawned_and_valid_on_success_path")

	# Contract: on detach frame, chunk spawns at player position so arguments match.
	_assert_vec2_approx(got_player_pos, got_chunk_pos, "drf4_detach_args_equal_on_spawn_frame")
	_assert_vec2_approx(got_player_pos, player.global_position, "drf4_detach_player_position_matches_global_position")
	if player._chunk_node != null and is_instance_valid(player._chunk_node):
		_assert_vec2_approx(got_chunk_pos, player._chunk_node.global_position, "drf4_detach_chunk_position_matches_chunk_global_position")

	root.free()


func test_drf4_recall_started_emitted_once_when_recall_begins_with_current_positions() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf4_recall_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: drf4_recall_started_emitted_once_when_recall_begins_with_current_positions — no valid physics space for CharacterBody2D")
		root.free()
		return
	_cleanup_input()

	if not player.has_signal("recall_started"):
		_fail("drf4_recall_signal_missing", "PlayerController must declare signal recall_started(Vector2, Vector2)")
		root.free()
		return

	# Arrange: detach once to create a chunk and set has_chunk=false.
	_pulse_detach(player, 0.016)
	if player._chunk_node == null or not is_instance_valid(player._chunk_node):
		_fail("drf4_recall_requires_chunk", "Detach did not spawn a valid chunk; cannot test recall_started")
		root.free()
		return

	player._recall_in_progress = false

	var count: int = 0
	var got_player_pos: Vector2 = Vector2.INF
	var got_chunk_pos: Vector2 = Vector2.INF
	var chunk_pos_at_callback: Vector2 = Vector2.INF

	player.recall_started.connect(func(pp: Vector2, cp: Vector2) -> void:
		count += 1
		got_player_pos = pp
		got_chunk_pos = cp
		if player._chunk_node != null and is_instance_valid(player._chunk_node):
			chunk_pos_at_callback = player._chunk_node.global_position
	)

	# Act: pulse detach again to start recall.
	_cleanup_input()
	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")

	_assert_true(count == 1, "drf4_recall_started_emitted_once_on_begin")
	_assert_true(player._recall_in_progress, "drf4_recall_in_progress_flag_set_on_begin")
	_assert_vec2_approx(got_player_pos, player.global_position, "drf4_recall_player_position_matches_global_position")
	# Contract: chunk_position is the current chunk global position on that frame.
	_assert_vec2_approx(got_chunk_pos, chunk_pos_at_callback, "drf4_recall_chunk_position_matches_current_chunk_global_position")

	root.free()


func test_drf4_chunk_reabsorbed_emitted_once_before_chunk_is_queued_for_free() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf4_reabsorb_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: drf4_chunk_reabsorbed_emitted_once_before_chunk_is_queued_for_free — no valid physics space for CharacterBody2D")
		root.free()
		return
	_cleanup_input()

	if not player.has_signal("chunk_reabsorbed"):
		_fail("drf4_reabsorb_signal_missing", "PlayerController must declare signal chunk_reabsorbed(Vector2, Vector2)")
		root.free()
		return

	# Arrange: detach to create a chunk.
	_pulse_detach(player, 0.016)
	if player._chunk_node == null or not is_instance_valid(player._chunk_node):
		_fail("drf4_reabsorb_requires_chunk", "Detach did not spawn a valid chunk; cannot test chunk_reabsorbed")
		root.free()
		return

	# Deterministic: force recall completion on the next frame.
	player._recall_in_progress = true
	player._recall_timer = player._RECALL_TRAVEL_TIME - 0.016

	var count: int = 0
	var callback_chunk_node_valid: bool = false
	var callback_chunk_node_not_queued: bool = false

	player.chunk_reabsorbed.connect(func(_pp: Vector2, _cp: Vector2) -> void:
		count += 1
		if player._chunk_node != null and is_instance_valid(player._chunk_node):
			callback_chunk_node_valid = true
			callback_chunk_node_not_queued = not player._chunk_node.is_queued_for_deletion()
	)

	_cleanup_input()
	player._physics_process(0.016)

	_assert_true(count == 1, "drf4_chunk_reabsorbed_emitted_once_on_successful_reabsorb")
	_assert_true(callback_chunk_node_valid, "drf4_chunk_reabsorbed_callback_chunk_valid")
	_assert_true(callback_chunk_node_not_queued, "drf4_chunk_reabsorbed_emitted_before_queue_free")
	_assert_true(player._chunk_node == null or not is_instance_valid(player._chunk_node),
		"drf4_after_reabsorb_chunk_node_cleared_or_freed")

	root.free()


func test_drf4_signal_ordering_detach_then_recall_started_then_chunk_reabsorbed() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf4_order_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()
	_cleanup_input()

	var required: Array[String] = ["detach_fired", "recall_started", "chunk_reabsorbed"]
	for s in required:
		if not player.has_signal(s):
			_fail("drf4_order_signal_missing_" + s, "PlayerController must declare signal '" + s + "' to test ordering")
			root.free()
			return

	var order: Array[String] = []
	player.detach_fired.connect(func(_pp: Vector2, _cp: Vector2) -> void: order.append("detach_fired"))
	player.recall_started.connect(func(_pp: Vector2, _cp: Vector2) -> void: order.append("recall_started"))
	player.chunk_reabsorbed.connect(func(_pp: Vector2, _cp: Vector2) -> void: order.append("chunk_reabsorbed"))

	# Detach.
	_pulse_detach(player, 0.016)

	# Recall start.
	_cleanup_input()
	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")

	# Force reabsorb next frame.
	player._recall_in_progress = true
	player._recall_timer = player._RECALL_TRAVEL_TIME - 0.016
	_cleanup_input()
	player._physics_process(0.016)

	var ok: bool = order.size() == 3 and order[0] == "detach_fired" and order[1] == "recall_started" and order[2] == "chunk_reabsorbed"
	_assert_true(ok, "drf4_ordering_detach_recall_started_reabsorb")

	root.free()


# ---------------------------------------------------------------------------
# DRF-1/2/3 — Presentation reaction is headless-verifiable
# ---------------------------------------------------------------------------

func test_drf1_presentation_records_detach_cue_trigger() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf1_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: drf1_presentation_records_detach_cue_trigger — no valid physics space for CharacterBody2D")
		root.free()
		return

	var presenter: Node = _find_fx_presenter(root)
	_assert_true(presenter != null, "drf1_presenter_exists_with_test_hook")
	if presenter == null:
		root.free()
		return

	if not player.has_signal("detach_fired"):
		_fail("drf1_signal_missing_detach_fired", "detach_fired signal missing; cannot verify presentation response")
		root.free()
		return

	var before: Dictionary = _get_fx_state(presenter)
	var before_flag: bool = before.has("detach_triggered") and bool(before["detach_triggered"])
	_assert_false(before_flag, "drf1_detach_triggered_initially_false")

	_pulse_detach(player, 0.016)

	var after: Dictionary = _get_fx_state(presenter)
	var after_flag: bool = after.has("detach_triggered") and bool(after["detach_triggered"])
	_assert_true(after_flag, "drf1_detach_triggered_flips_true_after_detach_fired")
	if after.has("last_event"):
		_assert_true(str(after["last_event"]) == "detach", "drf1_last_event_is_detach_if_present")

	root.free()


func test_drf2_presentation_records_recall_started_cue_trigger() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf2_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: drf2_presentation_records_recall_started_cue_trigger — no valid physics space for CharacterBody2D")
		root.free()
		return

	var presenter: Node = _find_fx_presenter(root)
	_assert_true(presenter != null, "drf2_presenter_exists_with_test_hook")
	if presenter == null:
		root.free()
		return

	if not player.has_signal("recall_started"):
		_fail("drf2_signal_missing_recall_started", "recall_started signal missing; cannot verify presentation response")
		root.free()
		return

	# Ensure we can trigger recall start.
	_pulse_detach(player, 0.016)
	if player._chunk_node == null or not is_instance_valid(player._chunk_node):
		_fail("drf2_requires_chunk", "Detach did not spawn a valid chunk; cannot trigger recall_started")
		root.free()
		return

	var before: Dictionary = _get_fx_state(presenter)
	var before_flag: bool = before.has("recall_started_triggered") and bool(before["recall_started_triggered"])
	_assert_false(before_flag, "drf2_recall_started_triggered_initially_false")

	_cleanup_input()
	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")

	var after: Dictionary = _get_fx_state(presenter)
	var after_flag: bool = after.has("recall_started_triggered") and bool(after["recall_started_triggered"])
	_assert_true(after_flag, "drf2_recall_started_triggered_flips_true_after_recall_started")
	if after.has("last_event"):
		_assert_true(str(after["last_event"]) == "recall_started", "drf2_last_event_is_recall_started_if_present")

	root.free()


func test_drf3_presentation_records_reabsorb_cue_trigger() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf3_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()

	var world_2d: World2D = player.get_world_2d()
	if world_2d == null or not world_2d.space.is_valid():
		print("  SKIP: drf3_presentation_records_reabsorb_cue_trigger — no valid physics space for CharacterBody2D")
		root.free()
		return

	var presenter: Node = _find_fx_presenter(root)
	_assert_true(presenter != null, "drf3_presenter_exists_with_test_hook")
	if presenter == null:
		root.free()
		return

	if not player.has_signal("chunk_reabsorbed"):
		_fail("drf3_signal_missing_chunk_reabsorbed", "chunk_reabsorbed signal missing; cannot verify presentation response")
		root.free()
		return

	# Trigger a deterministic reabsorb on next frame.
	_pulse_detach(player, 0.016)
	if player._chunk_node == null or not is_instance_valid(player._chunk_node):
		_fail("drf3_requires_chunk", "Detach did not spawn a valid chunk; cannot trigger chunk_reabsorbed")
		root.free()
		return

	var before: Dictionary = _get_fx_state(presenter)
	var before_flag: bool = before.has("reabsorbed_triggered") and bool(before["reabsorbed_triggered"])
	_assert_false(before_flag, "drf3_reabsorbed_triggered_initially_false")

	player._recall_in_progress = true
	player._recall_timer = player._RECALL_TRAVEL_TIME - 0.016
	_cleanup_input()
	player._physics_process(0.016)

	var after: Dictionary = _get_fx_state(presenter)
	var after_flag: bool = after.has("reabsorbed_triggered") and bool(after["reabsorbed_triggered"])
	_assert_true(after_flag, "drf3_reabsorbed_triggered_flips_true_after_chunk_reabsorbed")
	if after.has("last_event"):
		_assert_true(str(after["last_event"]) == "chunk_reabsorbed", "drf3_last_event_is_chunk_reabsorbed_if_present")

	root.free()


# ---------------------------------------------------------------------------
# DRF-NF1 — Non-blocking proxy: movement not frozen by cues
# ---------------------------------------------------------------------------

func test_drf_nf1_detach_and_recall_do_not_zero_or_freeze_horizontal_velocity() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: PlayerController = _get_player(root)
	if player == null:
		_fail("drf_nf1_player_exists", "Player node is not a PlayerController in test_movement.tscn")
		root.free()
		return

	player._ready()
	_cleanup_input()

	# Prime movement to the right.
	Input.action_press("move_right")
	player._physics_process(0.016)
	var vx_before: float = player.velocity.x
	_assert_true(vx_before > 0.0, "drf_nf1_prime_velocity_positive")

	# Detach while holding move_right — movement must still be processed.
	Input.action_press("detach")
	player._physics_process(0.016)
	Input.action_release("detach")
	var vx_after_detach: float = player.velocity.x
	_assert_true(vx_after_detach > 0.0, "drf_nf1_detach_frame_velocity_positive")

	# Recall start (requires chunk exists) while still holding move_right.
	if player._chunk_node != null and is_instance_valid(player._chunk_node):
		Input.action_press("detach")
		player._physics_process(0.016)
		Input.action_release("detach")
		var vx_after_recall_start: float = player.velocity.x
		_assert_true(vx_after_recall_start > 0.0, "drf_nf1_recall_start_frame_velocity_positive")
	else:
		_fail("drf_nf1_requires_chunk_for_recall_start", "chunk not present after detach; cannot verify recall-start non-blocking")

	_cleanup_input()
	root.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_detach_recall_fx.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_drf4_signals_declared_with_vector2_vector2_signatures()
	test_drf4_detach_fired_emitted_once_on_successful_detach_and_positions_equal()
	test_drf4_recall_started_emitted_once_when_recall_begins_with_current_positions()
	test_drf4_chunk_reabsorbed_emitted_once_before_chunk_is_queued_for_free()
	test_drf4_signal_ordering_detach_then_recall_started_then_chunk_reabsorbed()

	test_drf1_presentation_records_detach_cue_trigger()
	test_drf2_presentation_records_recall_started_cue_trigger()
	test_drf3_presentation_records_reabsorb_cue_trigger()

	test_drf_nf1_detach_and_recall_do_not_zero_or_freeze_horizontal_velocity()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

