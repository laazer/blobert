#
# test_infection_ui.gd
#
# Headless behavioral tests for the "Basic UI feedback (infection loop)" slice.
# These tests validate structural and behavioral contracts for the infection UI
# container and absorb prompt, as defined in basic_ui_feedback_infection_spec.md.
#
# Ticket: basic_ui_feedback_infection.md
# Spec coverage:
#   - INF-UI-1 — Infection UI container and scene integration
#   - INF-UI-2 — Absorb prompt text, visibility, and layout
#   - INF-UI-3 — Absorb prompt behavior over time
#   - INF-UI-4 — Headless compatibility and failure detectability (subset)
#

class_name InfectionUiTests
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


func _load_infection_scene() -> Node:
	# CHECKPOINT [M2-UI-INF-001]:
	#   Assumption: The canonical infection-loop test scene is
	#   res://scenes/test_infection_loop.tscn, similar in spirit to
	#   test_movement.tscn for core movement. Its root node hosts the
	#   InfectionUI CanvasLayer used in these tests.
	#   Confidence: Medium.
	var packed: PackedScene = load("res://scenes/test_infection_loop.tscn") as PackedScene
	if packed == null:
		_fail("infection_scene_load", "could not load res://scenes/test_infection_loop.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("infection_scene_instantiate", "instantiate() returned null for test_infection_loop.tscn")
		return null
	return inst


func _find_infection_ui(root: Node) -> CanvasLayer:
	if root == null:
		return null
	var infection_ui: CanvasLayer = root.get_node_or_null("InfectionUI") as CanvasLayer
	return infection_ui


func _find_absorb_prompt_label(root: Node) -> Label:
	var infection_ui: CanvasLayer = _find_infection_ui(root)
	if infection_ui == null:
		return null
	var label: Label = infection_ui.get_node_or_null("AbsorbPromptLabel") as Label
	return label


func _has_dynamic_world_ancestor(node: Node) -> bool:
	var current: Node = node
	while current != null:
		if current is CharacterBody2D or current is RigidBody2D or current is StaticBody2D:
			return true
		current = current.get_parent()
	return false


# Screen-space central area for CanvasLayer UI (same coord system as Label global rect).
func _central_play_area_bounds_screen() -> Rect2:
	var cx: float = 640.0
	var cy: float = 360.0
	var half: float = 200.0
	return Rect2(Vector2(cx - half, cy - half), Vector2(half * 2, half * 2))


func _central_play_area_bounds(root: Node) -> Rect2:
	# Reuses the same definition as HumanPlayableCoreTests._central_play_area_bounds:
	# a rectangle spanning the main floor and a generous buffer around the player.
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


func _label_global_position(label: Label) -> Vector2:
	if label == null:
		return Vector2.ZERO
	return label.get_global_transform().origin


func _label_global_rect(label: Label) -> Rect2:
	if label == null:
		return Rect2()
	# CHECKPOINT [M2-UI-INF-004]:
	#   Assumption: Using Control.get_global_rect() as the authoritative
	#   screen-space bounding box for AbsorbPromptLabel is sufficient to
	#   enforce the "no overlap with central play area" requirement from
	#   INF-UI-2.D. Tests treat any intersection between this rect and the
	#   central play area rectangle as a spec violation, even if only a
	#   small portion overlaps.
	#   Confidence: Medium.
	var control := label as Control
	return control.get_global_rect()


func _set_absorb_available_and_step(root: Node, available: bool, frames: int) -> Label:
	# CHECKPOINT [M2-UI-INF-002]:
	#   Assumption: The InfectionUI CanvasLayer's script exposes a method
	#   set_absorb_available(available: bool) that is the production API by
	#   which the infection/interaction layer communicates "absorb available"
	#   state to the UI. Tests call this method directly and then advance the
	#   UI for a fixed number of _process frames to observe prompt behavior.
	#   Confidence: Medium.
	var infection_ui: CanvasLayer = _find_infection_ui(root)
	if infection_ui == null:
		_fail("absorb_available_api_infection_ui_missing", "InfectionUI node not found for absorb-available tests")
		return null

	if not infection_ui.has_method("set_absorb_available"):
		_fail("absorb_available_api_missing", "InfectionUI must implement set_absorb_available(available: bool) for UI gating")
		return null

	infection_ui.call("set_absorb_available", available)
	for _i in range(frames):
		infection_ui.call("_process", 0.016)

	return _find_absorb_prompt_label(root)


func _run_absorb_available_sequence(sequence: Array) -> Array[bool]:
	var root: Node = _load_infection_scene()
	if root == null:
		return []

	var vis: Array[bool] = []
	for available in sequence:
		var label: Label = _set_absorb_available_and_step(root, available, 1)
		if label == null:
			root.free()
			return []
		vis.append(label.visible)

	root.free()
	return vis


func _find_infection_handler(root: Node) -> Node:
	if root == null:
		return null
	return root.get_node_or_null("InfectionInteractionHandler")


# ---------------------------------------------------------------------------
# INF-UI-1 — Infection UI container and scene integration
# ---------------------------------------------------------------------------

func test_infection_ui_container_exists_and_is_canvas_layer() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var infection_ui: CanvasLayer = _find_infection_ui(root)
	_assert_true(infection_ui != null,
		"inf_ui_1_container_present — InfectionUI CanvasLayer exists as child of infection-loop scene root")

	if infection_ui != null:
		_assert_false(_has_dynamic_world_ancestor(infection_ui),
			"inf_ui_1_container_not_under_dynamic_world — InfectionUI is not parented under moving physics bodies")

	root.free()


func test_infection_ui_children_not_under_dynamic_world_nodes() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var infection_ui: CanvasLayer = _find_infection_ui(root)
	if infection_ui == null:
		root.free()
		return

	var any_under_dynamic_world: bool = false
	for node in infection_ui.get_children():
		if _has_dynamic_world_ancestor(node):
			any_under_dynamic_world = true
			break

	_assert_false(any_under_dynamic_world,
		"inf_ui_1_children_not_under_dynamic_world — infection UI subtree has no dynamic-world ancestors")

	root.free()


# ---------------------------------------------------------------------------
# INF-UI-2 — Absorb prompt text, visibility, and layout
# ---------------------------------------------------------------------------

func test_absorb_prompt_label_exists_and_is_label() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var label: Label = _find_absorb_prompt_label(root)
	_assert_true(label != null,
		"inf_ui_2_absorb_prompt_present — InfectionUI contains AbsorbPromptLabel node")

	root.free()


func test_absorb_prompt_text_contains_absorb_case_insensitive() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var label: Label = _find_absorb_prompt_label(root)
	if label == null:
		root.free()
		return

	var text_lower: String = label.text.to_lower()
	_assert_true("absorb" in text_lower,
		"inf_ui_2_absorb_prompt_text_contains_keyword — AbsorbPromptLabel.text contains 'absorb' (case-insensitive)")

	root.free()


func test_absorb_prompt_readability_alpha_and_scale() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var label: Label = _find_absorb_prompt_label(root)
	if label == null:
		root.free()
		return

	var canvas_item := label as CanvasItem
	var alpha_ok: bool = canvas_item.modulate.a > 0.0
	_assert_true(alpha_ok,
		"inf_ui_2_absorb_prompt_alpha_non_zero — AbsorbPromptLabel has modulate alpha > 0 (not fully transparent)")

	var scale: Vector2 = label.scale
	var not_tiny: bool = abs(scale.x) >= 0.5 and abs(scale.y) >= 0.5
	_assert_true(not_tiny,
		"inf_ui_2_absorb_prompt_scale_not_tiny — AbsorbPromptLabel scale is not effectively zero on either axis")

	root.free()


func test_absorb_prompt_layout_outside_central_play_area_and_not_extreme() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var label: Label = _find_absorb_prompt_label(root)
	if label == null:
		root.free()
		return

	# Use screen-space bounds so we compare Label (CanvasLayer) coords with same space.
	var central_bounds: Rect2 = _central_play_area_bounds_screen()
	var center: Vector2 = central_bounds.position + central_bounds.size * 0.5

	var pos: Vector2 = _label_global_position(label)
	var outside_central: bool = not _point_inside_rect(pos, central_bounds)
	var distance_to_center: float = center.distance_to(pos)
	var not_extreme_distance: bool = distance_to_center <= 2000.0

	_assert_true(outside_central,
		"inf_ui_2_absorb_prompt_outside_central_area — AbsorbPromptLabel is placed outside central play area bounds")
	_assert_true(not_extreme_distance,
		"inf_ui_2_absorb_prompt_not_extremely_far — AbsorbPromptLabel is within a sane distance of the central play area")

	root.free()


func test_absorb_prompt_bounding_box_does_not_overlap_central_play_area() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var label: Label = _find_absorb_prompt_label(root)
	if label == null:
		root.free()
		return

	# Use screen-space bounds so we compare Label (CanvasLayer) rect with same space.
	var central_bounds: Rect2 = _central_play_area_bounds_screen()
	var label_rect: Rect2 = _label_global_rect(label)

	var intersects: bool = central_bounds.intersects(label_rect)
	_assert_false(intersects,
		"inf_ui_2_absorb_prompt_bounding_box_outside_central_area — AbsorbPromptLabel global rect does not intersect central play area")

	root.free()


func test_absorb_prompt_default_invisible_on_scene_load() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var label: Label = _find_absorb_prompt_label(root)
	if label == null:
		root.free()
		return

	_assert_false(label.visible,
		"inf_ui_2_absorb_prompt_default_hidden — AbsorbPromptLabel is not visible immediately after scene load")

	root.free()


# ---------------------------------------------------------------------------
# INF-UI-3 — Absorb prompt behavior over time
# ---------------------------------------------------------------------------

func test_absorb_prompt_visibility_follows_absorb_available_with_max_one_frame_lag() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	# Start from default state: absorb not available, prompt hidden.
	var label: Label = _find_absorb_prompt_label(root)
	if label == null:
		root.free()
		return

	# Turn availability on and advance one frame: prompt must be visible by then.
	label = _set_absorb_available_and_step(root, true, 1)
	if label == null:
		root.free()
		return
	_assert_true(label.visible,
		"inf_ui_3_visibility_tracks_true_state — AbsorbPromptLabel is visible within one frame of absorb becoming available")

	# Turn availability off and advance one frame: prompt must be hidden by then.
	label = _set_absorb_available_and_step(root, false, 1)
	if label == null:
		root.free()
		return
	_assert_false(label.visible,
		"inf_ui_3_visibility_tracks_false_state — AbsorbPromptLabel is hidden within one frame of absorb becoming unavailable")

	root.free()


func test_absorb_prompt_no_flicker_under_stable_true_or_false() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	# Stable true: prompt remains visible for N consecutive frames.
	var label: Label = _set_absorb_available_and_step(root, true, 1)
	if label == null:
		root.free()
		return

	var stable_true_ok: bool = true
	for _i in range(5):
		if not label.visible:
			stable_true_ok = false
			break
		# Advance UI one frame while keeping availability true.
		label = _set_absorb_available_and_step(root, true, 1)
		if label == null:
			root.free()
			return

	_assert_true(stable_true_ok,
		"inf_ui_3_no_flicker_when_available_true — AbsorbPromptLabel stays visible across stable absorb-available frames")

	# Stable false: prompt remains hidden for N consecutive frames.
	label = _set_absorb_available_and_step(root, false, 1)
	if label == null:
		root.free()
		return

	var stable_false_ok: bool = true
	for _j in range(5):
		if label.visible:
			stable_false_ok = false
			break
		label = _set_absorb_available_and_step(root, false, 1)
		if label == null:
			root.free()
			return

	_assert_true(stable_false_ok,
		"inf_ui_3_no_flicker_when_available_false — AbsorbPromptLabel stays hidden across stable non-available frames")

	root.free()


func test_absorb_prompt_reentrancy_toggles_cleanly_over_multiple_transitions() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var sequence_ok: bool = true

	var label: Label = _set_absorb_available_and_step(root, false, 1)
	if label == null:
		root.free()
		return
	sequence_ok = sequence_ok and (not label.visible)

	label = _set_absorb_available_and_step(root, true, 1)
	if label == null:
		root.free()
		return
	sequence_ok = sequence_ok and label.visible

	label = _set_absorb_available_and_step(root, false, 1)
	if label == null:
		root.free()
		return
	sequence_ok = sequence_ok and (not label.visible)

	label = _set_absorb_available_and_step(root, true, 1)
	if label == null:
		root.free()
		return
	sequence_ok = sequence_ok and label.visible

	_assert_true(sequence_ok,
		"inf_ui_3_reentrancy_behavior — AbsorbPromptLabel mirrors multiple true/false toggles without stale visibility")

	root.free()


func test_absorb_prompt_visibility_is_deterministic_for_boolean_sequence() -> void:
	var sequence: Array[bool] = [
		false, false, true, true, true,
		false, true, false, false, true,
		true, false
	]

	var first_run: Array[bool] = _run_absorb_available_sequence(sequence)
	var second_run: Array[bool] = _run_absorb_available_sequence(sequence)

	var deterministic: bool = first_run.size() == second_run.size()
	if deterministic:
		for i in range(first_run.size()):
			if first_run[i] != second_run[i]:
				deterministic = false
				break

	_assert_true(deterministic,
		"inf_ui_3_visibility_deterministic_for_sequence — AbsorbPromptLabel visibility is deterministic for a fixed availability sequence")


# ---------------------------------------------------------------------------
# INF-UI-4 — Headless compatibility and failure modes (subset)
# ---------------------------------------------------------------------------

func test_infection_ui_scene_instantiates_headless_without_errors() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	# If we reach here without crashing, basic headless instantiation works.
	_pass("inf_ui_4_headless_scene_instantiation — infection-loop scene and InfectionUI instantiate in headless test harness")

	root.free()


func test_infection_ui_scene_can_be_instantiated_and_freed_repeatedly() -> void:
	var iterations: int = 25
	var all_ok: bool = true

	for _i in range(iterations):
		var root: Node = _load_infection_scene()
		if root == null:
			all_ok = false
			break

		var infection_ui: CanvasLayer = _find_infection_ui(root)
		if infection_ui == null:
			all_ok = false
			root.free()
			break

		root.free()

	_assert_true(all_ok,
		"inf_ui_4_repeated_headless_instantiation — InfectionUI scene can be instantiated and freed repeatedly without errors")


# ---------------------------------------------------------------------------
# INF-UI-5 / R3, R5 — Mutation acquisition plumbing to InfectionUI
# ---------------------------------------------------------------------------

func test_mutation_label_becomes_visible_after_inventory_gain_via_handler() -> void:
	var root: Node = _load_infection_scene()
	if root == null:
		return

	var infection_ui: CanvasLayer = _find_infection_ui(root)
	var handler: Node = _find_infection_handler(root)
	if infection_ui == null or handler == null:
		root.free()
		return

	if not handler.has_method("get_mutation_inventory"):
		_fail("inf_ui_5_handler_inventory_api_missing", "InfectionInteractionHandler must expose get_mutation_inventory() for mutation UI")
		root.free()
		return

	var inv: Object = handler.get_mutation_inventory()
	if inv == null or not inv.has_method("grant") or not inv.has_method("get_granted_count"):
		_fail("inf_ui_5_inventory_missing_or_incomplete", "Handler.get_mutation_inventory() must return object with grant/get_granted_count")
		root.free()
		return

	# Initial process: no mutations granted → mutation label hidden.
	infection_ui._process(0.016)
	var mutation_label: Label = infection_ui.get_node_or_null("MutationLabel") as Label
	if mutation_label == null:
		root.free()
		return

	var visible_before: bool = mutation_label.visible

	# Grant one mutation via inventory and re-process; label must become visible.
	inv.grant("test_mutation_id")
	infection_ui._process(0.016)
	var visible_after: bool = mutation_label.visible

	_assert_false(visible_before,
		"inf_ui_5_mutation_label_hidden_before_gain — MutationLabel hidden when inventory has zero mutations")
	_assert_true(visible_after,
		"inf_ui_5_mutation_label_visible_after_gain — MutationLabel visible after inventory grants at least one mutation")

	root.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_infection_ui.gd ---")
	_pass_count = 0
	_fail_count = 0

	# INF-UI-1 — container and hierarchy
	test_infection_ui_container_exists_and_is_canvas_layer()
	test_infection_ui_children_not_under_dynamic_world_nodes()

	# INF-UI-2 — absorb prompt presence, text, readability, layout
	test_absorb_prompt_label_exists_and_is_label()
	test_absorb_prompt_text_contains_absorb_case_insensitive()
	test_absorb_prompt_readability_alpha_and_scale()
	test_absorb_prompt_layout_outside_central_play_area_and_not_extreme()
	test_absorb_prompt_bounding_box_does_not_overlap_central_play_area()
	test_absorb_prompt_default_invisible_on_scene_load()

	# INF-UI-3 — absorb prompt behavior over time
	test_absorb_prompt_visibility_follows_absorb_available_with_max_one_frame_lag()
	test_absorb_prompt_no_flicker_under_stable_true_or_false()
	test_absorb_prompt_reentrancy_toggles_cleanly_over_multiple_transitions()
	test_absorb_prompt_visibility_is_deterministic_for_boolean_sequence()

	# INF-UI-4 — headless instantiation smoke
	test_infection_ui_scene_instantiates_headless_without_errors()
	test_infection_ui_scene_can_be_instantiated_and_freed_repeatedly()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

