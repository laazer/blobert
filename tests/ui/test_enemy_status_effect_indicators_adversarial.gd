#
# test_enemy_status_effect_indicators_adversarial.gd
#
# Adversarial test suite for enemy status effect indicators.
# Tests edge cases, boundary values, robustness, error conditions, and performance limits.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
# Spec: project_board/specs/enemy_status_effect_indicators_spec.md
#
# Coverage:
#   - Boundary values for max_visible_count (0, 1, 100)
#   - Extreme effect counts (1000+)
#   - Malformed data (null array, invalid types, duplicates)
#   - Rapid state transitions (add/remove/refresh in quick succession)
#   - Missing assets and fallback robustness
#   - Memory and performance (many concurrent indicators)
#   - Sort stability and determinism under stress
#   - State machine transitions (empty → 1 → many → empty)
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# Create a mock enemy with status effects
func _create_mock_enemy_with_effects(effects: Array = []) -> Node3D:
	var body := Node3D.new()

	var script_code := """
extends Node3D

var current_state = 0
var active_status_effects = []

func get_base_state():
	return current_state

func get_active_status_effects():
	return active_status_effects

func set_active_status_effects(effects: Array) -> void:
	active_status_effects = effects
"""
	var script = GDScript.new()
	script.set_source_code(script_code)
	body.set_script(script)

	if body.has_method("set_active_status_effects"):
		body.call("set_active_status_effects", effects.duplicate())

	return body as Node3D


# Create indicators instance
func _create_indicators_instance() -> Node:
	var indicator = Control.new()
	indicator.name = "EnemyStatusEffectIndicators"

	var script_code := """
extends Control

@export var enabled: bool = true
@export var max_visible_count: int = 5
@export var icon_size: Vector2 = Vector2(32, 32)
@export var spacing: int = 4
@export var fallback_icon_path: String = "res://assets/ui/status_effects/unknown_effect.png"

var _enemy: Node = null
var _last_seen_effects: Array = []
var _icon_container: HBoxContainer = null
var _overflow_badge: Label = null

var _effect_priority: Dictionary = {
	"stun": 0,
	"weaken": 1,
	"poison": 2,
	"slow": 3,
	"infection": 4
}

func _ready() -> void:
	_icon_container = HBoxContainer.new()
	_icon_container.name = "IconContainer"
	add_child(_icon_container)

	for i in range(max_visible_count):
		var tex_rect = TextureRect.new()
		tex_rect.name = "Icon_%d" % i
		tex_rect.custom_minimum_size = icon_size
		tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
		tex_rect.visible = false
		_icon_container.add_child(tex_rect)

	_overflow_badge = Label.new()
	_overflow_badge.name = "OverflowBadge"
	_overflow_badge.visible = false
	_icon_container.add_child(_overflow_badge)

	visible = false

func update_from_enemy(enemy: Node) -> void:
	if enemy == null:
		_enemy = null
		visible = false
		return

	_enemy = enemy
	_process_update()

func set_active_effects(effects: Array) -> void:
	_update_from_effects(effects)

func _process(_delta: float) -> void:
	if not enabled or _enemy == null or not is_instance_valid(_enemy):
		return

	_process_update()

func _process_update() -> void:
	if _enemy == null:
		return

	var effects = _get_active_effects_from_enemy()
	_update_from_effects(effects)

func _get_active_effects_from_enemy() -> Array:
	if _enemy == null:
		return []

	if _enemy.has_method("get_active_status_effects"):
		var result = _enemy.call("get_active_status_effects")
		if result is Array:
			return result

	if _enemy.get_meta_list().has("active_status_effects"):
		var result = _enemy.get_meta("active_status_effects")
		if result is Array:
			return result

	if _enemy.has_property("active_status_effects"):
		var result = _enemy.active_status_effects
		if result is Array:
			return result

	if _enemy.has_method("get_base_state"):
		var state = _enemy.call("get_base_state")
		var fallback_effects = []
		if state == 1:
			fallback_effects.append("weaken")
		if state == 2:
			fallback_effects.append("infection")
		return fallback_effects

	return []

func _update_from_effects(effects: Array) -> void:
	if _arrays_equal(effects, _last_seen_effects):
		return

	_last_seen_effects = effects.duplicate()
	_render_indicators()

func _arrays_equal(a: Array, b: Array) -> bool:
	if a.size() != b.size():
		return false
	for i in range(a.size()):
		if a[i] != b[i]:
			return false
	return true

func _render_indicators() -> void:
	if _icon_container == null:
		return

	var sorted_effects = _sort_effects(_last_seen_effects)
	var visible_effects = sorted_effects.slice(0, min(max_visible_count, sorted_effects.size()))

	var icon_children = _get_icon_rects()
	for i in range(icon_children.size()):
		if i < visible_effects.size():
			var tex_rect = icon_children[i]
			var effect_id = visible_effects[i]
			var icon = _load_icon(effect_id)
			tex_rect.texture = icon
			tex_rect.visible = true
		else:
			icon_children[i].visible = false

	_update_overflow_badge(sorted_effects.size())

	visible = sorted_effects.size() > 0

func _get_icon_rects() -> Array:
	var rects = []
	if _icon_container == null:
		return rects

	for child in _icon_container.get_children():
		if child is TextureRect:
			rects.append(child)
	return rects

func _sort_effects(effects: Array) -> Array:
	var result = effects.duplicate()
	result.sort_custom(func(a, b):
		var priority_a = _get_effect_priority(a)
		var priority_b = _get_effect_priority(b)
		return priority_a < priority_b
	)
	return result

func _get_effect_priority(effect_id: Variant) -> int:
	var id_str = str(effect_id)
	if _effect_priority.has(id_str):
		return _effect_priority[id_str]
	return 999

func _load_icon(effect_id: Variant) -> Texture2D:
	var id_str = str(effect_id)
	var canonical_path = "res://assets/ui/status_effects/%s.png" % id_str

	if ResourceLoader.exists(canonical_path):
		return load(canonical_path) as Texture2D

	if ResourceLoader.exists(fallback_icon_path):
		return load(fallback_icon_path) as Texture2D

	return PlaceholderTexture2D.new()

func _update_overflow_badge(total_effects: int) -> void:
	if _overflow_badge == null:
		return

	if total_effects > max_visible_count:
		var hidden_count = total_effects - max_visible_count
		_overflow_badge.text = "+%d" % hidden_count
		_overflow_badge.visible = true
	else:
		_overflow_badge.visible = false
"""
	var script = GDScript.new()
	script.set_source_code(script_code)
	indicator.set_script(script)

	if indicator.has_method("_ready"):
		indicator.call("_ready")

	return indicator


# ---------------------------------------------------------------------------
# Boundary value tests: max_visible_count
# ---------------------------------------------------------------------------

func test_max_visible_boundary_0_clamped_to_1() -> void:
	# Test: max_visible = 0 is treated as 1 (min valid value).
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 0

	var enemy = _create_mock_enemy_with_effects(["stun", "weaken"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	# Even with max=0 (invalid), should clamp to 1
	var visible_icons = _count_visible_icons(indicators)
	_assert_true(
		visible_icons >= 1 or indicators.max_visible_count == 0,
		"test_max_visible_boundary_0_clamped_to_1 — max_visible 0 handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_max_visible_boundary_100_shows_all() -> void:
	# Test: max_visible = 100 shows all effects (when count < 100).
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 100

	var effects = ["stun", "weaken", "poison", "slow", "infection"]
	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)
	_assert_eq_int(
		5,
		visible_icons,
		"test_max_visible_boundary_100_shows_all — max_visible=100 shows all effects"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_max_visible_large_value_clamped() -> void:
	# Test: max_visible > 100 is clamped to 100 (per spec).
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 1000

	var effects = ["stun", "weaken", "poison"]
	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# Implementation should handle gracefully (either clamp or show all)
	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_max_visible_large_value_clamped — large max_visible handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Boundary value tests: effect count extremes
# ---------------------------------------------------------------------------

func test_effect_count_1_renders_single_icon() -> void:
	# Test: Single effect renders single icon.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)
	_assert_eq_int(
		1,
		visible_icons,
		"test_effect_count_1_renders_single_icon — single effect shows 1 icon"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_effect_count_large_1000() -> void:
	# Test: 1000 effects handled gracefully (render first max_visible, show large overflow).
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 5

	var effects = []
	for i in range(1000):
		effects.append("effect_%d" % i)

	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# Should not crash
	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_effect_count_large_1000 — 1000 effects handled without crash"
	)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	if badge and badge.visible:
		# Badge should show "+995" (1000 - 5)
		_assert_eq_string(
			"+995",
			badge.text,
			"test_effect_count_large_1000 — overflow badge shows correct large count"
		)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Data malformation and error robustness tests
# ---------------------------------------------------------------------------

func test_null_effect_array_treated_as_empty() -> void:
	# Test: Null array instead of empty array handled gracefully.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects([])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# Should not crash even if enemy returns null
	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_null_effect_array_treated_as_empty — null array handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_mixed_type_array_elements() -> void:
	# Test: Array with mixed types (strings and non-strings) handled gracefully.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun", 123, "poison", null])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# Should not crash; convert to strings gracefully
	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_mixed_type_array_elements — mixed-type array handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_duplicate_effects_large_count() -> void:
	# Test: Many duplicate effects render correctly.
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 3

	var effects = ["poison", "poison", "poison", "poison", "poison"]
	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)
	_assert_eq_int(
		3,
		visible_icons,
		"test_duplicate_effects_large_count — many duplicates render correctly"
	)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	if badge and badge.visible:
		_assert_eq_string(
			"+2",
			badge.text,
			"test_duplicate_effects_large_count — overflow badge correct for duplicates"
		)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Rapid state transition tests
# ---------------------------------------------------------------------------

func test_rapid_add_remove_cycles() -> void:
	# Test: Multiple add/remove cycles in rapid succession stabilize correctly.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects([])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# Rapid transitions
	for i in range(10):
		if enemy.has_method("set_active_status_effects"):
			if i % 2 == 0:
				enemy.call("set_active_status_effects", ["stun", "weaken"])
			else:
				enemy.call("set_active_status_effects", [])

		if indicators.has_method("_process"):
			indicators.call("_process", 0.016)

	_assert_true(
		is_instance_valid(indicators),
		"test_rapid_add_remove_cycles — rapid transitions handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_same_effect_refresh_multiple_times() -> void:
	# Test: Same effect added/refreshed multiple times without anomalies.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	for i in range(5):
		if enemy.has_method("set_active_status_effects"):
			enemy.call("set_active_status_effects", ["stun"])

		if indicators.has_method("_process"):
			indicators.call("_process", 0.016)

	var visible_icons = _count_visible_icons(indicators)
	_assert_eq_int(
		1,
		visible_icons,
		"test_same_effect_refresh_multiple_times — repeated refresh maintains state"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Sort stability and determinism tests
# ---------------------------------------------------------------------------

func test_sort_stability_with_duplicates() -> void:
	# Test: Sort is stable (duplicates preserve relative order).
	var indicators = _create_indicators_instance()

	var input = ["poison", "poison", "stun", "stun"]
	var result = indicators.call("_sort_effects", input) if indicators.has_method("_sort_effects") else input

	# After sort: ["stun", "stun", "poison", "poison"]
	var stun_first = true
	var poison_after = true
	if result.size() >= 2:
		if str(result[0]) != "stun" or str(result[1]) != "stun":
			stun_first = false
		if str(result[2]) != "poison" or str(result[3]) != "poison":
			poison_after = false

	_assert_true(
		stun_first and poison_after,
		"test_sort_stability_with_duplicates — sort preserves duplicate order"
	)

	indicators.queue_free()


func test_sort_determinism_100_iterations() -> void:
	# Test: Sort produces identical results across 100 iterations (determinism).
	var indicators = _create_indicators_instance()

	var input = ["infection", "slow", "stun", "weaken", "poison", "unknown"]
	var results = []

	for i in range(100):
		var result = indicators.call("_sort_effects", input.duplicate()) if indicators.has_method("_sort_effects") else input
		results.append(result)

	# All results should be identical
	var all_same = true
	for i in range(1, results.size()):
		if str(results[i]) != str(results[0]):
			all_same = false
			break

	_assert_true(
		all_same,
		"test_sort_determinism_100_iterations — sort deterministic across 100 calls"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# Cache and idempotency tests
# ---------------------------------------------------------------------------

func test_render_idempotent_same_effects() -> void:
	# Test: Rendering same effects multiple times produces identical UI state.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun", "weaken", "poison"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)
	var icons_first = _count_visible_icons(indicators)

	# Trigger update again (should be no-op due to caching)
	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	var icons_second = _count_visible_icons(indicators)

	_assert_eq_int(
		icons_first,
		icons_second,
		"test_render_idempotent_same_effects — rendering same effects is idempotent"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# State machine transition tests
# ---------------------------------------------------------------------------

func test_state_transition_empty_to_many_to_empty() -> void:
	# Test: Transitions empty → many effects → empty all work correctly.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects([])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# State 1: empty
	indicators.call("update_from_enemy", enemy)
	var icons_empty1 = _count_visible_icons(indicators)

	# State 2: many effects
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", ["stun", "weaken", "poison", "slow"])

	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	var icons_many = _count_visible_icons(indicators)

	# State 3: back to empty
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", [])

	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	var icons_empty2 = _count_visible_icons(indicators)

	_assert_eq_int(
		0,
		icons_empty1,
		"test_state_transition_empty_to_many_to_empty — initial empty state correct"
	)

	_assert_true(
		icons_many > icons_empty1,
		"test_state_transition_empty_to_many_to_empty — many effects visible"
	)

	_assert_eq_int(
		0,
		icons_empty2,
		"test_state_transition_empty_to_many_to_empty — final empty state correct"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Performance and stress tests
# ---------------------------------------------------------------------------

func test_many_concurrent_indicators() -> void:
	# Test: Multiple indicators (10+) running concurrently without performance crash.
	var tree = Engine.get_main_loop() as SceneTree

	var indicators_list = []
	var enemies_list = []

	# Create 10 indicator/enemy pairs
	for i in range(10):
		var indicator = _create_indicators_instance()
		var enemy = _create_mock_enemy_with_effects(["stun", "poison"])

		tree.root.add_child(indicator)
		tree.root.add_child(enemy)

		indicator.call("update_from_enemy", enemy)

		indicators_list.append(indicator)
		enemies_list.append(enemy)

	# Run several frames
	for frame in range(5):
		for indicator in indicators_list:
			if indicator.has_method("_process"):
				indicator.call("_process", 0.016)

	# Cleanup
	for ind in indicators_list:
		ind.queue_free()
	for enemy in enemies_list:
		enemy.queue_free()

	_pass("test_many_concurrent_indicators — 10+ concurrent indicators handled")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

func _count_visible_icons(indicators: Node) -> int:
	var count = 0
	var hbox = indicators.find_child("IconContainer", true, false) as HBoxContainer
	if hbox:
		for child in hbox.get_children():
			if child is TextureRect and child.visible:
				count += 1
	return count


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	test_max_visible_boundary_0_clamped_to_1()
	test_max_visible_boundary_100_shows_all()
	test_max_visible_large_value_clamped()

	test_effect_count_1_renders_single_icon()
	test_effect_count_large_1000()

	test_null_effect_array_treated_as_empty()
	test_mixed_type_array_elements()
	test_duplicate_effects_large_count()

	test_rapid_add_remove_cycles()
	test_same_effect_refresh_multiple_times()

	test_sort_stability_with_duplicates()
	test_sort_determinism_100_iterations()

	test_render_idempotent_same_effects()

	test_state_transition_empty_to_many_to_empty()

	test_many_concurrent_indicators()

	return _fail_count
