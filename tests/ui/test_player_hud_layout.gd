#
# test_player_hud_layout.gd
#
# Behavioral tests for the Player HUD layout reorganization.
#
# Ticket:  player_hud.md
# Spec:    agent_context/agents/2_spec/player_hud_spec.md
#          Parts 1–6; test cases T-6.1 through T-6.12
#
# Scope:
#   T-6.1  — HPBar is ProgressBar, not TextureProgressBar
#   T-6.2  — HPBar is Range (cast compatibility; regression guard)
#   T-6.3  — HPBar min_value == 0.0 and max_value >= 1.0 and show_percentage == false
#   T-6.4  — All 15 flat get_node_or_null binding paths resolve non-null
#   T-6.5  — Hints node resolves non-null
#   T-6.6  — Hints has exactly 4 named children
#   T-6.7  — 28 pairwise disjointness checks on always-visible node set (Part 5.3)
#   T-6.8  — All always-visible node rects fit within 3200x1880 viewport
#   T-6.9  — Legacy nodes (MutationSlotLabel, MutationIcon) don't intersect always-visible set
#   T-6.10 — Contextual prompt nodes don't intersect always-visible set
#   T-6.11 — InputHintsConfig default for input_hints_enabled is false
#   T-6.12 — MutationSlotLabel and MutationIcon are visible=false by scene default
#
# RED-PHASE: Tests T-6.1, T-6.3, T-6.7, T-6.8, T-6.9, T-6.10, T-6.11, T-6.12
# will FAIL until the implementation in game_ui.tscn and input_hints_config.gd is
# applied (Task 2 and Task 3 of the execution plan).
#
# Scene loading strategy:
#   game_ui.tscn instantiates InfectionUI (extends CanvasLayer) as its script.
#   InfectionUI._ready() calls get_tree().get_first_node_in_group("player"), which
#   returns null in headless (no crash). The CanvasLayer and its Control children
#   carry offset_* properties that are readable immediately after add_child without
#   a rendered frame.
#
# Headless safety:
#   Uses Engine.get_main_loop() as SceneTree and tree.root.add_child(ui) so that
#   InfectionUI._ready() has a valid get_tree() call (no crash). All assertions are
#   structural (offset values, node types, child counts) — no _process() is called.
#

extends Object

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " -- " + message)


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


func _assert_eq_float(expected: float, actual: float, test_name: String) -> void:
	if absf(expected - actual) < 0.001:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + " got " + str(actual))


func _assert_ge_float(actual: float, minimum: float, test_name: String) -> void:
	if actual >= minimum:
		_pass(test_name)
	else:
		_fail(test_name, "expected >= " + str(minimum) + " got " + str(actual))


func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
	if expected == actual:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + " got " + str(actual))


# ---------------------------------------------------------------------------
# Bounding rect helpers (Spec Part 6, Section 6.3)
# ---------------------------------------------------------------------------

# _rect: construct a Rect2 from explicit offset values.
func _rect(left: float, top: float, right: float, bottom: float) -> Rect2:
	return Rect2(Vector2(left, top), Vector2(right - left, bottom - top))


# _node_rect: extract the bounding rect from a named direct child of the
# GameUI CanvasLayer, using its offset_* properties.
func _node_rect(ui: CanvasLayer, node_name: String) -> Rect2:
	var n: Control = ui.get_node(node_name) as Control
	return _rect(n.offset_left, n.offset_top, n.offset_right, n.offset_bottom)


# _hints_child_rect: extract the bounding rect from a named child of the
# Hints Control node (children carry viewport-absolute offsets since Hints
# is positioned at origin).
func _hints_child_rect(ui: CanvasLayer, child_name: String) -> Rect2:
	var hints: Control = ui.get_node("Hints") as Control
	var n: Control = hints.get_node(child_name) as Control
	return _rect(n.offset_left, n.offset_top, n.offset_right, n.offset_bottom)


# ---------------------------------------------------------------------------
# Scene loading
# ---------------------------------------------------------------------------

# _load_game_ui: load and instantiate game_ui.tscn, add it to the scene tree
# so InfectionUI._ready() has a valid get_tree() context, and return it.
# Returns null on load failure (test is already failed by caller).
func _load_game_ui() -> CanvasLayer:
	var packed: PackedScene = load("res://scenes/ui/game_ui.tscn") as PackedScene
	if packed == null:
		return null
	var ui: Node = packed.instantiate()
	if ui == null:
		return null
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree != null and tree.root != null:
		tree.root.add_child(ui)
	return ui as CanvasLayer


func _free_ui(ui: Node) -> void:
	if ui == null:
		return
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree != null and tree.root != null and ui.is_inside_tree():
		tree.root.remove_child(ui)
	ui.queue_free()


# ---------------------------------------------------------------------------
# Always-visible node set (Spec Part 5.3)
#
# Returns an Array of [name, rect] pairs in the order specified by the spec.
# These 8 nodes are visible by scene-file default and not toggled off at runtime.
# ---------------------------------------------------------------------------

func _always_visible_spec_rects() -> Array:
	return [
		["HPBar",            _rect(20.0,  8.0,  400.0,  28.0)],
		["HPLabel",          _rect(20.0, 36.0,  400.0,  62.0)],
		["ChunkStatusLabel", _rect(20.0, 70.0,  400.0,  96.0)],
		["ClingStatusLabel", _rect(20.0, 104.0, 400.0, 130.0)],
		["MutationIcon1",    _rect(20.0, 200.0,  46.0, 226.0)],
		["MutationSlot1Label", _rect(52.0, 200.0, 400.0, 226.0)],
		["MutationIcon2",    _rect(20.0, 240.0,  46.0, 266.0)],
		["MutationSlot2Label", _rect(52.0, 240.0, 400.0, 266.0)],
	]


# ---------------------------------------------------------------------------
# T-6.1 — HPBar is ProgressBar, not TextureProgressBar
# Spec: AC-2.1, AC-2.2
# Red phase: fails because scene currently uses TextureProgressBar.
# ---------------------------------------------------------------------------

func test_t61_hpbar_is_progress_bar() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.1_hpbar_is_progress_bar", "game_ui.tscn failed to load")
		return
	var hp_bar: Node = ui.get_node_or_null("HPBar")
	if hp_bar == null:
		_fail("t-6.1_hpbar_is_progress_bar", "HPBar node not found in game_ui.tscn")
		_free_ui(ui)
		return
	# AC-2.1: must be a ProgressBar instance
	_assert_true(
		hp_bar is ProgressBar,
		"t-6.1_hpbar_is_progress_bar -- HPBar must be ProgressBar per spec AC-2.1"
	)
	# AC-2.2: must NOT be a TextureProgressBar instance
	_assert_false(
		hp_bar is TextureProgressBar,
		"t-6.1_hpbar_not_texture_progress_bar -- HPBar must not be TextureProgressBar per spec AC-2.2"
	)
	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.2 — HPBar is Range (cast compatibility; regression guard)
# Spec: AC-2.3
# Note: TextureProgressBar also inherits Range; this test may pass before
# implementation. Its value is as a regression guard, not a red-phase test.
# ---------------------------------------------------------------------------

func test_t62_hpbar_is_range() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.2_hpbar_is_range", "game_ui.tscn failed to load")
		return
	var hp_bar: Node = ui.get_node_or_null("HPBar")
	if hp_bar == null:
		_fail("t-6.2_hpbar_is_range", "HPBar node not found in game_ui.tscn")
		_free_ui(ui)
		return
	# AC-2.3: must be a Range instance (ensures infection_ui.gd cast to Range is valid)
	_assert_true(
		hp_bar is Range,
		"t-6.2_hpbar_is_range -- HPBar must be Range per spec AC-2.3 (infection_ui.gd cast compat)"
	)
	# AC-2.6: node name must be exactly "HPBar"
	_assert_true(
		hp_bar.name == "HPBar",
		"t-6.2_hpbar_name_preserved -- HPBar.name must be exactly 'HPBar' per spec AC-2.6"
	)
	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.3 — HPBar min_value, max_value, and show_percentage
# Spec: AC-2.4, AC-2.5, AC-2.7
# Red phase: fails because current scene does not set these values.
# ---------------------------------------------------------------------------

func test_t63_hpbar_min_max_show_percentage() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.3_hpbar_min_max", "game_ui.tscn failed to load")
		return
	var hp_bar: Node = ui.get_node_or_null("HPBar")
	if hp_bar == null:
		_fail("t-6.3_hpbar_min_max", "HPBar node not found in game_ui.tscn")
		_free_ui(ui)
		return
	if not (hp_bar is Range):
		_fail("t-6.3_hpbar_min_max", "HPBar is not a Range; cannot read min_value/max_value")
		_free_ui(ui)
		return
	var bar: Range = hp_bar as Range
	# AC-2.4: min_value == 0.0
	_assert_eq_float(
		0.0, bar.min_value,
		"t-6.3_hpbar_min_value -- HPBar.min_value must be 0.0 per spec AC-2.4"
	)
	# AC-2.5: max_value >= 1.0 (scene default 100.0)
	_assert_ge_float(
		bar.max_value, 1.0,
		"t-6.3_hpbar_max_value -- HPBar.max_value must be >= 1.0 per spec AC-2.5"
	)
	# AC-2.7: show_percentage must be false (avoids double display with HPLabel)
	# Only ProgressBar has show_percentage; guard with is ProgressBar check.
	if hp_bar is ProgressBar:
		_assert_false(
			(hp_bar as ProgressBar).show_percentage,
			"t-6.3_hpbar_show_percentage_false -- HPBar.show_percentage must be false per spec AC-2.7"
		)
	else:
		_fail("t-6.3_hpbar_show_percentage_false", "HPBar is not ProgressBar; AC-2.7 not verifiable")
	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.4 — All 15 flat get_node_or_null binding paths resolve non-null
# Spec: AC-4.1, AC-4.2; Spec Part 4, Table 4.1 (flat paths only)
# ---------------------------------------------------------------------------

func test_t64_all_bindings_resolve() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.4_all_bindings_resolve", "game_ui.tscn failed to load")
		return

	# All flat get_node_or_null paths used by infection_ui.gd
	var flat_paths: Array[String] = [
		"AbsorbPromptLabel",
		"FusePromptLabel",
		"HPLabel",
		"HPBar",
		"ChunkStatusLabel",
		"ClingStatusLabel",
		"MutationLabel",
		"MutationSlotLabel",
		"AbsorbFeedbackLabel",
		"MutationIcon",
		"MutationSlot1Label",
		"MutationIcon1",
		"MutationSlot2Label",
		"MutationIcon2",
		"FusionActiveLabel",
	]

	for path in flat_paths:
		var node: Node = ui.get_node_or_null(path)
		_assert_true(
			node != null,
			"t-6.4_binding_resolves_" + path + " -- get_node_or_null('" + path + "') must return non-null per spec AC-4.1"
		)

	# AC-4.2: HPBar cast to Range must return non-null
	var hp_bar_as_range: Range = ui.get_node_or_null("HPBar") as Range
	_assert_true(
		hp_bar_as_range != null,
		"t-6.4_hpbar_cast_range -- (HPBar as Range) must be non-null per spec AC-4.2"
	)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.5 — Hints node resolves non-null
# Spec: AC-4.3
# ---------------------------------------------------------------------------

func test_t65_hints_resolves() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.5_hints_resolves", "game_ui.tscn failed to load")
		return
	var hints: Node = ui.get_node_or_null("Hints")
	_assert_true(
		hints != null,
		"t-6.5_hints_resolves -- get_node_or_null('Hints') must return non-null per spec AC-4.3"
	)
	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.6 — Hints has exactly 4 named children
# Spec: AC-4.4
# Expected children (in declaration order): MoveHint, JumpHint,
# DetachRecallHint, AbsorbHint
# ---------------------------------------------------------------------------

func test_t66_hints_children_count() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.6_hints_children_count", "game_ui.tscn failed to load")
		return
	var hints: Node = ui.get_node_or_null("Hints")
	if hints == null:
		_fail("t-6.6_hints_children_count", "Hints node not found; cannot check child count")
		_free_ui(ui)
		return

	# AC-4.4: exactly 4 children
	var children: Array = hints.get_children()
	_assert_eq_int(
		4, children.size(),
		"t-6.6_hints_children_count -- Hints must have exactly 4 children per spec AC-4.4"
	)

	# AC-4.4: named labels present
	var expected_names: Array[String] = ["MoveHint", "JumpHint", "DetachRecallHint", "AbsorbHint"]
	for node_name in expected_names:
		var child: Node = hints.get_node_or_null(node_name)
		_assert_true(
			child != null,
			"t-6.6_hints_child_" + node_name + " -- Hints must contain child '" + node_name + "' per spec AC-4.4"
		)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.7 — 28 pairwise disjointness checks on always-visible node set
# Spec: AC-5.1
# Uses actual node offset_* values from the loaded scene, compared against
# spec-defined expected rects. Fails if any always-visible node has not been
# repositioned to its spec position (because positions still overlap before
# implementation).
# Red phase: current scene nodes overlap (e.g., HPLabel top==28 same as
# HPBar bottom==24, but HPLabel right==20 and nodes are zero-width).
# After implementation all 28 pairs are disjoint.
# ---------------------------------------------------------------------------

func test_t67_always_visible_no_overlap() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.7_always_visible_no_overlap", "game_ui.tscn failed to load")
		return

	# Compute actual bounding rects from scene node offset_* values
	var node_names: Array[String] = [
		"HPBar", "HPLabel", "ChunkStatusLabel", "ClingStatusLabel",
		"MutationIcon1", "MutationSlot1Label", "MutationIcon2", "MutationSlot2Label"
	]
	var rects: Array = []
	for node_name in node_names:
		var n: Control = ui.get_node_or_null(node_name) as Control
		if n == null:
			_fail(
				"t-6.7_always_visible_no_overlap",
				"node '" + node_name + "' not found; cannot complete overlap check"
			)
			_free_ui(ui)
			return
		rects.append(_rect(n.offset_left, n.offset_top, n.offset_right, n.offset_bottom))

	# Generate all C(8,2) = 28 unique pairs and assert disjointness
	var pair_count: int = 0
	for i in range(rects.size()):
		for j in range(i + 1, rects.size()):
			var r_a: Rect2 = rects[i]
			var r_b: Rect2 = rects[j]
			var name_a: String = node_names[i]
			var name_b: String = node_names[j]
			pair_count += 1
			_assert_false(
				r_a.intersects(r_b),
				"t-6.7_no_overlap_" + name_a + "_vs_" + name_b
				+ " -- rects must be disjoint per spec AC-5.1; got "
				+ str(r_a) + " vs " + str(r_b)
			)

	# Sanity: confirm all 28 pairs were checked
	if pair_count != 28:
		_fail("t-6.7_pair_count", "expected 28 pairs, checked " + str(pair_count))

	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.8 — All always-visible node rects fit within 3200x1880 viewport
# Spec: AC-5.2
# Red phase: current nodes have zero-width/height rects (offset_right == offset_left)
# which technically fit within the viewport, but after T-6.7 passes the nodes
# will also need to be within bounds. Asserting proper-width rects within bounds.
# We assert the spec-defined expected positions are within bounds (not the current
# degenerate zero-area nodes). The test asserts actual node positions against the
# viewport bounds, using the actual offset values.
# ---------------------------------------------------------------------------

func test_t68_nodes_within_viewport() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.8_nodes_within_viewport", "game_ui.tscn failed to load")
		return

	var viewport_rect: Rect2 = Rect2(0.0, 0.0, 3200.0, 1880.0)
	var node_names: Array[String] = [
		"HPBar", "HPLabel", "ChunkStatusLabel", "ClingStatusLabel",
		"MutationIcon1", "MutationSlot1Label", "MutationIcon2", "MutationSlot2Label"
	]

	for node_name in node_names:
		var n: Control = ui.get_node_or_null(node_name) as Control
		if n == null:
			_fail(
				"t-6.8_nodes_within_viewport",
				"node '" + node_name + "' not found"
			)
			_free_ui(ui)
			return
		var r: Rect2 = _rect(n.offset_left, n.offset_top, n.offset_right, n.offset_bottom)
		# position >= (0,0)
		_assert_true(
			r.position.x >= 0.0,
			"t-6.8_" + node_name + "_left_ge_0 -- offset_left must be >= 0 per spec AC-5.2"
		)
		_assert_true(
			r.position.y >= 0.0,
			"t-6.8_" + node_name + "_top_ge_0 -- offset_top must be >= 0 per spec AC-5.2"
		)
		# right edge <= 3200
		_assert_true(
			r.position.x + r.size.x <= 3200.0,
			"t-6.8_" + node_name + "_right_le_3200 -- offset_right must be <= 3200 per spec AC-5.2; got "
			+ str(r.position.x + r.size.x)
		)
		# bottom edge <= 1880
		_assert_true(
			r.position.y + r.size.y <= 1880.0,
			"t-6.8_" + node_name + "_bottom_le_1880 -- offset_bottom must be <= 1880 per spec AC-5.2; got "
			+ str(r.position.y + r.size.y)
		)
		# width > 0 (nodes must have non-degenerate rects after implementation)
		_assert_true(
			r.size.x > 0.0,
			"t-6.8_" + node_name + "_width_positive -- node must have positive width after layout impl"
		)
		# height > 0
		_assert_true(
			r.size.y > 0.0,
			"t-6.8_" + node_name + "_height_positive -- node must have positive height after layout impl"
		)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.9 — Legacy nodes don't intersect always-visible set
# Spec: AC-5.3, AC-5.4
# Legacy nodes: MutationSlotLabel (Rect2(52,390,248,26)), MutationIcon (Rect2(20,390,26,26))
# Red phase: current positions DO intersect always-visible nodes (they are at Y 115–143
# which overlaps with spec positions for MutationSlot1Label/MutationIcon1 at Y 200–226).
# After implementation they are at Y 390–416 with no overlap.
# ---------------------------------------------------------------------------

func test_t69_legacy_nodes_no_overlap_with_always_visible() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.9_legacy_no_overlap", "game_ui.tscn failed to load")
		return

	var legacy_names: Array[String] = ["MutationSlotLabel", "MutationIcon"]
	var always_visible_names: Array[String] = [
		"HPBar", "HPLabel", "ChunkStatusLabel", "ClingStatusLabel",
		"MutationIcon1", "MutationSlot1Label", "MutationIcon2", "MutationSlot2Label"
	]

	for legacy_name in legacy_names:
		var ln: Control = ui.get_node_or_null(legacy_name) as Control
		if ln == null:
			_fail("t-6.9_legacy_no_overlap", "legacy node '" + legacy_name + "' not found")
			_free_ui(ui)
			return
		var legacy_rect: Rect2 = _rect(ln.offset_left, ln.offset_top, ln.offset_right, ln.offset_bottom)
		for av_name in always_visible_names:
			var avn: Control = ui.get_node_or_null(av_name) as Control
			if avn == null:
				_fail("t-6.9_legacy_no_overlap", "always-visible node '" + av_name + "' not found")
				_free_ui(ui)
				return
			var av_rect: Rect2 = _rect(avn.offset_left, avn.offset_top, avn.offset_right, avn.offset_bottom)
			_assert_false(
				legacy_rect.intersects(av_rect),
				"t-6.9_" + legacy_name + "_vs_" + av_name
				+ " -- legacy node must not intersect always-visible node per spec AC-5.3/AC-5.4; got "
				+ str(legacy_rect) + " vs " + str(av_rect)
			)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.10 — Contextual prompt nodes don't intersect always-visible set
# Spec: AC-5.5
# Contextual nodes: AbsorbPromptLabel, FusePromptLabel, AbsorbFeedbackLabel
# (AbsorbPromptLabel and AbsorbFeedbackLabel are intentionally co-located —
# excluded from pairwise check between themselves per spec Section 5.5)
# Red phase: current positions (Y 164–196) overlap with already-visible nodes
# at Y 145–197 for slot labels. After implementation they are at Y 1800–1864.
# ---------------------------------------------------------------------------

func test_t610_contextual_no_overlap_with_status() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.10_contextual_no_overlap", "game_ui.tscn failed to load")
		return

	var contextual_names: Array[String] = [
		"AbsorbPromptLabel", "FusePromptLabel", "AbsorbFeedbackLabel"
	]
	var always_visible_names: Array[String] = [
		"HPBar", "HPLabel", "ChunkStatusLabel", "ClingStatusLabel",
		"MutationIcon1", "MutationSlot1Label", "MutationIcon2", "MutationSlot2Label"
	]

	for ctx_name in contextual_names:
		var cn: Control = ui.get_node_or_null(ctx_name) as Control
		if cn == null:
			_fail("t-6.10_contextual_no_overlap", "contextual node '" + ctx_name + "' not found")
			_free_ui(ui)
			return
		var ctx_rect: Rect2 = _rect(cn.offset_left, cn.offset_top, cn.offset_right, cn.offset_bottom)
		for av_name in always_visible_names:
			var avn: Control = ui.get_node_or_null(av_name) as Control
			if avn == null:
				_fail("t-6.10_contextual_no_overlap", "always-visible node '" + av_name + "' not found")
				_free_ui(ui)
				return
			var av_rect: Rect2 = _rect(avn.offset_left, avn.offset_top, avn.offset_right, avn.offset_bottom)
			_assert_false(
				ctx_rect.intersects(av_rect),
				"t-6.10_" + ctx_name + "_vs_" + av_name
				+ " -- contextual node must not intersect always-visible node per spec AC-5.5; got "
				+ str(ctx_rect) + " vs " + str(av_rect)
			)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# T-6.11 — InputHintsConfig default for input_hints_enabled is false
# Spec: AC-3.1, AC-3.2, AC-3.3
# Red phase: current file has `var input_hints_enabled: bool = true`.
# After Task 3, default changes to false.
# ---------------------------------------------------------------------------

func test_t611_input_hints_config_default_false() -> void:
	var script: GDScript = load("res://scripts/ui/input_hints_config.gd") as GDScript
	if script == null:
		_fail("t-6.11_input_hints_config_default_false", "input_hints_config.gd not found at res://scripts/ui/input_hints_config.gd")
		return

	var config: Object = script.new()
	if config == null:
		_fail("t-6.11_input_hints_config_default_false", "input_hints_config.gd could not be instantiated")
		return

	# AC-3.2: property exists
	_assert_true(
		"input_hints_enabled" in config,
		"t-6.11_property_exists -- InputHintsConfig must have 'input_hints_enabled' property per spec AC-3.2"
	)

	# AC-3.3: property is bool
	_assert_true(
		typeof(config.get("input_hints_enabled")) == TYPE_BOOL,
		"t-6.11_property_is_bool -- input_hints_enabled must be bool per spec AC-3.3"
	)

	# AC-3.1: default is false
	_assert_false(
		config.get("input_hints_enabled") as bool,
		"t-6.11_default_false -- InputHintsConfig.input_hints_enabled must default to false per spec AC-3.1"
	)

	config.free()


# ---------------------------------------------------------------------------
# T-6.12 — Legacy nodes have visible=false in scene default
# Spec: Part 1.2 Region 5; Part 5.3 note on MutationSlotLabel runtime override
# MutationSlotLabel and MutationIcon must be visible=false in the fresh instance.
# Red phase: current scene does NOT set visible=false on MutationIcon; it defaults
# to visible=true. After implementation both have visible=false.
# ---------------------------------------------------------------------------

func test_t612_legacy_nodes_visible_false_default() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("t-6.12_legacy_visible_false", "game_ui.tscn failed to load")
		return

	var mutation_slot_label: Node = ui.get_node_or_null("MutationSlotLabel")
	var mutation_icon: Node = ui.get_node_or_null("MutationIcon")

	if mutation_slot_label == null:
		_fail("t-6.12_legacy_visible_false", "MutationSlotLabel not found")
		_free_ui(ui)
		return
	if mutation_icon == null:
		_fail("t-6.12_legacy_visible_false", "MutationIcon not found")
		_free_ui(ui)
		return

	# MutationSlotLabel must have visible=false in scene default
	_assert_false(
		mutation_slot_label.visible,
		"t-6.12_mutation_slot_label_hidden -- MutationSlotLabel.visible must be false by scene default per spec Region 5"
	)

	# MutationIcon must have visible=false in scene default
	_assert_false(
		mutation_icon.visible,
		"t-6.12_mutation_icon_hidden -- MutationIcon.visible must be false by scene default per spec Region 5"
	)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# Bonus: exact offset value assertions for all repositioned nodes
# These are structural guards derived directly from the spec's Appendix A
# bounding rectangle reference table. They verify each node is at its
# specified position (not merely non-overlapping with other nodes).
# These tests all fail in red phase (current positions differ from spec).
# ---------------------------------------------------------------------------

func _assert_node_offsets(
	ui: CanvasLayer,
	node_name: String,
	expected_left: float,
	expected_top: float,
	expected_right: float,
	expected_bottom: float,
	test_prefix: String
) -> void:
	var n: Control = ui.get_node_or_null(node_name) as Control
	if n == null:
		_fail(test_prefix + "_not_found", "node '" + node_name + "' not found in game_ui.tscn")
		return
	_assert_eq_float(expected_left,   n.offset_left,   test_prefix + "_offset_left")
	_assert_eq_float(expected_top,    n.offset_top,    test_prefix + "_offset_top")
	_assert_eq_float(expected_right,  n.offset_right,  test_prefix + "_offset_right")
	_assert_eq_float(expected_bottom, n.offset_bottom, test_prefix + "_offset_bottom")


func test_bonus_exact_offsets_status_strip() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("bonus_offsets_status_strip", "game_ui.tscn failed to load")
		return

	# Spec Region 1 — Top-Left Status Strip
	_assert_node_offsets(ui, "HPBar",            20.0,  8.0,  400.0,  28.0, "bonus_HPBar")
	_assert_node_offsets(ui, "HPLabel",          20.0, 36.0,  400.0,  62.0, "bonus_HPLabel")
	_assert_node_offsets(ui, "ChunkStatusLabel", 20.0, 70.0,  400.0,  96.0, "bonus_ChunkStatusLabel")
	_assert_node_offsets(ui, "ClingStatusLabel", 20.0, 104.0, 400.0, 130.0, "bonus_ClingStatusLabel")

	_free_ui(ui)


func test_bonus_exact_offsets_mutation_panel() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("bonus_offsets_mutation_panel", "game_ui.tscn failed to load")
		return

	# Spec Region 2 — Mid-Left Mutation Panel
	_assert_node_offsets(ui, "MutationIcon1",     20.0, 200.0,  46.0, 226.0, "bonus_MutationIcon1")
	_assert_node_offsets(ui, "MutationSlot1Label", 52.0, 200.0, 400.0, 226.0, "bonus_MutationSlot1Label")
	_assert_node_offsets(ui, "MutationIcon2",     20.0, 240.0,  46.0, 266.0, "bonus_MutationIcon2")
	_assert_node_offsets(ui, "MutationSlot2Label", 52.0, 240.0, 400.0, 266.0, "bonus_MutationSlot2Label")

	_free_ui(ui)


func test_bonus_exact_offsets_lower_left_and_prompts() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("bonus_offsets_lower_left", "game_ui.tscn failed to load")
		return

	# Spec Region 3 — Fusion Active Notice
	_assert_node_offsets(ui, "FusionActiveLabel", 20.0, 310.0, 300.0, 340.0, "bonus_FusionActiveLabel")
	# Spec Region 4 — Mutation Count
	_assert_node_offsets(ui, "MutationLabel",     20.0, 350.0, 300.0, 375.0, "bonus_MutationLabel")
	# Spec Region 5 — Legacy Compat
	_assert_node_offsets(ui, "MutationIcon",      20.0, 390.0,  46.0, 416.0, "bonus_MutationIcon")
	_assert_node_offsets(ui, "MutationSlotLabel", 52.0, 390.0, 300.0, 416.0, "bonus_MutationSlotLabel")
	# Spec Region 6 — Contextual Center-Bottom
	_assert_node_offsets(ui, "AbsorbPromptLabel",   1400.0, 1800.0, 1800.0, 1830.0, "bonus_AbsorbPromptLabel")
	_assert_node_offsets(ui, "FusePromptLabel",     1400.0, 1834.0, 1800.0, 1864.0, "bonus_FusePromptLabel")
	_assert_node_offsets(ui, "AbsorbFeedbackLabel", 1400.0, 1800.0, 1800.0, 1830.0, "bonus_AbsorbFeedbackLabel")

	_free_ui(ui)


func test_bonus_exact_offsets_hints_children() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("bonus_offsets_hints", "game_ui.tscn failed to load")
		return

	var hints: Node = ui.get_node_or_null("Hints")
	if hints == null:
		_fail("bonus_offsets_hints", "Hints node not found")
		_free_ui(ui)
		return

	# Spec Region 7 — Input Hints (children of Hints)
	var hint_specs: Array = [
		["MoveHint",         1300.0, 12.0,  1600.0, 38.0],
		["JumpHint",         1300.0, 44.0,  1500.0, 70.0],
		["DetachRecallHint", 1300.0, 76.0,  1700.0, 102.0],
		["AbsorbHint",       1620.0, 12.0,  2000.0, 38.0],
	]
	for entry in hint_specs:
		var child_name: String = entry[0]
		var n: Control = hints.get_node_or_null(child_name) as Control
		if n == null:
			_fail("bonus_offsets_hints_" + child_name, "child node '" + child_name + "' not found in Hints")
			continue
		_assert_eq_float(entry[1], n.offset_left,   "bonus_hints_" + child_name + "_offset_left")
		_assert_eq_float(entry[2], n.offset_top,    "bonus_hints_" + child_name + "_offset_top")
		_assert_eq_float(entry[3], n.offset_right,  "bonus_hints_" + child_name + "_offset_right")
		_assert_eq_float(entry[4], n.offset_bottom, "bonus_hints_" + child_name + "_offset_bottom")

	_free_ui(ui)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- tests/ui/test_player_hud_layout.gd ---")
	_pass_count = 0
	_fail_count = 0

	# T-6.1: HPBar type (red phase — TextureProgressBar → ProgressBar)
	test_t61_hpbar_is_progress_bar()

	# T-6.2: HPBar is Range (regression guard; may pass before impl)
	test_t62_hpbar_is_range()

	# T-6.3: HPBar min_value, max_value, show_percentage (red phase)
	test_t63_hpbar_min_max_show_percentage()

	# T-6.4: All flat binding paths resolve (should pass before impl)
	test_t64_all_bindings_resolve()

	# T-6.5: Hints node resolves (should pass before impl)
	test_t65_hints_resolves()

	# T-6.6: Hints has 4 children (should pass before impl)
	test_t66_hints_children_count()

	# T-6.7: 28 pairwise disjointness checks (red phase — current nodes overlap)
	test_t67_always_visible_no_overlap()

	# T-6.8: All always-visible nodes within 3200x1880 (red phase — zero-area nodes)
	test_t68_nodes_within_viewport()

	# T-6.9: Legacy nodes don't intersect always-visible set (red phase)
	test_t69_legacy_nodes_no_overlap_with_always_visible()

	# T-6.10: Contextual prompts don't intersect always-visible set (red phase)
	test_t610_contextual_no_overlap_with_status()

	# T-6.11: InputHintsConfig default is false (red phase — currently true)
	test_t611_input_hints_config_default_false()

	# T-6.12: Legacy nodes visible=false by scene default (red phase — MutationIcon is true)
	test_t612_legacy_nodes_visible_false_default()

	# Bonus: exact offset value assertions for all repositioned nodes (all red phase)
	test_bonus_exact_offsets_status_strip()
	test_bonus_exact_offsets_mutation_panel()
	test_bonus_exact_offsets_lower_left_and_prompts()
	test_bonus_exact_offsets_hints_children()

	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
