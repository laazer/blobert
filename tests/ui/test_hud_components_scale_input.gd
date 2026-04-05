#
# test_hud_components_scale_input.gd
#
# Behavioral tests for MAINT-HCSI — hud_components_scale_input.
# Spec: project_board/specs/hud_components_scale_input_spec.md
#
# HCSI-4: GameUI root type/name/script + flat and nested get_node paths on instantiated root.
# HCSI-1: single exported hud_scale (float), default 1.0.
# HCSI-5: uniform scale — global rect sizes scale ~linearly with hud_scale; same factor across widgets.
# HCSI-6: at default scale, transformed global rects stay within 3200×1880 design viewport (spot check).
#
# Pre-implementation: HCSI-1 / HCSI-5 / HCSI-6 fail until infection_ui.gd exposes hud_scale and applies it.
#
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _HUD_VP_W: float = 3200.0
const _HUD_VP_H: float = 1880.0
const _FLOAT_TOL: float = 0.001
const _RATIO_TOL: float = 0.05
const _SCALE_HIGH: float = 2.0


func _assert_eq_float(expected: float, actual: float, test_name: String) -> void:
	if absf(expected - actual) < _FLOAT_TOL:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + " got " + str(actual))


func _assert_ratio_near(expected: float, num: float, denom: float, test_name: String) -> void:
	if denom <= _FLOAT_TOL:
		_fail(test_name, "baseline size too small for ratio check (denom=" + str(denom) + ")")
		return
	var r: float = num / denom
	if absf(r - expected) <= _RATIO_TOL:
		_pass(test_name)
	else:
		_fail(test_name, "expected ratio ~" + str(expected) + " got " + str(r) + " (num=" + str(num) + " denom=" + str(denom) + ")")


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


func _script_path_ends_with(ui: Node, suffix: String) -> bool:
	var scr: Variant = ui.get_script()
	if scr == null:
		return false
	var p: String = (scr as Resource).resource_path
	return p.ends_with(suffix)


# ---------------------------------------------------------------------------
# HCSI-4 — root + path contract on instantiated GameUI
# ---------------------------------------------------------------------------

func test_hcsi4_root_canvas_layer_named_gameui_with_infection_script() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-4_load", "game_ui.tscn failed to load")
		return
	_assert_true(
		ui is CanvasLayer,
		"hcsi-4_root_is_canvas_layer -- GameUI root must be CanvasLayer (HCSI-4.1)"
	)
	_assert_true(
		ui.name == "GameUI",
		"hcsi-4_root_name_gameui -- root name must be GameUI (HCSI-4.1)"
	)
	_assert_true(
		_script_path_ends_with(ui, "infection_ui.gd"),
		"hcsi-4_root_script_infection_ui -- root script must be infection_ui.gd (HCSI-4.1)"
	)
	_free_ui(ui)


func test_hcsi4_flat_widget_paths_resolve_on_root() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-4_flat_paths_load", "game_ui.tscn failed to load")
		return

	var flat_paths: Array[String] = [
		"HPBar", "HPLabel", "ChunkStatusLabel", "ClingStatusLabel", "Hints",
		"AbsorbPromptLabel", "FusePromptLabel", "FusionActiveLabel", "AbsorbFeedbackLabel",
		"MutationIcon", "MutationSlotLabel", "MutationSlot1Label", "MutationIcon1",
		"MutationSlot2Label", "MutationIcon2", "MutationLabel",
	]
	for path in flat_paths:
		var node: Node = ui.get_node_or_null(path)
		_assert_true(
			node != null,
			"hcsi-4_path_" + path + " -- get_node_or_null('" + path + "') non-null on GameUI root (HCSI-4.2)"
		)

	_free_ui(ui)


func test_hcsi4_nested_hints_paths_resolve() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-4_nested_load", "game_ui.tscn failed to load")
		return

	var nested: Array[String] = [
		"Hints/MoveHint", "Hints/JumpHint", "Hints/DetachRecallHint", "Hints/AbsorbHint",
	]
	for path in nested:
		var node: Node = ui.get_node_or_null(path)
		_assert_true(
			node != null,
			"hcsi-4_nested_" + path.replace("/", "_")
			+ " -- get_node_or_null('" + path + "') non-null (HCSI-4.3)"
		)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# HCSI-1 — single hud_scale parameter, default 1.0
# ---------------------------------------------------------------------------

func test_hcsi1_hud_scale_exists_and_defaults_to_one() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-1_load", "game_ui.tscn failed to load")
		return

	if not ("hud_scale" in ui):
		_fail(
			"hcsi-1_hud_scale_exported",
			"GameUI must expose 'hud_scale' (float) per HCSI-1 — not found on instance"
		)
		_free_ui(ui)
		return

	var v: Variant = ui.get("hud_scale")
	if typeof(v) != TYPE_FLOAT:
		_fail(
			"hcsi-1_hud_scale_type",
			"hud_scale must be TYPE_FLOAT, got type " + str(typeof(v)) + " — HCSI-1"
		)
		_free_ui(ui)
		return

	_assert_eq_float(1.0, v as float, "hcsi-1_hud_scale_default -- hud_scale must default to 1.0 (HCSI-1.2 / HCSI-2)")

	_free_ui(ui)


# ---------------------------------------------------------------------------
# HCSI-5 — uniform scale via global rect proportions + cross-widget same factor
# ---------------------------------------------------------------------------

func test_hcsi5_global_sizes_scale_uniformly_with_hud_scale() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-5_load", "game_ui.tscn failed to load")
		return

	if not ("hud_scale" in ui):
		_fail("hcsi-5_hud_scale_missing", "hud_scale required for HCSI-5 scale test")
		_free_ui(ui)
		return

	var hp: Control = ui.get_node_or_null("HPBar") as Control
	var move_hint: Control = ui.get_node_or_null("Hints/MoveHint") as Control
	if hp == null or move_hint == null:
		_fail("hcsi-5_nodes", "HPBar and Hints/MoveHint required for HCSI-5")
		_free_ui(ui)
		return

	ui.set("hud_scale", 1.0)
	var b_hp: Vector2 = hp.get_global_rect().size
	var b_mh: Vector2 = move_hint.get_global_rect().size

	if b_hp.x <= _FLOAT_TOL or b_hp.y <= _FLOAT_TOL:
		_fail("hcsi-5_baseline_hp", "HPBar global size must be non-degenerate at hud_scale=1.0")
		_free_ui(ui)
		return
	if b_mh.x <= _FLOAT_TOL or b_mh.y <= _FLOAT_TOL:
		_fail("hcsi-5_baseline_movehint", "MoveHint global size must be non-degenerate at hud_scale=1.0")
		_free_ui(ui)
		return

	ui.set("hud_scale", _SCALE_HIGH)
	var a_hp: Vector2 = hp.get_global_rect().size
	var a_mh: Vector2 = move_hint.get_global_rect().size

	_assert_ratio_near(_SCALE_HIGH, a_hp.x, b_hp.x, "hcsi-5_hp_global_width_scales -- HCSI-5.1")
	_assert_ratio_near(_SCALE_HIGH, a_hp.y, b_hp.y, "hcsi-5_hp_global_height_scales -- HCSI-5.1")
	_assert_ratio_near(_SCALE_HIGH, a_mh.x, b_mh.x, "hcsi-5_movehint_global_width_scales -- HCSI-5.1")
	_assert_ratio_near(_SCALE_HIGH, a_mh.y, b_mh.y, "hcsi-5_movehint_global_height_scales -- HCSI-5.1")

	var rx_hp: float = a_hp.x / b_hp.x
	var rx_mh: float = a_mh.x / b_mh.x
	if absf(rx_hp - rx_mh) <= _RATIO_TOL:
		_pass("hcsi-5_same_scale_factor_hp_vs_movehint -- uniform scalar across HUD subtree (HCSI-5.1)")
	else:
		_fail(
			"hcsi-5_same_scale_factor_hp_vs_movehint",
			"HP vs MoveHint X scale factors differ: " + str(rx_hp) + " vs " + str(rx_mh)
		)

	ui.set("hud_scale", 1.0)
	_free_ui(ui)


func test_hcsi5_hud_scale_property_tracks_set_value() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-5b_load", "game_ui.tscn failed to load")
		return
	if not ("hud_scale" in ui):
		_fail("hcsi-5b_hud_scale_missing", "hud_scale required")
		_free_ui(ui)
		return

	ui.set("hud_scale", _SCALE_HIGH)
	_assert_eq_float(_SCALE_HIGH, ui.get("hud_scale") as float, "hcsi-5b_hud_scale_reads_back -- property tracks setter (HCSI-6 spot)")

	ui.set("hud_scale", 1.0)
	_free_ui(ui)


# ---------------------------------------------------------------------------
# HCSI-6 — transformed bounds at default scale (global space, not raw offset caps)
# ---------------------------------------------------------------------------

func test_hcsi6_global_rects_within_design_viewport_at_default_scale() -> void:
	var ui: CanvasLayer = _load_game_ui()
	if ui == null:
		_fail("hcsi-6_load", "game_ui.tscn failed to load")
		return
	if not ("hud_scale" in ui):
		_fail("hcsi-6_hud_scale_missing", "hud_scale required for HCSI-6 default-scale global check")
		_free_ui(ui)
		return

	ui.set("hud_scale", 1.0)

	var names: Array[String] = ["HPBar", "HPLabel", "FusePromptLabel"]
	for node_name in names:
		var c: Control = ui.get_node_or_null(node_name) as Control
		if c == null:
			_fail("hcsi-6_" + node_name + "_missing", "node not found")
			_free_ui(ui)
			return
		var gr: Rect2 = c.get_global_rect()
		var tol: float = 1.0
		_assert_true(
			gr.position.x >= -tol and gr.position.y >= -tol,
			"hcsi-6_" + node_name + "_global_top_left -- global rect within viewport (HCSI-6)"
		)
		_assert_true(
			gr.end.x <= _HUD_VP_W + tol and gr.end.y <= _HUD_VP_H + tol,
			"hcsi-6_" + node_name + "_global_bottom_right -- global rect within 3200×1880 at hud_scale=1.0 (HCSI-6)"
		)

	_free_ui(ui)


# ---------------------------------------------------------------------------
# run_all
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- tests/ui/test_hud_components_scale_input.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_hcsi4_root_canvas_layer_named_gameui_with_infection_script()
	test_hcsi4_flat_widget_paths_resolve_on_root()
	test_hcsi4_nested_hints_paths_resolve()
	test_hcsi1_hud_scale_exists_and_defaults_to_one()
	test_hcsi5_global_sizes_scale_uniformly_with_hud_scale()
	test_hcsi5_hud_scale_property_tracks_set_value()
	test_hcsi6_global_rects_within_design_viewport_at_default_scale()

	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
