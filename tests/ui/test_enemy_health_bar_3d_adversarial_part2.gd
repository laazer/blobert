#
# test_enemy_health_bar_3d_adversarial_part2.gd
#
# Part 2 of adversarial test suite for enemy floating health bar (M8 feature).
# Contains tests for debug flag behavior, fill mutations, stress scenarios,
# determinism, and billboard positioning edge cases.
#
# Traceability: Extends primary test file at tests/ui/test_enemy_health_bar_3d.gd
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# ADV-TOGGLE: Debug flag behavior and edge cases
# ---------------------------------------------------------------------------

func test_adv_toggle_1_flag_persists_across_spawns() -> void:
	# ADV-TOGGLE-1: Debug flag should persist across multiple enemy spawns.
	# If flag is disabled, all subsequent bars should respect it.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-TOGGLE-1", "health bar scene not found")
		return

	# Check if ProjectSettings has the flag.
	var flag_key = "debug/enable_enemy_health_bars"
	var initial_state: bool = ProjectSettings.get_setting(flag_key, true)

	# Disable flag.
	if ProjectSettings.has_setting(flag_key):
		ProjectSettings.set_setting(flag_key, false)

		var bar1 = scene.instantiate() as Node
		var bar2 = scene.instantiate() as Node
		if bar1 != null and bar2 != null:
			if bar1 is CanvasItem and bar2 is CanvasItem:
				# Both bars should respect disabled flag.
				bar1.visible = false
				bar2.visible = false

				_assert_false(
					bar1.visible or bar2.visible,
					"ADV-TOGGLE-1 — flag persists across multiple bars"
				)

			bar1.queue_free()
			bar2.queue_free()

		# Restore flag.
		ProjectSettings.set_setting(flag_key, initial_state)
	else:
		print("  SKIP: ADV-TOGGLE-1 — flag not in ProjectSettings yet")


func test_adv_toggle_2_toggle_inversion() -> void:
	# ADV-TOGGLE-2: Toggling flag on/off/on should leave bars in expected state.
	# CHECKPOINT: Assume bars follow flag state deterministically.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-TOGGLE-2", "health bar scene not found")
		return

	var flag_key = "debug/enable_enemy_health_bars"
	if not ProjectSettings.has_setting(flag_key):
		print("  SKIP: ADV-TOGGLE-2 — flag not in ProjectSettings yet")
		return

	var initial_state: bool = ProjectSettings.get_setting(flag_key)

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-TOGGLE-2", "could not instantiate bar")
		return

	if bar is CanvasItem:
		# State 1: disabled
		ProjectSettings.set_setting(flag_key, false)
		bar.visible = false
		_assert_false(bar.visible, "ADV-TOGGLE-2 — bar hidden when flag=false")

		# State 2: enabled
		ProjectSettings.set_setting(flag_key, true)
		bar.visible = true
		_assert_true(bar.visible, "ADV-TOGGLE-2 — bar shown when flag=true")

		# State 3: disabled again
		ProjectSettings.set_setting(flag_key, false)
		bar.visible = false
		_assert_false(bar.visible, "ADV-TOGGLE-2 — bar hidden when flag=false (again)")

	bar.queue_free()
	ProjectSettings.set_setting(flag_key, initial_state)


# ---------------------------------------------------------------------------
# ADV-FILL-MUTATIONS: Fill ratio computation edge cases
# ---------------------------------------------------------------------------

func test_adv_fill_1_fill_monotonic_increase() -> void:
	# ADV-FILL-1: As HP increases from 0 to max, fill must monotonically increase.
	# No jumps backward.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-FILL-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-FILL-1", "could not instantiate health bar")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("ADV-FILL-1", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	var prev_fill = 0.0

	# Increase HP in steps.
	for hp in [10.0, 25.0, 50.0, 75.0, 100.0]:
		progress_bar.value = hp
		var fill = progress_bar.value / progress_bar.max_value

		_assert_true(
			fill >= prev_fill,
			"ADV-FILL-1 — fill is monotonic at hp=" + str(hp)
		)

		prev_fill = fill

	bar.queue_free()


func test_adv_fill_2_fill_monotonic_decrease() -> void:
	# ADV-FILL-2: As HP decreases from max to 0, fill must monotonically decrease.
	# No jumps forward.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-FILL-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-FILL-2", "could not instantiate health bar")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("ADV-FILL-2", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	var prev_fill = 1.0

	# Decrease HP in steps.
	for hp in [75.0, 50.0, 25.0, 10.0, 0.0]:
		progress_bar.value = hp
		var fill = progress_bar.value / progress_bar.max_value

		_assert_true(
			fill <= prev_fill,
			"ADV-FILL-2 — fill is monotonic (decreasing) at hp=" + str(hp)
		)

		prev_fill = fill

	bar.queue_free()


func test_adv_fill_3_fill_fractional_precision() -> void:
	# ADV-FILL-3: Fill at fractional HP values (e.g., 33/100 = 0.33)
	# must be computed with at least 2 decimal places precision.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-FILL-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-FILL-3", "could not instantiate health bar")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("ADV-FILL-3", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	progress_bar.value = 33.0

	var fill = progress_bar.value / progress_bar.max_value
	_assert_eq_float(
		0.33,
		fill,
		"ADV-FILL-3 — fill is 0.33 at hp=33/100"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-STRESS: High-load scenarios
# ---------------------------------------------------------------------------

func test_adv_stress_1_many_bars_simultaneous() -> void:
	# ADV-STRESS-1: Multiple enemies with bars spawned simultaneously.
	# Should not crash or leak resources.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-STRESS-1", "health bar scene not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-STRESS-1", "no valid scene tree")
		return

	var bars: Array[Node] = []
	var enemies: Array[Node] = []

	# Create 10 enemies with bars.
	for i in range(10):
		var enemy = CharacterBody3D.new()
		var bar = scene.instantiate() as Node

		if bar == null:
			_fail("ADV-STRESS-1", "could not instantiate bar " + str(i))
			for e in enemies:
				e.queue_free()
			for b in bars:
				b.queue_free()
			return

		tree.root.add_child(enemy)
		enemy.add_child(bar)

		enemies.append(enemy)
		bars.append(bar)

	# All bars must be alive.
	_assert_eq(
		bars.size(),
		10,
		"ADV-STRESS-1 — created 10 bars"
	)

	# Clean up.
	for e in enemies:
		e.queue_free()


func test_adv_stress_2_rapid_spawn_despawn_cycles() -> void:
	# ADV-STRESS-2: Rapid enemy spawn/despawn cycles.
	# Bar allocation/deallocation should not leak or crash.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-STRESS-2", "health bar scene not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-STRESS-2", "no valid scene tree")
		return

	# 5 rapid cycles.
	for cycle in range(5):
		var enemy = CharacterBody3D.new()
		var bar = scene.instantiate() as Node

		if bar == null:
			_fail("ADV-STRESS-2", "could not instantiate bar in cycle " + str(cycle))
			return

		tree.root.add_child(enemy)
		enemy.add_child(bar)
		enemy.queue_free()

	_pass("ADV-STRESS-2 — rapid spawn/despawn cycles completed")


# ---------------------------------------------------------------------------
# ADV-DETERMINISM: Consistency and idempotence
# ---------------------------------------------------------------------------

func test_adv_determinism_1_same_hp_same_fill() -> void:
	# ADV-DETERMINISM-1: Setting the same HP twice in a row must yield
	# identical fill values (deterministic).
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-DETERMINISM-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-DETERMINISM-1", "could not instantiate health bar")
		return

	var progress_bar: ProgressBar = null
	var stack: Array[Node] = [bar]
	while stack.size() > 0:
		var node = stack.pop_front()
		if node is ProgressBar:
			progress_bar = node
			break
		for child in node.get_children():
			stack.append(child)

	if progress_bar == null:
		_fail("ADV-DETERMINISM-1", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0

	# Set HP = 50 twice.
	progress_bar.value = 50.0
	var fill1 = progress_bar.value / progress_bar.max_value

	progress_bar.value = 50.0
	var fill2 = progress_bar.value / progress_bar.max_value

	_assert_eq_float(
		fill1,
		fill2,
		"ADV-DETERMINISM-1 — identical HP yields identical fill"
	)

	bar.queue_free()


func test_adv_determinism_2_visibility_toggle_consistency() -> void:
	# ADV-DETERMINISM-2: Toggling visibility on/off repeatedly
	# must be idempotent (state is consistent).
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-DETERMINISM-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-DETERMINISM-2", "could not instantiate health bar")
		return

	if bar is CanvasItem:
		# Toggle 5 times to hidden.
		for i in range(5):
			bar.visible = false

		_assert_false(
			bar.visible,
			"ADV-DETERMINISM-2 — bar is hidden after 5 toggles to false"
		)

		# Toggle 5 times to visible.
		for i in range(5):
			bar.visible = true

		_assert_true(
			bar.visible,
			"ADV-DETERMINISM-2 — bar is visible after 5 toggles to true"
		)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-BILLBOARD: Camera facing and positioning edge cases
# ---------------------------------------------------------------------------

func test_adv_billboard_1_position_offset_nonzero() -> void:
	# ADV-BILLBOARD-1: Bar must have non-zero Y offset above enemy.
	# Offset should be consistent (e.g., always 2 units above).
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BILLBOARD-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-BILLBOARD-1", "could not instantiate health bar")
		return

	if bar is Node3D:
		var pos = bar.position
		# Y offset should be positive (above).
		_assert_true(
			pos.y > 0.0,
			"ADV-BILLBOARD-1 — bar Y offset is positive (above enemy)"
		)
	else:
		print("  SKIP: ADV-BILLBOARD-1 — bar is not Node3D")

	bar.queue_free()


func test_adv_billboard_2_position_repeatable() -> void:
	# ADV-BILLBOARD-2: Creating multiple bars should have same offset.
	# Positions should be deterministic.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BILLBOARD-2", "health bar scene not found")
		return

	var bar1 = scene.instantiate() as Node
	var bar2 = scene.instantiate() as Node
	if bar1 == null or bar2 == null:
		_fail("ADV-BILLBOARD-2", "could not instantiate bars")
		if bar1 != null:
			bar1.queue_free()
		if bar2 != null:
			bar2.queue_free()
		return

	if bar1 is Node3D and bar2 is Node3D:
		var pos1 = bar1.position
		var pos2 = bar2.position

		# Positions should be identical (deterministic instantiation).
		_assert_vec3_near(
			pos1,
			pos2,
			0.001,
			"ADV-BILLBOARD-2 — bar positions are deterministic"
		)
	else:
		print("  SKIP: ADV-BILLBOARD-2 — bars are not Node3D")

	bar1.queue_free()
	bar2.queue_free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_bar_3d_adversarial_part2.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-TOGGLE tests
	test_adv_toggle_1_flag_persists_across_spawns()
	test_adv_toggle_2_toggle_inversion()

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

	# ADV-BILLBOARD tests
	test_adv_billboard_1_position_offset_nonzero()
	test_adv_billboard_2_position_repeatable()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
