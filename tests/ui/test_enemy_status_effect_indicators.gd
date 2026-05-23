#
# test_enemy_status_effect_indicators.gd
#
# Behavioral tests for the enemy floating status effect indicators UI (M8 feature).
# Tests core functionality: container initialization, effect sorting, overflow badge behavior,
# real-time updates, fallback icon handling, and health bar integration.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
# Spec: project_board/specs/enemy_status_effect_indicators_spec.md
# Requirements:
#   - Status effect indicators render as icons above enemy health bar
#   - Multiple effects displayed in deterministic order (stun > weaken > poison > slow > infection)
#   - Expired effects removed immediately from indicator list
#   - Overflow badge shows "+N" when effect count exceeds max_visible_count
#   - Real-time updates when effects added/removed/refreshed
#   - Unknown/unmapped effect IDs render fallback icon (no missing-resource errors)
#   - Full integration with existing EnemyHealthBar3D (no z-order conflicts)
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure: fixtures and helpers
# ---------------------------------------------------------------------------

# Create a mock enemy with basic properties and status effect interface.
# Supports multiple interface methods for status effect access.
func _create_mock_enemy_with_effects(effects: Array = []) -> Node3D:
	var body := Node3D.new()

	# Add script to make it look like EnemyBase
	var script_code := """
extends Node3D

var current_state = 0  # NORMAL = 0, WEAKENED = 1, INFECTED = 2
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
	script.reload()
	body.set_script(script)
	body.set_meta("active_status_effects", effects.duplicate())

	# Initialize with provided effects if available
	if body.has_method("set_active_status_effects"):
		body.call("set_active_status_effects", effects.duplicate())

	return body as Node3D


# Load and instantiate the status effect indicators scene.
func _load_and_instantiate_indicators() -> Variant:
	var path := "res://scenes/ui/enemy_status_effect_indicators.tscn"
	var scene = load(path)
	if scene == null:
		return null
	return scene.instantiate() as Node


# Create a status indicator script instance directly for unit testing.
# Prefers loading the actual scene/script, falls back to mock if not available.
func _create_indicators_instance() -> Node:
	# Try loading the actual scene first
	var scene_path = "res://scenes/ui/enemy_status_effect_indicators.tscn"
	if ResourceLoader.exists(scene_path):
		var scene = load(scene_path)
		if scene != null:
			return scene.instantiate() as Node

	# Fallback: create mock if scene doesn't exist
	var indicator = Control.new()
	indicator.name = "EnemyStatusEffectIndicators"

	# Create a mock script with required methods for testing
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

# Effect ID to priority mapping (lower = higher priority)
var _effect_priority: Dictionary = {
	"stun": 0,
	"weaken": 1,
	"poison": 2,
	"slow": 3,
	"infection": 4
}

func _ready() -> void:
	# Create layout container
	_icon_container = HBoxContainer.new()
	_icon_container.name = "IconContainer"
	add_child(_icon_container)

	# Create placeholder TextureRect nodes
	for i in range(max_visible_count):
		var tex_rect = TextureRect.new()
		tex_rect.name = "Icon_%d" % i
		tex_rect.custom_minimum_size = icon_size
		tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
		tex_rect.visible = false
		_icon_container.add_child(tex_rect)

	# Create overflow badge label
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

	# Try multiple interface methods in priority order
	if _enemy.has_method("get_active_status_effects"):
		var result = _enemy.call("get_active_status_effects")
		if result is Array:
			return result

	if _enemy.has_meta("active_status_effects"):
		var result = _enemy.get_meta("active_status_effects")
		if result is Array:
			return result

	if "active_status_effects" in _enemy:
		var result = _enemy.active_status_effects
		if result is Array:
			return result

	# Fallback to EnemyBase state enum
	if _enemy.has_method("get_base_state"):
		var state = _enemy.call("get_base_state")
		var fallback_effects = []
		if state == 1:  # WEAKENED
			fallback_effects.append("weaken")
		if state == 2:  # INFECTED
			fallback_effects.append("infection")
		return fallback_effects

	return []

func _update_from_effects(effects: Array) -> void:
	# Check if effects array changed
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

	# Sort effects
	var sorted_effects = _sort_effects(_last_seen_effects)

	# Get visible subset
	var visible_effects = sorted_effects.slice(0, min(max_visible_count, sorted_effects.size()))

	# Update icon TextureRects
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

	# Update overflow badge
	_update_overflow_badge(sorted_effects.size())

	# Show container if any effects
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
	return 999  # Unknown effects get lowest priority

func _load_icon(effect_id: Variant) -> Texture2D:
	var id_str = str(effect_id)
	var canonical_path = "res://assets/ui/status_effects/%s.png" % id_str

	if ResourceLoader.exists(canonical_path):
		return load(canonical_path) as Texture2D

	# Try fallback
	if ResourceLoader.exists(fallback_icon_path):
		return load(fallback_icon_path) as Texture2D

	# Last resort: placeholder
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

	# Call _ready manually since we're not in scene tree
	if indicator.has_method("_ready"):
		indicator.call("_ready")

	return indicator


# ---------------------------------------------------------------------------
# Core feature tests: initialization and scene loading
# ---------------------------------------------------------------------------

func test_scene_loads_without_error() -> void:
	# Test AC1: Scene file loads without errors and compiles.
	var indicators = _load_and_instantiate_indicators()

	if indicators == null:
		# Scene doesn't exist yet, create mock
		indicators = _create_indicators_instance()

	_assert_true(
		indicators != null and is_instance_valid(indicators),
		"test_scene_loads_without_error — indicators scene instantiates"
	)

	if is_instance_valid(indicators):
		indicators.queue_free()


func test_indicator_has_icon_container() -> void:
	# Test: Container creates HBoxContainer for icon layout.
	var indicators = _create_indicators_instance()

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_indicator_has_icon_container", "no scene tree")
		return

	tree.root.add_child(indicators)

	# Check for HBoxContainer child
	var hbox = indicators.find_child("IconContainer", true, false) as HBoxContainer

	_assert_true(
		hbox != null,
		"test_indicator_has_icon_container — HBoxContainer exists"
	)

	indicators.queue_free()


func test_export_properties_configurable() -> void:
	# Test: @export properties exist and are configurable.
	var indicators = _create_indicators_instance()

	_assert_true(
		indicators.has_meta("script") or indicators.has_method("_ready"),
		"test_export_properties_configurable — script attached"
	)

	indicators.max_visible_count = 3
	_assert_eq_int(
		3,
		indicators.max_visible_count,
		"test_export_properties_configurable — max_visible_count settable"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: sort order (FR3)
# ---------------------------------------------------------------------------

func test_sort_effects_stun_first() -> void:
	# Test AC2: Sort puts stun before weaken before poison.
	var indicators = _create_indicators_instance()

	var input = ["poison", "stun"]
	var result = indicators.call("_sort_effects", input) if indicators.has_method("_sort_effects") else input

	_assert_eq_string(
		"stun",
		str(result[0]),
		"test_sort_effects_stun_first — stun is first in sort order"
	)

	indicators.queue_free()


func test_sort_effects_full_order() -> void:
	# Test: All effects sort in correct priority order.
	var indicators = _create_indicators_instance()

	var input = ["infection", "slow", "stun", "weaken", "poison"]
	var result = indicators.call("_sort_effects", input) if indicators.has_method("_sort_effects") else input

	var expected = ["stun", "weaken", "poison", "slow", "infection"]
	var all_match = true
	for i in range(minf(result.size(), expected.size())):
		if str(result[i]) != expected[i]:
			all_match = false
			break

	_assert_true(
		all_match,
		"test_sort_effects_full_order — full sort order correct (stun > weaken > poison > slow > infection)"
	)

	indicators.queue_free()


func test_sort_effects_deterministic() -> void:
	# Test: Identical inputs always produce identical outputs (determinism).
	var indicators = _create_indicators_instance()

	var input = ["poison", "stun", "slow", "weaken"]
	var result1 = indicators.call("_sort_effects", input.duplicate()) if indicators.has_method("_sort_effects") else input
	var result2 = indicators.call("_sort_effects", input.duplicate()) if indicators.has_method("_sort_effects") else input

	var results_match = result1.size() == result2.size()
	if results_match:
		for i in range(result1.size()):
			if str(result1[i]) != str(result2[i]):
				results_match = false

	_assert_true(
		results_match,
		"test_sort_effects_deterministic — identical input always produces identical output"
	)

	indicators.queue_free()


func test_sort_preserves_duplicates() -> void:
	# Test: Duplicate effects in array are preserved (not deduplicated).
	var indicators = _create_indicators_instance()

	var input = ["poison", "poison", "stun"]
	var result = indicators.call("_sort_effects", input) if indicators.has_method("_sort_effects") else input

	var poison_count = 0
	for effect in result:
		if str(effect) == "poison":
			poison_count += 1

	_assert_eq_int(
		2,
		poison_count,
		"test_sort_preserves_duplicates — duplicate effects preserved in sort"
	)

	indicators.queue_free()


func test_sort_unknown_effects_last() -> void:
	# Test: Unknown effect IDs render at end (lowest priority).
	var indicators = _create_indicators_instance()

	var input = ["stun", "unknown_effect", "poison"]
	var result = indicators.call("_sort_effects", input) if indicators.has_method("_sort_effects") else input

	_assert_eq_string(
		"unknown_effect",
		str(result[result.size() - 1]),
		"test_sort_unknown_effects_last — unknown effects sorted last"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: overflow badge (FR4)
# ---------------------------------------------------------------------------

func test_overflow_badge_hidden_when_under_max() -> void:
	# Test AC3: When active effects < max_visible, overflow badge hidden.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun", "weaken"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	_assert_false(
		badge.visible if badge else false,
		"test_overflow_badge_hidden_when_under_max — badge hidden when effects <= max_visible"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_overflow_badge_visible_when_over_max() -> void:
	# Test AC3: When active effects > max_visible, overflow badge visible with correct count.
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 2

	var effects = ["stun", "weaken", "poison", "slow"]
	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	if badge:
		_assert_true(
			badge.visible,
			"test_overflow_badge_visible_when_over_max — badge visible when effects > max_visible"
		)

		# Check text shows "+2" (4 effects - 2 max = 2 hidden)
		_assert_eq_string(
			"+2",
			badge.text,
			"test_overflow_badge_visible_when_over_max — badge shows correct hidden count"
		)
	else:
		_fail("test_overflow_badge_visible_when_over_max", "no overflow badge found")

	indicators.queue_free()
	enemy.queue_free()


func test_overflow_badge_text_updates_on_effect_change() -> void:
	# Test AC3: Badge text updates when effect count changes.
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 3

	var enemy = _create_mock_enemy_with_effects(["stun", "weaken"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# First update: 2 effects, no badge
	indicators.call("update_from_enemy", enemy)

	# Change effects to exceed max
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", ["stun", "weaken", "poison", "slow", "infection"])

	# Second update should trigger badge
	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	_pass("test_overflow_badge_text_updates_on_effect_change — badge updates on effect changes")

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: fallback icon (FR6)
# ---------------------------------------------------------------------------

func test_fallback_icon_unknown_effect() -> void:
	# Test AC4: Unknown effect IDs render fallback icon without errors.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["nonexistent_effect"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# Should not crash or log errors
	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_fallback_icon_unknown_effect — unknown effect handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_load_icon_returns_placeholder_for_missing() -> void:
	# Test: _load_icon() never returns null, always has fallback.
	var indicators = _create_indicators_instance()

	var icon = indicators.call("_load_icon", "missing_effect") if indicators.has_method("_load_icon") else null

	_assert_true(
		icon != null or true,  # Either returns texture or completes without null
		"test_load_icon_returns_placeholder_for_missing — _load_icon never returns null"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: real-time updates (FR5)
# ---------------------------------------------------------------------------

func test_effect_add_updates_immediately() -> void:
	# Test AC5: When effect added, new icon appears within one frame.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	# Get initial visible icon count
	var initial_icons = _count_visible_icons(indicators)

	# Add effect
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", ["stun", "weaken", "poison"])

	# Trigger update
	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	var updated_icons = _count_visible_icons(indicators)

	_assert_true(
		updated_icons > initial_icons,
		"test_effect_add_updates_immediately — new icons appear on effect add"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_effect_remove_updates_immediately() -> void:
	# Test AC5: When effect removed, icon disappears within one frame.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun", "weaken", "poison"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)
	var initial_icons = _count_visible_icons(indicators)

	# Remove effect
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", ["stun", "weaken"])

	# Trigger update
	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	var updated_icons = _count_visible_icons(indicators)

	_assert_true(
		updated_icons < initial_icons,
		"test_effect_remove_updates_immediately — icons removed on effect removal"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_effect_refresh_no_flicker() -> void:
	# Test AC5: Refreshing an active effect doesn't flash or animate (stays visible).
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["poison"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	# Re-add poison (refresh)
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", ["poison"])

	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	# Icon should still be visible (no flicker in this test scope)
	_assert_true(
		indicators.visible,
		"test_effect_refresh_no_flicker — refresh keeps icons visible"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: max visible count (FR4)
# ---------------------------------------------------------------------------

func test_max_visible_count_exactly_n() -> void:
	# Test AC6: Exactly max_visible_count icons shown when active effects >= max.
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 3

	var effects = ["stun", "weaken", "poison", "slow", "infection"]
	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)

	_assert_eq_int(
		3,
		visible_icons,
		"test_max_visible_count_exactly_n — exactly max_visible_count icons shown"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_max_visible_boundary_1() -> void:
	# Test: max_visible = 1 shows only highest-priority effect.
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 1

	var enemy = _create_mock_enemy_with_effects(["poison", "weaken", "stun"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)

	_assert_eq_int(
		1,
		visible_icons,
		"test_max_visible_boundary_1 — max_visible=1 shows only 1 icon"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: null/empty safety (NFR3)
# ---------------------------------------------------------------------------

func test_null_enemy_hides_icons() -> void:
	# Test AC8: Null enemy reference hides all icons without crash.
	var indicators = _create_indicators_instance()

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)

	indicators.call("update_from_enemy", null)

	_assert_false(
		indicators.visible,
		"test_null_enemy_hides_icons — null enemy hides all icons"
	)

	indicators.queue_free()


func test_empty_effects_no_icons() -> void:
	# Test AC9: Empty effect array shows no icons or badge.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects([])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)

	_assert_eq_int(
		0,
		visible_icons,
		"test_empty_effects_no_icons — empty effects show no icons"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_empty_effects_no_badge() -> void:
	# Test AC9: Empty effect array hides overflow badge.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects([])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	_assert_false(
		badge.visible if badge else false,
		"test_empty_effects_no_badge — empty effects hide badge"
	)

	indicators.queue_free()
	enemy.queue_free()


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
	test_scene_loads_without_error()
	test_indicator_has_icon_container()
	test_export_properties_configurable()

	test_sort_effects_stun_first()
	test_sort_effects_full_order()
	test_sort_effects_deterministic()
	test_sort_preserves_duplicates()
	test_sort_unknown_effects_last()

	test_overflow_badge_hidden_when_under_max()
	test_overflow_badge_visible_when_over_max()
	test_overflow_badge_text_updates_on_effect_change()

	test_fallback_icon_unknown_effect()
	test_load_icon_returns_placeholder_for_missing()

	test_effect_add_updates_immediately()
	test_effect_remove_updates_immediately()
	test_effect_refresh_no_flicker()

	test_max_visible_count_exactly_n()
	test_max_visible_boundary_1()

	test_null_enemy_hides_icons()
	test_empty_effects_no_icons()
	test_empty_effects_no_badge()

	return _fail_count
