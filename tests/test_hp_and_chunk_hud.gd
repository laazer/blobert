#
# test_hp_and_chunk_hud.gd
#
# Headless behavioral tests for the HP and chunk HUD.
# These tests validate that both the core movement scene (`test_movement.tscn`)
# and the infection-loop scene (`test_infection_loop.tscn`) expose a readable
# HP bar plus numeric value and a clear chunk attached/detached indicator,
# driven every frame from the PlayerController's `current_hp` and `has_chunk`
# fields without overlapping the central play space.
#
# Ticket: hp_and_chunk_hud.md
#

class_name HpAndChunkHudTests
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


func _load_core_scene() -> Node:
	var packed: PackedScene = load("res://scenes/test_movement.tscn") as PackedScene
	if packed == null:
		_fail("hud_core_scene_load", "could not load res://scenes/test_movement.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("hud_core_scene_instantiate", "instantiate() returned null for test_movement.tscn")
		return null
	return inst


func _load_infection_scene() -> Node:
	var packed: PackedScene = load("res://scenes/test_infection_loop.tscn") as PackedScene
	if packed == null:
		_fail("hud_infection_scene_load", "could not load res://scenes/test_infection_loop.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("hud_infection_scene_instantiate", "instantiate() returned null for test_infection_loop.tscn")
		return null
	return inst


func _find_player(root: Node) -> PlayerController:
	if root == null:
		return null
	var player: PlayerController = root.get_node_or_null("Player") as PlayerController
	return player


func _find_floor(root: Node) -> StaticBody2D:
	if root == null:
		return null
	var floor: StaticBody2D = root.get_node_or_null("Floor") as StaticBody2D
	return floor


func _central_play_area_bounds(root: Node) -> Rect2:
	var player: CharacterBody2D = root.get_node_or_null("Player") as CharacterBody2D
	var floor: StaticBody2D = root.get_node_or_null("Floor") as StaticBody2D
	if player == null or floor == null:
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


func _find_hud_layer_with_hp(root: Node) -> CanvasLayer:
	if root == null:
		return null
	for candidate in root.find_children("*", "CanvasLayer", true, false):
		var layer := candidate as CanvasLayer
		if layer == null:
			continue
		# Look for an HPLabel child anywhere under this layer.
		var hp_label: Label = layer.get_node_or_null("HPLabel") as Label
		if hp_label == null:
			var matches: Array = layer.find_children("HPLabel", "Label", true, false)
			if matches.size() > 0:
				hp_label = matches[0] as Label
		if hp_label != null:
			return layer
	return null


func _get_hp_label(hud: CanvasLayer) -> Label:
	if hud == null:
		return null
	var label: Label = hud.get_node_or_null("HPLabel") as Label
	if label != null:
		return label
	var matches: Array = hud.find_children("HPLabel", "Label", true, false)
	if matches.size() > 0:
		return matches[0] as Label
	return null


func _get_chunk_label(hud: CanvasLayer) -> Label:
	if hud == null:
		return null
	var label: Label = hud.get_node_or_null("ChunkStatusLabel") as Label
	if label != null:
		return label
	var matches: Array = hud.find_children("ChunkStatusLabel", "Label", true, false)
	if matches.size() > 0:
		return matches[0] as Label
	return null


func _get_hp_bar(hud: CanvasLayer) -> Range:
	if hud == null:
		return null
	# Prefer a child explicitly named HPBar, but fall back to first Range under the HUD.
	var bar_node: Node = hud.get_node_or_null("HPBar")
	if bar_node != null and bar_node is Range:
		return bar_node as Range

	for child in hud.find_children("*", "", true, false):
		var range_node := child as Range
		if range_node != null:
			return range_node
	return null


func _control_global_rect(control: Control) -> Rect2:
	if control == null:
		return Rect2()
	return control.get_global_rect()


func _central_play_area_bounds_screen() -> Rect2:
	var cx: float = 640.0
	var cy: float = 360.0
	var half: float = 200.0
	return Rect2(Vector2(cx - half, cy - half), Vector2(half * 2, half * 2))


func _central_bounds_and_center(root: Node) -> Dictionary:
	var bounds: Rect2 = _central_play_area_bounds(root)
	var center: Vector2 = bounds.position + bounds.size * 0.5
	return {"bounds": bounds, "center": center}


func _central_bounds_and_center_screen() -> Dictionary:
	var bounds: Rect2 = _central_play_area_bounds_screen()
	var center: Vector2 = bounds.position + bounds.size * 0.5
	return {"bounds": bounds, "center": center}


func _label_contains_number(label: Label, value: float) -> bool:
	if label == null:
		return false
	var text_lower: String = label.text.to_lower()
	var expected_int_text: String = str(int(round(value)))
	return expected_int_text in text_lower


func _configure_player_hp_and_chunk(player: PlayerController, hp_value: float, has_chunk: bool) -> void:
	if player == null:
		return
	player._current_state.current_hp = hp_value
	player._current_state.has_chunk = has_chunk


func _attach_player_to_hud_if_supported(hud: CanvasLayer, player: PlayerController) -> void:
	if hud == null or player == null:
		return
	# Only assign if the HUD script actually exposes a _player property.
	if "_player" in hud:
		hud._player = player


# ---------------------------------------------------------------------------
# Structural presence: HP & chunk HUD in both scenes
# ---------------------------------------------------------------------------

func test_core_scene_has_hp_and_chunk_hud_elements() -> void:
	var root: Node = _load_core_scene()
	if root == null:
		return

	var hud: CanvasLayer = _find_hud_layer_with_hp(root)
	_assert_true(hud != null,
		"hud_core_canvas_layer_present — core movement scene exposes a HUD CanvasLayer with HP controls")

	if hud != null:
		var hp_label: Label = _get_hp_label(hud)
		var chunk_label: Label = _get_chunk_label(hud)
		var hp_bar: Range = _get_hp_bar(hud)

		_assert_true(hp_label != null,
			"hud_core_hp_label_present — HPLabel exists under the core HUD CanvasLayer")
		_assert_true(chunk_label != null,
			"hud_core_chunk_label_present — ChunkStatusLabel exists under the core HUD CanvasLayer")
		_assert_true(hp_bar != null,
			"hud_core_hp_bar_present — HP bar (Range-derived control) exists under the core HUD CanvasLayer")

	root.free()


func test_infection_scene_has_hp_and_chunk_hud_elements() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var hud: CanvasLayer = _find_hud_layer_with_hp(root)
	_assert_true(hud != null,
		"hud_infection_canvas_layer_present — infection-loop scene exposes a HUD CanvasLayer with HP controls")

	if hud != null:
		var hp_label: Label = _get_hp_label(hud)
		var chunk_label: Label = _get_chunk_label(hud)
		var hp_bar: Range = _get_hp_bar(hud)

		_assert_true(hp_label != null,
			"hud_infection_hp_label_present — HPLabel exists under the infection HUD CanvasLayer")
		_assert_true(chunk_label != null,
			"hud_infection_chunk_label_present — ChunkStatusLabel exists under the infection HUD CanvasLayer")
		_assert_true(hp_bar != null,
			"hud_infection_hp_bar_present — HP bar (Range-derived control) exists under the infection HUD CanvasLayer")

	root.free()


# ---------------------------------------------------------------------------
# Layout: HUD elements stay out of central play area and within sane distance
# ---------------------------------------------------------------------------

func _assert_hud_elements_layout_ok(root: Node, scene_name: String) -> void:
	if root == null:
		return

	var hud: CanvasLayer = _find_hud_layer_with_hp(root)
	if hud == null:
		_fail(scene_name + "_hud_layout_hud_missing",
			"HUD CanvasLayer with HPLabel not found; cannot assert layout")
		return

	var hp_label: Label = _get_hp_label(hud)
	var chunk_label: Label = _get_chunk_label(hud)
	var hp_bar: Range = _get_hp_bar(hud)

	# HUD elements are CanvasLayer children; use screen-space bounds for like-for-like comparison.
	var bounds_and_center := _central_bounds_and_center_screen()
	var central_bounds: Rect2 = bounds_and_center["bounds"]
	var center: Vector2 = bounds_and_center["center"]

	var all_outside: bool = true
	var all_within_distance: bool = true

	var candidates: Array = []
	if hp_label != null:
		candidates.append(hp_label as Control)
	if chunk_label != null:
		candidates.append(chunk_label as Control)
	if hp_bar != null and hp_bar is Control:
		candidates.append(hp_bar as Control)

	for control in candidates:
		var rect: Rect2 = _control_global_rect(control)
		if central_bounds.intersects(rect):
			all_outside = false
			break
		var rect_center: Vector2 = rect.position + rect.size * 0.5
		var distance_to_center: float = center.distance_to(rect_center)
		if distance_to_center > 2000.0:
			all_within_distance = false
			break

	_assert_true(all_outside,
		scene_name + "_hud_elements_outside_central_area — HP and chunk HUD elements do not overlap central play area bounds")
	_assert_true(all_within_distance,
		scene_name + "_hud_elements_not_extremely_far — HP and chunk HUD elements are within a sane distance of the play area")


func test_core_hud_layout_respects_central_play_area() -> void:
	var root: Node = _load_core_scene()
	if root == null:
		return
	_assert_hud_elements_layout_ok(root, "core")
	root.free()


func test_infection_hud_layout_respects_central_play_area() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return
	_assert_hud_elements_layout_ok(root, "infection")
	root.free()


func _assert_hud_readability_for_scene(root: Node, scene_name: String) -> void:
	if root == null:
		return

	var hud: CanvasLayer = _find_hud_layer_with_hp(root)
	if hud == null:
		_fail(scene_name + "_hud_readability_hud_missing",
			"HUD CanvasLayer with HPLabel not found; cannot assert readability")
		return

	var hp_label: Label = _get_hp_label(hud)
	var chunk_label: Label = _get_chunk_label(hud)
	var hp_bar: Range = _get_hp_bar(hud)

	var any_missing: bool = (hp_label == null or chunk_label == null or hp_bar == null)
	_assert_false(any_missing,
		scene_name + "_hud_readability_elements_present — HPLabel, ChunkStatusLabel, and HP bar exist for readability checks")
	if any_missing:
		return

	var labels: Array[Label] = [hp_label, chunk_label]
	for label in labels:
		var canvas_item := label as CanvasItem
		var alpha_ok: bool = canvas_item.modulate.a > 0.0
		var scale: Vector2 = label.scale
		var not_tiny: bool = abs(scale.x) >= 0.5 and abs(scale.y) >= 0.5

		_assert_true(alpha_ok,
			scene_name + "_hud_label_alpha_non_zero — HUD text label has modulate alpha > 0 (not fully transparent)")
		_assert_true(not_tiny,
			scene_name + "_hud_label_scale_not_tiny — HUD text label scale is not effectively zero on either axis")

	var bar_control: Control = hp_bar as Control
	var bar_canvas_item := bar_control as CanvasItem
	var bar_alpha_ok: bool = bar_canvas_item.modulate.a > 0.0
	var bar_scale: Vector2 = bar_control.scale
	var bar_not_tiny: bool = abs(bar_scale.x) >= 0.5 and abs(bar_scale.y) >= 0.5

	_assert_true(bar_alpha_ok,
		scene_name + "_hud_bar_alpha_non_zero — HP bar has modulate alpha > 0 (not fully transparent)")
	_assert_true(bar_not_tiny,
		scene_name + "_hud_bar_scale_not_tiny — HP bar scale is not effectively zero on either axis")


func test_core_hud_readability_for_hp_and_chunk_elements() -> void:
	var root: Node = _load_core_scene()
	if root == null:
		return
	_assert_hud_readability_for_scene(root, "core")
	root.free()


func test_infection_hud_readability_for_hp_and_chunk_elements() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return
	_assert_hud_readability_for_scene(root, "infection")
	root.free()


# ---------------------------------------------------------------------------
# Behavior: HP and chunk HUD track PlayerController state
# ---------------------------------------------------------------------------

func _assert_hud_tracks_hp_and_chunk_for_scene(load_scene_func: Callable, scene_name: String) -> void:
	var root: Node = load_scene_func.call() as Node
	if root == null:
		return

	var player: PlayerController = _find_player(root)
	if player == null:
		_fail(scene_name + "_hud_player_exists", "Player node is not a PlayerController in " + scene_name + " scene")
		root.free()
		return

	player._ready()

	var hud: CanvasLayer = _find_hud_layer_with_hp(root)
	if hud == null:
		_fail(scene_name + "_hud_behavior_hud_missing",
			"HUD CanvasLayer with HPLabel not found; cannot assert behavior")
		root.free()
		return

	_attach_player_to_hud_if_supported(hud, player)

	var hp_label: Label = _get_hp_label(hud)
	var chunk_label: Label = _get_chunk_label(hud)
	var hp_bar: Range = _get_hp_bar(hud)

	if hp_label == null or chunk_label == null or hp_bar == null:
		_fail(scene_name + "_hud_behavior_elements_missing",
			"HPLabel, ChunkStatusLabel, and HP bar must all exist to assert HUD behavior")
		root.free()
		return

	# Baseline: full HP, chunk attached.
	_configure_player_hp_and_chunk(player, 100.0, true)
	hud._process(0.016)

	var label_full_hp: String = hp_label.text
	var chunk_full_hp: String = chunk_label.text
	var bar_value_full: float = hp_bar.value

	_assert_true(_label_contains_number(hp_label, 100.0),
		scene_name + "_hud_hp_label_shows_full_hp — HP label text contains the full-HP value after update")
	_assert_true("attached" in chunk_full_hp.to_lower(),
		scene_name + "_hud_chunk_label_shows_attached — chunk label indicates attached state when has_chunk=true")

	# Reduced HP, chunk detached.
	_configure_player_hp_and_chunk(player, 50.0, false)
	hud._process(0.016)

	var label_low_hp: String = hp_label.text
	var chunk_low_hp: String = chunk_label.text
	var bar_value_low: float = hp_bar.value

	_assert_true(_label_contains_number(hp_label, 50.0),
		scene_name + "_hud_hp_label_shows_reduced_hp — HP label text updates to show reduced HP value")
	_assert_true("detached" in chunk_low_hp.to_lower(),
		scene_name + "_hud_chunk_label_shows_detached — chunk label indicates detached state when has_chunk=false")

	# HP bar must monotonically decrease as HP decreases.
	_assert_true(bar_value_low < bar_value_full - EPSILON,
		scene_name + "_hud_hp_bar_monotonic_decrease — HP bar value decreases when HP decreases from 100 to 50")

	root.free()


func test_core_hud_tracks_hp_and_chunk_state() -> void:
	_assert_hud_tracks_hp_and_chunk_for_scene(_load_core_scene, "core")


func test_infection_hud_tracks_hp_and_chunk_state() -> void:
	_assert_hud_tracks_hp_and_chunk_for_scene(_load_infection_scene, "infection")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_hp_and_chunk_hud.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Structural presence
	test_core_scene_has_hp_and_chunk_hud_elements()
	test_infection_scene_has_hp_and_chunk_hud_elements()

	# Layout
	test_core_hud_layout_respects_central_play_area()
	test_infection_hud_layout_respects_central_play_area()
	test_core_hud_readability_for_hp_and_chunk_elements()
	test_infection_hud_readability_for_hp_and_chunk_elements()

	# Behavior
	test_core_hud_tracks_hp_and_chunk_state()
	test_infection_hud_tracks_hp_and_chunk_state()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

