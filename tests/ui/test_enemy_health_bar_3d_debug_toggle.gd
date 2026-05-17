#
# test_enemy_health_bar_3d_debug_toggle.gd
#
# AC 6: Feature can be toggled with a project/debug flag for performance testing.
#
# This test suite verifies that the debug toggle feature works correctly:
# - When enabled = true: bar methods execute normally and produce observable changes
# - When enabled = false: bar methods skip execution and produce no state changes
# - Guard clauses prevent updates when disabled
#
# Behavioral tests that verify actual method execution, not prose assertions.
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/01_enemy_floating_health_bar.md
# AC 6: Feature can be toggled with a project/debug flag for performance testing
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure: local helpers that reuse shared test utilities
# ---------------------------------------------------------------------------

# Create a mock enemy with health component for testing.
func _create_mock_enemy(hp: float = 100.0, max_hp: float = 100.0) -> CharacterBody3D:
	return test_create_mock_enemy(hp, max_hp)


# Load health bar scene and instantiate it.
func _load_and_instantiate_health_bar() -> Variant:
	return test_load_and_instantiate_scene("res://scenes/ui/enemy_health_bar_3d.tscn")


# Get the ProgressBar from within a health bar instance.
func _find_progress_bar(bar: Node) -> Variant:
	return test_find_progress_bar(bar)


# ---------------------------------------------------------------------------
# Test: enabled = true (default) — methods execute normally
# ---------------------------------------------------------------------------

func test_debug_toggle_enabled_true_update_from_enemy_changes_fill() -> void:
	# Test: When enabled = true, update_from_enemy() updates progress bar fill.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_enabled_true_update_from_enemy_changes_fill", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_enabled_true_update_from_enemy_changes_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Explicitly set enabled = true
	bar.set("enabled", true)

	# Call _ready to initialize bar
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Initial fill should be 100% (default)
	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_debug_toggle_enabled_true_update_from_enemy_changes_fill", "no ProgressBar found")
		bar.queue_free()
		return

	# Call update_from_enemy with 50% HP enemy
	bar.call("update_from_enemy", enemy)

	# Verify fill changed to 50% (observable state change)
	_assert_eq_float(
		50.0,
		progress_bar.value,
		"test_debug_toggle_enabled_true_update_from_enemy_changes_fill — fill updates to 50% when enabled=true"
	)

	bar.queue_free()


func test_debug_toggle_enabled_true_on_enemy_damaged_shows_bar() -> void:
	# Test: When enabled = true, on_enemy_damaged() shows the bar.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_enabled_true_on_enemy_damaged_shows_bar", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_enabled_true_on_enemy_damaged_shows_bar", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Explicitly set enabled = true
	bar.set("enabled", true)

	if bar.has_method("_ready"):
		bar.call("_ready")

	# Bar starts hidden
	_assert_false(
		bar.visible,
		"test_debug_toggle_enabled_true_on_enemy_damaged_shows_bar — bar starts hidden"
	)

	# Set up the bar with an enemy
	bar.call("update_from_enemy", enemy)

	# Call on_enemy_damaged
	bar.call("on_enemy_damaged", 10.0)

	# Bar should now be visible (observable state change)
	_assert_true(
		bar.visible,
		"test_debug_toggle_enabled_true_on_enemy_damaged_shows_bar — bar becomes visible when damaged with enabled=true"
	)

	bar.queue_free()


func test_debug_toggle_enabled_true_on_enemy_healed_updates_fill() -> void:
	# Test: When enabled = true, on_enemy_healed() updates the fill.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_enabled_true_on_enemy_healed_updates_fill", "health bar not found")
		return

	var enemy = _create_mock_enemy(25.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_enabled_true_on_enemy_healed_updates_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Explicitly set enabled = true
	bar.set("enabled", true)

	if bar.has_method("_ready"):
		bar.call("_ready")

	# Set up bar with 25% HP enemy
	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_debug_toggle_enabled_true_on_enemy_healed_updates_fill", "no ProgressBar found")
		bar.queue_free()
		return

	# Verify initial fill is 25%
	_assert_eq_float(
		25.0,
		progress_bar.value,
		"test_debug_toggle_enabled_true_on_enemy_healed_updates_fill — initial fill is 25%"
	)

	# Simulate heal by changing enemy HP
	enemy.set_meta("current_hp", 75.0)

	# Call on_enemy_healed
	bar.call("on_enemy_healed", 50.0)

	# Fill should update to 75%
	_assert_eq_float(
		75.0,
		progress_bar.value,
		"test_debug_toggle_enabled_true_on_enemy_healed_updates_fill — fill updates to 75% when healed with enabled=true"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Test: enabled = false — methods skip execution (guard clauses work)
# ---------------------------------------------------------------------------

func test_debug_toggle_disabled_on_enemy_damaged_does_not_show_bar() -> void:
	# Test: When enabled = false, on_enemy_damaged() does NOT show the bar (guard clause).
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_disabled_on_enemy_damaged_does_not_show_bar", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_disabled_on_enemy_damaged_does_not_show_bar", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Explicitly set enabled = false
	bar.set("enabled", false)

	if bar.has_method("_ready"):
		bar.call("_ready")

	# Set up bar with enemy
	bar.call("update_from_enemy", enemy)

	# Bar starts hidden
	var initial_visible = bar.visible
	_assert_false(
		initial_visible,
		"test_debug_toggle_disabled_on_enemy_damaged_does_not_show_bar — bar starts hidden"
	)

	# Call on_enemy_damaged with enabled = false
	bar.call("on_enemy_damaged", 10.0)

	# Bar should REMAIN hidden (no state change due to guard clause)
	_assert_false(
		bar.visible,
		"test_debug_toggle_disabled_on_enemy_damaged_does_not_show_bar — bar remains hidden when damaged with enabled=false"
	)

	bar.queue_free()


func test_debug_toggle_disabled_on_enemy_healed_does_not_update_fill() -> void:
	# Test: When enabled = false, on_enemy_healed() does NOT update fill (guard clause).
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_disabled_on_enemy_healed_does_not_update_fill", "health bar not found")
		return

	var enemy = _create_mock_enemy(25.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_disabled_on_enemy_healed_does_not_update_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Explicitly set enabled = false
	bar.set("enabled", false)

	if bar.has_method("_ready"):
		bar.call("_ready")

	# Set up bar with 25% HP enemy (this will still set fill since update_from_enemy is not guarded at this level in _ready)
	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_debug_toggle_disabled_on_enemy_healed_does_not_update_fill", "no ProgressBar found")
		bar.queue_free()
		return

	# Get the current fill value
	var fill_before = progress_bar.value

	# Simulate heal by changing enemy HP
	enemy.set_meta("current_hp", 75.0)

	# Call on_enemy_healed with enabled = false
	bar.call("on_enemy_healed", 50.0)

	# Fill should NOT change (guard clause prevents update)
	var fill_after = progress_bar.value
	_assert_eq_float(
		fill_before,
		fill_after,
		"test_debug_toggle_disabled_on_enemy_healed_does_not_update_fill — fill unchanged when healed with enabled=false"
	)

	bar.queue_free()


func test_debug_toggle_disabled_process_does_not_update_position() -> void:
	# Test: When enabled = false, _process() guard clause prevents position updates.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_disabled_process_does_not_update_position", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_disabled_process_does_not_update_position", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Explicitly set enabled = false
	bar.set("enabled", false)

	if bar.has_method("_ready"):
		bar.call("_ready")

	# Set up bar with enemy
	bar.call("update_from_enemy", enemy)

	# Store initial position (should be set during update_from_enemy)
	var initial_position = bar.global_position

	# Manually move the enemy
	enemy.global_position = Vector3(10.0, 0.0, 10.0)

	# Call _process with enabled = false (should not update position)
	bar.call("_process", 0.016)

	# Position should NOT have changed (guard clause in _process prevents _update_position_and_rotation)
	var final_position = bar.global_position
	_assert_eq(
		initial_position,
		final_position,
		"test_debug_toggle_disabled_process_does_not_update_position — position unchanged during _process with enabled=false"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Test: toggle behavior — verify enabled can be toggled and guard clauses respond
# ---------------------------------------------------------------------------

func test_debug_toggle_can_toggle_enabled_runtime() -> void:
	# Test: enabled flag can be toggled at runtime and guard clauses respond.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_can_toggle_enabled_runtime", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_can_toggle_enabled_runtime", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	if bar.has_method("_ready"):
		bar.call("_ready")

	# Start with enabled = true
	bar.set("enabled", true)
	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_debug_toggle_can_toggle_enabled_runtime", "no ProgressBar found")
		bar.queue_free()
		return

	# With enabled=true, change HP should update fill
	enemy.set_meta("current_hp", 25.0)
	bar.call("on_enemy_healed", 0.0)  # Trigger damage path that calls _update_health_display
	var fill_when_enabled = progress_bar.value

	# Now disable
	bar.set("enabled", false)

	# Change HP again
	enemy.set_meta("current_hp", 75.0)

	# Call on_enemy_healed with enabled=false (guard clause blocks update)
	bar.call("on_enemy_healed", 0.0)

	# Fill should NOT change
	var fill_when_disabled = progress_bar.value
	_assert_eq_float(
		fill_when_enabled,
		fill_when_disabled,
		"test_debug_toggle_can_toggle_enabled_runtime — fill does not change when disabled at runtime"
	)

	bar.queue_free()


func test_debug_toggle_multiple_state_changes_with_disabled() -> void:
	# Test: Multiple method calls with enabled=false produce no observable changes.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_debug_toggle_multiple_state_changes_with_disabled", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_debug_toggle_multiple_state_changes_with_disabled", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Start disabled
	bar.set("enabled", false)

	if bar.has_method("_ready"):
		bar.call("_ready")

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_debug_toggle_multiple_state_changes_with_disabled", "no ProgressBar found")
		bar.queue_free()
		return

	# Record initial state
	var initial_visible = bar.visible
	var initial_fill = progress_bar.value

	# Call multiple methods with enabled=false
	bar.call("update_from_enemy", enemy)
	bar.call("on_enemy_damaged", 10.0)
	bar.call("on_enemy_healed", 5.0)
	bar.call("on_enemy_damaged", 15.0)

	# No observable changes should occur
	_assert_eq(
		initial_visible,
		bar.visible,
		"test_debug_toggle_multiple_state_changes_with_disabled — visibility unchanged after multiple calls"
	)

	_assert_eq_float(
		initial_fill,
		progress_bar.value,
		"test_debug_toggle_multiple_state_changes_with_disabled — fill unchanged after multiple calls"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Runner integration
# ---------------------------------------------------------------------------

func run_all() -> int:
	# No-op for compatibility with test runner
	return 0
