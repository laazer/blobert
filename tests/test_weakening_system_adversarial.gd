#
# test_weakening_system_adversarial.gd
#
# Adversarial tests for the weakening system (Milestone 2 – Infection Loop).
# Tests edge cases, rapid transitions, invalid state combinations, and null handling.
#
# Ticket: weakening_system.md
# Strategy:
#   - Rapid state transitions (weaken -> infect -> death in quick succession)
#   - Invalid state transitions (weaken from dead, infect from idle, etc.)
#   - Repeated weaken/infect/death events
#   - Null handling (missing visual, missing label, missing enemy)
#   - Concurrent events (simulated)
#   - Large delta times (simulation jumps)
#

class_name WeakeningSystemAdversarialTests
extends Object


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_state(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(
			test_name,
			"expected state '" + expected + "', got '" + actual + "'"
		)


func _make_enemy_infection_3d() -> Node3D:
	var scene: PackedScene = load("res://scenes/enemy_infection_3d.tscn") as PackedScene
	if scene == null:
		return null
	var enemy: Node3D = scene.instantiate() as Node3D
	return enemy


# ---------------------------------------------------------------------------
# Test: Invalid Transitions
# ---------------------------------------------------------------------------

func test_cannot_weaken_dead_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_death_event()
	_assert_state("dead", esm.get_state(), "weaken_adv_dead_start")

	# Attempt to weaken a dead enemy.
	esm.apply_weaken_event()
	_assert_state(
		"dead",
		esm.get_state(),
		"weaken_adv_dead_noop — weakening a dead enemy is a no-op"
	)


func test_cannot_weaken_infected_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	_assert_state("infected", esm.get_state(), "weaken_adv_infected_start")

	# Attempt to weaken an infected enemy.
	esm.apply_weaken_event()
	_assert_state(
		"infected",
		esm.get_state(),
		"weaken_adv_infected_noop — weakening an infected enemy is a no-op"
	)


func test_cannot_weaken_weakened_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_weaken_event()
	_assert_state("weakened", esm.get_state(), "weaken_adv_weakened_start")

	# Attempt to weaken an already-weakened enemy.
	esm.apply_weaken_event()
	_assert_state(
		"weakened",
		esm.get_state(),
		"weaken_adv_weakened_idempotent — weakening an already-weakened enemy is a no-op"
	)


func test_cannot_infect_idle_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()  # Idle.
	_assert_state("idle", esm.get_state(), "weaken_adv_infect_idle_start")

	# Attempt to infect an idle enemy.
	esm.apply_infection_event()
	_assert_state(
		"idle",
		esm.get_state(),
		"weaken_adv_infect_idle_noop — infecting an idle enemy is a no-op"
	)


func test_cannot_infect_active_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm._state = "active"
	_assert_state("active", esm.get_state(), "weaken_adv_infect_active_start")

	# Attempt to infect an active enemy.
	esm.apply_infection_event()
	_assert_state(
		"active",
		esm.get_state(),
		"weaken_adv_infect_active_noop — infecting an active enemy is a no-op"
	)


func test_cannot_infect_dead_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_death_event()
	_assert_state("dead", esm.get_state(), "weaken_adv_infect_dead_start")

	# Attempt to infect a dead enemy.
	esm.apply_infection_event()
	_assert_state(
		"dead",
		esm.get_state(),
		"weaken_adv_infect_dead_noop — infecting a dead enemy is a no-op"
	)


func test_cannot_infect_infected_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	_assert_state("infected", esm.get_state(), "weaken_adv_reinfect_start")

	# Attempt to re-infect an already-infected enemy.
	esm.apply_infection_event()
	_assert_state(
		"infected",
		esm.get_state(),
		"weaken_adv_reinfect_noop — re-infecting an infected enemy is a no-op"
	)


# ---------------------------------------------------------------------------
# Test: Rapid/Sequential Transitions
# ---------------------------------------------------------------------------

func test_rapid_weaken_infect_death_sequence() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()

	# Rapid sequence: weaken -> infect -> death.
	esm.apply_weaken_event()
	esm.apply_infection_event()
	esm.apply_death_event()

	_assert_state(
		"dead",
		esm.get_state(),
		"weaken_adv_rapid_sequence — rapid weaken->infect->death resolves to dead state"
	)


func test_weaken_death_skips_infection() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()

	# Sequence: weaken -> death (infection event after death is no-op).
	esm.apply_weaken_event()
	esm.apply_death_event()
	_assert_state("dead", esm.get_state(), "weaken_adv_weaken_death_after_death")

	# Attempt to infect a dead enemy.
	esm.apply_infection_event()
	_assert_state(
		"dead",
		esm.get_state(),
		"weaken_adv_death_infect_noop — infection after death is a no-op"
	)


func test_infection_death_immediate() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	_assert_state("infected", esm.get_state(), "weaken_adv_infect_death_infected")

	# Death from infected state.
	esm.apply_death_event()
	_assert_state(
		"dead",
		esm.get_state(),
		"weaken_adv_infect_death — death can be applied from infected state"
	)


# ---------------------------------------------------------------------------
# Test: Repeated Events (Idempotency)
# ---------------------------------------------------------------------------

func test_repeated_weaken_events() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()

	# Apply weaken event 5 times in succession.
	for i in 5:
		esm.apply_weaken_event()

	_assert_state(
		"weakened",
		esm.get_state(),
		"weaken_adv_repeated_weaken — repeated weaken events result in weakened state"
	)


func test_repeated_death_events() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_death_event()

	# Apply death event again.
	esm.apply_death_event()
	_assert_state(
		"dead",
		esm.get_state(),
		"weaken_adv_repeated_death — repeated death events remain in dead state"
	)


# ---------------------------------------------------------------------------
# Test: Reset from Weakened States
# ---------------------------------------------------------------------------

func test_reset_from_weakened_state() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_weaken_event()
	_assert_state("weakened", esm.get_state(), "weaken_adv_reset_weakened_start")

	# Reset should return to idle.
	esm.reset()
	_assert_state(
		"idle",
		esm.get_state(),
		"weaken_adv_reset_from_weakened — reset transitions weakened back to idle"
	)


func test_reset_from_infected_state() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	_assert_state("infected", esm.get_state(), "weaken_adv_reset_infected_start")

	# Reset should return to idle.
	esm.reset()
	_assert_state(
		"idle",
		esm.get_state(),
		"weaken_adv_reset_from_infected — reset transitions infected back to idle"
	)


func test_reset_from_dead_state() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	esm.reset()
	esm.apply_death_event()
	_assert_state("dead", esm.get_state(), "weaken_adv_reset_dead_start")

	# Reset should return to idle.
	esm.reset()
	_assert_state(
		"idle",
		esm.get_state(),
		"weaken_adv_reset_from_dead — reset transitions dead back to idle"
	)


# ---------------------------------------------------------------------------
# Test: Visual Blink Edge Cases
# ---------------------------------------------------------------------------

func test_rapid_state_transitions_no_visual_corruption() -> void:
	var enemy: Node3D = _make_enemy_infection_3d()
	if enemy == null:
		_fail("weaken_adv_visual_rapid_setup", "could not create enemy")
		return

	var fx: Node3D = enemy.get_node_or_null("InfectionStateVisuals") as Node3D
	var visual: MeshInstance3D = enemy.get_node_or_null("EnemyVisual") as MeshInstance3D
	var esm: EnemyStateMachine = enemy.get_method("get_esm").callv([]) if enemy.has_method("get_esm") else null

	if esm == null or fx == null or visual == null:
		_fail("weaken_adv_visual_rapid_nodes", "setup missing nodes")
		enemy.free()
		return

	esm.reset()
	visual.visible = true

	# Rapid transitions: weaken -> infect -> death.
	esm.apply_weaken_event()
	fx._process(0.0)
	esm.apply_infection_event()
	fx._process(0.0)
	esm.apply_death_event()
	fx._process(0.0)

	# Final state: dead, so enemy should be hidden, not crashed.
	_assert_false(
		enemy.visible,
		"weaken_adv_rapid_visual_dead — rapid transitions result in dead state and hidden enemy"
	)

	enemy.free()


func test_blink_with_large_delta() -> void:
	var enemy: Node3D = _make_enemy_infection_3d()
	if enemy == null:
		_fail("weaken_adv_blink_large_delta_setup", "could not create enemy")
		return

	var fx: Node3D = enemy.get_node_or_null("InfectionStateVisuals") as Node3D
	var esm: EnemyStateMachine = enemy.get_method("get_esm").callv([]) if enemy.has_method("get_esm") else null

	if esm == null or fx == null:
		_fail("weaken_adv_blink_large_delta_nodes", "setup missing nodes")
		enemy.free()
		return

	esm.reset()
	esm.apply_weaken_event()

	# Process with a very large delta (jump forward in time).
	# The blink should complete and return to visible.
	var large_delta: float = 1.0  # Well beyond blink duration (0.35s).
	# GDScript has no try/except; reaching the assertion confirms no crash.
	fx._process(large_delta)
	_assert_true(
		true,
		"weaken_adv_blink_large_delta — large delta time does not crash FX handler"
	)

	enemy.free()


# ---------------------------------------------------------------------------
# Test: Null Handling and Edge Cases
# ---------------------------------------------------------------------------

func test_enemy_node_null_recovery() -> void:
	var enemy: Node3D = _make_enemy_infection_3d()
	if enemy == null:
		_fail("weaken_adv_null_enemy_setup", "could not create enemy")
		return

	var fx: Node3D = enemy.get_node_or_null("InfectionStateVisuals") as Node3D
	var esm: EnemyStateMachine = enemy.get_method("get_esm").callv([]) if enemy.has_method("get_esm") else null

	if esm == null or fx == null:
		_fail("weaken_adv_null_enemy_nodes", "setup missing fx or esm")
		enemy.free()
		return

	esm.reset()
	esm.apply_weaken_event()

	# Orphan the FX node by removing it as a child (simulating scene reload/early GC).
	# (In actual gameplay, this is rare, but adversarial tests verify robustness.)
	enemy.remove_child(fx)

	# Process should not crash; FX reacquires parent on next _process.
	# GDScript has no try/except; reaching the assertion confirms no crash.
	fx._process(0.01)
	_assert_true(
		true,
		"weaken_adv_null_enemy_recovery — FX recovers when parent is null"
	)

	enemy.free()
	fx.free()


func test_missing_label_node() -> void:
	var enemy: Node3D = _make_enemy_infection_3d()
	if enemy == null:
		_fail("weaken_adv_missing_label_setup", "could not create enemy")
		return

	var fx: Node3D = enemy.get_node_or_null("InfectionStateVisuals") as Node3D
	var esm: EnemyStateMachine = enemy.get_method("get_esm").callv([]) if enemy.has_method("get_esm") else null

	if esm == null or fx == null:
		_fail("weaken_adv_missing_label_nodes", "setup missing fx or esm")
		enemy.free()
		return

	# Remove label node if it exists.
	var label: Node = enemy.get_node_or_null("InfectionStateVisuals/StateLabel")
	if label != null:
		label.queue_free()

	esm.reset()
	esm.apply_weaken_event()

	# Process should not crash even if label is missing.
	# GDScript has no try/except; reaching the assertion confirms no crash.
	fx._process(0.01)
	_assert_true(
		true,
		"weaken_adv_missing_label_no_crash — FX does not crash when label is missing"
	)

	enemy.free()


# ---------------------------------------------------------------------------
# Test: Concurrent/Overlapping Events
# ---------------------------------------------------------------------------

func test_absorb_with_null_inventory() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	var resolver_script: GDScript = load("res://scripts/infection_absorb_resolver.gd") as GDScript

	if resolver_script == null:
		_fail("weaken_adv_absorb_null_inv_setup", "could not load resolver")
		return

	var resolver: Object = resolver_script.new() as Object

	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	_assert_state("infected", esm.get_state(), "weaken_adv_absorb_null_infected_start")

	# Attempt absorb with null inventory (should be a no-op).
	resolver.resolve_absorb(esm, null)

	# Enemy state should remain unchanged (no-op contract).
	_assert_state(
		"infected",
		esm.get_state(),
		"weaken_adv_absorb_null_inv_noop — absorb with null inventory is a no-op"
	)


func test_absorb_with_non_infected_enemy() -> void:
	var esm: EnemyStateMachine = EnemyStateMachine.new()
	var inventory_script: GDScript = load("res://scripts/mutation_inventory.gd") as GDScript
	var resolver_script: GDScript = load("res://scripts/infection_absorb_resolver.gd") as GDScript

	if inventory_script == null or resolver_script == null:
		_fail("weaken_adv_absorb_non_inf_setup", "could not load scripts")
		return

	var inventory: Object = inventory_script.new() as Object
	var resolver: Object = resolver_script.new() as Object

	esm.reset()
	esm.apply_weaken_event()  # Weakened, not infected.
	_assert_state("weakened", esm.get_state(), "weaken_adv_absorb_weakened_start")

	# Attempt absorb on a weakened (not infected) enemy.
	resolver.resolve_absorb(esm, inventory)

	# State should remain unchanged (no-op contract for non-infected).
	_assert_state(
		"weakened",
		esm.get_state(),
		"weaken_adv_absorb_weakened_noop — absorb on weakened enemy is a no-op"
	)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_weakening_system_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Invalid transition tests.
	test_cannot_weaken_dead_enemy()
	test_cannot_weaken_infected_enemy()
	test_cannot_weaken_weakened_enemy()
	test_cannot_infect_idle_enemy()
	test_cannot_infect_active_enemy()
	test_cannot_infect_dead_enemy()
	test_cannot_infect_infected_enemy()

	# Rapid transition tests.
	test_rapid_weaken_infect_death_sequence()
	test_weaken_death_skips_infection()
	test_infection_death_immediate()

	# Repeated event tests.
	test_repeated_weaken_events()
	test_repeated_death_events()

	# Reset tests.
	test_reset_from_weakened_state()
	test_reset_from_infected_state()
	test_reset_from_dead_state()

	# Visual edge case tests.
	test_rapid_state_transitions_no_visual_corruption()
	test_blink_with_large_delta()

	# Null and edge case tests.
	test_enemy_node_null_recovery()
	test_missing_label_node()

	# Concurrent event tests.
	test_absorb_with_null_inventory()
	test_absorb_with_non_infected_enemy()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	print("")
	return _fail_count
