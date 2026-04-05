#
# test_player_hud_layout.gd
#
# Behavioral tests for the Player HUD layout reorganization.
#
# Ticket:  player_hud.md
# Spec:    agent_context/agents/2_spec/player_hud_spec.md
#          Parts 1–6; test cases T-6.1 through T-6.12
#
# MAINT-HCSI (hud_components_scale_input): overlap / viewport / offset assertions use
# _control_design_rect() — scene-local offset_* (design space). See
# tests/ui/test_hud_components_scale_input.gd for global rect + hud_scale (HCSI-5/6).
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

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

# _assert_eq_float uses a wider tolerance (0.001) than test_utils (0.0001) for HUD pixel layout.
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


# ---------------------------------------------------------------------------
# Bounding rect helpers (Spec Part 6, Section 6.3)
# ---------------------------------------------------------------------------

# _rect: construct a Rect2 from explicit offset values.
func _rect(left: float, top: float, right: float, bottom: float) -> Rect2:
	return Rect2(Vector2(left, top), Vector2(right - left, bottom - top))


# _control_design_rect: scene-local layout rect from offset_* (HCSI-2 / HCSI-6 design space).
func _control_design_rect(n: Control) -> Rect2:
	return _rect(n.offset_left, n.offset_top, n.offset_right, n.offset_bottom)


# _node_rect: design-space rect for a named direct child of the GameUI CanvasLayer.
func _node_rect(ui: CanvasLayer, node_name: String) -> Rect2:
	var n: Control = ui.get_node(node_name) as Control
	return _control_design_rect(n)


# _hints_child_rect: design-space rect for a named child under Hints.
func _hints_child_rect(ui: CanvasLayer, child_name: String) -> Rect2:
	var hints: Control = ui.get_node("Hints") as Control
	var n: Control = hints.get_node(child_name) as Control
	return _control_design_rect(n)


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
		rects.append(_control_design_rect(n))

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
		var r: Rect2 = _control_design_rect(n)
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
		var legacy_rect: Rect2 = _control_design_rect(ln)
		for av_name in always_visible_names:
			var avn: Control = ui.get_node_or_null(av_name) as Control
			if avn == null:
				_fail("t-6.9_legacy_no_overlap", "always-visible node '" + av_name + "' not found")
				_free_ui(ui)
				return
			var av_rect: Rect2 = _control_design_rect(avn)
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
		var ctx_rect: Rect2 = _control_design_rect(cn)
		for av_name in always_visible_names:
			var avn: Control = ui.get_node_or_null(av_name) as Control
			if avn == null:
				_fail("t-6.10_contextual_no_overlap", "always-visible node '" + av_name + "' not found")
				_free_ui(ui)
				return
			var av_rect: Rect2 = _control_design_rect(avn)
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
	# HCSI-2: at hud_scale 1.0, scene offset_* remain the authoring source of truth.
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
# ADVERSARIAL EXTENSION — Test Breaker Agent
#
# 8 distinct failure modes targeting blind spots in the T-6.x suite.
# All tests are deterministic and reproducible. None change expected outputs.
# Each test is annotated with the mutation vector it defends against.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ADV-1 — Rect2.intersects shared-edge semantics oracle
#
# Mutation vector: An implementation that checks rect overlap with ">=" instead
# of ">" would incorrectly flag shared-edge rectangles as overlapping. The spec
# relies on Godot's Rect2.intersects() returning false for shared-edge pairs
# (e.g., HPBar bottom=28 and HPLabel top=28 are adjacent, not overlapping).
# This test documents and verifies that oracle assumption with no scene loading.
# If Godot's semantics ever change, this test surfaces it before the overlap
# suite becomes unreliable.
#
# Red phase: PASSES (engine behavior check, not impl-dependent).
# Green phase: PASSES (regression guard only).
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_rect2_intersects_shared_edge_semantics() -> void:
	# Two rectangles sharing only their right/left edge — should NOT intersect.
	var r1: Rect2 = Rect2(Vector2(20.0, 8.0), Vector2(380.0, 20.0))   # HPBar spec rect
	var r2: Rect2 = Rect2(Vector2(20.0, 28.0), Vector2(380.0, 26.0))  # one pixel below HPBar

	# Shared edge at Y=28: r1's bottom edge equals r2's top edge.
	# Godot 4 Rect2.intersects() excludes shared edges — returns false.
	_assert_false(
		r1.intersects(r2),
		"adv-1_shared_edge_y -- Rect2.intersects must return false for rectangles sharing only a Y edge (Godot 4 exclusive-edge semantics)"
	)

	# Same for X axis: two rects sharing only a right/left edge.
	var r3: Rect2 = Rect2(Vector2(20.0, 200.0), Vector2(26.0, 26.0))  # MutationIcon1 spec rect
	var r4: Rect2 = Rect2(Vector2(46.0, 200.0), Vector2(348.0, 26.0)) # starts at r3's right edge

	_assert_false(
		r3.intersects(r4),
		"adv-1_shared_edge_x -- Rect2.intersects must return false for rectangles sharing only an X edge (Godot 4 exclusive-edge semantics)"
	)

	# Confirm that actual overlap (1 pixel interior) DOES return true (oracle sanity).
	var r5: Rect2 = Rect2(Vector2(20.0, 200.0), Vector2(26.0, 26.0))
	var r6: Rect2 = Rect2(Vector2(45.0, 200.0), Vector2(348.0, 26.0)) # overlaps by 1px at X=45

	_assert_true(
		r5.intersects(r6),
		"adv-1_actual_overlap -- Rect2.intersects must return true for rectangles with 1px interior overlap (oracle sanity check)"
	)


# ---------------------------------------------------------------------------
# ADV-2 — HPBar exact class string (HSlider / non-ProgressBar Range mutation)
#
# Mutation vector: An implementation that substitutes HSlider, VSlider, SpinBox,
# or ScrollBar for ProgressBar would pass T-6.2 (is Range), would NOT pass
# T-6.1 (is ProgressBar), BUT the goal here is a mutation-matrix complement:
# assert get_class() == "ProgressBar" to make the exact Godot built-in class
# unambiguous and give a clear failure message naming the actual wrong class.
#
# Red phase: FAILS (current scene uses TextureProgressBar —
#   get_class() == "TextureProgressBar", not "ProgressBar").
# Green phase: PASSES.
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_hpbar_exact_class_string() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-2_hpbar_exact_class", "game_ui.tscn failed to load")
		return
	var hp_bar: Node = ui.get_node_or_null("HPBar")
	if hp_bar == null:
		_fail("adv-2_hpbar_exact_class", "HPBar node not found in game_ui.tscn")
		_free_ui(ui)
		return

	# get_class() returns the exact Godot built-in class string, unaffected by
	# script inheritance. This distinguishes ProgressBar from all other Range
	# subtypes (HSlider, VSlider, ScrollBar, SpinBox, TextureProgressBar).
	_assert_true(
		hp_bar.get_class() == "ProgressBar",
		"adv-2_hpbar_exact_class -- HPBar.get_class() must be 'ProgressBar'; got '"
		+ hp_bar.get_class() + "' -- catches HSlider/VSlider/ScrollBar substitutions that satisfy 'is Range'"
	)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# ADV-3 — Contextual prompts must be in the center-bottom region (Y >= 1780)
#
# Mutation vector: An implementation that repositions AbsorbPromptLabel,
# FusePromptLabel, AbsorbFeedbackLabel to Y=300 (below the mutation panel but
# above the 1780 floor) would pass T-6.10 (no overlap with always-visible set
# which ends at Y=266) but violate the spec's center-bottom region requirement.
# This test catches that failure mode with an explicit Y lower bound.
#
# Red phase: FAILS (current scene has all three at Y ~164–196).
# Green phase: PASSES (spec positions at Y=1800).
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_contextual_prompts_in_bottom_region() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-3_contextual_bottom_region", "game_ui.tscn failed to load")
		return

	var contextual_names: Array[String] = [
		"AbsorbPromptLabel", "FusePromptLabel", "AbsorbFeedbackLabel"
	]

	for node_name in contextual_names:
		var n: Control = ui.get_node_or_null(node_name) as Control
		if n == null:
			_fail("adv-3_contextual_bottom_region", "node '" + node_name + "' not found")
			_free_ui(ui)
			return

		# Spec Region 6: Y range 1800–1870, X range 1400–1800.
		# Conservative floor: offset_top >= 1780 (20px margin below spec minimum).
		# This also catches off-by-one repositioning to Y=1799.
		_assert_true(
			n.offset_top >= 1780.0,
			"adv-3_" + node_name + "_top_ge_1780 -- contextual prompt must be in center-bottom region (offset_top >= 1780); got "
			+ str(n.offset_top) + " -- catches nodes moved to Y~300 which pass T-6.10 but violate spec region"
		)

		# X lower bound: offset_left >= 1300 (not in top-left status strip).
		_assert_true(
			n.offset_left >= 1300.0,
			"adv-3_" + node_name + "_left_ge_1300 -- contextual prompt must not be in left panel (offset_left >= 1300); got "
			+ str(n.offset_left)
		)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# ADV-4 — FusionActiveLabel in left panel (X < 400, Y in 310–340)
#
# Mutation vector: An implementation that skips repositioning FusionActiveLabel
# (currently at Y=212–236) to Y=310–340 would pass T-6.7 only if it also moves
# other nodes. But a partial implementation that moves status strip nodes without
# moving FusionActiveLabel would leave it in the mid-panel range. This structural
# range test provides an explicit Y floor/ceiling assertion independent of the
# exact-offset bonus test.
#
# Red phase: FAILS (current FusionActiveLabel offset_top = 212.0, spec = 310.0).
# Green phase: PASSES.
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_fusion_active_label_in_left_panel() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-4_fusion_label_region", "game_ui.tscn failed to load")
		return

	var n: Control = ui.get_node_or_null("FusionActiveLabel") as Control
	if n == null:
		_fail("adv-4_fusion_label_region", "FusionActiveLabel not found in game_ui.tscn")
		_free_ui(ui)
		return

	# Region 3 spec: X 20–300, Y 310–340.
	_assert_true(
		n.offset_left >= 20.0 and n.offset_left < 400.0,
		"adv-4_fusion_label_x_in_left_panel -- FusionActiveLabel offset_left must be in [20, 400); got "
		+ str(n.offset_left)
	)
	_assert_true(
		n.offset_right <= 400.0,
		"adv-4_fusion_label_right_le_400 -- FusionActiveLabel must stay within left panel (offset_right <= 400); got "
		+ str(n.offset_right)
	)
	_assert_true(
		n.offset_top >= 310.0,
		"adv-4_fusion_label_top_ge_310 -- FusionActiveLabel offset_top must be >= 310 (spec Region 3); got "
		+ str(n.offset_top) + " -- catches nodes not moved from Y=212"
	)
	_assert_true(
		n.offset_bottom <= 340.0,
		"adv-4_fusion_label_bottom_le_340 -- FusionActiveLabel offset_bottom must be <= 340 (spec Region 3); got "
		+ str(n.offset_bottom)
	)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# ADV-5 — ColorRect type preservation for all slot icon nodes
#
# Mutation vector: If MutationIcon1, MutationIcon2, or MutationIcon are
# accidentally replaced with Panel, TextureRect, or other Control subclass,
# infection_ui.gd's `get_node_or_null("MutationIcon1") as ColorRect` cast
# returns null and slot icon colors stop updating silently.
# T-6.4 only verifies non-null by path — not the node type.
#
# Red phase: PASSES (current scene already has ColorRect nodes — this is a
# regression guard that would fail if implementation accidentally changed type).
# Green phase: PASSES.
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_colorect_node_types() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-5_colorect_types", "game_ui.tscn failed to load")
		return

	var colorect_names: Array[String] = ["MutationIcon1", "MutationIcon2", "MutationIcon"]

	for node_name in colorect_names:
		var n: Node = ui.get_node_or_null(node_name)
		if n == null:
			_fail("adv-5_colorect_types", "node '" + node_name + "' not found")
			_free_ui(ui)
			return

		# Must resolve to non-null ColorRect (not just non-null Node).
		_assert_true(
			n is ColorRect,
			"adv-5_" + node_name + "_is_colorect -- " + node_name
			+ " must be ColorRect so infection_ui.gd cast succeeds; got class '"
			+ n.get_class() + "' -- catches accidental Panel/TextureRect substitution"
		)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# ADV-6 — HPBar initial value == 100.0 (spec Part 2.2)
#
# Mutation vector: The spec requires `value = 100.0` on the HPBar scene node
# so the bar visually starts full in the editor. An implementation that omits
# this property leaves `value = 0` (Godot default for Range), showing an empty
# bar in-editor. T-6.3 checks min_value and max_value but not value.
#
# Red phase: FAILS (current TextureProgressBar has no explicit value property;
# Godot initializes Range.value to 0.0 by default).
# Green phase: PASSES (spec sets value = 100.0).
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_hpbar_initial_value() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-6_hpbar_initial_value", "game_ui.tscn failed to load")
		return

	var hp_bar: Node = ui.get_node_or_null("HPBar")
	if hp_bar == null:
		_fail("adv-6_hpbar_initial_value", "HPBar not found")
		_free_ui(ui)
		return
	if not (hp_bar is Range):
		_fail("adv-6_hpbar_initial_value", "HPBar is not Range; cannot read value")
		_free_ui(ui)
		return

	var bar: Range = hp_bar as Range
	# Spec Part 2.2: value = 100.0 — bar starts full in editor.
	_assert_eq_float(
		100.0, bar.value,
		"adv-6_hpbar_initial_value -- HPBar.value must be 100.0 at scene default per spec Part 2.2 AC; got "
		+ str(bar.value) + " -- a zero-value bar is invisible/empty in the editor"
	)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# ADV-7 — Hints container must be visible=true by scene default
#
# Mutation vector: A naive "hide all hints" implementation might set
# `visible = false` on the Hints Control node itself rather than on individual
# child labels. This permanently hides all input hints regardless of
# InputHintsConfig, because runtime code sets per-label visibility (not the
# container's). T-6.11 and T-6.12 verify per-label defaults but nothing verifies
# the container is not accidentally hidden.
#
# Red phase: PASSES (current scene has no explicit visible=false on Hints).
# Green phase: PASSES.
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_hints_container_visible_by_default() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-7_hints_container_visible", "game_ui.tscn failed to load")
		return

	var hints: Node = ui.get_node_or_null("Hints")
	if hints == null:
		_fail("adv-7_hints_container_visible", "Hints node not found")
		_free_ui(ui)
		return

	# Hints must be visible=true so per-label visibility logic in
	# _update_input_hints_visibility() is not permanently masked.
	_assert_true(
		hints.visible,
		"adv-7_hints_container_visible -- Hints.visible must be true by scene default; "
		+ "a hidden container permanently masks all hint labels regardless of InputHintsConfig"
	)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# ADV-8 — Dynamic node name patterns in infection_ui.gd must resolve
#
# Mutation vector: infection_ui.gd builds node names dynamically:
#   "MutationSlot" + str(n) + "Label"  (n = 1, 2)
#   "MutationIcon" + str(n)            (n = 1, 2)
# T-6.4 checks these paths by their static string values, but does not verify
# them via the same dynamic construction pattern used in infection_ui.gd. A
# node named "MutationSlot_1_Label" (underscore variant) would fail the dynamic
# lookup silently. This test explicitly constructs the names using the same
# string template as infection_ui.gd to confirm the node name contract.
#
# Red phase: PASSES (nodes already exist with correct names).
# Green phase: PASSES (regression guard for renaming accidents).
# CHECKPOINT
# ---------------------------------------------------------------------------

func test_adv_dynamic_slot_node_names_match_infection_ui_pattern() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("adv-8_dynamic_slot_names", "game_ui.tscn failed to load")
		return

	# Replicate the exact string-construction pattern from infection_ui.gd
	# _update_slot_display(): "MutationSlot" + str(slot_number) + "Label"
	# and "MutationIcon" + str(slot_number), where slot_number is 1 or 2.
	for slot_number in [1, 2]:
		var label_name: String = "MutationSlot" + str(slot_number) + "Label"
		var icon_name: String = "MutationIcon" + str(slot_number)

		var label_node: Node = ui.get_node_or_null(label_name)
		_assert_true(
			label_node != null,
			"adv-8_dynamic_" + label_name + " -- node constructed as 'MutationSlot' + str("
			+ str(slot_number) + ") + 'Label' must resolve; infection_ui.gd uses this exact pattern"
		)

		var icon_node: Node = ui.get_node_or_null(icon_name)
		_assert_true(
			icon_node != null,
			"adv-8_dynamic_" + icon_name + " -- node constructed as 'MutationIcon' + str("
			+ str(slot_number) + ") must resolve; infection_ui.gd uses this exact pattern"
		)

		# Verify Label type for label node
		if label_node != null:
			_assert_true(
				label_node is Label,
				"adv-8_dynamic_" + label_name + "_is_label -- dynamic slot label must be Label type; got '"
				+ label_node.get_class() + "'"
			)

		# Verify ColorRect type for icon node
		if icon_node != null:
			_assert_true(
				icon_node is ColorRect,
				"adv-8_dynamic_" + icon_name + "_is_colorect -- dynamic slot icon must be ColorRect type; got '"
				+ icon_node.get_class() + "'"
			)

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

	# --- Adversarial extension (Test Breaker Agent) ---

	# ADV-1: Rect2.intersects shared-edge semantics oracle (regression guard; passes pre-impl)
	test_adv_rect2_intersects_shared_edge_semantics()

	# ADV-2: HPBar exact class string — catches HSlider/VSlider substitution (red phase)
	test_adv_hpbar_exact_class_string()

	# ADV-3: Contextual prompts Y >= 1780 center-bottom region guard (red phase)
	test_adv_contextual_prompts_in_bottom_region()

	# ADV-4: FusionActiveLabel structural region bounds X<400, Y 310-340 (red phase)
	test_adv_fusion_active_label_in_left_panel()

	# ADV-5: ColorRect type preservation for all slot icon nodes (regression guard)
	test_adv_colorect_node_types()

	# ADV-6: HPBar initial value == 100.0 by scene default (red phase)
	test_adv_hpbar_initial_value()

	# ADV-7: Hints container visible=true by scene default (regression guard)
	test_adv_hints_container_visible_by_default()

	# ADV-8: Dynamic slot node name pattern matches infection_ui.gd construction (regression guard)
	test_adv_dynamic_slot_node_names_match_infection_ui_pattern()

	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
