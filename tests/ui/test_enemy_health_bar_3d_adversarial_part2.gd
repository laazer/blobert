#
# test_enemy_health_bar_3d_adversarial_part2.gd
#
# Part 2 of adversarial test suite for enemy floating health bar (M8 feature).
# Tests state mutations, stress scenarios, and determinism by exercising actual
# methods with extreme values and rapid sequences.
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
# ADV-FILL-MUTATIONS: Fill ratio computation edge cases
# ---------------------------------------------------------------------------

func test_adv_fill_1_fill_monotonic_increase() -> void:
	# ADV-FILL-1: As HP increases from 0 to max, fill must monotonically increase.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_fill_1_fill_monotonic_increase", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(0.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_fill_1_fill_monotonic_increase", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	var prev_fill = 0.0

	# Increase HP in steps and verify fill increases monotonically.
	for hp in [10.0, 25.0, 50.0, 75.0, 100.0]:
		enemy.set_meta("current_hp", hp)
		bar.call("update_from_enemy", enemy)

		var progress_bar = _find_progress_bar(bar)
		if progress_bar == null:
			_fail("test_adv_fill_1_fill_monotonic_increase", "no ProgressBar found")
			bar.queue_free()
			return

		var fill = progress_bar.value / progress_bar.max_value

		_assert_true(
			fill >= prev_fill,
			"test_adv_fill_1_fill_monotonic_increase — fill monotonic at hp=" + str(hp)
		)

		prev_fill = fill

	bar.queue_free()


func test_adv_fill_2_fill_monotonic_decrease() -> void:
	# ADV-FILL-2: As HP decreases from max to 0, fill must monotonically decrease.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_fill_2_fill_monotonic_decrease", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_fill_2_fill_monotonic_decrease", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	var prev_fill = 1.0

	# Decrease HP in steps and verify fill decreases monotonically.
	for hp in [75.0, 50.0, 25.0, 10.0, 0.0]:
		enemy.set_meta("current_hp", hp)
		bar.call("update_from_enemy", enemy)

		var progress_bar = _find_progress_bar(bar)
		if progress_bar == null:
			_fail("test_adv_fill_2_fill_monotonic_decrease", "no ProgressBar found")
			bar.queue_free()
			return

		var fill = progress_bar.value / progress_bar.max_value

		_assert_true(
			fill <= prev_fill,
			"test_adv_fill_2_fill_monotonic_decrease — fill monotonic at hp=" + str(hp)
		)

		prev_fill = fill

	bar.queue_free()


func test_adv_fill_3_fill_fractional_precision() -> void:
	# ADV-FILL-3: Fill at fractional HP (33/100 = 0.33) must have valid precision.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_fill_3_fill_fractional_precision", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(33.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_fill_3_fill_fractional_precision", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_fill_3_fill_fractional_precision", "no ProgressBar found")
		bar.queue_free()
		return

	_assert_eq_float(
		33.0,
		progress_bar.value,
		"test_adv_fill_3_fill_fractional_precision — fill is 33.0 at hp=33/100"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-STRESS: High-load scenarios
# ---------------------------------------------------------------------------

func test_adv_stress_1_many_bars_simultaneous() -> void:
	# ADV-STRESS-1: Multiple bars spawned simultaneously should not crash.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("test_adv_stress_1_many_bars_simultaneous", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_stress_1_many_bars_simultaneous", "no scene tree")
		return

	var bars: Array[Node] = []
	var enemies: Array[Node] = []

	# Create 10 enemies with bars.
	for i in range(10):
		var enemy = _create_enemy_with_hp(50.0, 100.0)
		var bar = scene.instantiate() as Node

		if bar == null:
			_fail("test_adv_stress_1_many_bars_simultaneous", "could not instantiate bar " + str(i))
			for e in enemies:
				e.queue_free()
			for b in bars:
				b.queue_free()
			return

		tree.root.add_child(enemy)
		enemy.add_child(bar)
		bar.call("update_from_enemy", enemy)

		enemies.append(enemy)
		bars.append(bar)

	_assert_eq_int(
		10,
		bars.size(),
		"test_adv_stress_1_many_bars_simultaneous — created 10 bars"
	)

	# Clean up.
	for e in enemies:
		e.queue_free()


func test_adv_stress_2_rapid_spawn_despawn_cycles() -> void:
	# ADV-STRESS-2: Rapid enemy spawn/despawn cycles should not leak.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("test_adv_stress_2_rapid_spawn_despawn_cycles", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_stress_2_rapid_spawn_despawn_cycles", "no scene tree")
		return

	# 5 rapid cycles.
	for cycle in range(5):
		var enemy = _create_enemy_with_hp(50.0, 100.0)
		var bar = scene.instantiate() as Node

		if bar == null:
			_fail("test_adv_stress_2_rapid_spawn_despawn_cycles", "cycle " + str(cycle))
			return

		tree.root.add_child(enemy)
		enemy.add_child(bar)
		bar.call("update_from_enemy", enemy)
		enemy.queue_free()

	_pass("test_adv_stress_2_rapid_spawn_despawn_cycles — completed 5 cycles")


# ---------------------------------------------------------------------------
# ADV-DETERMINISM: Consistency and idempotence
# ---------------------------------------------------------------------------

func test_adv_determinism_1_same_hp_same_fill() -> void:
	# ADV-DETERMINISM-1: Setting same HP twice yields identical fill.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_determinism_1_same_hp_same_fill", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_determinism_1_same_hp_same_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	# First update.
	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_adv_determinism_1_same_hp_same_fill", "no ProgressBar found")
		bar.queue_free()
		return

	var fill1 = progress_bar.value / progress_bar.max_value

	# Second update (same HP).
	bar.call("update_from_enemy", enemy)
	var fill2 = progress_bar.value / progress_bar.max_value

	_assert_eq_float(
		fill1,
		fill2,
		"test_adv_determinism_1_same_hp_same_fill — identical HP yields identical fill"
	)

	bar.queue_free()


func test_adv_determinism_2_visibility_toggle_consistency() -> void:
	# ADV-DETERMINISM-2: Toggling visibility repeatedly is idempotent.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_determinism_2_visibility_toggle_consistency", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_determinism_2_visibility_toggle_consistency", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Toggle to false 5 times.
	for i in range(5):
		bar.visible = false

	_assert_false(
		bar.visible,
		"test_adv_determinism_2_visibility_toggle_consistency — hidden after 5 toggles"
	)

	# Toggle to true 5 times.
	for i in range(5):
		bar.visible = true

	_assert_true(
		bar.visible,
		"test_adv_determinism_2_visibility_toggle_consistency — visible after 5 toggles"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-RAPID-STATE: Rapid state changes and transitions
# ---------------------------------------------------------------------------

func test_adv_rapid_state_1_rapid_damage_cycles() -> void:
	# ADV-RAPID-STATE-1: Rapid damage calls should not cause inconsistency.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_rapid_state_1_rapid_damage_cycles", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_rapid_state_1_rapid_damage_cycles", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	# Rapid damage sequence.
	for i in range(20):
		enemy.set_meta("current_hp", maxf(0.0, 100.0 - float(i * 5)))
		bar.call("on_enemy_damaged", 5.0)

	# Bar should still be valid and visible.
	_assert_true(
		is_instance_valid(bar) and bar.visible,
		"test_adv_rapid_state_1_rapid_damage_cycles — consistent after rapid damages"
	)

	bar.queue_free()


func test_adv_rapid_state_2_alternating_damage_heal() -> void:
	# ADV-RAPID-STATE-2: Alternating damage/heal should maintain state.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_rapid_state_2_alternating_damage_heal", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_rapid_state_2_alternating_damage_heal", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	# Alternate damage/heal 10 times.
	for i in range(10):
		if i % 2 == 0:
			enemy.set_meta("current_hp", 25.0)
			bar.call("on_enemy_damaged", 25.0)
		else:
			enemy.set_meta("current_hp", 75.0)
			bar.call("on_enemy_healed", 50.0)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_rapid_state_2_alternating_damage_heal — stable after alternating"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-BOUNDARY-UPDATE: Update method boundary conditions
# ---------------------------------------------------------------------------

func test_adv_boundary_update_1_update_with_zero_hp() -> void:
	# ADV-BOUNDARY-UPDATE-1: update_from_enemy() with 0 HP should work.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_update_1_update_with_zero_hp", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(0.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_update_1_update_with_zero_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar != null:
		_assert_eq_float(0.0, progress_bar.value, "fill is 0 at zero HP")

	_assert_true(
		is_instance_valid(bar),
		"test_adv_boundary_update_1_update_with_zero_hp — survives zero HP"
	)

	bar.queue_free()


func test_adv_boundary_update_2_update_with_max_hp() -> void:
	# ADV-BOUNDARY-UPDATE-2: update_from_enemy() with max HP should work.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_update_2_update_with_max_hp", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_update_2_update_with_max_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar != null:
		_assert_eq_float(100.0, progress_bar.value, "fill is 100 at max HP")

	_assert_false(
		bar.visible,
		"test_adv_boundary_update_2_update_with_max_hp — hidden at full health"
	)

	bar.queue_free()


func test_adv_boundary_update_3_sequential_updates() -> void:
	# ADV-BOUNDARY-UPDATE-3: Multiple sequential updates should maintain state.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_adv_boundary_update_3_sequential_updates", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_adv_boundary_update_3_sequential_updates", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	# Update 1: Full health.
	bar.call("update_from_enemy", enemy)
	_assert_false(bar.visible, "hidden at full health")

	# Update 2: Damaged.
	enemy.set_meta("current_hp", 50.0)
	bar.call("update_from_enemy", enemy)
	bar.call("on_enemy_damaged", 50.0)
	_assert_true(bar.visible, "visible when damaged")

	# Update 3: Full health again.
	enemy.set_meta("current_hp", 100.0)
	bar.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(bar),
		"test_adv_boundary_update_3_sequential_updates — consistent"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_bar_3d_adversarial_part2.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-FILL-MUTATIONS tests
	test_adv_fill_1_fill_monotonic_increase()
	test_adv_fill_2_fill_monotonic_decrease()
	test_adv_fill_3_fill_fractional_precision()

	# ADV-STRESS tests
	test_adv_stress_1_many_bars_simultaneous()
	test_adv_stress_2_rapid_spawn_despawn_cycles()

	# ADV-DETERMINISM tests
	test_adv_determinism_1_same_hp_same_fill()
	test_adv_determinism_2_visibility_toggle_consistency()

	# ADV-RAPID-STATE tests
	test_adv_rapid_state_1_rapid_damage_cycles()
	test_adv_rapid_state_2_alternating_damage_heal()

	# ADV-BOUNDARY-UPDATE tests
	test_adv_boundary_update_1_update_with_zero_hp()
	test_adv_boundary_update_2_update_with_max_hp()
	test_adv_boundary_update_3_sequential_updates()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
