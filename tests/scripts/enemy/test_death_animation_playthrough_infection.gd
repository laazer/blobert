#
# test_death_animation_playthrough_infection.gd
#
# Death sequence interaction with infection/chunk paths and InfectionInteractionHandler.
#
# Spec: project_board/specs/death_animation_playthrough_spec.md
# Traceability: DAP-1.3, DAP-1.4, DAP-1.5, DAP-1.6, DAP-1.7, DAP-NF2
#

extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


# Same pattern as test_soft_death_and_restart.gd _make_iih_ready() — no SceneTree parent
# so _inventory exists before _process (avoids deferred _ready before first frame).
func _new_handler_ready() -> Node:
	var handler_script: GDScript = load("res://scripts/infection/infection_interaction_handler.gd") as GDScript
	if handler_script == null:
		return null
	var handler: Node = handler_script.new() as Node
	if handler == null:
		return null
	handler._ready()
	return handler


# DAP-1.3 — no chunk_attached while enemy ESM is dead (full window until free).
func test_dap_13_no_chunk_attached_when_dead() -> void:
	const NAME := "DAP-1.3 — dead enemy does not emit chunk_attached for new chunk contact"
	var packed: PackedScene = load("res://scenes/enemy/enemy_infection_3d.tscn") as PackedScene
	if packed == null:
		_fail(NAME, "could not load enemy_infection_3d.tscn")
		return
	var enemy: EnemyInfection3D = packed.instantiate() as EnemyInfection3D
	if enemy == null:
		_fail(NAME, "instantiate failed")
		return
	var st: SceneTree = Engine.get_main_loop() as SceneTree
	if st == null or st.root == null:
		enemy.free()
		_fail(NAME, "no SceneTree root")
		return
	var emissions: Array[RigidBody3D] = []
	enemy.chunk_attached.connect(func(c: RigidBody3D) -> void:
		emissions.append(c)
	)
	st.root.add_child(enemy)
	var esm: EnemyStateMachine = enemy.get_esm()
	esm.apply_death_event()
	var fx: Node = enemy.get_node_or_null("InfectionStateFx3D")
	if fx != null and fx.has_method("_process"):
		fx._process(0.0)
	var chunk := RigidBody3D.new()
	chunk.add_to_group("chunk")
	var area: Area3D = enemy.get_node_or_null("InteractionArea") as Area3D
	if area == null:
		st.root.remove_child(enemy)
		enemy.free()
		_fail(NAME, "InteractionArea missing")
		return
	area.body_entered.emit(chunk)
	_assert_eq_int(0, emissions.size(), NAME + " — no emission when dead")
	st.root.remove_child(enemy)
	enemy.free()


# DAP-1.4 — absorb input does not mutate inventory when target ESM is dead (handler path).
func test_dap_14_absorb_dead_target_no_inventory_mutation() -> void:
	const NAME := "DAP-1.4 — absorb input does not mutate inventory when target is dead"
	var handler: Node = _new_handler_ready()
	if handler == null:
		_fail(NAME, "handler init failed")
		return
	var esm := EnemyStateMachine.new()
	esm.apply_death_event()
	handler.set_target_esm(esm, null)
	var inv: Variant = handler.get_mutation_inventory()
	if inv == null or not inv.has_method("get_granted_count"):
		handler.free()
		_fail(NAME, "mutation inventory missing get_granted_count")
		return
	var before: int = inv.get_granted_count()
	Input.action_press("absorb")
	handler._process(0.0)
	Input.action_release("absorb")
	var after: int = inv.get_granted_count()
	_assert_eq_int(before, after, NAME + " — granted_count unchanged")
	handler.free()


# DAP-1.5 — infect input does not call apply_infection_event when target is dead (state stays dead).
func test_dap_15_infect_dead_target_state_unchanged() -> void:
	const NAME := "DAP-1.5 — infect input leaves dead ESM in dead"
	var handler: Node = _new_handler_ready()
	if handler == null:
		_fail(NAME, "handler init failed")
		return
	var esm := EnemyStateMachine.new()
	esm.apply_death_event()
	handler.set_target_esm(esm, null)
	Input.action_press("infect")
	handler._process(0.0)
	Input.action_release("infect")
	_assert_eq_string("dead", esm.get_state(), NAME + " — state remains dead")
	handler.free()


# DAP-1.6 — absorb prompt predicate: handler uses can_absorb(esm); dead target => false (set_absorb_available false).
func test_dap_16_absorb_predicate_false_when_target_dead() -> void:
	const NAME := "DAP-1.6 — can_absorb false for dead ESM (same predicate as set_absorb_available)"
	var resolver := InfectionAbsorbResolver.new()
	var esm := EnemyStateMachine.new()
	esm.apply_death_event()
	_assert_false(resolver.can_absorb(esm), NAME + " — can_absorb(dead) == false")


# DAP-1.7 — enemy removed from tree during Death playback; advancing AnimationPlayer must not error.
func test_dap_17_tree_detach_during_death_animation_pump_safe() -> void:
	const NAME := "DAP-1.7 — detach during Death + advance AnimationPlayer completes without crash"
	var path := "res://scenes/enemies/generated/adhesion_bug_animated_00.tscn"
	if not ResourceLoader.exists(path):
		_fail(NAME, "missing scene")
		return
	var packed: PackedScene = load(path) as PackedScene
	var inst: CharacterBody3D = packed.instantiate() as CharacterBody3D
	var eac: EnemyAnimationController = inst.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	var ap: AnimationPlayer = inst.get_node_or_null("AnimationPlayer") as AnimationPlayer
	if eac == null or ap == null:
		inst.free()
		_fail(NAME, "missing controller or AnimationPlayer")
		return
	var esm := EnemyStateMachine.new()
	eac.setup(esm)
	var st: SceneTree = Engine.get_main_loop() as SceneTree
	st.root.add_child(inst)
	eac._ready()
	if not eac._ready_ok:
		st.root.remove_child(inst)
		inst.free()
		_fail(NAME, "controller not ready")
		return
	esm.apply_death_event()
	eac._physics_process(0.016)
	st.root.remove_child(inst)
	for _i in 120:
		if is_instance_valid(ap):
			ap.advance(1.0 / 60.0)
	inst.free()
	_pass(NAME + " — completed pump loop")


func run_all() -> int:
	print("--- test_death_animation_playthrough_infection.gd ---")
	_pass_count = 0
	_fail_count = 0
	test_dap_13_no_chunk_attached_when_dead()
	test_dap_14_absorb_dead_target_no_inventory_mutation()
	test_dap_15_infect_dead_target_state_unchanged()
	test_dap_16_absorb_predicate_false_when_target_dead()
	test_dap_17_tree_detach_during_death_animation_pump_safe()
	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
