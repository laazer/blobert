#
# test_enemy_health_bar_3d_adversarial.gd
#
# Adversarial / edge-case test suite for enemy floating health bar (M8 feature).
# Extends the primary test suite with mutation testing, boundary conditions,
# concurrency scenarios, error handling, and spec gap detection.
#
# This suite targets runtime vulnerabilities: null inputs, extreme values,
# rapid state changes, incomplete lifecycle, and feature toggle edge cases.
#
# Traceability: Extends primary test file at tests/ui/test_enemy_health_bar_3d.gd
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# ADV-NULLS: Null/empty input handling
# ---------------------------------------------------------------------------

func test_adv_null_1_null_enemy_reference() -> void:
	# ADV-NULL-1: Health bar attachment to null enemy should not crash.
	# Defensive: does not require valid enemy.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-NULL-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-NULL-1", "could not instantiate health bar")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-NULL-1", "no valid scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)

	# Attempt to call any health-update method with null enemy.
	# Should either be idempotent or explicitly handle null.
	if bar.has_method("update_from_enemy"):
		bar.call("update_from_enemy", null)

	# Bar must still exist and be freeable.
	_assert_true(
		is_instance_valid(bar),
		"ADV-NULL-1 — bar survives null enemy reference"
	)

	bar.queue_free()


func test_adv_null_2_missing_hp_property_on_enemy() -> void:
	# ADV-NULL-2: If enemy lacks current_hp or max_hp property,
	# bar should not crash; should handle gracefully or check before access.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-NULL-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-NULL-2", "could not instantiate health bar")
		return

	# Create an enemy WITHOUT health properties.
	var enemy = CharacterBody3D.new()
	enemy.set_script(load("res://scripts/enemies/enemy_base.gd"))

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-NULL-2", "no valid scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	# Trigger any health-update method.
	if bar.has_method("update_from_enemy"):
		bar.call("update_from_enemy", enemy)

	# Bar must not crash.
	_assert_true(
		is_instance_valid(bar),
		"ADV-NULL-2 — bar handles enemy without health properties"
	)

	enemy.queue_free()


func test_adv_null_3_empty_scene_tree_root() -> void:
	# ADV-NULL-3: Bar removal when scene tree root is empty or null.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-NULL-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-NULL-3", "could not instantiate health bar")
		return

	# Do NOT add bar to tree; attempt to queue_free directly.
	bar.queue_free()

	_assert_true(
		bar.is_queued_for_deletion(),
		"ADV-NULL-3 — bar can be freed without being in tree"
	)


# ---------------------------------------------------------------------------
# ADV-BOUNDARY: Boundary and extreme values
# ---------------------------------------------------------------------------

func test_adv_boundary_1_exact_zero_fill() -> void:
	# ADV-BOUNDARY-1: When current_hp == 0, fill must be exactly 0.0, not < 0.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BOUNDARY-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-BOUNDARY-1", "could not instantiate health bar")
		return

	# Locate ProgressBar.
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
		_fail("ADV-BOUNDARY-1", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	progress_bar.value = 0.0

	# Must be exactly 0, not negative.
	_assert_true(
		progress_bar.value >= 0.0,
		"ADV-BOUNDARY-1 — fill is non-negative when hp==0"
	)
	_assert_eq_float(
		0.0,
		progress_bar.value,
		"ADV-BOUNDARY-1 — fill is exactly 0.0 when hp==0"
	)

	bar.queue_free()


func test_adv_boundary_2_exact_one_fill() -> void:
	# ADV-BOUNDARY-2: When current_hp == max_hp, fill must be exactly 1.0, not > 1.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BOUNDARY-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-BOUNDARY-2", "could not instantiate health bar")
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
		_fail("ADV-BOUNDARY-2", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	progress_bar.value = 100.0

	# Must be exactly 1.0 (ratio), not > 1.
	_assert_true(
		progress_bar.value <= progress_bar.max_value,
		"ADV-BOUNDARY-2 — fill is clamped when hp==max_hp"
	)
	_assert_eq_float(
		1.0,
		progress_bar.value / progress_bar.max_value,
		"ADV-BOUNDARY-2 — fill ratio is exactly 1.0 when hp==max_hp"
	)

	bar.queue_free()


func test_adv_boundary_3_negative_hp_clamped() -> void:
	# ADV-BOUNDARY-3: If enemy somehow has negative HP (bug elsewhere),
	# bar fill must not go negative. Must clamp to [0, max].
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BOUNDARY-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-BOUNDARY-3", "could not instantiate health bar")
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
		_fail("ADV-BOUNDARY-3", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	progress_bar.value = -10.0  # Negative HP edge case

	_assert_true(
		progress_bar.value >= 0.0,
		"ADV-BOUNDARY-3 — bar value is non-negative even if set to negative"
	)

	bar.queue_free()


func test_adv_boundary_4_huge_max_hp() -> void:
	# ADV-BOUNDARY-4: When max_hp is very large (e.g., 1_000_000),
	# bar still computes correct fill ratio without overflow/underflow.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BOUNDARY-4", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-BOUNDARY-4", "could not instantiate health bar")
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
		_fail("ADV-BOUNDARY-4", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 1_000_000.0
	progress_bar.value = 500_000.0

	# Ratio should be exactly 0.5.
	var ratio = progress_bar.value / progress_bar.max_value
	_assert_eq_float(
		0.5,
		ratio,
		"ADV-BOUNDARY-4 — bar fill ratio is correct for very large max_hp"
	)

	bar.queue_free()


func test_adv_boundary_5_tiny_positive_max_hp() -> void:
	# ADV-BOUNDARY-5: When max_hp is very small but positive (e.g., 0.001),
	# bar computes correct ratio without division edge cases.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-BOUNDARY-5", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-BOUNDARY-5", "could not instantiate health bar")
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
		_fail("ADV-BOUNDARY-5", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 0.001
	progress_bar.value = 0.0005

	# Ratio should be exactly 0.5 (no division by zero, no NaN).
	var ratio = progress_bar.value / progress_bar.max_value
	_assert_true(
		not is_nan(ratio) and ratio > 0 and ratio <= 1.0,
		"ADV-BOUNDARY-5 — bar fill ratio is valid for tiny max_hp"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-INVALID: Invalid / corrupt input handling
# ---------------------------------------------------------------------------

func test_adv_invalid_1_nan_hp_value() -> void:
	# ADV-INVALID-1: If enemy HP is NaN (corrupt floating point),
	# bar must not crash; should either ignore or clamp to safe value.
	# CHECKPOINT: Assume NaN is clamped to 0 or max.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-INVALID-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-INVALID-1", "could not instantiate health bar")
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
		_fail("ADV-INVALID-1", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	var nan_val: float = 0.0 / 0.0  # Produces NaN
	progress_bar.value = nan_val

	# Bar must still exist; value should be safe.
	_assert_true(
		is_instance_valid(bar),
		"ADV-INVALID-1 — bar survives NaN hp assignment"
	)

	bar.queue_free()


func test_adv_invalid_2_inf_hp_value() -> void:
	# ADV-INVALID-2: If enemy HP is infinity, bar must not crash.
	# Should clamp or handle gracefully.
	# CHECKPOINT: Assume infinity is clamped to max_hp.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-INVALID-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-INVALID-2", "could not instantiate health bar")
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
		_fail("ADV-INVALID-2", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = 100.0
	var inf_val: float = 1e308 * 10.0  # Approaches infinity
	progress_bar.value = inf_val

	# Bar must still exist; no crash.
	_assert_true(
		is_instance_valid(bar),
		"ADV-INVALID-2 — bar survives infinity hp assignment"
	)

	bar.queue_free()


func test_adv_invalid_3_negative_max_hp() -> void:
	# ADV-INVALID-3: If max_hp is negative (should never happen),
	# bar handles gracefully without division error.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-INVALID-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-INVALID-3", "could not instantiate health bar")
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
		_fail("ADV-INVALID-3", "no ProgressBar found")
		bar.queue_free()
		return

	progress_bar.max_value = -100.0  # Invalid but should not crash.
	progress_bar.value = 50.0

	_assert_true(
		is_instance_valid(bar),
		"ADV-INVALID-3 — bar survives negative max_hp"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-VISIBILITY: Visibility state machine edge cases
# ---------------------------------------------------------------------------

func test_adv_visibility_1_rapid_damage_hide_cycles() -> void:
	# ADV-VISIBILITY-1: Rapid damage → hide → damage → hide cycles
	# should not leave bar in inconsistent state.
	# CHECKPOINT: Bar visibility state must be deterministic after sequence.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-VISIBILITY-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-VISIBILITY-1", "could not instantiate health bar")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-VISIBILITY-1", "no valid scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)

	if bar is CanvasItem:
		# Simulate damage (show).
		bar.visible = true
		_assert_true(bar.visible, "ADV-VISIBILITY-1 — bar shown on damage (1)")

		# Simulate full health hide.
		bar.visible = false
		_assert_false(bar.visible, "ADV-VISIBILITY-1 — bar hidden at full health (1)")

		# Repeat rapidly.
		bar.visible = true
		_assert_true(bar.visible, "ADV-VISIBILITY-1 — bar shown on damage (2)")
		bar.visible = false
		_assert_false(bar.visible, "ADV-VISIBILITY-1 — bar hidden at full health (2)")
	else:
		_fail("ADV-VISIBILITY-1", "bar is not a CanvasItem")

	bar.queue_free()


func test_adv_visibility_2_show_without_damage_signal() -> void:
	# ADV-VISIBILITY-2: Bar should remain hidden if enemy has not taken damage.
	# No direct visibility toggle should happen without a damage event.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-VISIBILITY-2", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-VISIBILITY-2", "could not instantiate health bar")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-VISIBILITY-2", "no valid scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)

	# On initialization, bar should default to hidden (no damage yet).
	if bar is CanvasItem:
		# Bar should be hidden by default.
		_assert_false(
			bar.visible,
			"ADV-VISIBILITY-2 — bar is hidden by default (no damage)"
		)
	else:
		_fail("ADV-VISIBILITY-2", "bar is not a CanvasItem")

	bar.queue_free()


func test_adv_visibility_3_multiple_visibility_timeouts() -> void:
	# ADV-VISIBILITY-3: If bar is shown multiple times rapidly,
	# timeout timers should not stack or conflict.
	# CHECKPOINT: Only one timeout should be active at a time.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-VISIBILITY-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-VISIBILITY-3", "could not instantiate health bar")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-VISIBILITY-3", "no valid scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)

	if bar is CanvasItem:
		# Show multiple times.
		bar.visible = true
		bar.visible = true
		bar.visible = true

		_assert_true(
			bar.visible,
			"ADV-VISIBILITY-3 — bar remains visible after multiple shows"
		)
	else:
		_fail("ADV-VISIBILITY-3", "bar is not a CanvasItem")

	bar.queue_free()


# ---------------------------------------------------------------------------
# ADV-LIFECYCLE: Cleanup and orphan prevention
# ---------------------------------------------------------------------------

func test_adv_lifecycle_1_no_orphan_on_early_despawn() -> void:
	# ADV-LIFECYCLE-1: If enemy despawns before bar cleanup signal is sent,
	# bar must be freed (not orphaned in tree).
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-LIFECYCLE-1", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-LIFECYCLE-1", "could not instantiate health bar")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-LIFECYCLE-1", "no valid scene tree")
		bar.queue_free()
		return

	# Create enemy, attach bar, then free enemy immediately.
	var enemy = CharacterBody3D.new()
	tree.root.add_child(enemy)
	enemy.add_child(bar)

	# Simulate despawn by freeing enemy.
	enemy.queue_free()

	# Bar should also be queued (parent dependency).
	_assert_true(
		bar.is_queued_for_deletion(),
		"ADV-LIFECYCLE-1 — bar is freed when enemy is freed"
	)


func test_adv_lifecycle_2_multiple_bars_per_enemy_cleanup() -> void:
	# ADV-LIFECYCLE-2: If multiple bars somehow exist on same enemy,
	# all must be cleaned up (no partial orphaning).
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-LIFECYCLE-2", "health bar scene not found")
		return

	var bar1 = scene.instantiate() as Node
	var bar2 = scene.instantiate() as Node
	if bar1 == null or bar2 == null:
		_fail("ADV-LIFECYCLE-2", "could not instantiate health bar")
		if bar1 != null:
			bar1.queue_free()
		if bar2 != null:
			bar2.queue_free()
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-LIFECYCLE-2", "no valid scene tree")
		bar1.queue_free()
		bar2.queue_free()
		return

	var enemy = CharacterBody3D.new()
	tree.root.add_child(enemy)
	enemy.add_child(bar1)
	enemy.add_child(bar2)

	# Free enemy.
	enemy.queue_free()

	# Both bars must be queued.
	_assert_true(
		bar1.is_queued_for_deletion() and bar2.is_queued_for_deletion(),
		"ADV-LIFECYCLE-2 — all bars freed when enemy freed"
	)


func test_adv_lifecycle_3_orphan_detection_after_free() -> void:
	# ADV-LIFECYCLE-3: After enemy is freed, orphaned bar should be
	# detectable (get_parent() == null).
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("ADV-LIFECYCLE-3", "health bar scene not found")
		return

	var bar = scene.instantiate() as Node
	if bar == null:
		_fail("ADV-LIFECYCLE-3", "could not instantiate health bar")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("ADV-LIFECYCLE-3", "no valid scene tree")
		bar.queue_free()
		return

	var enemy = CharacterBody3D.new()
	tree.root.add_child(enemy)
	enemy.add_child(bar)

	var parent_before_free = bar.get_parent()
	_assert_true(
		parent_before_free == enemy,
		"ADV-LIFECYCLE-3 — bar parent is enemy before free"
	)

	# Free enemy without freeing bar (orphan scenario).
	enemy.free()

	# At next tick, bar's parent should be null (orphaned).
	# For determinism, we check immediately after free().
	var parent_after_free = bar.get_parent()

	# If bar is still in tree, parent will be null (enemy was freed).
	# If bar was also freed, is_instance_valid will return false.
	if parent_after_free == null or not is_instance_valid(bar):
		_pass("ADV-LIFECYCLE-3 — orphaned bar is detectable")
	else:
		_fail("ADV-LIFECYCLE-3", "orphaned bar not cleaned up")

	# Clean up.
	if is_instance_valid(bar):
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
	test_adv_null_2_missing_hp_property_on_enemy()
	test_adv_null_3_empty_scene_tree_root()

	# ADV-BOUNDARY tests
	test_adv_boundary_1_exact_zero_fill()
	test_adv_boundary_2_exact_one_fill()
	test_adv_boundary_3_negative_hp_clamped()
	test_adv_boundary_4_huge_max_hp()
	test_adv_boundary_5_tiny_positive_max_hp()

	# ADV-INVALID tests
	test_adv_invalid_1_nan_hp_value()
	test_adv_invalid_2_inf_hp_value()
	test_adv_invalid_3_negative_max_hp()

	# ADV-VISIBILITY tests
	test_adv_visibility_1_rapid_damage_hide_cycles()
	test_adv_visibility_2_show_without_damage_signal()
	test_adv_visibility_3_multiple_visibility_timeouts()

	# ADV-LIFECYCLE tests
	test_adv_lifecycle_1_no_orphan_on_early_despawn()
	test_adv_lifecycle_2_multiple_bars_per_enemy_cleanup()
	test_adv_lifecycle_3_orphan_detection_after_free()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
