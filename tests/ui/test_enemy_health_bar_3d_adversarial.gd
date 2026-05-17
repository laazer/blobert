#
# test_enemy_health_bar_3d_adversarial.gd
#
# Adversarial / edge-case test suite for enemy floating health bar (M8 feature).
# Tests boundary conditions, null/empty inputs, invalid data, and error handling
# by exercising actual methods (update_from_enemy, on_enemy_damaged) with extreme values.
#
# Traceability: Extends primary test file at tests/ui/test_enemy_health_bar_3d.gd
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure: fixtures and helpers
# ---------------------------------------------------------------------------

func _create_enemy_with_hp(hp: float = 100.0, max_hp: float = 100.0) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.set_script(load("res://scripts/enemies/enemy_base.gd"))
	body.set_meta("current_hp", hp)
	body.set_meta("max_hp", max_hp)
	return body


func _load_health_bar() -> Variant:
	var path := "res://scenes/ui/enemy_health_bar_3d.tscn"
	var scene = load(path)
	if scene == null:
		return null
	return scene.instantiate() as Node


func _find_progress_bar(bar: Node) -> Variant:
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			return node
		for child in node.get_children():
			stack.append(child)
	return null


# ---------------------------------------------------------------------------
# ADV-NULLS: Null/empty input handling
# ---------------------------------------------------------------------------

func test_adv_null_1_null_enemy_reference() -> void:
	# ADV-NULL-1: update_from_enemy(null) should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_null_1_null_enemy_reference", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_null_1_null_enemy_reference", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	bar.call("update_from_enemy", null)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_null_1_null_enemy_reference — bar survives null enemy"
	)

	bar.queue_free()


func test_adv_null_2_missing_hp_properties() -> void:
	# ADV-NULL-2: Enemy without health properties should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_null_2_missing_hp_properties", "health bar not found")
		return

	# Create enemy without health metas.
	var enemy = CharacterBody3D.new()
	enemy.set_script(load("res://scripts/enemies/enemy_base.gd"))

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_null_2_missing_hp_properties", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_null_2_missing_hp_properties — bar handles enemy without HP"
	)

	bar.queue_free()


func test_adv_null_3_damage_on_null_enemy() -> void:
	# ADV-NULL-3: on_enemy_damaged() with bar not initialized should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_null_3_damage_on_null_enemy", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_null_3_damage_on_null_enemy", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Call on_enemy_damaged without setting enemy first.
	bar.call("on_enemy_damaged", 10.0)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_null_3_damage_on_null_enemy — bar handles damage with no enemy"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-BOUNDARY: Boundary and extreme values
# ---------------------------------------------------------------------------

func test_adv_boundary_1_exact_zero_fill() -> void:
	# ADV-BOUNDARY-1: When current_hp == 0, fill must be exactly 0.0.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_1_exact_zero_fill", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(0.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_1_exact_zero_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_boundary_1_exact_zero_fill", "no ProgressBar found")
		bar.queue_free()
		return

	_assert_eq_float(
		0.0,
		progress_bar.value,
		"test_adv_boundary_1_exact_zero_fill — fill is 0.0 at zero HP"
	)

	bar.queue_free()


func test_adv_boundary_2_exact_one_fill() -> void:
	# ADV-BOUNDARY-2: When current_hp == max_hp, fill must be exactly 100.0.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_2_exact_one_fill", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_2_exact_one_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_boundary_2_exact_one_fill", "no ProgressBar found")
		bar.queue_free()
		return

	_assert_eq_float(
		100.0,
		progress_bar.value,
		"test_adv_boundary_2_exact_one_fill — fill is 100.0 at full HP"
	)

	bar.queue_free()


func test_adv_boundary_3_negative_hp_clamped() -> void:
	# ADV-BOUNDARY-3: If enemy has negative HP (defensive), fill should not go negative.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_3_negative_hp_clamped", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(-10.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_3_negative_hp_clamped", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_boundary_3_negative_hp_clamped", "no ProgressBar found")
		bar.queue_free()
		return

	# Fill should be clamped to >= 0.
	_assert_true(
		progress_bar.value >= 0.0,
		"test_adv_boundary_3_negative_hp_clamped — fill non-negative even with negative HP"
	)

	bar.queue_free()


func test_adv_boundary_4_huge_max_hp() -> void:
	# ADV-BOUNDARY-4: Very large max_hp (1M+) should compute correct ratio without overflow.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_4_huge_max_hp", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(500_000.0, 1_000_000.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_4_huge_max_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_boundary_4_huge_max_hp", "no ProgressBar found")
		bar.queue_free()
		return

	# Ratio should be 0.5, so value should be 50.0.
	_assert_eq_float(
		50.0,
		progress_bar.value,
		"test_adv_boundary_4_huge_max_hp — correct ratio for huge HP values"
	)

	bar.queue_free()


func test_adv_boundary_5_tiny_positive_max_hp() -> void:
	# ADV-BOUNDARY-5: Very small max_hp (0.001) should compute correct ratio.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_5_tiny_positive_max_hp", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(0.0005, 0.001)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_5_tiny_positive_max_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_boundary_5_tiny_positive_max_hp", "no ProgressBar found")
		bar.queue_free()
		return

	# Ratio should be 0.5, so value should be 50.0.
	_assert_eq_float(
		50.0,
		progress_bar.value,
		"test_adv_boundary_5_tiny_positive_max_hp — correct ratio for tiny HP values"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-INVALID: Invalid / corrupt floating point
# ---------------------------------------------------------------------------

func test_adv_invalid_1_nan_hp() -> void:
	# ADV-INVALID-1: NaN HP value should not crash; bar should remain valid.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_invalid_1_nan_hp", "health bar not found")
		return

	var enemy = CharacterBody3D.new()
	enemy.set_script(load("res://scripts/enemies/enemy_base.gd"))
	var nan_val: float = 0.0 / 0.0
	enemy.set_meta("current_hp", nan_val)
	enemy.set_meta("max_hp", 100.0)

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_invalid_1_nan_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_invalid_1_nan_hp — bar survives NaN HP"
	)

	bar.queue_free()


func test_adv_invalid_2_inf_hp() -> void:
	# ADV-INVALID-2: Infinity HP should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_invalid_2_inf_hp", "health bar not found")
		return

	var enemy = CharacterBody3D.new()
	enemy.set_script(load("res://scripts/enemies/enemy_base.gd"))
	var inf_val: float = 1e308 * 10.0
	enemy.set_meta("current_hp", inf_val)
	enemy.set_meta("max_hp", 100.0)

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_invalid_2_inf_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_invalid_2_inf_hp — bar survives infinity HP"
	)

	bar.queue_free()


func test_adv_invalid_3_negative_max_hp() -> void:
	# ADV-INVALID-3: Negative max_hp should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_invalid_3_negative_max_hp", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(50.0, -100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_invalid_3_negative_max_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_invalid_3_negative_max_hp — bar survives negative max_hp"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-VISIBILITY: Visibility state machine edge cases
# ---------------------------------------------------------------------------

func test_adv_visibility_1_rapid_damage_hide_cycles() -> void:
	# ADV-VISIBILITY-1: Rapid damage → visibility → heal → hide cycles
	# should not leave bar in inconsistent state.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_visibility_1_rapid_damage_hide_cycles", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_visibility_1_rapid_damage_hide_cycles", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	# Cycle 1: damage → show
	enemy.set_meta("current_hp", 75.0)
	bar.call("on_enemy_damaged", 25.0)
	_assert_true(bar.visible, "cycle 1: visible after damage")

	# Cycle 2: recover → hide timeout starts
	enemy.set_meta("current_hp", 100.0)
	bar.call("on_enemy_healed", 25.0)

	# Cycle 3: damage again (interrupt timeout)
	enemy.set_meta("current_hp", 50.0)
	bar.call("on_enemy_damaged", 50.0)
	_assert_true(bar.visible, "cycle 3: visible after re-damage")

	_assert_true(
		is_instance_valid(bar),
		"test_adv_visibility_1_rapid_damage_hide_cycles — state consistent after cycles"
	)

	bar.queue_free()


func test_adv_visibility_2_hidden_by_default() -> void:
	# ADV-VISIBILITY-2: Bar should be hidden by default on full-health enemy.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_visibility_2_hidden_by_default", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_visibility_2_hidden_by_default", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	_assert_false(
		bar.visible,
		"test_adv_visibility_2_hidden_by_default — bar hidden on init at full health"
	)

	bar.queue_free()


func test_adv_visibility_3_multiple_visibility_toggles() -> void:
	# ADV-VISIBILITY-3: Multiple rapid visibility changes should not cause crashes.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_visibility_3_multiple_visibility_toggles", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_visibility_3_multiple_visibility_toggles", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	# Simulate rapid damage events.
	for i in range(10):
		enemy.set_meta("current_hp", 50.0 + float(i))
		bar.call("on_enemy_damaged", 1.0)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_visibility_3_multiple_visibility_toggles — stable after rapid events"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-LIFECYCLE: Cleanup and orphan prevention
# ---------------------------------------------------------------------------

func test_adv_lifecycle_1_parent_reparenting() -> void:
	# ADV-LIFECYCLE-1: Bar attached to enemy should be freed when enemy is freed.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_lifecycle_1_parent_reparenting", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_lifecycle_1_parent_reparenting", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	# Free enemy (bar should follow).
	enemy.queue_free()

	_assert_true(
		bar.is_queued_for_deletion(),
		"test_adv_lifecycle_1_parent_reparenting — bar freed when enemy freed"
	)


func test_adv_lifecycle_2_multiple_bars_per_enemy() -> void:
	# ADV-LIFECYCLE-2: Multiple bars on same enemy should all be freed.
	var bar1 = _load_health_bar()
	var bar2 = _load_health_bar()
	if bar1 == null or bar2 == null:
		_fail("test_adv_lifecycle_2_multiple_bars_per_enemy", "health bar not found")
		if bar1 != null:
			bar1.queue_free()
		if bar2 != null:
			bar2.queue_free()
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_lifecycle_2_multiple_bars_per_enemy", "no scene tree")
		bar1.queue_free()
		bar2.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar1)
	enemy.add_child(bar2)

	# Free enemy.
	enemy.queue_free()

	_assert_true(
		bar1.is_queued_for_deletion() and bar2.is_queued_for_deletion(),
		"test_adv_lifecycle_2_multiple_bars_per_enemy — all bars freed"
	)


func test_adv_lifecycle_3_orphan_detection() -> void:
	# ADV-LIFECYCLE-3: Orphaned bar (parent freed) should have null parent.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_lifecycle_3_orphan_detection", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_lifecycle_3_orphan_detection", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	# Verify parent is set.
	_assert_true(bar.get_parent() == enemy, "bar parent is enemy")

	# Free enemy without freeing bar.
	enemy.free()

	# After free, bar's parent should be null or bar should be invalid.
	var parent = bar.get_parent()
	var is_valid = is_instance_valid(bar)

	# Either orphaned (null parent) or freed along with enemy.
	_assert_true(
		parent == null or not is_valid,
		"test_adv_lifecycle_3_orphan_detection — orphaned bar detectable"
	)

	if is_valid and parent == null:
		bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-INTEGRATION: Method call order and state consistency
# ---------------------------------------------------------------------------

func test_adv_integration_1_update_then_damage() -> void:
	# ADV-INTEGRATION-1: update_from_enemy() followed by on_enemy_damaged()
	# should maintain consistent state.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_integration_1_update_then_damage", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_integration_1_update_then_damage", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)
	_assert_false(bar.visible, "bar hidden after update at full health")

	enemy.set_meta("current_hp", 75.0)
	bar.call("on_enemy_damaged", 25.0)
	_assert_true(bar.visible, "bar shown after damage")

	var progress_bar = _find_progress_bar(bar)
	if progress_bar != null:
		_assert_eq_float(75.0, progress_bar.value, "fill reflects damage")

	bar.queue_free()


func test_adv_integration_2_damage_without_update() -> void:
	# ADV-INTEGRATION-2: on_enemy_damaged() called before update_from_enemy()
	# should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_integration_2_damage_without_update", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_integration_2_damage_without_update", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Call damage before update_from_enemy.
	bar.call("on_enemy_damaged", 10.0)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_integration_2_damage_without_update — stable without prior update"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_bar_3d_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-NULLS tests
	test_adv_null_1_null_enemy_reference()
	test_adv_null_2_missing_hp_properties()
	test_adv_null_3_damage_on_null_enemy()

	# ADV-BOUNDARY tests
	test_adv_boundary_1_exact_zero_fill()
	test_adv_boundary_2_exact_one_fill()
	test_adv_boundary_3_negative_hp_clamped()
	test_adv_boundary_4_huge_max_hp()
	test_adv_boundary_5_tiny_positive_max_hp()

	# ADV-INVALID tests
	test_adv_invalid_1_nan_hp()
	test_adv_invalid_2_inf_hp()
	test_adv_invalid_3_negative_max_hp()

	# ADV-VISIBILITY tests
	test_adv_visibility_1_rapid_damage_hide_cycles()
	test_adv_visibility_2_hidden_by_default()
	test_adv_visibility_3_multiple_visibility_toggles()

	# ADV-LIFECYCLE tests
	test_adv_lifecycle_1_parent_reparenting()
	test_adv_lifecycle_2_multiple_bars_per_enemy()
	test_adv_lifecycle_3_orphan_detection()

	# ADV-INTEGRATION tests
	test_adv_integration_1_update_then_damage()
	test_adv_integration_2_damage_without_update()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
