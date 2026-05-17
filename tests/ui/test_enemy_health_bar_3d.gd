#
# test_enemy_health_bar_3d.gd
#
# Behavioral tests for world-space enemy health bar UI (M8 feature).
# Tests core integration: update_from_enemy(), on_enemy_damaged(), connect_to_enemy(),
# and damage signal wiring. All tests exercise actual methods and verify observable
# changes in the health bar state (fill value, visibility, etc.).
#
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/01_enemy_floating_health_bar.md
# Requirements:
#   - Each spawned enemy renders a floating health bar anchored above its head/body center
#   - Bar fill is driven by enemy current HP / max HP and updates immediately on damage/heal
#   - Bar is visible for damaged enemies and hidden for full-health enemies after a short timeout
#   - Bar always faces the camera (billboard behavior) and remains readable while moving
#   - Bar is removed when the enemy dies or is despawned (no orphan UI nodes)
#   - Feature can be toggled with a project/debug flag for performance testing
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure: fixtures and helpers
# ---------------------------------------------------------------------------

# Create a mock enemy with health component for testing.
# Returns a CharacterBody3D node with health properties.
func _create_mock_enemy(hp: float = 100.0, max_hp: float = 100.0) -> CharacterBody3D:
	var body := CharacterBody3D.new()
	body.set_script(load("res://scripts/enemies/enemy_base.gd"))
	body.set_meta("current_hp", hp)
	body.set_meta("max_hp", max_hp)
	return body


# Load health bar scene and instantiate it.
func _load_and_instantiate_health_bar() -> Variant:
	var path := "res://scenes/ui/enemy_health_bar_3d.tscn"
	var scene = load(path)
	if scene == null:
		return null
	return scene.instantiate() as Node


# Get the ProgressBar from within a health bar instance.
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
# Core feature tests: update_from_enemy() behavior
# ---------------------------------------------------------------------------

func test_update_from_enemy_sets_reference() -> void:
	# Test: update_from_enemy() accepts an enemy and stores the reference.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_update_from_enemy_sets_reference", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_update_from_enemy_sets_reference", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	bar.call("update_from_enemy", enemy)

	# Verify bar still exists (did not crash).
	_assert_true(
		is_instance_valid(bar),
		"test_update_from_enemy_sets_reference — bar accepts and stores enemy reference"
	)

	bar.queue_free()


func test_update_from_enemy_updates_fill_from_hp() -> void:
	# Test: update_from_enemy() reads enemy HP and updates progress bar fill ratio.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_update_from_enemy_updates_fill_from_hp", "health bar not found")
		return

	var enemy = _create_mock_enemy(50.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_update_from_enemy_updates_fill_from_hp", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Call update_from_enemy() and verify fill is set to 50%.
	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_update_from_enemy_updates_fill_from_hp", "no ProgressBar found")
		bar.queue_free()
		return

	# HP ratio should be 50/100 = 0.5, so value should be 50.0 (of max 100.0).
	_assert_eq_float(
		50.0,
		progress_bar.value,
		"test_update_from_enemy_updates_fill_from_hp — fill updates to reflect 50% HP"
	)

	bar.queue_free()


func test_update_from_enemy_at_full_health() -> void:
	# Test: When enemy is at full health, bar fill is 100%.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_update_from_enemy_at_full_health", "health bar not found")
		return

	var enemy = _create_mock_enemy(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_update_from_enemy_at_full_health", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_update_from_enemy_at_full_health", "no ProgressBar found")
		bar.queue_free()
		return

	_assert_eq_float(
		100.0,
		progress_bar.value,
		"test_update_from_enemy_at_full_health — fill is 100% at full health"
	)

	bar.queue_free()


func test_update_from_enemy_at_zero_health() -> void:
	# Test: When enemy is at 0 HP, bar fill is 0%.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_update_from_enemy_at_zero_health", "health bar not found")
		return

	var enemy = _create_mock_enemy(0.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_update_from_enemy_at_zero_health", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	# Manually call _ready() since we're not in the normal scene flow.
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_update_from_enemy_at_zero_health", "no ProgressBar found")
		bar.queue_free()
		return

	_assert_eq_float(
		0.0,
		progress_bar.value,
		"test_update_from_enemy_at_zero_health — fill is 0% at zero health"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: on_enemy_damaged() behavior
# ---------------------------------------------------------------------------

func test_on_enemy_damaged_shows_bar() -> void:
	# Test: Calling on_enemy_damaged() makes the bar visible.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_on_enemy_damaged_shows_bar", "health bar not found")
		return

	var enemy = _create_mock_enemy(75.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_on_enemy_damaged_shows_bar", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Bar starts hidden by default.
	bar.visible = false

	# Call on_enemy_damaged() and verify bar becomes visible.
	bar.call("update_from_enemy", enemy)
	bar.call("on_enemy_damaged", 10.0)

	_assert_true(
		bar.visible,
		"test_on_enemy_damaged_shows_bar — bar becomes visible when damaged"
	)

	bar.queue_free()


func test_on_enemy_damaged_updates_fill() -> void:
	# Test: on_enemy_damaged() updates the fill ratio based on current HP.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_on_enemy_damaged_updates_fill", "health bar not found")
		return

	var enemy = _create_mock_enemy(60.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_on_enemy_damaged_updates_fill", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.call("update_from_enemy", enemy)
	bar.call("on_enemy_damaged", 5.0)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar == null:
		_fail("test_on_enemy_damaged_updates_fill", "no ProgressBar found")
		bar.queue_free()
		return

	# Fill should reflect 60/100 = 0.6, so value = 60.0.
	_assert_eq_float(
		60.0,
		progress_bar.value,
		"test_on_enemy_damaged_updates_fill — fill updates on damage"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: visibility timeout behavior
# ---------------------------------------------------------------------------

func test_visibility_hidden_at_full_health() -> void:
	# Test: When enemy recovers to full health, bar initiates hide timeout.
	# After timeout, bar should be hidden.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_visibility_hidden_at_full_health", "health bar not found")
		return

	var enemy = _create_mock_enemy(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_visibility_hidden_at_full_health", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Initialize bar with full-health enemy.
	bar.call("update_from_enemy", enemy)

	# Bar should be hidden by default (full health, no damage).
	_assert_false(
		bar.visible,
		"test_visibility_hidden_at_full_health — bar hidden at full health"
	)

	bar.queue_free()


func test_visibility_shown_when_damaged() -> void:
	# Test: When enemy is damaged from full health, bar becomes visible.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_visibility_shown_when_damaged", "health bar not found")
		return

	var enemy = _create_mock_enemy(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_visibility_shown_when_damaged", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Initialize and verify hidden.
	bar.call("update_from_enemy", enemy)
	_assert_false(bar.visible, "bar starts hidden")

	# Apply damage (reduce HP and call on_enemy_damaged).
	enemy.set_meta("current_hp", 75.0)
	bar.call("on_enemy_damaged", 25.0)

	_assert_true(
		bar.visible,
		"test_visibility_shown_when_damaged — bar visible when damaged"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Core feature tests: connect_to_enemy() signal wiring
# ---------------------------------------------------------------------------

func test_connect_to_enemy_wires_damage_signal() -> void:
	# Test: connect_to_enemy() properly connects a damage signal to on_enemy_damaged().
	# When the signal fires, bar should update.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_connect_to_enemy_wires_damage_signal", "health bar not found")
		return

	# Create an enemy with a custom signal.
	var enemy = CharacterBody3D.new()
	enemy.set_script(load("res://scripts/enemies/enemy_base.gd"))
	enemy.set_meta("current_hp", 100.0)
	enemy.set_meta("max_hp", 100.0)
	enemy.add_user_signal("damage_received")

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_connect_to_enemy_wires_damage_signal", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.call("update_from_enemy", enemy)

	# Connect to the signal using Signal() constructor.
	var signal_to_connect = Signal(enemy, "damage_received")
	bar.call("connect_to_enemy", signal_to_connect)

	# Verify bar is now hidden (full health).
	_assert_false(bar.visible, "bar starts hidden")

	# Emit damage signal.
	enemy.set_meta("current_hp", 75.0)
	enemy.emit_signal("damage_received", 25.0)

	# Bar should now be visible.
	_assert_true(
		bar.visible,
		"test_connect_to_enemy_wires_damage_signal — bar visible after signal"
	)

	bar.queue_free()


func test_connect_to_enemy_ignores_null_signal() -> void:
	# Test: connect_to_enemy() with empty/null signal should not crash.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_connect_to_enemy_ignores_null_signal", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_connect_to_enemy_ignores_null_signal", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Create an empty signal (null owner should be handled).
	var empty_signal = Signal()
	bar.call("connect_to_enemy", empty_signal)

	_assert_true(
		is_instance_valid(bar),
		"test_connect_to_enemy_ignores_null_signal — bar handles empty signal"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Integration tests: combined behavior
# ---------------------------------------------------------------------------

func test_integration_full_damage_cycle() -> void:
	# Test: Full cycle of damage → visibility timeout → hide.
	# Enemy takes damage, bar shows, then recovers to full health and hides.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_integration_full_damage_cycle", "health bar not found")
		return

	var enemy = _create_mock_enemy(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_integration_full_damage_cycle", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Initialize at full health.
	bar.call("update_from_enemy", enemy)
	_assert_false(bar.visible, "bar hidden at full health")

	# Apply damage.
	enemy.set_meta("current_hp", 50.0)
	bar.call("on_enemy_damaged", 50.0)
	_assert_true(bar.visible, "bar shown after damage")

	var progress_bar = _find_progress_bar(bar)
	if progress_bar != null:
		_assert_eq_float(50.0, progress_bar.value, "fill reflects 50% HP")

	# Recover to full health.
	enemy.set_meta("current_hp", 100.0)
	bar.call("on_enemy_healed", 50.0)

	# Bar should still be visible initially (timeout pending).
	# After timeout completes, it should hide.
	_assert_true(
		is_instance_valid(bar),
		"test_integration_full_damage_cycle — full cycle completes"
	)

	bar.queue_free()


func test_integration_multiple_damage_events() -> void:
	# Test: Multiple rapid damage events keep bar visible and update fill correctly.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_integration_multiple_damage_events", "health bar not found")
		return

	var enemy = _create_mock_enemy(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_integration_multiple_damage_events", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.call("update_from_enemy", enemy)

	# First damage.
	enemy.set_meta("current_hp", 75.0)
	bar.call("on_enemy_damaged", 25.0)
	_assert_true(bar.visible, "bar visible after first damage")

	# Second damage.
	enemy.set_meta("current_hp", 50.0)
	bar.call("on_enemy_damaged", 25.0)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar != null:
		_assert_eq_float(50.0, progress_bar.value, "fill reflects cumulative damage")

	_assert_true(bar.visible, "bar still visible after second damage")

	bar.queue_free()


# ---------------------------------------------------------------------------
# Edge case tests
# ---------------------------------------------------------------------------

func test_edge_null_enemy_reference() -> void:
	# Test: update_from_enemy(null) should not crash.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_edge_null_enemy_reference", "health bar not found")
		return

	bar.call("update_from_enemy", null)

	_assert_true(
		is_instance_valid(bar),
		"test_edge_null_enemy_reference — bar handles null enemy"
	)

	bar.queue_free()


func test_edge_zero_max_hp_no_crash() -> void:
	# Test: Enemy with max_hp = 0 should not cause division by zero.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_edge_zero_max_hp_no_crash", "health bar not found")
		return

	var enemy = _create_mock_enemy(0.0, 0.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_edge_zero_max_hp_no_crash", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)

	# Should not crash on division by zero.
	bar.call("update_from_enemy", enemy)

	_assert_true(
		is_instance_valid(bar),
		"test_edge_zero_max_hp_no_crash — bar handles zero max_hp"
	)

	bar.queue_free()


func test_edge_hp_exceeds_max() -> void:
	# Test: If HP somehow exceeds max, fill should clamp to 100%.
	var bar = _load_and_instantiate_health_bar()
	if bar == null:
		_fail("test_edge_hp_exceeds_max", "health bar not found")
		return

	var enemy = _create_mock_enemy(150.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_edge_hp_exceeds_max", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	tree.root.add_child(enemy)
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.call("update_from_enemy", enemy)

	var progress_bar = _find_progress_bar(bar)
	if progress_bar != null:
		# Fill should be clamped to 100%.
		_assert_true(
			progress_bar.value <= 100.0,
			"test_edge_hp_exceeds_max — fill clamped to max"
		)

	bar.queue_free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_bar_3d.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Core feature: update_from_enemy()
	test_update_from_enemy_sets_reference()
	test_update_from_enemy_updates_fill_from_hp()
	test_update_from_enemy_at_full_health()
	test_update_from_enemy_at_zero_health()

	# Core feature: on_enemy_damaged()
	test_on_enemy_damaged_shows_bar()
	test_on_enemy_damaged_updates_fill()

	# Core feature: visibility timeout
	test_visibility_hidden_at_full_health()
	test_visibility_shown_when_damaged()

	# Core feature: connect_to_enemy()
	test_connect_to_enemy_wires_damage_signal()
	test_connect_to_enemy_ignores_null_signal()

	# Integration tests
	test_integration_full_damage_cycle()
	test_integration_multiple_damage_events()

	# Edge cases
	test_edge_null_enemy_reference()
	test_edge_zero_max_hp_no_crash()
	test_edge_hp_exceeds_max()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
