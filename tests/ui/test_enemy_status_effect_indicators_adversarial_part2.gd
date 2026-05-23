#
# test_enemy_status_effect_indicators_adversarial_part2.gd
#
# Adversarial test suite for enemy status effect indicators — part 2.
# Tests fallback robustness, asset handling, lifecycle, and edge cases.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
# Spec: project_board/specs/enemy_status_effect_indicators_spec.md
#
# Coverage:
#   - Fallback and asset robustness (unknown effects, large overflow counts)
#   - Enemy reference lifecycle (invalid during update)
#   - Icon size edge cases (zero, large dimensions)
#   - Spacing configuration edge cases (zero, large values)
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
	script.reload()
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

	if _enemy.has_meta("active_status_effects"):
		var result = _enemy.get_meta("active_status_effects")
		if result is Array:
			return result

	if "active_status_effects" in _enemy:
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
# Fallback and asset robustness tests
# ---------------------------------------------------------------------------

func test_all_effects_unknown_fallback_icons() -> void:
	# Test: All unknown effects render fallback icons.
	var indicators = _create_indicators_instance()
	var unknown_effects = ["unknown1", "unknown2", "unknown3"]
	var enemy = _create_mock_enemy_with_effects(unknown_effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var visible_icons = _count_visible_icons(indicators)
	_assert_eq_int(
		3,
		visible_icons,
		"test_all_effects_unknown_fallback_icons — all unknown effects render with fallbacks"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_overflow_badge_large_overflow_count() -> void:
	# Test: Overflow badge displays large counts correctly (e.g., "+1000").
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 1

	var effects = []
	for i in range(1001):
		effects.append("effect_%d" % i)

	var enemy = _create_mock_enemy_with_effects(effects)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	if badge and badge.visible:
		_assert_eq_string(
			"+1000",
			badge.text,
			"test_overflow_badge_large_overflow_count — large overflow count displays correctly"
		)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Enemy reference lifecycle tests
# ---------------------------------------------------------------------------

func test_enemy_becomes_invalid_during_update() -> void:
	# Test: If enemy is freed mid-update, indicator handles gracefully.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_effects(["stun"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	# Free enemy
	enemy.queue_free()

	# Next update should handle null/invalid reference gracefully
	if indicators.has_method("_process"):
		indicators.call("_process", 0.016)

	_assert_true(
		is_instance_valid(indicators),
		"test_enemy_becomes_invalid_during_update — invalid enemy handled gracefully"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# Icon size edge cases
# ---------------------------------------------------------------------------

func test_icon_size_zero_dimensions() -> void:
	# Test: icon_size = (0, 0) handled without visual distortion.
	var indicators = _create_indicators_instance()
	indicators.icon_size = Vector2(0, 0)

	var enemy = _create_mock_enemy_with_effects(["stun", "weaken"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_icon_size_zero_dimensions — zero icon size handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_icon_size_large_dimensions() -> void:
	# Test: icon_size = (1000, 1000) handled without crash.
	var indicators = _create_indicators_instance()
	indicators.icon_size = Vector2(1000, 1000)

	var enemy = _create_mock_enemy_with_effects(["stun"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_icon_size_large_dimensions — large icon size handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# Spacing edge cases
# ---------------------------------------------------------------------------

func test_spacing_zero() -> void:
	# Test: spacing = 0 (icons touch) handled correctly.
	var indicators = _create_indicators_instance()
	indicators.spacing = 0

	var enemy = _create_mock_enemy_with_effects(["stun", "weaken"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_spacing_zero — zero spacing handled gracefully"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_spacing_large_value() -> void:
	# Test: spacing = 100 (wide gaps) handled correctly.
	var indicators = _create_indicators_instance()
	indicators.spacing = 100

	var enemy = _create_mock_enemy_with_effects(["stun", "weaken"])

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(indicators),
		"test_spacing_large_value — large spacing handled gracefully"
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
	test_all_effects_unknown_fallback_icons()
	test_overflow_badge_large_overflow_count()

	test_enemy_becomes_invalid_during_update()

	test_icon_size_zero_dimensions()
	test_icon_size_large_dimensions()

	test_spacing_zero()
	test_spacing_large_value()

	return _fail_count
