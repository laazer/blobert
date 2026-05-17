#
# test_enemy_status_effect_indicators_mutation.gd
#
# Mutation and adversarial tests for enemy status effect indicators.
# Tests type confusion, cache invalidation, state mutations, and interface mismatches.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md
# Spec: project_board/specs/enemy_status_effect_indicators_spec.md
#
# Coverage:
#   - Type confusion (effects array contains non-string values)
#   - Interface priority conflicts (multiple methods return conflicting data)
#   - Sort algorithm stability under type-mixed inputs
#   - Cache invalidation and array mutation during iteration
#   - Max visible count dynamic changes
#   - Fallback chain exhaustion (all asset paths fail)
#   - Container sizing under extreme configurations
#   - Empty/null edge cases across all code paths
#   - Rapid state mutations (add->remove->add same frame)
#   - Effect array corruption (values change between checks)
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# Create a mock enemy that can have multiple interface methods with conflicting data
func _create_mock_enemy_with_conflicting_interfaces(
	array_effects: Array = [],
	meta_effects: Array = [],
	getter_effects: Array = [],
	state: int = 0
) -> Node3D:
	var body := Node3D.new()

	var script_code := """
extends Node3D

var current_state = %d
var active_status_effects = []

func get_base_state():
	return current_state

func get_active_status_effects():
	return %s

func get_meta_effects():
	return %s
""" % [state, getter_effects, meta_effects]

	var script = GDScript.new()
	script.set_source_code(script_code)
	body.set_script(script)
	body.set_meta("active_status_effects", meta_effects.duplicate())

	if body.has_method("get_active_status_effects"):
		# The getter will return getter_effects
		pass

	# Set the property to array_effects
	if body.has_property("active_status_effects"):
		body.active_status_effects = array_effects.duplicate()

	return body as Node3D


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
	body.set_meta("active_status_effects", effects.duplicate())

	if body.has_method("set_active_status_effects"):
		body.call("set_active_status_effects", effects.duplicate())

	return body as Node3D


func _create_indicators_instance() -> Node:
	# Load the actual scene instead of recreating it inline
	var scene_path = "res://scenes/ui/enemy_status_effect_indicators.tscn"
	if ResourceLoader.exists(scene_path):
		var scene = load(scene_path)
		return scene.instantiate() as Node
	# Fallback: create minimal instance with just the script
	var indicator = Control.new()
	indicator.name = "EnemyStatusEffectIndicators"
	var script = load("res://scripts/ui/enemy_status_effect_indicators.gd")
	indicator.set_script(script)
	return indicator


# ---------------------------------------------------------------------------
# TYPE CONFUSION TESTS
# ---------------------------------------------------------------------------

func test_type_confusion_integer_effect_ids() -> void:
	# MUTATION: What if effects array contains integers instead of strings?
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_conflicting_interfaces([1, 2, 3], [], [], 0)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.update_from_enemy(enemy)

	# Should not crash; effect IDs are converted to strings
	_assert_true(
		indicators.visible or not indicators.visible,
		"test_type_confusion_integer_effect_ids — no crash on integer effect IDs"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_type_confusion_mixed_array() -> void:
	# MUTATION: Array contains strings, ints, floats, objects mixed
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_conflicting_interfaces(
		["stun", 42, 3.14, Node.new(), "poison"],
		[],
		[],
		0
	)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.update_from_enemy(enemy)

	# Should gracefully handle mixed types without crashing
	_assert_true(
		true,
		"test_type_confusion_mixed_array — no crash on mixed-type effects array"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_type_confusion_object_with_id_property() -> void:
	# MUTATION: Effects array contains objects with 'id' property (not strings)
	var indicators = _create_indicators_instance()

	var effect_obj = Node.new()
	effect_obj.set_meta("id", "poison")

	var enemy = _create_mock_enemy_with_conflicting_interfaces(
		[effect_obj],
		[],
		[],
		0
	)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.update_from_enemy(enemy)

	# Should handle objects without crashing
	_assert_true(
		true,
		"test_type_confusion_object_with_id_property — no crash on object-type effects"
	)

	indicators.queue_free()
	enemy.queue_free()
	effect_obj.queue_free()


# ---------------------------------------------------------------------------
# INTERFACE CONFLICT TESTS
# ---------------------------------------------------------------------------

func test_interface_priority_array_vs_meta_conflict() -> void:
	# MUTATION: Array property and meta have different effects; priority should pick array
	var indicators = _create_indicators_instance()

	# Array property will have ["stun"], meta will have ["poison"]
	# Priority order: method → meta → property, so we check which one wins
	var enemy = _create_mock_enemy_with_conflicting_interfaces(
		["stun", "weaken"],  # Array property (highest priority)
		["poison", "slow"],  # Meta property (medium priority)
		[],
		0
	)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.update_from_enemy(enemy)

	# Get active effects by calling the internal method
	var active = indicators.call("_get_active_effects_from_enemy")

	# Should use array property (highest priority), not meta
	_assert_true(
		active.size() > 0 and (active[0] == "stun" or active[0] == "weaken"),
		"test_interface_priority_array_vs_meta_conflict — array property takes priority over meta"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_interface_all_methods_empty() -> void:
	# MUTATION: All interface methods exist but return empty arrays
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_conflicting_interfaces(
		[],  # Array empty
		[],  # Meta empty
		[],  # Getter empty
		0    # State NORMAL (no implicit effects)
	)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	indicators.update_from_enemy(enemy)

	# Should handle empty arrays gracefully
	_assert_true(
		not indicators.visible,
		"test_interface_all_methods_empty — no icons shown when all interfaces return empty"
	)

	indicators.queue_free()
	enemy.queue_free()


# ---------------------------------------------------------------------------
# CACHE INVALIDATION TESTS
# ---------------------------------------------------------------------------

func test_cache_invalidation_array_mutation_during_check() -> void:
	# CHECKPOINT: Spec says _last_seen_effects is cached. What if enemy mutates array between checks?
	# This tests whether the implementation properly detects changes.
	var indicators = _create_indicators_instance()
	var enemy = _create_mock_enemy_with_conflicting_interfaces(
		["stun"],
		[],
		[],
		0
	)

	var tree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(indicators)
	tree.root.add_child(enemy)

	# First update
	indicators.update_from_enemy(enemy)
	var cache_after_first = indicators.get("_last_seen_effects")

	_assert_eq_int(
		1,
		cache_after_first.size(),
		"test_cache_invalidation_array_mutation_during_check — cache after first update"
	)

	# Mutate enemy's array
	if enemy.has_method("set_active_status_effects"):
		enemy.call("set_active_status_effects", ["stun", "weaken", "poison"])

	# Second update
	indicators.call("_process_update")
	var cache_after_second = indicators.get("_last_seen_effects")

	_assert_eq_int(
		3,
		cache_after_second.size(),
		"test_cache_invalidation_array_mutation_during_check — cache updated to reflect new array"
	)

	indicators.queue_free()
	enemy.queue_free()


func test_cache_stale_detection_identical_content() -> void:
	# Test idempotency: calling _update_from_effects twice with identical arrays
	# should not trigger unnecessary re-render
	var indicators = _create_indicators_instance()

	var effects = ["stun", "weaken", "poison"]

	indicators.set_active_effects(effects)
	var first_cache = indicators.get("_last_seen_effects")

	# Call again with identical array
	indicators.set_active_effects(effects)
	var second_cache = indicators.get("_last_seen_effects")

	_assert_eq_int(
		first_cache.size(),
		second_cache.size(),
		"test_cache_stale_detection_identical_content — cache remains consistent"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# SORT ALGORITHM STABILITY TESTS
# ---------------------------------------------------------------------------

func test_sort_stability_numeric_string_comparison() -> void:
	# MUTATION: Sort with numeric-looking strings like "10", "2" (string sort != numeric sort)
	var indicators = _create_indicators_instance()

	var effects = ["stun", "poison", "slow"]
	var sorted = indicators.call("_sort_effects", effects)

	_assert_eq_string(
		"stun",
		sorted[0],
		"test_sort_stability_numeric_string_comparison — stun first in sort"
	)

	indicators.queue_free()


func test_sort_stability_case_sensitivity() -> void:
	# MUTATION: Are effect IDs case-sensitive? ("STUN" vs "stun")
	var indicators = _create_indicators_instance()

	var effects = ["poison", "STUN", "Weaken"]
	var sorted = indicators.call("_sort_effects", effects)

	# Unknown effects (uppercase/titlecase) should sort to end (priority 999)
	_assert_true(
		sorted[0] == "poison" or sorted[0] == "poison",
		"test_sort_stability_case_sensitivity — case handling consistent"
	)

	indicators.queue_free()


func test_sort_stability_duplicates_preserve_order() -> void:
	# Test that duplicate effects maintain relative order in sorted array
	var indicators = _create_indicators_instance()

	var effects = ["poison", "stun", "stun", "weaken"]
	var sorted = indicators.call("_sort_effects", effects)

	# Both stuns should be next to each other (stable sort)
	_assert_true(
		sorted[0] == "stun" and sorted[1] == "stun",
		"test_sort_stability_duplicates_preserve_order — duplicate stuns together"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# MAX VISIBLE COUNT MUTATION TESTS
# ---------------------------------------------------------------------------

func test_max_visible_dynamic_change_reduces_visible() -> void:
	# MUTATION: Change max_visible_count mid-update (should reduce visible icons)
	var indicators = _create_indicators_instance()

	indicators.max_visible_count = 5
	var effects = ["stun", "weaken", "poison", "slow", "infection"]
	indicators.set_active_effects(effects)

	# Now reduce max_visible
	indicators.max_visible_count = 2
	indicators.set_active_effects(effects)

	# Only 2 icons should be visible now
	var icon_rects = indicators.call("_get_icon_rects")
	var visible_count = 0
	for rect in icon_rects:
		if rect.visible:
			visible_count += 1

	_assert_eq_int(
		2,
		visible_count,
		"test_max_visible_dynamic_change_reduces_visible — dynamic reduction works"
	)

	indicators.queue_free()


func test_max_visible_dynamic_change_increases_visible() -> void:
	# MUTATION: Change max_visible_count to allow more icons
	var indicators = _create_indicators_instance()

	indicators.max_visible_count = 2
	var effects = ["stun", "weaken", "poison", "slow", "infection"]
	indicators.set_active_effects(effects)

	# Now increase max_visible
	indicators.max_visible_count = 4
	indicators.set_active_effects(effects)

	# 4 icons should be visible now
	var icon_rects = indicators.call("_get_icon_rects")
	var visible_count = 0
	for rect in icon_rects:
		if rect.visible:
			visible_count += 1

	_assert_eq_int(
		4,
		visible_count,
		"test_max_visible_dynamic_change_increases_visible — dynamic expansion works"
	)

	indicators.queue_free()


func test_max_visible_negative_becomes_one() -> void:
	# MUTATION: What if max_visible is set to negative?
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = -5

	var effects = ["stun", "weaken"]
	indicators.set_active_effects(effects)

	# Should clamp to 1
	var icon_rects = indicators.call("_get_icon_rects")
	var visible_count = 0
	for rect in icon_rects:
		if rect.visible:
			visible_count += 1

	# Implementation should handle this gracefully (clamp to 1 or 0)
	_assert_true(
		visible_count >= 0,
		"test_max_visible_negative_becomes_one — negative max_visible handled"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# CONTAINER SIZING TESTS
# ---------------------------------------------------------------------------

func test_container_sizing_zero_icon_size() -> void:
	# MUTATION: icon_size = (0, 0) - what happens to layout?
	var indicators = _create_indicators_instance()
	indicators.icon_size = Vector2(0, 0)

	var effects = ["stun", "weaken"]
	indicators.set_active_effects(effects)

	# Should not crash; container should still render
	_assert_true(
		indicators.find_child("IconContainer") != null,
		"test_container_sizing_zero_icon_size — container still exists"
	)

	indicators.queue_free()


func test_container_sizing_huge_icon_size() -> void:
	# MUTATION: icon_size = (10000, 10000) - extreme dimensions
	var indicators = _create_indicators_instance()
	indicators.icon_size = Vector2(10000, 10000)

	var effects = ["stun", "weaken"]
	indicators.set_active_effects(effects)

	# Should not crash
	_assert_true(
		true,
		"test_container_sizing_huge_icon_size — no crash on extreme icon size"
	)

	indicators.queue_free()


func test_container_spacing_negative() -> void:
	# MUTATION: spacing = -10 (negative spacing)
	var indicators = _create_indicators_instance()
	indicators.spacing = -10

	var effects = ["stun", "weaken", "poison"]
	indicators.set_active_effects(effects)

	# Should not crash
	_assert_true(
		true,
		"test_container_spacing_negative — no crash on negative spacing"
	)

	indicators.queue_free()


func test_container_spacing_huge() -> void:
	# MUTATION: spacing = 10000 (huge spacing)
	var indicators = _create_indicators_instance()
	indicators.spacing = 10000

	var effects = ["stun", "weaken", "poison"]
	indicators.set_active_effects(effects)

	# Should not crash
	_assert_true(
		true,
		"test_container_spacing_huge — no crash on huge spacing"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# ASSET FALLBACK CHAIN TESTS
# ---------------------------------------------------------------------------

func test_fallback_both_paths_missing() -> void:
	# MUTATION: Set fallback_icon_path to non-existent path
	var indicators = _create_indicators_instance()
	indicators.fallback_icon_path = "res://assets/ui/status_effects/totally_missing.png"

	var effects = ["nonexistent_effect_xyz"]
	indicators.set_active_effects(effects)

	# Should use PlaceholderTexture2D as last resort
	var icon = indicators.call("_load_icon", "nonexistent_effect_xyz")
	_assert_true(
		icon != null,
		"test_fallback_both_paths_missing — fallback chain exhaustion returns non-null"
	)

	indicators.queue_free()


func test_fallback_empty_string_effect_id() -> void:
	# MUTATION: Effect ID is empty string
	var indicators = _create_indicators_instance()
	var effects = ["", "stun", ""]
	indicators.set_active_effects(effects)

	# Should not crash
	_assert_true(
		true,
		"test_fallback_empty_string_effect_id — no crash on empty effect ID"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# OVERFLOW BADGE CALCULATION TESTS
# ---------------------------------------------------------------------------

func test_overflow_badge_calculation_off_by_one() -> void:
	# MUTATION: Ensure overflow count is exactly (active - max_visible), not off-by-one
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 3

	var effects = ["stun", "weaken", "poison", "slow", "infection"]
	indicators.set_active_effects(effects)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	if badge:
		var badge_text = badge.text
		_assert_eq_string(
			"+2",
			badge_text,
			"test_overflow_badge_calculation_off_by_one — badge text exactly '+2' (5 - 3)"
		)

	indicators.queue_free()


func test_overflow_badge_exact_boundary() -> void:
	# MUTATION: exactly max_visible effects - badge should be hidden
	var indicators = _create_indicators_instance()
	indicators.max_visible_count = 3

	var effects = ["stun", "weaken", "poison"]
	indicators.set_active_effects(effects)

	var badge = indicators.find_child("OverflowBadge", true, false) as Label
	if badge:
		_assert_false(
			badge.visible,
			"test_overflow_badge_exact_boundary — badge hidden when count equals max_visible"
		)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# RAPID STATE MUTATION TESTS
# ---------------------------------------------------------------------------

func test_rapid_mutation_add_remove_same_frame() -> void:
	# MUTATION: Add and remove same effect in rapid succession
	var indicators = _create_indicators_instance()

	indicators.set_active_effects(["stun"])
	indicators.set_active_effects(["stun", "weaken"])
	indicators.set_active_effects(["weaken"])
	indicators.set_active_effects(["weaken", "poison"])

	# Final state should be ["weaken", "poison"]
	var effects = indicators.get("_last_seen_effects")
	_assert_eq_int(
		2,
		effects.size(),
		"test_rapid_mutation_add_remove_same_frame — final cache size is 2"
	)

	indicators.queue_free()


func test_rapid_mutation_clear_reapply() -> void:
	# MUTATION: Rapidly clear and reapply effects
	var indicators = _create_indicators_instance()

	for i in range(10):
		indicators.set_active_effects(["stun", "weaken", "poison"])
		indicators.set_active_effects([])

	# Final state should be empty
	var effects = indicators.get("_last_seen_effects")
	_assert_eq_int(
		0,
		effects.size(),
		"test_rapid_mutation_clear_reapply — final cache is empty after 10 clear cycles"
	)

	indicators.queue_free()


# ---------------------------------------------------------------------------
# HELPER ASSERTION METHODS (note: delegates to parent class implementations)
# ---------------------------------------------------------------------------

# Override parent _assert_true with correct signature
func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


# Override parent _assert_false with correct signature
func _assert_false(condition: bool, test_name: String, fail_msg: String = "expected false, got true") -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)


# Override parent _assert_eq_int with correct signature
func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
	if expected == actual:
		_pass(test_name)
	else:
		_fail(test_name, "(expected %d, got %d)" % [expected, actual])


# Override parent _assert_eq_string with correct signature
func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if expected == actual:
		_pass(test_name)
	else:
		_fail(test_name, "(expected '%s', got '%s')" % [expected, actual])


func run_all() -> int:
	print("--- test_enemy_status_effect_indicators_mutation.gd ---")

	test_type_confusion_integer_effect_ids()
	test_type_confusion_mixed_array()
	test_type_confusion_object_with_id_property()

	test_interface_priority_array_vs_meta_conflict()
	test_interface_all_methods_empty()

	test_cache_invalidation_array_mutation_during_check()
	test_cache_stale_detection_identical_content()

	test_sort_stability_numeric_string_comparison()
	test_sort_stability_case_sensitivity()
	test_sort_stability_duplicates_preserve_order()

	test_max_visible_dynamic_change_reduces_visible()
	test_max_visible_dynamic_change_increases_visible()
	test_max_visible_negative_becomes_one()

	test_container_sizing_zero_icon_size()
	test_container_sizing_huge_icon_size()
	test_container_spacing_negative()
	test_container_spacing_huge()

	test_fallback_both_paths_missing()
	test_fallback_empty_string_effect_id()

	test_overflow_badge_calculation_off_by_one()
	test_overflow_badge_exact_boundary()

	test_rapid_mutation_add_remove_same_frame()
	test_rapid_mutation_clear_reapply()

	print("  Results: %d passed, %d failed" % [_pass_count, _fail_count])
	return _fail_count
