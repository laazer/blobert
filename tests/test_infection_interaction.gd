#
# test_infection_interaction.gd
#
# Primary behavioral tests for the infection interaction loop (weakened → infected
# → absorb → mutation granted). Covers pure logic: absorb resolution, mutation
# granting, and no softlock/undefined state. Uses EnemyStateMachine (existing)
# and expects MutationInventory and InfectionAbsorbResolver modules (see
# agent_context/projects/blobert/CHECKPOINTS.md).
#
# Ticket: infection_interaction.md
# Spec: Derived from ticket ACs and execution plan Tasks 1–4. No standalone
#       infection_interaction_spec.md found; see CHECKPOINTS.md.
#
# Coverage:
#   AC: Weakened enemy can be infected (ESM covered in test_enemy_state_machine.gd).
#   AC: Infected state distinct; player can absorb to gain mutation.
#   AC: At least one mutation granted and usable after absorb.
#   AC: No softlock or undefined state when infecting/absorbing.
#   Task 3: Normal success path, invalid infection attempts, repeated infection,
#           absorb without infection, multiple enemies.
#   Task 4: Scene structure (test_infection_loop loads; Player, InfectionUI present).
#

class_name InfectionInteractionTests
extends Object


# Default mutation ID for "at least one mutation" (milestone minimum).
const DEFAULT_MUTATION_ID: String = "infection_mutation_01"

const ALLOWED_ESM_STATES: Array[String] = [
	"idle",
	"active",
	"weakened",
	"infected",
	"dead",
]

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


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _assert_eq_int(expected: int, actual: int, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))


func _make_esm() -> EnemyStateMachine:
	return EnemyStateMachine.new()


func _state_of(esm: EnemyStateMachine) -> String:
	return esm.get_state()


func _drive_to_weakened(esm: EnemyStateMachine) -> void:
	esm.apply_weaken_event()


func _drive_to_infected(esm: EnemyStateMachine) -> void:
	esm.apply_weaken_event()
	esm.apply_infection_event()


func _drive_to_dead(esm: EnemyStateMachine) -> void:
	esm.apply_death_event()


# Load MutationInventory script; returns null if not found. Caller must handle null.
func _load_mutation_inventory_script() -> GDScript:
	return load("res://scripts/mutation_inventory.gd") as GDScript


# Load InfectionAbsorbResolver script; returns null if not found.
func _load_absorb_resolver_script() -> GDScript:
	return load("res://scripts/infection_absorb_resolver.gd") as GDScript


# Returns [inventory_instance, resolver_instance] or [null, null] if scripts missing.
func _require_infection_modules() -> Array:
	var inv_script: GDScript = _load_mutation_inventory_script()
	var res_script: GDScript = _load_absorb_resolver_script()
	if inv_script == null or res_script == null:
		return [null, null]
	return [inv_script.new(), res_script.new()]


func _state_allowed(state: String) -> bool:
	return state in ALLOWED_ESM_STATES


func _load_enemy_infection_script() -> GDScript:
	return load("res://scripts/enemy_infection.gd") as GDScript


func _make_enemy_infection_instance() -> Object:
	var script: GDScript = _load_enemy_infection_script()
	if script == null:
		return null
	var instance: Object = script.new()
	# enemy_infection.gd extends Node2D; _ready() wires up its internal ESM.
	if instance.has_method("_ready"):
		instance._ready()
	return instance


# ---------------------------------------------------------------------------
# Module availability (fail fast with clear message)
# ---------------------------------------------------------------------------

func test_mutation_inventory_script_exists() -> void:
	var script: GDScript = _load_mutation_inventory_script()
	if script != null:
		_pass("ii_modules_mutation_inventory_script_exists — mutation_inventory.gd loads")
	else:
		_fail(
			"ii_modules_mutation_inventory_script_exists",
			"res://scripts/mutation_inventory.gd not found; implement MutationInventory (grant, has, get_granted_count) per ticket"
		)


func test_infection_absorb_resolver_script_exists() -> void:
	var script: GDScript = _load_absorb_resolver_script()
	if script != null:
		_pass("ii_modules_absorb_resolver_script_exists — infection_absorb_resolver.gd loads")
	else:
		_fail(
			"ii_modules_absorb_resolver_script_exists",
			"res://scripts/infection_absorb_resolver.gd not found; implement InfectionAbsorbResolver (can_absorb, resolve_absorb) per ticket"
		)


# ---------------------------------------------------------------------------
# MutationInventory API (grant, has, get_granted_count)
# ---------------------------------------------------------------------------

func test_mutation_inventory_initial_count_zero() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	if inv == null:
		_fail("ii_inv_initial_zero", "MutationInventory script missing; skipping")
		return
	var count: int = inv.get_granted_count()
	_assert_eq_int(0, count, "ii_inv_initial_zero — get_granted_count() is 0 when no grants")
	if inv != null and inv.has(DEFAULT_MUTATION_ID):
		_fail("ii_inv_initial_no_has", "has() must be false for any id when no grants")
	else:
		_pass("ii_inv_initial_no_has — has() false for default mutation when no grants")


func test_mutation_inventory_grant_and_has() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	if inv == null:
		_fail("ii_inv_grant_has", "MutationInventory script missing; skipping")
		return
	inv.grant(DEFAULT_MUTATION_ID)
	_assert_true(inv.has(DEFAULT_MUTATION_ID), "ii_inv_grant_has — has(id) true after grant(id)")
	_assert_eq_int(1, inv.get_granted_count(), "ii_inv_grant_count_one — get_granted_count() is 1 after one grant")
	inv.grant("other_id")
	_assert_true(inv.has("other_id"), "ii_inv_grant_other_has — has(other_id) true after second grant")
	_assert_eq_int(2, inv.get_granted_count(), "ii_inv_grant_count_two — get_granted_count() is 2 after two grants")
	# Idempotent grant of same ID: spec says "one mutation per valid absorb"; we allow same id twice to be count 2 or 1 per design; test only that state remains valid
	_assert_true(inv.has(DEFAULT_MUTATION_ID), "ii_inv_still_has_first — has(default) still true after second grant")


# ---------------------------------------------------------------------------
# InfectionAbsorbResolver: can_absorb(esm) true only when state == infected
# ---------------------------------------------------------------------------

func test_can_absorb_true_only_when_infected() -> void:
	var arr: Array = _require_infection_modules()
	var resolver = arr[1]
	if resolver == null:
		_fail("ii_can_absorb_resolver", "InfectionAbsorbResolver script missing; skipping")
		return
	var esm: EnemyStateMachine = _make_esm()
	_assert_false(resolver.can_absorb(esm), "ii_can_absorb_idle_false — can_absorb false when idle")
	_drive_to_weakened(esm)
	_assert_false(resolver.can_absorb(esm), "ii_can_absorb_weakened_false — can_absorb false when weakened")
	esm.apply_infection_event()
	_assert_true(resolver.can_absorb(esm), "ii_can_absorb_infected_true — can_absorb true when infected")
	esm.apply_death_event()
	_assert_false(resolver.can_absorb(esm), "ii_can_absorb_dead_false — can_absorb false when dead")


# ---------------------------------------------------------------------------
# resolve_absorb: on infected → ESM dead, one mutation granted; on non-infected no-op
# ---------------------------------------------------------------------------

func test_resolve_absorb_on_infected_transitions_esm_to_dead_and_grants_one_mutation() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	var resolver = arr[1]
	if inv == null or resolver == null:
		_fail("ii_resolve_infected", "scripts missing; skipping")
		return
	var esm: EnemyStateMachine = _make_esm()
	_drive_to_infected(esm)
	_assert_eq_string("infected", _state_of(esm), "ii_resolve_pre_infected — precondition: ESM infected")
	var count_before: int = inv.get_granted_count()
	resolver.resolve_absorb(esm, inv)
	_assert_eq_string("dead", _state_of(esm), "ii_resolve_esm_dead — resolve_absorb(infected) transitions ESM to dead")
	_assert_eq_int(count_before + 1, inv.get_granted_count(), "ii_resolve_grants_one — resolve_absorb grants exactly one mutation")
	_assert_true(inv.has(DEFAULT_MUTATION_ID), "ii_resolve_grants_known_id — granted mutation is the default milestone mutation (usable)")


func test_resolve_absorb_on_non_infected_is_noop() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	var resolver = arr[1]
	if inv == null or resolver == null:
		_fail("ii_resolve_noop", "scripts missing; skipping")
		return
	# Idle
	var esm_idle: EnemyStateMachine = _make_esm()
	resolver.resolve_absorb(esm_idle, inv)
	_assert_eq_string("idle", _state_of(esm_idle), "ii_resolve_noop_idle — resolve_absorb on idle leaves state idle")
	_assert_eq_int(0, inv.get_granted_count(), "ii_resolve_noop_idle_count — no mutation granted on idle absorb")
	# Weakened
	var esm_weak: EnemyStateMachine = _make_esm()
	_drive_to_weakened(esm_weak)
	resolver.resolve_absorb(esm_weak, inv)
	_assert_eq_string("weakened", _state_of(esm_weak), "ii_resolve_noop_weakened — resolve_absorb on weakened leaves state weakened")
	_assert_eq_int(0, inv.get_granted_count(), "ii_resolve_noop_weakened_count — no mutation granted on weakened absorb")
	# Dead
	var esm_dead: EnemyStateMachine = _make_esm()
	_drive_to_dead(esm_dead)
	resolver.resolve_absorb(esm_dead, inv)
	_assert_eq_string("dead", _state_of(esm_dead), "ii_resolve_noop_dead — resolve_absorb on dead leaves state dead")
	_assert_eq_int(0, inv.get_granted_count(), "ii_resolve_noop_dead_count — no mutation granted on dead absorb")
	# Absorb on already-dead (from previous infected absorb) leaves inventory unchanged
	var esm2: EnemyStateMachine = _make_esm()
	_drive_to_infected(esm2)
	resolver.resolve_absorb(esm2, inv)
	var count_after_one: int = inv.get_granted_count()
	resolver.resolve_absorb(esm2, inv)  # same ESM, now dead
	_assert_eq_int(count_after_one, inv.get_granted_count(), "ii_resolve_noop_double_absorb — second absorb on same (dead) ESM does not grant again")
	_assert_eq_string("dead", _state_of(esm2), "ii_resolve_noop_double_absorb_state — state remains dead")


# ---------------------------------------------------------------------------
# Full loop: weaken → infect → absorb → mutation granted (no softlock)
# ---------------------------------------------------------------------------

func test_full_loop_weaken_infect_absorb_grants_one_mutation_esm_dead() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	var resolver = arr[1]
	if inv == null or resolver == null:
		_fail("ii_full_loop", "scripts missing; skipping")
		return
	var esm: EnemyStateMachine = _make_esm()
	_drive_to_weakened(esm)
	_assert_eq_string("weakened", _state_of(esm), "ii_full_loop_weakened")
	esm.apply_infection_event()
	_assert_eq_string("infected", _state_of(esm), "ii_full_loop_infected")
	_assert_true(resolver.can_absorb(esm), "ii_full_loop_can_absorb")
	resolver.resolve_absorb(esm, inv)
	_assert_eq_string("dead", _state_of(esm), "ii_full_loop_esm_dead_after_absorb")
	_assert_eq_int(1, inv.get_granted_count(), "ii_full_loop_one_mutation_granted")
	_assert_true(inv.has(DEFAULT_MUTATION_ID), "ii_full_loop_mutation_usable — at least one mutation granted and identifiable (usable)")
	_assert_true(_state_allowed(_state_of(esm)), "ii_full_loop_state_allowed — ESM state remains in allowed set (no undefined state)")


func test_repeated_infection_on_same_esm_idempotent_then_absorb_once() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	var resolver = arr[1]
	if inv == null or resolver == null:
		_fail("ii_repeated_infect", "scripts missing; skipping")
		return
	var esm: EnemyStateMachine = _make_esm()
	_drive_to_infected(esm)
	esm.apply_infection_event()
	esm.apply_infection_event()
	_assert_eq_string("infected", _state_of(esm), "ii_repeated_infect_still_infected — repeated infection event leaves state infected")
	resolver.resolve_absorb(esm, inv)
	_assert_eq_int(1, inv.get_granted_count(), "ii_repeated_infect_one_absorb_one_grant — one absorb grants one mutation")
	_assert_eq_string("dead", _state_of(esm), "ii_repeated_infect_dead — ESM dead after absorb")
	_assert_true(_state_allowed(_state_of(esm)), "ii_repeated_infect_state_allowed — no undefined state")
	resolver.resolve_absorb(esm, inv)
	_assert_eq_int(1, inv.get_granted_count(), "ii_repeated_infect_absorb_again_no_extra_grant — absorb on dead does not grant again")


# ---------------------------------------------------------------------------
# Multiple enemies: absorb one infected → one mutation; other ESM unchanged
# ---------------------------------------------------------------------------

func test_multiple_enemies_absorb_one_grants_one_other_unchanged() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	var resolver = arr[1]
	if inv == null or resolver == null:
		_fail("ii_multi_enemy", "scripts missing; skipping")
		return
	var esm_a: EnemyStateMachine = _make_esm()
	var esm_b: EnemyStateMachine = _make_esm()
	_drive_to_infected(esm_a)
	_drive_to_weakened(esm_b)
	resolver.resolve_absorb(esm_a, inv)
	_assert_eq_string("dead", _state_of(esm_a), "ii_multi_a_dead — absorbed ESM is dead")
	_assert_eq_string("weakened", _state_of(esm_b), "ii_multi_b_unchanged — other ESM still weakened (unchanged)")
	_assert_eq_int(1, inv.get_granted_count(), "ii_multi_one_grant — one mutation granted for one absorb")
	# Absorb B (weakened) is no-op
	resolver.resolve_absorb(esm_b, inv)
	_assert_eq_string("weakened", _state_of(esm_b), "ii_multi_b_still_weakened — absorb on weakened does not change state")
	_assert_eq_int(1, inv.get_granted_count(), "ii_multi_still_one_grant — no extra mutation")
	# Infect B and absorb
	esm_b.apply_infection_event()
	resolver.resolve_absorb(esm_b, inv)
	_assert_eq_string("dead", _state_of(esm_b), "ii_multi_b_dead_after_infect_absorb")
	_assert_eq_int(2, inv.get_granted_count(), "ii_multi_two_grants — second valid absorb grants second mutation")
	_assert_true(_state_allowed(_state_of(esm_a)) and _state_allowed(_state_of(esm_b)), "ii_multi_both_allowed — both ESMs in allowed set (no softlock)")


# ---------------------------------------------------------------------------
# No undefined state: mixed sequence leaves ESM state in allowed set
# ---------------------------------------------------------------------------

func test_absorb_resolution_never_produces_undefined_state() -> void:
	var arr: Array = _require_infection_modules()
	var inv = arr[0]
	var resolver = arr[1]
	if inv == null or resolver == null:
		_fail("ii_no_undefined", "scripts missing; skipping")
		return
	var esm: EnemyStateMachine = _make_esm()
	# Absorb on idle, weakened, infected, dead
	for _i in range(2):
		resolver.resolve_absorb(esm, inv)
		_assert_true(_state_allowed(_state_of(esm)), "ii_no_undefined_idle_absorb — state allowed after absorb on idle")
	esm.apply_weaken_event()
	for _j in range(2):
		resolver.resolve_absorb(esm, inv)
		_assert_true(_state_allowed(_state_of(esm)), "ii_no_undefined_weakened_absorb — state allowed after absorb on weakened")
	esm.apply_infection_event()
	resolver.resolve_absorb(esm, inv)
	_assert_true(_state_allowed(_state_of(esm)), "ii_no_undefined_infected_absorb — state allowed after absorb on infected")
	resolver.resolve_absorb(esm, inv)
	resolver.resolve_absorb(esm, inv)
	_assert_true(_state_allowed(_state_of(esm)), "ii_no_undefined_dead_absorb — state allowed after repeated absorb on dead")


# ---------------------------------------------------------------------------
# Scene structure: test_infection_loop loads; Player and InfectionUI present
# ---------------------------------------------------------------------------

func test_infection_loop_scene_loads() -> void:
	var packed: PackedScene = load("res://scenes/test_infection_loop.tscn") as PackedScene
	if packed == null:
		_fail("ii_scene_loads", "could not load res://scenes/test_infection_loop.tscn")
		return
	var root: Node = packed.instantiate()
	if root == null:
		_fail("ii_scene_instantiate", "instantiate() returned null for test_infection_loop.tscn")
		return
	_pass("ii_scene_loads — test_infection_loop.tscn loads and instantiates headless")
	root.free()


func test_infection_loop_scene_has_player_and_infection_ui() -> void:
	var packed: PackedScene = load("res://scenes/test_infection_loop.tscn") as PackedScene
	if packed == null:
		_fail("ii_scene_structure", "scene not loaded; skipping")
		return
	var root: Node = packed.instantiate()
	if root == null:
		_fail("ii_scene_structure", "instantiate failed; skipping")
		return
	var player: Node = root.get_node_or_null("Player")
	var infection_ui: Node = root.get_node_or_null("InfectionUI")
	_assert_true(player != null, "ii_scene_has_player — scene has Player node")
	_assert_true(infection_ui != null, "ii_scene_has_infection_ui — scene has InfectionUI node")
	root.free()


# ---------------------------------------------------------------------------
# Engine wiring: chunk-contact infection trigger (EnemyInfection)
# ---------------------------------------------------------------------------

func test_enemy_infection_chunk_contact_from_idle_results_in_infected_state() -> void:
	var enemy_obj: Object = _make_enemy_infection_instance()
	if enemy_obj == null:
		_fail("ii_enemy_infection_chunk_idle", "enemy_infection.gd could not be loaded/instantiated")
		return

	if not enemy_obj.has_method("get_esm") or not enemy_obj.has_method("_on_body_entered"):
		_fail("ii_enemy_infection_chunk_idle", "EnemyInfection instance missing get_esm/_on_body_entered API")
		return

	var esm: EnemyStateMachine = enemy_obj.get_esm()
	_assert_eq_string("idle", _state_of(esm), "ii_enemy_infection_chunk_idle_pre_idle — ESM starts in idle")

	var chunk: Node2D = Node2D.new()
	chunk.add_to_group("chunk")

	enemy_obj._on_body_entered(chunk)

	var state_after: String = _state_of(esm)
	_assert_eq_string("infected", state_after, "ii_enemy_infection_chunk_idle_infected — chunk contact drives idle → weakened → infected")
	_assert_true(_state_allowed(state_after), "ii_enemy_infection_chunk_idle_state_allowed — resulting state in allowed set")


func test_enemy_infection_chunk_contact_when_already_infected_is_idempotent() -> void:
	var enemy_obj: Object = _make_enemy_infection_instance()
	if enemy_obj == null:
		_fail("ii_enemy_infection_chunk_infected", "enemy_infection.gd could not be loaded/instantiated")
		return

	if not enemy_obj.has_method("get_esm") or not enemy_obj.has_method("_on_body_entered"):
		_fail("ii_enemy_infection_chunk_infected", "EnemyInfection instance missing get_esm/_on_body_entered API")
		return

	var esm: EnemyStateMachine = enemy_obj.get_esm()
	# First contact: drive to infected.
	var chunk: Node2D = Node2D.new()
	chunk.add_to_group("chunk")
	enemy_obj._on_body_entered(chunk)
	_assert_eq_string("infected", _state_of(esm), "ii_enemy_infection_chunk_infected_pre_infected — precondition infected")

	# Second contact: must leave state at infected (no undefined / no softlock).
	enemy_obj._on_body_entered(chunk)
	var state_after: String = _state_of(esm)
	_assert_eq_string("infected", state_after, "ii_enemy_infection_chunk_infected_idempotent — repeated chunk contact leaves state infected")
	_assert_true(_state_allowed(state_after), "ii_enemy_infection_chunk_infected_state_allowed — state remains within allowed set")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_infection_interaction.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Module availability
	test_mutation_inventory_script_exists()
	test_infection_absorb_resolver_script_exists()

	# MutationInventory API
	test_mutation_inventory_initial_count_zero()
	test_mutation_inventory_grant_and_has()

	# can_absorb
	test_can_absorb_true_only_when_infected()

	# resolve_absorb
	test_resolve_absorb_on_infected_transitions_esm_to_dead_and_grants_one_mutation()
	test_resolve_absorb_on_non_infected_is_noop()

	# Full loop and edge cases
	test_full_loop_weaken_infect_absorb_grants_one_mutation_esm_dead()
	test_repeated_infection_on_same_esm_idempotent_then_absorb_once()
	test_multiple_enemies_absorb_one_grants_one_other_unchanged()
	test_absorb_resolution_never_produces_undefined_state()

	# Scene structure (Task 4 subset)
	test_infection_loop_scene_loads()
	test_infection_loop_scene_has_player_and_infection_ui()
	# Engine wiring: chunk-contact infection trigger (R1, R4)
	test_enemy_infection_chunk_contact_from_idle_results_in_infected_state()
	test_enemy_infection_chunk_contact_when_already_infected_is_idempotent()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
