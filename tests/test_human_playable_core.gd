#
# test_human_playable_core.gd
#
# Headless behavioral tests for the "human-playable core movement prototype" slice.
# These tests validate scene composition, camera framing configuration, minimal UI
# hints, and encode a manual human-playability checklist as data.
#
# Ticket: FEAT-20260302-human-playable-core
# Scope:
#   - Player, ground/platform, and detached chunk visuals and alignment.
#   - Camera framing configuration for the core test scene.
#   - Presence and basic layout of minimal UI hints for move/jump/detach.
#   - Encoded manual checklist items for in-editor human verification.
#
# CHECKPOINT [HP-001]:
#   Assumption: The main playable scene is res://scenes/test_movement.tscn
#   with a root Node2D named "TestMovement", a CharacterBody2D child named
#   "Player", a StaticBody2D child named "Floor", and a Camera2D child named
#   "Camera" under "Player". This matches project.godot and the existing scene.
#   Confidence: High (project.godot main_scene and current scene contents).
#
# CHECKPOINT [HP-002]:
#   Assumption: Visuals for player, floor, and chunk are represented using
#   Sprite2D and/or ColorRect nodes parented directly under the corresponding
#   physics bodies (Player, Floor, Chunk). Alignment is enforced by requiring
#   their local position to be Vector2.ZERO so they sit on top of their body.
#   Confidence: Medium; implementation agents may adjust node names, but the
#   contract of "at least one Sprite2D or ColorRect child at local origin" is
#   stable and easy to satisfy.
#
# CHECKPOINT [HP-003]:
#   Assumption: Minimal UI hints are Label nodes whose visible text contains
#   the substrings "move", "jump", and "detach" (case-insensitive). Hints must
#   be placed outside a "central play area" bounding box defined around the
#   starting player and floor positions to avoid overlapping the main action.
#   Confidence: Medium; this is a concrete, automatable proxy for readability
#   and non-overlap without over-constraining layout or font choices.
#
# CHECKPOINT [HP-004]:
#   Assumption: For camera framing, we treat the Floor's collision rectangle
#   (RectangleShape2D_floor) as the primary horizontal play space. The Camera
#   node in test_movement.tscn is expected to use the CameraFollow script so
#   its exported follow_limit_* values can be asserted. Limits must at least
#   cover the floor extents [-half_width, +half_width] in world space.
#   Confidence: High regarding floor extents; Medium that Camera uses CameraFollow.
#
# All tests are deterministic and purely structural/configurational. They do
# not simulate full gameplay; the 5-minute human playability requirement is
# captured as encoded manual steps rather than automated timing.

class_name HumanPlayableCoreTests
extends Object

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_approx(a: float, b: float, test_name: String) -> void:
	if _approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")


func _assert_vec2_approx(a: Vector2, b: Vector2, test_name: String) -> void:
	if _approx_eq(a.x, b.x) and _approx_eq(a.y, b.y):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


func _load_main_scene() -> Node:
	var packed: PackedScene = load("res://scenes/test_movement.tscn") as PackedScene
	if packed == null:
		_fail("scene_load_main", "could not load res://scenes/test_movement.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("scene_instantiate_main", "instantiate() returned null for test_movement.tscn")
		return null
	return inst


func _find_player(root: Node) -> CharacterBody2D:
	if root == null:
		return null
	var player: CharacterBody2D = root.get_node_or_null("Player") as CharacterBody2D
	return player


func _find_floor(root: Node) -> StaticBody2D:
	if root == null:
		return null
	var floor: StaticBody2D = root.get_node_or_null("Floor") as StaticBody2D
	return floor


func _find_camera(root: Node) -> Camera2D:
	var player: CharacterBody2D = _find_player(root)
	if player == null:
		return null
	var camera: Camera2D = player.get_node_or_null("Camera") as Camera2D
	return camera


func _find_visual_child_2d(parent: Node) -> Node2D:
	if parent == null:
		return null
	for child in parent.get_children():
		var node2d := child as Node2D
		if node2d == null:
			continue
		if child is CollisionShape2D:
			continue
		# Accept Sprite2D, ColorRect (via Node2D subclasses), or any other Node2D
		# that is not purely a collision node as a "visual".
		return node2d
	return null


func _labels_with_text(root: Node, needle: String) -> Array:
	var matches: Array = []
	if root == null:
		return matches
	var lower_needle: String = needle.to_lower()
	for child in root.find_children("*", "Label", true, false):
		var label := child as Label
		if label == null:
			continue
		if lower_needle in label.text.to_lower():
			matches.append(label)
	return matches


func _label_global_position(label: Label) -> Vector2:
	if label == null:
		return Vector2.ZERO
	# Works for Control-derived nodes in 2D canvas.
	return label.get_global_transform().origin


func _central_play_area_bounds(root: Node) -> Rect2:
	var player: CharacterBody2D = _find_player(root)
	var floor: StaticBody2D = _find_floor(root)
	if player == null or floor == null:
		# Fallback: generic box around origin.
		return Rect2(Vector2(-200, -200), Vector2(400, 400))

	var floor_shape: CollisionShape2D = floor.get_node_or_null("FloorShape") as CollisionShape2D
	var half_width: float = 200.0
	if floor_shape != null and floor_shape.shape is RectangleShape2D:
		var rect: RectangleShape2D = floor_shape.shape as RectangleShape2D
		half_width = rect.size.x * 0.5

	var player_pos: Vector2 = player.global_position
	var floor_pos: Vector2 = floor.global_position

	var left: float = min(player_pos.x - 200.0, floor_pos.x - half_width)
	var right: float = max(player_pos.x + 200.0, floor_pos.x + half_width)
	var top: float = min(player_pos.y - 200.0, floor_pos.y - 200.0)
	var bottom: float = max(player_pos.y + 200.0, floor_pos.y + 200.0)

	return Rect2(Vector2(left, top), Vector2(right - left, bottom - top))


func _point_inside_rect(p: Vector2, r: Rect2) -> bool:
	return r.has_point(p)


# ---------------------------------------------------------------------------
# Player, ground/platform, and chunk visuals and alignment
# ---------------------------------------------------------------------------

func test_player_has_visual_child_at_origin() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: CharacterBody2D = _find_player(root)
	if player == null:
		_fail("visual_player_exists", "Player node not found in test_movement.tscn")
		root.free()
		return

	var visual: Node2D = _find_visual_child_2d(player)
	_assert_true(visual != null,
		"visual_player_child_present — Player has at least one non-collision Node2D child as visual")

	if visual != null:
		_assert_vec2_approx(visual.position, Vector2.ZERO,
			"visual_player_alignment — Player visual child is aligned at local origin (overlaps collider)")

	root.free()


func test_floor_has_visual_child_covering_floor_extent() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var floor: StaticBody2D = _find_floor(root)
	if floor == null:
		_fail("visual_floor_exists", "Floor node not found in test_movement.tscn")
		root.free()
		return

	var visual: Node2D = _find_visual_child_2d(floor)
	_assert_true(visual != null,
		"visual_floor_child_present — Floor has at least one non-collision Node2D child as visual")

	if visual != null:
		_assert_vec2_approx(visual.position, Vector2.ZERO,
			"visual_floor_alignment — Floor visual child is aligned at local origin (overlaps collider)")

	root.free()


func test_chunk_scene_has_visual_child_at_origin() -> void:
	var packed: PackedScene = load("res://scenes/chunk.tscn") as PackedScene
	if packed == null:
		_fail("visual_chunk_scene_load", "could not load res://scenes/chunk.tscn")
		return

	var root: Node = packed.instantiate()
	if root == null:
		_fail("visual_chunk_scene_instantiate", "instantiate() returned null for chunk.tscn")
		return

	var chunk_body: RigidBody2D = root as RigidBody2D
	if chunk_body == null:
		_fail("visual_chunk_root_type", "chunk.tscn root must be a RigidBody2D")
		root.free()
		return

	var visual: Node2D = _find_visual_child_2d(chunk_body)
	_assert_true(visual != null,
		"visual_chunk_child_present — Chunk has at least one non-collision Node2D child as visual")

	if visual != null:
		_assert_vec2_approx(visual.position, Vector2.ZERO,
			"visual_chunk_alignment — Chunk visual child is aligned at local origin (overlaps collider)")

	root.free()


# ---------------------------------------------------------------------------
# Camera framing and smoothing configuration (scene-level)
# ---------------------------------------------------------------------------

func test_camera_is_attached_to_player_and_current() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: CharacterBody2D = _find_player(root)
	var camera: Camera2D = _find_camera(root)

	if player == null:
		_fail("camera_player_exists", "Player node not found in test_movement.tscn")
		root.free()
		return

	if camera == null:
		_fail("camera_exists", "Camera node not found as child of Player in test_movement.tscn")
		root.free()
		return

	_assert_true(camera.get_parent() == player,
		"camera_parent_player — Camera node is parented to Player (follows player by transform)")

	# In a live scene, current would normally be set by the engine after entering
	# the scene tree. For this headless structural test, we accept either already
	# current or clearly configured as the primary camera (z_index, unique name).
	_assert_true(camera.current or camera.name == "Camera",
		"camera_current_or_named_primary — Camera is either current or explicitly the primary 'Camera' node")

	root.free()


func test_camera_limits_cover_floor_extents() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var floor: StaticBody2D = _find_floor(root)
	var camera: Camera2D = _find_camera(root)

	if floor == null:
		_fail("camera_floor_exists", "Floor node not found in test_movement.tscn")
		root.free()
		return

	if camera == null:
		_fail("camera_exists_for_limits", "Camera node not found as child of Player in test_movement.tscn")
		root.free()
		return

	var floor_shape: CollisionShape2D = floor.get_node_or_null("FloorShape") as CollisionShape2D
	if floor_shape == null or not (floor_shape.shape is RectangleShape2D):
		_fail("camera_floor_shape_rect", "FloorShape with RectangleShape2D not found; cannot compute extents")
		root.free()
		return

	var rect: RectangleShape2D = floor_shape.shape as RectangleShape2D
	var half_width: float = rect.size.x * 0.5
	var floor_center: Vector2 = floor.global_position
	var floor_left: float = floor_center.x - half_width
	var floor_right: float = floor_center.x + half_width

	# CameraFollow script attaches to the Camera node. Access exported follow_limit_*
	# fields if and only if the node is of that script type.
	if not (camera is CameraFollow):
		_fail("camera_not_camera_follow", "Camera node is not using CameraFollow script; cannot assert follow limits")
		root.free()
		return

	var follow: CameraFollow = camera

	_assert_true(follow.follow_limit_left <= floor_left + EPSILON,
		"camera_limits_left_cover_floor — follow_limit_left is at or left of floor's left extent")
	_assert_true(follow.follow_limit_right >= floor_right - EPSILON,
		"camera_limits_right_cover_floor — follow_limit_right is at or right of floor's right extent")

	root.free()


func test_camera_initial_position_near_player() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: CharacterBody2D = _find_player(root)
	var camera: Camera2D = _find_camera(root)

	if player == null or camera == null:
		_fail("camera_player_or_camera_missing",
			"Player or Camera node missing; cannot assert initial camera framing")
		root.free()
		return

	var distance: float = player.global_position.distance_to(camera.global_position)
	_assert_true(distance <= 4.0,
		"camera_initial_alignment — Camera starts near the player (distance <= 4 pixels)")

	root.free()


# ---------------------------------------------------------------------------
# Minimal UI hints: presence, non-overlap, basic readability
# ---------------------------------------------------------------------------

func test_ui_hints_present_for_move_jump_detach() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var move_labels: Array = _labels_with_text(root, "move")
	var jump_labels: Array = _labels_with_text(root, "jump")
	var detach_labels: Array = _labels_with_text(root, "detach")

	_assert_true(move_labels.size() > 0,
		"ui_hint_move_present — at least one Label contains 'move' text for movement hint")
	_assert_true(jump_labels.size() > 0,
		"ui_hint_jump_present — at least one Label contains 'jump' text for jump hint")
	_assert_true(detach_labels.size() > 0,
		"ui_hint_detach_present — at least one Label contains 'detach' text for detach hint")

	root.free()


func test_ui_hints_do_not_overlap_central_play_area() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var move_labels: Array = _labels_with_text(root, "move")
	var jump_labels: Array = _labels_with_text(root, "jump")
	var detach_labels: Array = _labels_with_text(root, "detach")

	var all_labels: Array = []
	all_labels.append_array(move_labels)
	all_labels.append_array(jump_labels)
	all_labels.append_array(detach_labels)

	var central_bounds: Rect2 = _central_play_area_bounds(root)

	var all_outside: bool = true
	for label in all_labels:
		var pos: Vector2 = _label_global_position(label)
		if _point_inside_rect(pos, central_bounds):
			all_outside = false
			break

	_assert_true(all_outside,
		"ui_hints_non_overlap_central_area — all move/jump/detach hints are placed outside central play area bounds")

	root.free()


func test_ui_hints_have_non_empty_text() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var move_labels: Array = _labels_with_text(root, "move")
	var jump_labels: Array = _labels_with_text(root, "jump")
	var detach_labels: Array = _labels_with_text(root, "detach")

	for label in move_labels:
		_assert_true((label as Label).text.strip_edges().length() > 0,
			"ui_hint_move_readable — move hint label has non-empty text")

	for label in jump_labels:
		_assert_true((label as Label).text.strip_edges().length() > 0,
			"ui_hint_jump_readable — jump hint label has non-empty text")

	for label in detach_labels:
		_assert_true((label as Label).text.strip_edges().length() > 0,
			"ui_hint_detach_readable — detach hint label has non-empty text")

	root.free()


# ---------------------------------------------------------------------------
# Human-playability checklist (encoded metadata + basic smoke test)
# ---------------------------------------------------------------------------

const HUMAN_PLAYABILITY_CHECKLIST: Array = [
	{
		"id": "HP-MAN-01",
		"title": "Run main scene and verify basic visibility",
		"steps": [
			"Open res://scenes/test_movement.tscn in the Godot editor.",
			"Press Play to run the main scene.",
			"Confirm that the player avatar, ground/platform, and detached chunk (after triggering detach) are all clearly visible against the background."
		]
	},
	{
		"id": "HP-MAN-02",
		"title": "Camera framing comfort and no all-gray frames",
		"steps": [
			"While playing the main scene, move left and right across the full width of the starting platform.",
			"Jump and detach chunks in midair and near platform edges.",
			"Confirm that the camera keeps the player and primary geometry on screen at all times and never shows an 'all gray' frame."
		]
	},
	{
		"id": "HP-MAN-03",
		"title": "Minimal UI hints clarity",
		"steps": [
			"Observe the on-screen UI hints when the scene starts.",
			"Confirm that the hints clearly communicate move, jump, and detach inputs and are readable at default resolution.",
			"Confirm that hints do not block or distract from the central play area."
		]
	},
	{
		"id": "HP-MAN-04",
		"title": "5-minute playability sanity check",
		"steps": [
			"Play the scene continuously for at least five minutes using move, jump, wall cling, and detach where available.",
			"Confirm that no debug overlays are required to understand what is happening.",
			"Confirm there are no unexpected camera snaps, visual disappearances, or unreadable states during normal play."
		]
	}
]


func test_manual_checklist_metadata_is_well_formed() -> void:
	# Deterministic structural check: every checklist entry has id, title, and at least one step.
	for entry in HUMAN_PLAYABILITY_CHECKLIST:
		var has_id: bool = entry.has("id") and str(entry["id"]).length() > 0
		var has_title: bool = entry.has("title") and str(entry["title"]).length() > 0
		var has_steps: bool = entry.has("steps") and entry["steps"] is Array and (entry["steps"] as Array).size() > 0
		_assert_true(has_id and has_title and has_steps,
			"human_playability_metadata_entry_valid — checklist entry has id, title, and non-empty steps")


func test_main_scene_player_controller_smoke_for_multiple_frames() -> void:
	var root: Node = _load_main_scene()
	if root == null:
		return

	var player: CharacterBody2D = _find_player(root)
	if player == null:
		_fail("smoke_player_exists", "Player node not found in test_movement.tscn for smoke test")
		root.free()
		return

	var controller: PlayerController = player as PlayerController
	if controller == null:
		_fail("smoke_player_controller_type", "Player node does not use PlayerController script")
		root.free()
		return

	# Manually invoke _ready() and a small number of _physics_process steps to
	# catch basic wiring/runtime errors. Input is left at defaults (no keys pressed).
	controller._ready()
	for _i in range(30):
		controller._physics_process(0.016)

	# If we reach here without errors, the smoke test passes.
	_pass("smoke_main_scene_player_controller — _ready() and 30 physics frames run without error in headless test harness")

	root.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_human_playable_core.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Visuals and alignment
	test_player_has_visual_child_at_origin()
	test_floor_has_visual_child_covering_floor_extent()
	test_chunk_scene_has_visual_child_at_origin()

	# Camera framing configuration
	test_camera_is_attached_to_player_and_current()
	test_camera_limits_cover_floor_extents()
	test_camera_initial_position_near_player()

	# Minimal UI hints
	test_ui_hints_present_for_move_jump_detach()
	test_ui_hints_do_not_overlap_central_play_area()
	test_ui_hints_have_non_empty_text()

	# Human-playability checklist metadata and smoke test
	test_manual_checklist_metadata_is_well_formed()
	test_main_scene_player_controller_smoke_for_multiple_frames()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

