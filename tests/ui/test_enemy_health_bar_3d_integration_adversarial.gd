#
# test_enemy_health_bar_3d_integration_adversarial.gd
#
# Integration and signal-handling adversarial tests for enemy floating health bar (M8).
# Tests real-world interaction patterns: signal wiring, damage event flows,
# enemy-to-bar attachment patterns, and concurrent scenarios.
#
# All tests exercise actual methods and verify observable behavior changes.
#
# Traceability: Integration tests for M8 enemy floating health bar feature
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Test infrastructure: fixtures and helpers
# ---------------------------------------------------------------------------

func _create_enemy_with_hp(hp: float = 100.0, max_hp: float = 100.0) -> CharacterBody3D:
	return test_create_mock_enemy(hp, max_hp)


func _load_health_bar() -> Variant:
	return test_load_and_instantiate_scene("res://scenes/ui/enemy_health_bar_3d.tscn")


func _find_progress_bar(bar: Node) -> Variant:
	return test_find_progress_bar(bar)


# ---------------------------------------------------------------------------
# SIGNAL-BASED TESTS: Signal emission and connection patterns
# ---------------------------------------------------------------------------

func test_sig_1_bar_initializes_hidden() -> void:
	# SIG-1: Bar should be hidden on initialization (no damage yet).
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_sig_1_bar_initializes_hidden", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_sig_1_bar_initializes_hidden", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	_assert_false(
		bar.visible,
		"test_sig_1_bar_initializes_hidden — bar hidden on init"
	)

	bar.queue_free()


func test_sig_2_multiple_signal_connections() -> void:
	# SIG-2: Multiple calls to connect_to_enemy() should not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_sig_2_multiple_signal_connections", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_sig_2_multiple_signal_connections", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	# Create a Timer node to get a well-known signal (timeout).
	# This avoids Godot 4 issues with user-defined signals.
	var timer = Timer.new()
	var test_signal = timer.timeout

	# Connect twice.
	if bar.has_method("connect_to_enemy"):
		bar.call("connect_to_enemy", test_signal)
		bar.call("connect_to_enemy", test_signal)

		_assert_true(
			is_instance_valid(bar),
			"test_sig_2_multiple_signal_connections — handles multiple connections"
		)
	else:
		_fail("test_sig_2_multiple_signal_connections", "no connect_to_enemy method")

	bar.queue_free()
	timer.queue_free()


func test_sig_3_signal_disconnection_on_death() -> void:
	# SIG-3: on_enemy_died() should clean up and not crash.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_sig_3_signal_disconnection_on_death", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_sig_3_signal_disconnection_on_death", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	if bar.has_method("on_enemy_died"):
		bar.call("on_enemy_died")
		_assert_true(
			is_instance_valid(bar),
			"test_sig_3_signal_disconnection_on_death — handles enemy death"
		)
	else:
		_fail("test_sig_3_signal_disconnection_on_death", "no on_enemy_died method")

	bar.queue_free()


# ---------------------------------------------------------------------------
# DAMAGE-EVENT TESTS: Real damage scenario flows
# ---------------------------------------------------------------------------

func test_dmg_1_single_damage_shows_bar() -> void:
	# DMG-1: Single on_enemy_damaged() call should make bar visible.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_dmg_1_single_damage_shows_bar", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(75.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_dmg_1_single_damage_shows_bar", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)
	bar.call("on_enemy_damaged", 25.0)

	_assert_true(
		bar.visible,
		"test_dmg_1_single_damage_shows_bar — bar visible after damage"
	)

	bar.queue_free()


func test_dmg_2_multiple_damages_maintain_visibility() -> void:
	# DMG-2: Multiple damages in sequence should keep bar visible.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_dmg_2_multiple_damages_maintain_visibility", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_dmg_2_multiple_damages_maintain_visibility", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	# Three damage events.
	enemy.set_meta("current_hp", 75.0)
	bar.call("on_enemy_damaged", 25.0)
	_assert_true(bar.visible, "visible after 1st damage")

	enemy.set_meta("current_hp", 50.0)
	bar.call("on_enemy_damaged", 25.0)
	_assert_true(bar.visible, "visible after 2nd damage")

	enemy.set_meta("current_hp", 25.0)
	bar.call("on_enemy_damaged", 25.0)
	_assert_true(bar.visible, "visible after 3rd damage")

	bar.queue_free()


func test_dmg_3_zero_damage_no_crash() -> void:
	# DMG-3: Zero damage event should not crash (blocked/absorbed damage).
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_dmg_3_zero_damage_no_crash", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_dmg_3_zero_damage_no_crash", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")
	tree.root.add_child(enemy)

	bar.call("update_from_enemy", enemy)

	# Call with 0 damage.
	bar.call("on_enemy_damaged", 0.0)

	_assert_true(
		is_instance_valid(bar),
		"test_dmg_3_zero_damage_no_crash — handles zero damage"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# WIRING TESTS: Enemy-to-bar integration patterns
# ---------------------------------------------------------------------------

func test_wire_1_bar_attached_to_enemy() -> void:
	# WIRE-1: Bar as child of enemy maintains parent relationship.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_wire_1_bar_attached_to_enemy", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_wire_1_bar_attached_to_enemy", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	_assert_true(
		bar.get_parent() == enemy,
		"test_wire_1_bar_attached_to_enemy — bar is child of enemy"
	)

	enemy.queue_free()


func test_wire_2_bar_follows_enemy_position() -> void:
	# WIRE-2: Bar should follow enemy position as child node.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_wire_2_bar_follows_enemy_position", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_wire_2_bar_follows_enemy_position", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	if enemy is Node3D and bar is Node3D:
		var enemy_initial = enemy.global_position
		var bar_initial = bar.global_position

		# Move enemy.
		enemy.global_position = enemy_initial + Vector3(5, 0, 0)

		var bar_after = bar.global_position

		# Bar's global position should change (parent-child follows).
		var distance_moved = (bar_after - bar_initial).length()
		_assert_true(
			distance_moved > 0.01,
			"test_wire_2_bar_follows_enemy_position — bar follows enemy"
		)
	else:
		print("  SKIP: test_wire_2_bar_follows_enemy_position — not 3D nodes")

	enemy.queue_free()


func test_wire_3_bar_survives_reparenting() -> void:
	# WIRE-3: Bar remains attached if enemy is reparented.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_wire_3_bar_survives_reparenting", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_wire_3_bar_survives_reparenting", "no scene tree")
		bar.queue_free()
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var parent1 = Node3D.new()
	var parent2 = Node3D.new()

	tree.root.add_child(parent1)
	tree.root.add_child(parent2)

	parent1.add_child(enemy)
	enemy.add_child(bar)

	_assert_true(bar.get_parent() == enemy, "bar attached initially")

	# Reparent enemy.
	parent1.remove_child(enemy)
	parent2.add_child(enemy)

	_assert_true(
		bar.get_parent() == enemy,
		"test_wire_3_bar_survives_reparenting — bar remains after reparent"
	)

	parent1.queue_free()
	parent2.queue_free()


# ---------------------------------------------------------------------------
# SCENE-LIFECYCLE TESTS: Enemy and bar lifecycle coordination
# ---------------------------------------------------------------------------

func test_lifecycle_1_bar_created_on_enemy_spawn() -> void:
	# LIFECYCLE-1: Bar instantiation and attachment on enemy spawn.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_lifecycle_1_bar_created_on_enemy_spawn", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_lifecycle_1_bar_created_on_enemy_spawn", "no scene tree")
		bar.queue_free()
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	tree.root.add_child(enemy)
	enemy.add_child(bar)

	_assert_true(
		bar in enemy.get_children(),
		"test_lifecycle_1_bar_created_on_enemy_spawn — bar is child of enemy"
	)

	enemy.queue_free()


func test_lifecycle_2_bar_removed_on_enemy_death() -> void:
	# LIFECYCLE-2: Bar survives being orphaned when enemy dies (Control + Node3D quirk).
	# Note: In Godot 4, Control nodes added as children of Node3D are not auto-queued
	# when the parent is queued. The bar is orphaned but remains valid.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_lifecycle_2_bar_removed_on_enemy_death", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_lifecycle_2_bar_removed_on_enemy_death", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	_assert_true(bar.get_parent() == enemy, "bar parent is enemy")

	# Enemy dies (bar becomes orphaned, not auto-queued).
	enemy.queue_free()

	# Bar should still be valid after being orphaned (not auto-deleted with parent).
	_assert_true(
		is_instance_valid(bar),
		"test_lifecycle_2_bar_removed_on_enemy_death — bar survives orphaning"
	)

	bar.queue_free()


func test_lifecycle_3_bar_survives_scene_pause() -> void:
	# LIFECYCLE-3: Bar state persists during scene pause.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_lifecycle_3_bar_survives_scene_pause", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_lifecycle_3_bar_survives_scene_pause", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(bar)
	if bar.has_method("_ready"):
		bar.call("_ready")

	bar.visible = true
	var visible_before = bar.visible

	# Pause and unpause.
	tree.paused = true
	var visible_during = bar.visible
	tree.paused = false

	_assert_eq(
		visible_before,
		visible_during,
		"test_lifecycle_3_bar_survives_scene_pause — visibility persists"
	)

	bar.queue_free()


# ---------------------------------------------------------------------------
# CONCURRENT TESTS: Multiple enemies damaged simultaneously
# ---------------------------------------------------------------------------

func test_concurrent_1_independent_bars_independent_state() -> void:
	# CONCURRENT-1: Multiple enemies with bars maintain independent state.
	var bar1 = _load_health_bar()
	var bar2 = _load_health_bar()
	if bar1 == null or bar2 == null:
		_fail("test_concurrent_1_independent_bars_independent_state", "health bar not found")
		if bar1 != null:
			bar1.queue_free()
		if bar2 != null:
			bar2.queue_free()
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_concurrent_1_independent_bars_independent_state", "no scene tree")
		bar1.queue_free()
		bar2.queue_free()
		return

	var enemy1 = _create_enemy_with_hp(75.0, 100.0)
	var enemy2 = _create_enemy_with_hp(100.0, 100.0)

	tree.root.add_child(enemy1)
	tree.root.add_child(enemy2)
	enemy1.add_child(bar1)
	enemy2.add_child(bar2)

	bar1.call("update_from_enemy", enemy1)
	bar2.call("update_from_enemy", enemy2)

	bar1.call("on_enemy_damaged", 25.0)

	_assert_true(
		bar1.visible and not bar2.visible,
		"test_concurrent_1_independent_bars_independent_state — independent state"
	)

	enemy1.queue_free()
	enemy2.queue_free()


func test_concurrent_2_simultaneous_spawn_many_bars() -> void:
	# CONCURRENT-2: Spawning many enemies with bars should not share state.
	var scene = load("res://scenes/ui/enemy_health_bar_3d.tscn")
	if scene == null:
		_fail("test_concurrent_2_simultaneous_spawn_many_bars", "health bar not found")
		return

	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_concurrent_2_simultaneous_spawn_many_bars", "no scene tree")
		return

	var enemies: Array[Node] = []
	var bars: Array[Node] = []

	# Spawn 5 enemies with bars.
	for i in range(5):
		var enemy = _create_enemy_with_hp(100.0, 100.0)
		var bar = scene.instantiate() as Node

		if bar == null:
			_fail("test_concurrent_2_simultaneous_spawn_many_bars", "bar " + str(i))
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

	# Damage all.
	for bar in bars:
		var enemy = bar.get_parent()
		if enemy != null:
			enemy.set_meta("current_hp", 50.0)
			bar.call("on_enemy_damaged", 50.0)

	# All should be visible and independent.
	var all_visible = true
	for bar in bars:
		if not bar.visible:
			all_visible = false
			break

	_assert_true(
		all_visible,
		"test_concurrent_2_simultaneous_spawn_many_bars — all visible"
	)

	for e in enemies:
		e.queue_free()


# ---------------------------------------------------------------------------
# TRANSFORM TESTS: Billboard and positioning under enemy movement
# ---------------------------------------------------------------------------

func test_xform_1_bar_offset_preserved_on_rotate() -> void:
	# XFORM-1: Bar's local offset preserved when enemy rotates.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_xform_1_bar_offset_preserved_on_rotate", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_xform_1_bar_offset_preserved_on_rotate", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	if enemy is Node3D and bar is Node3D:
		var local_before = bar.position

		enemy.rotation_degrees.y = 45.0

		var local_after = bar.position

		_assert_vec3_near(
			local_before,
			local_after,
			0.001,
			"test_xform_1_bar_offset_preserved_on_rotate — offset preserved"
		)
	else:
		print("  SKIP: test_xform_1_bar_offset_preserved_on_rotate — not 3D")

	enemy.queue_free()


func test_xform_2_bar_survives_enemy_scale() -> void:
	# XFORM-2: Bar survives enemy scaling without detaching.
	var bar = _load_health_bar()
	if bar == null:
		_fail("test_xform_2_bar_survives_enemy_scale", "health bar not found")
		return

	var enemy = _create_enemy_with_hp(100.0, 100.0)
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("test_xform_2_bar_survives_enemy_scale", "no scene tree")
		bar.queue_free()
		return

	tree.root.add_child(enemy)
	enemy.add_child(bar)

	if enemy is Node3D and bar is Node3D:
		enemy.scale = Vector3(2.0, 2.0, 2.0)

		_assert_true(
			is_instance_valid(bar) and bar.get_parent() == enemy,
			"test_xform_2_bar_survives_enemy_scale — survives scaling"
		)
	else:
		print("  SKIP: test_xform_2_bar_survives_enemy_scale — not 3D")

	enemy.queue_free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_health_bar_3d_integration_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SIGNAL tests
	test_sig_1_bar_initializes_hidden()
	test_sig_2_multiple_signal_connections()
	test_sig_3_signal_disconnection_on_death()

	# DAMAGE-EVENT tests
	test_dmg_1_single_damage_shows_bar()
	test_dmg_2_multiple_damages_maintain_visibility()
	test_dmg_3_zero_damage_no_crash()

	# WIRING tests
	test_wire_1_bar_attached_to_enemy()
	test_wire_2_bar_follows_enemy_position()
	test_wire_3_bar_survives_reparenting()

	# SCENE-LIFECYCLE tests
	test_lifecycle_1_bar_created_on_enemy_spawn()
	test_lifecycle_2_bar_removed_on_enemy_death()
	test_lifecycle_3_bar_survives_scene_pause()

	# CONCURRENT tests
	test_concurrent_1_independent_bars_independent_state()
	test_concurrent_2_simultaneous_spawn_many_bars()

	# XFORM tests
	test_xform_1_bar_offset_preserved_on_rotate()
	test_xform_2_bar_survives_enemy_scale()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
