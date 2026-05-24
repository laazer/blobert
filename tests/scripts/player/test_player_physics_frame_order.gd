#
# test_player_physics_frame_order.gd
#
# Primary behavioral tests for PlayerController3D physics frame order (M11-02).
# Spec: project_board/specs/player_physics_frame_order_spec.md (PFO-1..PFO-11)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/02_physics_frame_order.md
#
# Adversarial coverage: test_player_physics_frame_order_adversarial.gd (Test Breaker).
#

extends "res://tests/utils/test_utils.gd"

const PLAYER_SCENE_PATH: String = "res://scenes/player/player_3d.tscn"
const SANDBOX_SCENE_PATH: String = "res://scenes/levels/sandbox/test_movement_3d.tscn"
const FIXTURE_SCENE_PATH: String = "res://scenes/levels/sandbox/test_one_way_platform_3d.tscn"
const CONTROLLER_SCRIPT_PATH: String = "res://scripts/player/player_controller_3d.gd"

const PHYSICS_STEP: float = 1.0 / 60.0
const GROUND_MASK: int = 1
const FULL_GROUND_MASK: int = 3
const SETTLE_FRAMES: int = 90
const COYOTE_TIME_DEFAULT: float = 0.1
const JUMP_BUFFER_DEFAULT: float = 0.1
const UPWARD_VY_EPS: float = 0.35
const POS_EPS: float = 0.08
const LEDGE_SPAWN: Vector3 = Vector3(24.0, 1.0, 0.0)
const SHORT_FALL_BUMP_Y: float = 0.55

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Harness helpers
# ---------------------------------------------------------------------------

func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


func _load_player() -> CharacterBody3D:
	if not ResourceLoader.exists(PLAYER_SCENE_PATH):
		return null
	var packed: PackedScene = load(PLAYER_SCENE_PATH) as PackedScene
	if packed == null:
		return null
	return packed.instantiate() as CharacterBody3D


func _add_static_box(
	parent: Node3D,
	name: String,
	layer: int,
	center: Vector3,
	size: Vector3
) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = name
	body.collision_layer = layer
	body.collision_mask = 0
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	body.position = center
	parent.add_child(body)
	return body


func _load_sandbox_harness() -> Dictionary:
	var tree: SceneTree = _tree()
	if tree == null or tree.root == null:
		return {}
	if not ResourceLoader.exists(SANDBOX_SCENE_PATH):
		return {}
	var packed: PackedScene = load(SANDBOX_SCENE_PATH) as PackedScene
	if packed == null:
		return {}
	var root: Node3D = packed.instantiate() as Node3D
	if root == null:
		return {}
	tree.root.add_child(root)
	var player: CharacterBody3D = root.get_node_or_null("Player3D") as CharacterBody3D
	if player == null:
		tree.root.remove_child(root)
		root.free()
		return {}
	return {"tree": tree, "root": root, "player": player}


func _teardown_sandbox(harness: Dictionary) -> void:
	var root: Node = harness.get("root") as Node
	var tree: SceneTree = harness.get("tree") as SceneTree
	if root == null:
		return
	if tree != null and tree.root != null and root.is_inside_tree():
		tree.root.remove_child(root)
	root.free()


func _apply_player_props(player: CharacterBody3D, props: Dictionary) -> void:
	for key in props.keys():
		player.set(key, props[key])


func _press_jump_once() -> void:
	Input.action_press("jump")


func _hold_axis(axis: float) -> void:
	if axis < 0.0:
		Input.action_press("move_left")
		Input.action_release("move_right")
	elif axis > 0.0:
		Input.action_press("move_right")
		Input.action_release("move_left")
	else:
		Input.action_release("move_left")
		Input.action_release("move_right")


func _release_all_input() -> void:
	Input.action_release("move_left")
	Input.action_release("move_right")
	# Do not release jump here — _step_player releases jump after _physics_process so buffer tests
	# can arm jump_just_pressed on the airborne press frame.


func _step_player(player: CharacterBody3D, delta: float) -> void:
	if not player.is_node_ready():
		return
	player._physics_process(delta)
	Input.action_release("jump")


func _begin_short_fall(player: CharacterBody3D) -> bool:
	# Small drop: leave ground quickly, stay airborne long enough for 0.1s buffer after air-press.
	player.global_position.y += SHORT_FALL_BUMP_Y
	player.velocity = Vector3(0.0, -0.2, 0.0)
	for _i in range(30):
		_release_all_input()
		_step_player(player, PHYSICS_STEP)
		if not player.is_on_floor():
			return true
	return false


func _settle_on_floor(player: CharacterBody3D, spawn: Vector3) -> bool:
	if not player.is_inside_tree():
		return false
	player.position = spawn
	player.velocity = Vector3.ZERO
	for _i in range(SETTLE_FRAMES):
		_release_all_input()
		_step_player(player, PHYSICS_STEP)
	return player.is_on_floor()


func _player_vy(player: CharacterBody3D) -> float:
	return (player.velocity as Vector3).y


func _fail_missing_api(test_name: String, detail: String) -> void:
	_fail(test_name, detail + " — implement per player_physics_frame_order_spec.md")


# ---------------------------------------------------------------------------
# PFO-3: Jump buffer configuration (API + behavior)
# ---------------------------------------------------------------------------

func test_pfo3_jump_buffer_time_export_default() -> void:
	var player: CharacterBody3D = _load_player()
	if player == null:
		_fail_missing_api("pfo3_export_default", "player_3d.tscn missing")
		return
	if not ("jump_buffer_time" in player):
		_fail_missing_api(
			"pfo3_export_default",
			"@export jump_buffer_time missing on PlayerController3D"
		)
		player.free()
		return
	_assert_approx(
		float(player.get("jump_buffer_time")),
		JUMP_BUFFER_DEFAULT,
		"pfo3_jump_buffer_time_default_0_1"
	)
	player.free()


func test_pfo3_reset_hp_clears_buffered_jump_on_landing() -> void:
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo3_reset_clears_buffer", "test_movement_3d sandbox harness unavailable")
		return
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	if not ("jump_buffer_time" in player):
		_teardown_sandbox(harness)
		_fail_missing_api("pfo3_reset_clears_buffer", "jump_buffer_time export missing")
		return
	_apply_player_props(player, {"jump_buffer_time": JUMP_BUFFER_DEFAULT})
	if not _settle_on_floor(player, Vector3(0.0, 1.0, 0.0)):
		_teardown_sandbox(harness)
		_fail("pfo3_reset_clears_buffer", "player did not settle on ground")
		return
	if not _begin_short_fall(player):
		_teardown_sandbox(harness)
		_fail("pfo3_reset_clears_buffer", "could not enter short fall for buffer test")
		return
	_press_jump_once()
	player.call("reset_hp")
	for _i in range(8):
		_release_all_input()
		_step_player(player, PHYSICS_STEP)
	var landed_buffered_jump: bool = _player_vy(player) > UPWARD_VY_EPS
	_assert_false(
		landed_buffered_jump,
		"pfo3_reset_hp_clears_jump_buffer_before_landing"
	)
	_teardown_sandbox(harness)


func test_pfo3_jump_buffer_executes_jump_on_landing_after_air_press() -> void:
	# EC-1 / AC-PFO-3.4: jump while falling, land within buffer window → upward impulse on land.
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo3_buffer_landing_jump", "test_movement_3d sandbox harness unavailable")
		return
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	if not ("jump_buffer_time" in player):
		_teardown_sandbox(harness)
		_fail_missing_api("pfo3_buffer_landing_jump", "jump_buffer_time export missing")
		return
	_apply_player_props(player, {"jump_buffer_time": JUMP_BUFFER_DEFAULT})
	if not _settle_on_floor(player, Vector3(0.0, 1.0, 0.0)):
		_teardown_sandbox(harness)
		_fail("pfo3_buffer_landing_jump", "player did not settle before drop")
		return
	if not _begin_short_fall(player):
		_teardown_sandbox(harness)
		_fail("pfo3_buffer_landing_jump", "could not enter short fall for buffer test")
		return
	_press_jump_once()
	var saw_upward_on_landing: bool = false
	for _i in range(45):
		_release_all_input()
		var was_airborne: bool = not player.is_on_floor()
		_step_player(player, PHYSICS_STEP)
		if player.is_on_floor() and was_airborne and _player_vy(player) > UPWARD_VY_EPS:
			saw_upward_on_landing = true
			break
	_assert_true(
		saw_upward_on_landing,
		"pfo3_buffered_jump_fires_on_first_grounded_frame_after_air_press"
	)
	_teardown_sandbox(harness)


func test_pfo9_jump_buffer_disabled_when_export_zero() -> void:
	# EC-9 / AC-PFO-3.3: jump_buffer_time == 0 → no buffer consume on landing.
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo9_buffer_disabled_at_zero", "test_movement_3d sandbox harness unavailable")
		return
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	if not ("jump_buffer_time" in player):
		_teardown_sandbox(harness)
		_fail_missing_api("pfo9_buffer_disabled_at_zero", "jump_buffer_time export missing")
		return
	_apply_player_props(player, {"jump_buffer_time": 0.0})
	if not _settle_on_floor(player, Vector3(0.0, 1.0, 0.0)):
		_teardown_sandbox(harness)
		_fail("pfo9_buffer_disabled_at_zero", "player did not settle before drop")
		return
	if not _begin_short_fall(player):
		_teardown_sandbox(harness)
		_fail("pfo9_buffer_disabled_at_zero", "could not enter short fall for buffer test")
		return
	_press_jump_once()
	var saw_upward_on_landing: bool = false
	for _i in range(45):
		_release_all_input()
		var was_airborne: bool = not player.is_on_floor()
		_step_player(player, PHYSICS_STEP)
		if player.is_on_floor() and was_airborne and _player_vy(player) > UPWARD_VY_EPS:
			saw_upward_on_landing = true
			break
	_assert_false(
		saw_upward_on_landing,
		"pfo9_no_buffered_jump_when_jump_buffer_time_is_zero"
	)
	_teardown_sandbox(harness)


# ---------------------------------------------------------------------------
# PFO-4: Coyote time at controller boundary
# ---------------------------------------------------------------------------

func test_pfo4_coyote_jump_within_window_after_walking_off_ledge() -> void:
	# AC-PFO-4.3 / EC-3: walk off ledge, press jump within coyote_time → upward velocity.
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo4_coyote_off_ledge", "test_movement_3d sandbox harness unavailable")
		return
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	_apply_player_props(player, {"coyote_time": COYOTE_TIME_DEFAULT})
	if not _settle_on_floor(player, LEDGE_SPAWN):
		_teardown_sandbox(harness)
		_fail("pfo4_coyote_off_ledge", "player did not settle on sandbox floor")
		return
	var coyote_jump: bool = false
	for _i in range(80):
		_hold_axis(1.0)
		_step_player(player, PHYSICS_STEP)
		if not player.is_on_floor():
			_press_jump_once()
			_step_player(player, PHYSICS_STEP)
			if _player_vy(player) > UPWARD_VY_EPS:
				coyote_jump = true
			break
	_assert_true(
		coyote_jump,
		"pfo4_coyote_jump_within_0_1s_after_leaving_floor"
	)
	_teardown_sandbox(harness)


# ---------------------------------------------------------------------------
# PFO-7: One-way collision mask (behavior + test accessor)
# ---------------------------------------------------------------------------

func test_pfo7_get_one_way_collision_mask_accessor_exists() -> void:
	var player: CharacterBody3D = _load_player()
	if player == null:
		_fail_missing_api("pfo7_mask_accessor", "player_3d.tscn missing")
		return
	if not player.has_method("get_one_way_collision_mask"):
		_fail_missing_api(
			"pfo7_mask_accessor",
			"get_one_way_collision_mask() missing (PFO-7.5 test accessor)"
		)
		player.free()
		return
	_pass("pfo7_get_one_way_collision_mask_exists")
	player.free()


func test_pfo7_mask_excludes_one_way_while_ascending() -> void:
	# AC-PFO-7.1 / EC-5: velocity.y > 0 → mask == GROUND_MASK (1).
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo7_mask_ascending", "test_movement_3d sandbox harness unavailable")
		return
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	if not player.has_method("get_one_way_collision_mask"):
		_teardown_sandbox(harness)
		_fail_missing_api("pfo7_mask_ascending", "get_one_way_collision_mask() missing")
		return
	if not _settle_on_floor(player, Vector3(0.0, 1.0, 0.0)):
		_teardown_sandbox(harness)
		_fail("pfo7_mask_ascending", "player did not settle")
		return
	_press_jump_once()
	_step_player(player, PHYSICS_STEP)
	var mask_while_rising: int = int(player.call("get_one_way_collision_mask"))
	_assert_eq_int(
		GROUND_MASK,
		mask_while_rising,
		"pfo7_collision_mask_ground_only_while_velocity_y_positive"
	)
	_teardown_sandbox(harness)


func test_pfo7_mask_includes_one_way_while_falling_or_resting() -> void:
	# AC-PFO-7.4 / EC-6: velocity.y <= 0 on floor → mask includes one-way bit.
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo7_mask_descending", "test_movement_3d sandbox harness unavailable")
		return
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	if not player.has_method("get_one_way_collision_mask"):
		_teardown_sandbox(harness)
		_fail_missing_api("pfo7_mask_descending", "get_one_way_collision_mask() missing")
		return
	if not _settle_on_floor(player, Vector3(0.0, 1.0, 0.0)):
		_teardown_sandbox(harness)
		_fail("pfo7_mask_descending", "player did not settle on floor")
		return
	var mask_at_rest: int = int(player.call("get_one_way_collision_mask"))
	_assert_eq_int(
		FULL_GROUND_MASK,
		mask_at_rest,
		"pfo7_collision_mask_includes_one_way_at_rest_on_floor"
	)
	_teardown_sandbox(harness)


func test_pfo7_pass_through_one_way_from_below() -> void:
	# AC-PFO-7.2 / EC-7: ascending through one-way — no blocking collision.
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo7_pass_through_below", "test_movement_3d sandbox harness unavailable")
		return
	var root: Node3D = harness["root"] as Node3D
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	if not player.has_method("get_one_way_collision_mask"):
		_teardown_sandbox(harness)
		_fail_missing_api("pfo7_pass_through_below", "get_one_way_collision_mask() missing")
		return
	var platform_y: float = 2.5
	_add_static_box(root, "OneWayPlatform", 2, Vector3(0.0, platform_y, 0.0), Vector3(6.0, 0.25, 10.0))
	if not _settle_on_floor(player, Vector3(0.0, 1.0, 0.0)):
		_teardown_sandbox(harness)
		_fail("pfo7_pass_through_below", "player did not settle on ground")
		return
	_apply_player_props(player, {"jump_height": 150.0})
	var platform_top: float = platform_y + 0.125
	_press_jump_once()
	var passed_through: bool = false
	for _i in range(120):
		_release_all_input()
		_step_player(player, PHYSICS_STEP)
		if player.position.y > platform_top + POS_EPS:
			passed_through = true
			break
	_assert_true(
		passed_through,
		"pfo7_player_y_passes_one_way_platform_top_while_ascending"
	)
	_teardown_sandbox(harness)


func test_pfo7_lands_on_one_way_from_above() -> void:
	# AC-PFO-7.3 / EC-8: fall onto one-way → is_on_floor() true after slide.
	var harness: Dictionary = _load_sandbox_harness()
	if harness.is_empty():
		_fail("pfo7_land_from_above", "test_movement_3d sandbox harness unavailable")
		return
	var root: Node3D = harness["root"] as Node3D
	var player: CharacterBody3D = harness["player"] as CharacterBody3D
	var platform_y: float = 2.0
	_add_static_box(root, "OneWayPlatform", 2, Vector3(0.0, platform_y, 0.0), Vector3(8.0, 0.25, 10.0))
	player.position = Vector3(0.0, platform_y + 2.0, 0.0)
	player.velocity = Vector3.ZERO
	var landed_on_platform: bool = false
	for _i in range(180):
		_release_all_input()
		_step_player(player, PHYSICS_STEP)
		if player.is_on_floor() and player.position.y >= platform_y - POS_EPS:
			landed_on_platform = true
			break
	_assert_true(
		landed_on_platform,
		"pfo7_is_on_floor_true_after_falling_onto_one_way_platform"
	)
	_teardown_sandbox(harness)


# ---------------------------------------------------------------------------
# PFO-11: Test fixture scene
# ---------------------------------------------------------------------------

func test_pfo11_fixture_scene_loads_headless() -> void:
	if not ResourceLoader.exists(FIXTURE_SCENE_PATH):
		_fail_missing_api(
			"pfo11_fixture_exists",
			"fixture scene missing at " + FIXTURE_SCENE_PATH
		)
		return
	var packed: PackedScene = load(FIXTURE_SCENE_PATH) as PackedScene
	if packed == null:
		_fail("pfo11_fixture_loads", "PackedScene load returned null")
		return
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("pfo11_fixture_instantiate", "instantiate() returned null")
		return
	_assert_true(inst is Node3D, "pfo11_fixture_root_is_node3d")
	inst.free()


func test_pfo11_fixture_has_ground_and_one_way_nodes() -> void:
	if not ResourceLoader.exists(FIXTURE_SCENE_PATH):
		_fail_missing_api("pfo11_fixture_nodes", "fixture scene missing")
		return
	var packed: PackedScene = load(FIXTURE_SCENE_PATH) as PackedScene
	if packed == null:
		_fail("pfo11_fixture_nodes_load", "could not load fixture scene")
		return
	var inst: Node3D = packed.instantiate() as Node3D
	if inst == null:
		_fail("pfo11_fixture_nodes_inst", "instantiate failed")
		return
	var ground: Node = inst.get_node_or_null("Ground")
	var one_way: Node = inst.get_node_or_null("OneWayPlatform")
	_assert_true(ground != null and ground is StaticBody3D, "pfo11_fixture_has_ground_body")
	if ground is StaticBody3D:
		_assert_eq_int(1, (ground as StaticBody3D).collision_layer, "pfo11_ground_layer_bit_1")
	if one_way != null and one_way is StaticBody3D:
		_assert_eq_int(2, (one_way as StaticBody3D).collision_layer, "pfo11_one_way_layer_bit_2")
	else:
		_fail("pfo11_fixture_has_one_way_platform", "OneWayPlatform StaticBody3D missing")
	inst.free()


# ---------------------------------------------------------------------------
# PFO-10: Pipeline methods exist on controller script (structural contract)
# ---------------------------------------------------------------------------

func test_pfo10_private_pipeline_methods_declared() -> void:
	var gds: GDScript = load(CONTROLLER_SCRIPT_PATH) as GDScript
	if gds == null:
		_fail("pfo10_script_load", "could not load player_controller_3d.gd")
		return
	var src: String = gds.source_code
	var required: PackedStringArray = PackedStringArray([
		"func _tick_controller_timers",
		"func _dispatch_movement",
		"func _update_one_way_collision_mask",
		"func _sync_renderer_from_state",
	])
	for sig in required:
		if not src.contains(sig):
			_fail("pfo10_method_" + sig, "missing " + sig + " in player_controller_3d.gd")
			return
	_pass("pfo10_pipeline_private_methods_present")


func run_all() -> int:
	print("--- test_player_physics_frame_order.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_pfo3_jump_buffer_time_export_default()
	test_pfo3_reset_hp_clears_buffered_jump_on_landing()
	test_pfo3_jump_buffer_executes_jump_on_landing_after_air_press()
	test_pfo9_jump_buffer_disabled_when_export_zero()
	test_pfo4_coyote_jump_within_window_after_walking_off_ledge()
	test_pfo7_get_one_way_collision_mask_accessor_exists()
	test_pfo7_mask_excludes_one_way_while_ascending()
	test_pfo7_mask_includes_one_way_while_falling_or_resting()
	test_pfo7_pass_through_one_way_from_below()
	test_pfo7_lands_on_one_way_from_above()
	test_pfo11_fixture_scene_loads_headless()
	test_pfo11_fixture_has_ground_and_one_way_nodes()
	test_pfo10_private_pipeline_methods_declared()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
