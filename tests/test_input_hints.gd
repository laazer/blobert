#
# test_input_hints.gd
#
# Primary behavioral tests for input hint polish across core movement and
# infection-loop scenes. These tests validate that:
#   - On-screen hints exist for move (left/right), jump, detach/recall
#     (shared input), and absorb in the infection-loop scene.
#   - Hint texts use consistent action naming (move/jump/detach/recall/absorb)
#     and are placed in HUD regions that do not overlap the central play area
#     or the HP/chunk HUD.
#   - A single global configuration toggle controls visibility of all input
#     hints in both scenes without per-scene wiring.
# 
# Ticket: input_hint_polish_core_mechanics
#

class_name InputHintsTests
extends Object


var _pass_count: int = 0
var _fail_count: int = 0


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


func _load_core_scene() -> Node:
	var packed: PackedScene = load("res://scenes/test_movement.tscn") as PackedScene
	if packed == null:
		_fail("input_hints_core_scene_load", "could not load res://scenes/test_movement.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("input_hints_core_scene_instantiate", "instantiate() returned null for test_movement.tscn")
		return null
	return inst


func _load_infection_scene() -> Node:
	var packed: PackedScene = load("res://scenes/test_infection_loop.tscn") as PackedScene
	if packed == null:
		_fail("input_hints_infection_scene_load", "could not load res://scenes/test_infection_loop.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("input_hints_infection_scene_instantiate", "instantiate() returned null for test_infection_loop.tscn")
		return null
	return inst


func _find_infection_ui(root: Node) -> CanvasLayer:
	if root == null:
		return null
	var infection_ui: CanvasLayer = root.get_node_or_null("InfectionUI") as CanvasLayer
	return infection_ui


func _labels_with_text_under_infection_ui(root: Node, needle: String) -> Array:
	var matches: Array = []
	var infection_ui: CanvasLayer = _find_infection_ui(root)
	if infection_ui == null:
		return matches
	var lower_needle: String = needle.to_lower()
	for child in infection_ui.find_children("*", "Label", true, false):
		var label := child as Label
		if label == null:
			continue
		if lower_needle in label.text.to_lower():
			matches.append(label)
	return matches


func _central_play_area_bounds_screen() -> Rect2:
	var cx: float = 640.0
	var cy: float = 360.0
	var half: float = 200.0
	return Rect2(Vector2(cx - half, cy - half), Vector2(half * 2, half * 2))


func _central_play_area_bounds(root: Node) -> Rect2:
	var player: CharacterBody2D = root.get_node_or_null("Player") as CharacterBody2D
	var floor: StaticBody2D = root.get_node_or_null("Floor") as StaticBody2D
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


func _label_global_rect(label: Label) -> Rect2:
	if label == null:
		return Rect2()
	var control := label as Control
	if control == null:
		return Rect2()
	return control.get_global_rect()


func _hp_and_chunk_hud_bounds_in_infection_scene(root: Node) -> Rect2:
	var infection_ui: CanvasLayer = _find_infection_ui(root)
	if infection_ui == null:
		return Rect2()

	var nodes: Array = []
	nodes.append(infection_ui.get_node_or_null("HPLabel"))
	nodes.append(infection_ui.get_node_or_null("ChunkStatusLabel"))
	nodes.append(infection_ui.get_node_or_null("HPBar"))

	var have_any: bool = false
	var bounds := Rect2()

	for node in nodes:
		var control := node as Control
		if control == null:
			continue
		var rect: Rect2 = control.get_global_rect()
		if not have_any:
			bounds = rect
			have_any = true
		else:
			bounds = bounds.expand(rect.position)
			bounds = bounds.expand(rect.position + rect.size)

	return bounds


func _get_input_hints_config() -> Node:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return null
	return tree.root.get_node_or_null("InputHintsConfig")


func _get_core_hint_labels(root: Node) -> Array:
	var labels: Array = []
	if root == null:
		return labels
	var hints_root: Control = root.get_node_or_null("UI/Hints") as Control
	if hints_root == null:
		return labels

	var move_hint: Label = hints_root.get_node_or_null("MoveHint") as Label
	var jump_hint: Label = hints_root.get_node_or_null("JumpHint") as Label
	var detach_hint: Label = hints_root.get_node_or_null("DetachHint") as Label

	if move_hint != null:
		labels.append(move_hint)
	if jump_hint != null:
		labels.append(jump_hint)
	if detach_hint != null:
		labels.append(detach_hint)

	return labels


# ---------------------------------------------------------------------------
# Structural presence: infection-loop input hints for all core actions
# ---------------------------------------------------------------------------

func test_infection_scene_has_input_hints_for_all_core_actions() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var move_labels: Array = _labels_with_text_under_infection_ui(root, "move")
	var jump_labels: Array = _labels_with_text_under_infection_ui(root, "jump")
	var detach_labels: Array = _labels_with_text_under_infection_ui(root, "detach")
	var recall_labels: Array = _labels_with_text_under_infection_ui(root, "recall")
	var absorb_labels: Array = _labels_with_text_under_infection_ui(root, "absorb")

	_assert_true(move_labels.size() > 0,
		"input_hints_infection_move_hint_present — at least one InfectionUI label contains 'move' text")
	_assert_true(jump_labels.size() > 0,
		"input_hints_infection_jump_hint_present — at least one InfectionUI label contains 'jump' text")

	var detach_recall_ok: bool = false
	for label in detach_labels:
		var text_lower: String = (label as Label).text.to_lower()
		if "recall" in text_lower:
			detach_recall_ok = true
			break
	if not detach_recall_ok:
		for label in recall_labels:
			var text_lower: String = (label as Label).text.to_lower()
			if "detach" in text_lower:
				detach_recall_ok = true
				break

	_assert_true(detach_recall_ok,
		"input_hints_infection_detach_recall_shared_hint_present — at least one InfectionUI label references both detach and recall")

	_assert_true(absorb_labels.size() > 0,
		"input_hints_infection_absorb_hint_present — at least one InfectionUI label contains 'absorb' text")

	root.free()


# ---------------------------------------------------------------------------
# Layout: infection-loop hints avoid central play area and HP/chunk HUD
# ---------------------------------------------------------------------------

func test_infection_input_hints_respect_central_play_area_and_hud_safe_zones() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	# Hint labels are under CanvasLayer; use screen-space central bounds.
	var central_bounds: Rect2 = _central_play_area_bounds_screen()
	var hud_bounds: Rect2 = _hp_and_chunk_hud_bounds_in_infection_scene(root)
	var has_hud_bounds: bool = hud_bounds.size.length() > 0.0

	var keywords: Array = ["move", "jump", "detach", "recall", "absorb"]
	var all_outside: bool = true
	var all_outside_hud: bool = true

	for keyword in keywords:
		var labels: Array = _labels_with_text_under_infection_ui(root, keyword)
		for label in labels:
			var rect: Rect2 = _label_global_rect(label as Label)
			if central_bounds.intersects(rect):
				all_outside = false
				break
			if has_hud_bounds and hud_bounds.intersects(rect):
				all_outside_hud = false
				break
		if not all_outside or not all_outside_hud:
			break

	_assert_true(all_outside,
		"input_hints_infection_outside_central_area — infection input hints do not overlap central play area bounds")
	_assert_true(all_outside_hud,
		"input_hints_infection_outside_hud_area — infection input hints do not overlap HP/chunk HUD bounds")

	root.free()


func test_infection_input_hints_are_readable_when_visible() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var keywords: Array = ["move", "jump", "detach", "recall", "absorb"]

	for keyword in keywords:
		var labels: Array = _labels_with_text_under_infection_ui(root, keyword)
		for label in labels:
			var canvas_item := label as CanvasItem
			var alpha_ok: bool = canvas_item.modulate.a > 0.0
			_assert_true(alpha_ok,
				"input_hints_infection_" + keyword + "_alpha_non_zero — infection input hint label has modulate alpha > 0")

			var scale: Vector2 = (label as Label).scale
			var not_tiny: bool = abs(scale.x) >= 0.5 and abs(scale.y) >= 0.5
			_assert_true(not_tiny,
				"input_hints_infection_" + keyword + "_scale_not_tiny — infection input hint label scale is not effectively zero")

	root.free()


# ---------------------------------------------------------------------------
# Global toggle: InputHintsConfig gates hints in both scenes
# ---------------------------------------------------------------------------

func test_input_hints_default_visible_when_toggle_true() -> void:
	var config: Node = _get_input_hints_config()
	if config == null:
		_fail("input_hints_config_missing", "InputHintsConfig autoload not found at /root/InputHintsConfig")
		return

	if not ("input_hints_enabled" in config):
		_fail("input_hints_config_missing_flag", "InputHintsConfig must expose boolean property input_hints_enabled")
		return

	config.input_hints_enabled = true

	# Core movement scene: move/jump/detach hints should be visible when enabled.
	var core_root: Node = _load_core_scene()
	if core_root != null:
		var core_labels: Array = _get_core_hint_labels(core_root)
		for label in core_labels:
			_assert_true((label as Label).visible,
				"input_hints_core_visible_when_enabled — core movement input hints visible when global toggle is true")
		core_root.free()

	# Infection-loop scene: move/jump/detach/recall/absorb hints should be visible when enabled.
	var infection_root: Node = _load_infection_scene()
	if infection_root != null:
		var keywords: Array = ["move", "jump", "detach", "recall", "absorb"]
		for keyword in keywords:
			var labels: Array = _labels_with_text_under_infection_ui(infection_root, keyword)
			var any_visible: bool = false
			for label in labels:
				if (label as Label).visible:
					any_visible = true
					break
			_assert_true(any_visible,
				"input_hints_infection_" + keyword + "_visible_when_enabled — at least one infection hint for " + keyword + " is visible when global toggle is true")
		infection_root.free()


func test_input_hints_hidden_when_toggle_false() -> void:
	var config: Node = _get_input_hints_config()
	if config == null:
		_fail("input_hints_config_missing_for_disable", "InputHintsConfig autoload not found at /root/InputHintsConfig for disable test")
		return

	if not ("input_hints_enabled" in config):
		_fail("input_hints_config_missing_flag_for_disable", "InputHintsConfig must expose boolean property input_hints_enabled for disable test")
		return

	config.input_hints_enabled = false

	# Core movement scene: all input hints must be hidden when disabled.
	var core_root: Node = _load_core_scene()
	if core_root != null:
		var core_labels: Array = _get_core_hint_labels(core_root)
		for label in core_labels:
			_assert_false((label as Label).visible,
				"input_hints_core_hidden_when_disabled — core movement input hints hidden when global toggle is false")
		core_root.free()

	# Infection-loop scene: move/jump/detach/recall/absorb hints must all be hidden when disabled.
	var infection_root: Node = _load_infection_scene()
	if infection_root != null:
		var keywords: Array = ["move", "jump", "detach", "recall", "absorb"]
		for keyword in keywords:
			var labels: Array = _labels_with_text_under_infection_ui(infection_root, keyword)
			var any_visible: bool = false
			for label in labels:
				if (label as Label).visible:
					any_visible = true
					break
			_assert_false(any_visible,
				"input_hints_infection_" + keyword + "_hidden_when_disabled — infection input hints for " + keyword + " hidden when global toggle is false")
		infection_root.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_input_hints.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_infection_scene_has_input_hints_for_all_core_actions()
	test_infection_input_hints_respect_central_play_area_and_hud_safe_zones()
	test_infection_input_hints_are_readable_when_visible()
	test_input_hints_default_visible_when_toggle_true()
	test_input_hints_hidden_when_toggle_false()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

