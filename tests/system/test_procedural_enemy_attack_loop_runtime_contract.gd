#
# test_procedural_enemy_attack_loop_runtime_contract.gd
#
# Primary behavioral contract tests for M10-03 procedural enemy attack loop runtime.
# Spec: project_board/specs/procedural_enemy_attack_loop_runtime_spec.md
# Ticket: project_board/10_milestone_10_procedural_enemies_in_level/in_progress/03_procedural_enemy_attack_loop_runtime.md
#
# Trace IDs (PEAR-T-##):
# - R1 / AC-R1.x  -> PEAR-T-01 .. PEAR-T-07, PEAR-T-15
# - R2 / AC-R2.x  -> PEAR-T-08, PEAR-T-09
# - R3 / AC-R3.x  -> PEAR-T-10, PEAR-T-11
# - R4 / AC-R4.x  -> PEAR-T-08, PEAR-T-12, PEAR-T-13
# - R5 / AC-R5.x  -> PEAR-T-14, PEAR-T-16
# - R6 / AC-R6.x  -> PEAR-T-17 (suite traceability)
#

extends "res://tests/utils/test_utils.gd"

const ASSEMBLER_PATH: String = "res://scripts/system/run_scene_assembler.gd"
const SPEC_REF: String = "project_board/specs/procedural_enemy_attack_loop_runtime_spec.md"
const ROOM_COMBAT_01_PATH: String = "res://scenes/rooms/room_combat_01.tscn"

const _PHYSICS_STEP: float = 0.016
const _ACID_COOLDOWN_SEC: float = 3.0
const _PUMP_MAX_ITERS: int = 10000

var _pass_count: int = 0
var _fail_count: int = 0


func _load_source(path: String) -> String:
	if not ResourceLoader.exists(path):
		return ""
	var gds: GDScript = load(path) as GDScript
	if gds == null:
		return ""
	return gds.source_code


func _instantiate_scene(path: String) -> Node:
	if not ResourceLoader.exists(path):
		return null
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func _tree() -> SceneTree:
	return Engine.get_main_loop() as SceneTree


func _make_assembler_for_spawn_only() -> Object:
	var gds: GDScript = load(ASSEMBLER_PATH) as GDScript
	if gds == null or not gds.can_instantiate():
		return null
	var asm: Object = gds.new()
	var selector: Variant = asm.call("_build_enemy_visual_variant_selector")
	asm.set("_enemy_visual_variant_selector", selector)
	return asm


func _spawn_via_assembler(room: Node3D, room_path: String, assembler: Object) -> void:
	if room == null or assembler == null:
		return
	assembler.call("_spawn_generated_enemies_for_room", room, room_path)


func _free_assembler_instance(assembler: Object) -> void:
	if assembler is Node:
		var n: Node = assembler as Node
		if is_instance_valid(n) and not n.is_inside_tree():
			n.free()


func _detach_and_free(node: Node) -> void:
	if node == null or not is_instance_valid(node):
		return
	var p: Node = node.get_parent()
	if p != null:
		p.remove_child(node)
	node.free()


func _set_combat_declarations(room: Node, declarations: Array) -> void:
	room.set_meta("enemy_spawn_declarations", declarations)


func _list_procedural_enemy_roots(room: Node) -> Array[Node3D]:
	var out: Array[Node3D] = []
	if room == null:
		return out
	for child in room.get_children():
		if child is Node3D and (child as Node3D).has_meta("enemy_family"):
			out.append(child as Node3D)
	return out


func _prepare_infection_host(enemy: Node) -> void:
	# PEAR harness: mirrors production deferred wiring on EnemyInfection3D without requiring idle frames
	# (see enemy_infection_3d.gd call_deferred("_wire_and_notify_animation")).
	if not (enemy is EnemyInfection3D):
		return
	var host: EnemyInfection3D = enemy as EnemyInfection3D
	if not host.is_node_ready():
		host._ready()
	host.call("_wire_and_notify_animation")


func _count_acid_projectiles_under(node: Node) -> int:
	var n: int = 0
	if node == null:
		return 0
	for c in node.get_children():
		if c is AcidProjectile3D:
			n += 1
		n += _count_acid_projectiles_under(c)
	return n


func _count_attack_type_under(enemy: Node, attack_script: GDScript) -> int:
	var n: int = 0
	if enemy == null or attack_script == null:
		return 0
	for c in enemy.get_children():
		if c.get_script() == attack_script:
			n += 1
	return n


func _pump_acid_attack_integration(
	room: Node3D,
	enemy: EnemyInfection3D,
	atk: AcidSpitterRangedAttack,
	until_projectiles_at_least: int
) -> int:
	var ctrl: EnemyAnimationController = enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	var ap: AnimationPlayer = enemy.get_node_or_null("AnimationPlayer") as AnimationPlayer
	var iters: int = 0
	while _count_acid_projectiles_under(room) < until_projectiles_at_least and iters < _PUMP_MAX_ITERS:
		atk._physics_process(_PHYSICS_STEP)
		if ap != null:
			ap.advance(_PHYSICS_STEP)
		if ctrl != null:
			ctrl._physics_process(_PHYSICS_STEP)
		iters += 1
	return iters


func _setup_room_with_decl_and_spawn(
	declarations: Array,
	parent: Node,
	room_path: String
) -> Node3D:
	var room: Node3D = _instantiate_scene(ROOM_COMBAT_01_PATH) as Node3D
	if room == null:
		return null
	_set_combat_declarations(room, declarations)
	parent.add_child(room)
	var assembler: Object = _make_assembler_for_spawn_only()
	_spawn_via_assembler(room, room_path, assembler)
	_free_assembler_instance(assembler)
	return room


func test_pear_t_01_acid_spitter_exactly_one_m8_attack_node() -> void:
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-01_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty():
		_fail("PEAR-T-01_spawned_enemy_present", "assembler produced zero procedural enemies (selector/manifest/host)")
		_detach_and_free(room)
		return
	var enemy: Node3D = enemies[0]
	_assert_true(enemy is EnemyInfection3D, "PEAR-T-01_host_is_enemy_infection3d", "ADR-M10-03-01: M8 attack scripts require infection host contract")
	if not (enemy is EnemyInfection3D):
		_detach_and_free(room)
		return
	_prepare_infection_host(enemy)
	var acid_script: GDScript = load("res://scripts/enemy/acid_spitter_ranged_attack.gd") as GDScript
	var count: int = _count_attack_type_under(enemy, acid_script)
	_assert_eq_int(1, count, "PEAR-T-01_ac_r1_1_single_acid_attack_node")
	_detach_and_free(room)


func test_pear_t_02_carapace_exactly_one_m8_attack_node() -> void:
	var decl: Array = [{"enemy_family": "carapace_husk", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-02_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty():
		_fail("PEAR-T-02_spawned_enemy_present", "no spawned enemy")
		_detach_and_free(room)
		return
	var enemy: Node3D = enemies[0]
	_assert_true(enemy is EnemyInfection3D, "PEAR-T-02_host_is_enemy_infection3d")
	if not (enemy is EnemyInfection3D):
		_detach_and_free(room)
		return
	_prepare_infection_host(enemy)
	var script_res: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	_assert_eq_int(1, _count_attack_type_under(enemy, script_res), "PEAR-T-02_ac_r1_1_single_carapace_attack_node")
	_detach_and_free(room)


func test_pear_t_03_adhesion_exactly_one_m8_attack_node() -> void:
	var decl: Array = [{"enemy_family": "adhesion_bug", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-03_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty():
		_fail("PEAR-T-03_spawned_enemy_present", "no spawned enemy")
		_detach_and_free(room)
		return
	var enemy: Node3D = enemies[0]
	_assert_true(enemy is EnemyInfection3D, "PEAR-T-03_host_is_enemy_infection3d")
	if not (enemy is EnemyInfection3D):
		_detach_and_free(room)
		return
	_prepare_infection_host(enemy)
	var script_res: GDScript = load("res://scripts/enemy/adhesion_bug_lunge_attack.gd") as GDScript
	_assert_eq_int(1, _count_attack_type_under(enemy, script_res), "PEAR-T-03_ac_r1_1_single_adhesion_attack_node")
	_detach_and_free(room)


func test_pear_t_04_claw_exactly_one_m8_attack_node() -> void:
	var decl: Array = [{"enemy_family": "claw_crawler", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-04_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty():
		_fail("PEAR-T-04_spawned_enemy_present", "no spawned enemy")
		_detach_and_free(room)
		return
	var enemy: Node3D = enemies[0]
	_assert_true(enemy is EnemyInfection3D, "PEAR-T-04_host_is_enemy_infection3d")
	if not (enemy is EnemyInfection3D):
		_detach_and_free(room)
		return
	_prepare_infection_host(enemy)
	var script_res: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	_assert_eq_int(1, _count_attack_type_under(enemy, script_res), "PEAR-T-04_ac_r1_1_single_claw_attack_node")
	_detach_and_free(room)


func test_pear_t_05_attack_script_host_reference_non_null() -> void:
	# AC-R1.2 — family attack tick must see a non-null M8 host reference after wiring.
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-05_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-05_host_missing", "infection host required")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-05_attack_missing", "AcidSpitterRangedAttack not attached")
		_detach_and_free(room)
		return
	atk._ready()
	var host_ref: Variant = atk.get("_enemy")
	_assert_true(host_ref != null, "PEAR-T-05_ac_r1_2_enemy_ref_non_null", "attack host reference must not be null after _ready")
	_detach_and_free(room)


func test_pear_t_06_assembler_does_not_attach_attack_scripts_directly() -> void:
	# AC-R1.4 — RunSceneAssembler must not add parallel attack/damage nodes beyond spawn + metadata.
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(not src.is_empty(), "PEAR-T-06_assembler_source_loads")
	_assert_true(src.find("AcidSpitterRangedAttack") < 0, "PEAR-T-06_ac_r1_4_no_acid_node_literal")
	_assert_true(src.find("CarapaceHuskAttack") < 0, "PEAR-T-06_ac_r1_4_no_carapace_node_literal")
	_assert_true(src.find("AdhesionBugLungeAttack") < 0, "PEAR-T-06_ac_r1_4_no_adhesion_node_literal")
	_assert_true(src.find("ClawCrawlerAttack") < 0, "PEAR-T-06_ac_r1_4_no_claw_node_literal")


func test_pear_t_07_effective_mutation_drop_meta_matches_family_contract() -> void:
	var decl: Array = [{"enemy_family": "carapace_husk", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-07_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty():
		_fail("PEAR-T-07_spawned_enemy_present", "no spawned enemy")
		_detach_and_free(room)
		return
	var drop: String = str(enemies[0].get_meta("mutation_drop", "")).strip_edges()
	_assert_eq_string("carapace", drop, "PEAR-T-07_ac_r1_mutation_drop_carapace")
	_detach_and_free(room)


func test_pear_t_08_procedural_acid_completes_two_attack_cycles_headless() -> void:
	# AC-R2.1 / AC-R4.1 — ≥2 completed attack cycles (acid: ≥2 projectiles) with physics+animation pump only.
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-08_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-08_host_missing", "EnemyInfection3D host required for M8 acid loop")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-08_attack_missing", "acid attack not wired")
		_detach_and_free(room)
		return
	atk._ready()
	var player := Node3D.new()
	player.name = "TestPlayerPear08"
	player.add_to_group("player")
	room.add_child(player)
	player.position = enemy.position + Vector3(2.0, 0.0, 0.0)
	var iters: int = _pump_acid_attack_integration(room, enemy, atk, 2)
	_assert_true(iters < _PUMP_MAX_ITERS, "PEAR-T-08_ac_r2_1_two_cycles_within_cap", "exceeded pump cap — telegraph/cooldown loop stuck?")
	var proj: int = _count_acid_projectiles_under(room)
	_assert_true(proj >= 2, "PEAR-T-08_ac_r2_1_two_projectiles", "expected ≥2 acid projectiles for two cycles")
	_detach_and_free(room)


func test_pear_t_09_cooldown_separates_active_phases_acid() -> void:
	# AC-R2.2 — second active phase must not begin until cooldown elapses (simulated time via _physics_process deltas).
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-09_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-09_host_missing", "infection host required")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-09_attack_missing", "acid attack not wired")
		_detach_and_free(room)
		return
	atk._ready()
	var player := Node3D.new()
	player.add_to_group("player")
	room.add_child(player)
	player.position = enemy.position + Vector3(2.0, 0.0, 0.0)
	var ctrl: EnemyAnimationController = enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	var ap: AnimationPlayer = enemy.get_node_or_null("AnimationPlayer") as AnimationPlayer
	var sim_time: float = 0.0
	var iters_first: int = 0
	while _count_acid_projectiles_under(room) < 1 and iters_first < _PUMP_MAX_ITERS:
		atk._physics_process(_PHYSICS_STEP)
		if ap != null:
			ap.advance(_PHYSICS_STEP)
		if ctrl != null:
			ctrl._physics_process(_PHYSICS_STEP)
		sim_time += _PHYSICS_STEP
		iters_first += 1
	_assert_true(iters_first < _PUMP_MAX_ITERS, "PEAR-T-09_first_cycle_finishes")
	var sim_at_first_proj: float = sim_time
	var iters_second: int = 0
	while _count_acid_projectiles_under(room) < 2 and iters_second < _PUMP_MAX_ITERS:
		atk._physics_process(_PHYSICS_STEP)
		if ap != null:
			ap.advance(_PHYSICS_STEP)
		if ctrl != null:
			ctrl._physics_process(_PHYSICS_STEP)
		sim_time += _PHYSICS_STEP
		iters_second += 1
	_assert_true(iters_second < _PUMP_MAX_ITERS, "PEAR-T-09_second_cycle_finishes")
	var sim_between: float = sim_time - sim_at_first_proj
	var min_expected: float = _ACID_COOLDOWN_SEC * 0.92
	_assert_true(
		sim_between + 0.05 >= min_expected,
		"PEAR-T-09_ac_r2_2_cooldown_observed_between_cycles",
		"expected ≥%.2fs simulated cooldown between cycles (got %.3fs)" % [min_expected, sim_between]
	)
	_detach_and_free(room)


func test_pear_t_10_spawn_api_parity_root_vs_wrapper_parent() -> void:
	# AC-R3.1 / AC-R3.2 — same `_spawn_generated_enemies_for_room` hook: wiring parity across parent chain.
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var assembler: Object = _make_assembler_for_spawn_only()
	if assembler == null:
		_fail("PEAR-T-10_assembler", "assembler build failed")
		return

	var room_a: Node3D = _instantiate_scene(ROOM_COMBAT_01_PATH) as Node3D
	var room_b: Node3D = _instantiate_scene(ROOM_COMBAT_01_PATH) as Node3D
	if room_a == null or room_b == null:
		_fail("PEAR-T-10_room_load", "combat room missing")
		_free_assembler_instance(assembler)
		if room_a != null:
			_detach_and_free(room_a)
		if room_b != null:
			_detach_and_free(room_b)
		return
	_set_combat_declarations(room_a, decl)
	_set_combat_declarations(room_b, decl)
	tree.root.add_child(room_a)
	var level_wrap := Node3D.new()
	tree.root.add_child(level_wrap)
	level_wrap.add_child(room_b)

	_spawn_via_assembler(room_a, ROOM_COMBAT_01_PATH, assembler)
	_spawn_via_assembler(room_b, ROOM_COMBAT_01_PATH, assembler)

	var enemies_a: Array[Node3D] = _list_procedural_enemy_roots(room_a)
	var enemies_b: Array[Node3D] = _list_procedural_enemy_roots(room_b)
	_assert_eq_int(enemies_a.size(), enemies_b.size(), "PEAR-T-10_ac_r3_same_spawn_count")
	if enemies_a.is_empty() or enemies_b.is_empty():
		_fail("PEAR-T-10_enemies_spawned", "spawn count mismatch or zero")
		_free_assembler_instance(assembler)
		_detach_and_free(room_a)
		_detach_and_free(level_wrap)
		return
	_assert_true(enemies_a[0] is EnemyInfection3D, "PEAR-T-10_mode_a_host")
	_assert_true(enemies_b[0] is EnemyInfection3D, "PEAR-T-10_mode_b_host")
	_prepare_infection_host(enemies_a[0])
	_prepare_infection_host(enemies_b[0])
	var acid_script: GDScript = load("res://scripts/enemy/acid_spitter_ranged_attack.gd") as GDScript
	var ca: int = _count_attack_type_under(enemies_a[0], acid_script)
	var cb: int = _count_attack_type_under(enemies_b[0], acid_script)
	_assert_eq_int(ca, cb, "PEAR-T-10_ac_r3_attack_attachment_parity")
	_free_assembler_instance(assembler)
	_detach_and_free(room_a)
	_detach_and_free(level_wrap)


func test_pear_t_11_production_path_calls_shared_spawn_routine() -> void:
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(src.find("func _on_run_started") >= 0, "PEAR-T-11_has_on_run_started")
	_assert_true(src.find("_spawn_generated_enemies_for_room") >= 0, "PEAR-T-11_spawn_routine_present")
	var idx_run: int = src.find("func _on_run_started")
	var idx_spawn: int = src.find("_spawn_generated_enemies_for_room")
	_assert_true(idx_spawn > idx_run, "PEAR-T-11_spawn_invoked_after_run_handler_decl")


func test_pear_t_12_dead_host_suppresses_further_acid_cycles() -> void:
	# AC-R4.2 — real ESM `dead` must block new attack cycles on procedural infection host (ADR-M10-03-02).
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-12_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-12_host_missing", "EnemyInfection3D required for ESM dead contract")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var esm: Variant = enemy.get_esm()
	_assert_true(esm is EnemyStateMachine, "PEAR-T-12_esm_is_real_state_machine", "stub-only ESM cannot satisfy dead suppression contract")
	if not (esm is EnemyStateMachine):
		_detach_and_free(room)
		return
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-12_attack_missing", "acid attack not wired")
		_detach_and_free(room)
		return
	atk._ready()
	var player := Node3D.new()
	player.add_to_group("player")
	room.add_child(player)
	player.position = enemy.position + Vector3(2.0, 0.0, 0.0)
	var _it: int = _pump_acid_attack_integration(room, enemy, atk, 1)
	var count_after_one: int = _count_acid_projectiles_under(room)
	(esm as EnemyStateMachine).apply_death_event()
	var ctrl: EnemyAnimationController = enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	var ap: AnimationPlayer = enemy.get_node_or_null("AnimationPlayer") as AnimationPlayer
	for _i in range(8000):
		atk._physics_process(_PHYSICS_STEP)
		if ap != null:
			ap.advance(_PHYSICS_STEP)
		if ctrl != null:
			ctrl._physics_process(_PHYSICS_STEP)
	_assert_eq_int(count_after_one, _count_acid_projectiles_under(room), "PEAR-T-12_ac_r4_2_projectile_count_stable_after_death")
	_detach_and_free(room)


func test_pear_t_13_spawn_failure_logs_room_family_and_reason() -> void:
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(src.find("room=%s") >= 0 or src.find("room=") >= 0, "PEAR-T-13_log_room_placeholder")
	_assert_true(src.find("family=") >= 0, "PEAR-T-13_log_family_placeholder")
	_assert_true(src.find("error=") >= 0 or src.find("error:") >= 0, "PEAR-T-13_log_reason_key")


func test_pear_t_14_attack_scripts_use_o1_player_lookup_only() -> void:
	# AC-R5.1 — no broad group scans beyond `player` in family attack scripts.
	var paths: Array[String] = [
		"res://scripts/enemy/acid_spitter_ranged_attack.gd",
		"res://scripts/enemy/adhesion_bug_lunge_attack.gd",
		"res://scripts/enemy/carapace_husk_attack.gd",
		"res://scripts/enemy/claw_crawler_attack.gd",
	]
	for p in paths:
		var s: String = _load_source(p)
		if s.find("get_nodes_in_group") >= 0:
			_fail("PEAR-T-14_no_nodes_in_group_%s" % p, "get_nodes_in_group is forbidden for O(1) contract")
			continue
		_pass("PEAR-T-14_no_nodes_in_group_%s" % p)


func test_pear_t_15_no_duplicate_family_attack_siblings() -> void:
	# AC-R1.1 hardening — exactly one attack script instance per family on host.
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-15_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-15_host", "infection host required")
		_detach_and_free(room)
		return
	_prepare_infection_host(enemies[0])
	var acid_script: GDScript = load("res://scripts/enemy/acid_spitter_ranged_attack.gd") as GDScript
	var n: int = _count_attack_type_under(enemies[0], acid_script)
	_assert_eq_int(1, n, "PEAR-T-15_single_attack_no_double_attach")
	_detach_and_free(room)


func test_pear_t_16_suite_traceability_lists_spec_path() -> void:
	# AC-R6.1 documentation trace — this suite binds to the runtime spec path.
	var self_script: GDScript = load("res://tests/system/test_procedural_enemy_attack_loop_runtime_contract.gd") as GDScript
	if self_script == null:
		_fail("PEAR-T-16_self_load", "missing test script")
		return
	var body: String = self_script.source_code
	_assert_true(body.find(SPEC_REF) >= 0, "PEAR-T-16_spec_path_in_header")


func test_pear_t_17_unknown_family_declaration_fails_closed_without_spawn() -> void:
	var decl: Array = [{"enemy_family": "unknown_family", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-17_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	_assert_eq_int(0, enemies.size(), "PEAR-T-17_unknown_family_no_runtime_enemy_spawned")
	_detach_and_free(room)


func test_pear_t_18_acid_no_player_no_projectiles_under_stress() -> void:
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-18_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-18_host_missing", "EnemyInfection3D host required")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-18_attack_missing", "acid attack not wired")
		_detach_and_free(room)
		return
	atk._ready()
	var ctrl: EnemyAnimationController = enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	var ap: AnimationPlayer = enemy.get_node_or_null("AnimationPlayer") as AnimationPlayer
	for _i in range(5000):
		atk._physics_process(_PHYSICS_STEP)
		if ap != null:
			ap.advance(_PHYSICS_STEP)
		if ctrl != null:
			ctrl._physics_process(_PHYSICS_STEP)
	_assert_eq_int(0, _count_acid_projectiles_under(room), "PEAR-T-18_no_player_no_projectiles")
	_detach_and_free(room)


func test_pear_t_19_out_of_range_player_does_not_trigger_acid_attack() -> void:
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-19_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-19_host_missing", "EnemyInfection3D host required")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-19_attack_missing", "acid attack not wired")
		_detach_and_free(room)
		return
	atk._ready()
	var far_player := Node3D.new()
	far_player.name = "TestPlayerPear19Far"
	far_player.add_to_group("player")
	room.add_child(far_player)
	far_player.position = enemy.position + Vector3(200.0, 0.0, 0.0)
	var ctrl: EnemyAnimationController = enemy.get_node_or_null("EnemyAnimationController") as EnemyAnimationController
	var ap: AnimationPlayer = enemy.get_node_or_null("AnimationPlayer") as AnimationPlayer
	for _i in range(5000):
		atk._physics_process(_PHYSICS_STEP)
		if ap != null:
			ap.advance(_PHYSICS_STEP)
		if ctrl != null:
			ctrl._physics_process(_PHYSICS_STEP)
	_assert_eq_int(0, _count_acid_projectiles_under(room), "PEAR-T-19_far_player_no_projectiles")
	_detach_and_free(room)


func test_pear_t_20_three_cycles_do_not_burst_fire_same_frame() -> void:
	# CHECKPOINT conservative assumption: each cycle emits exactly one projectile, so three cycles produce exactly three.
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _setup_room_with_decl_and_spawn(decl, tree.root, ROOM_COMBAT_01_PATH)
	if room == null:
		_fail("PEAR-T-20_room_setup", "room instantiate failed")
		return
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	if enemies.is_empty() or not (enemies[0] is EnemyInfection3D):
		_fail("PEAR-T-20_host_missing", "EnemyInfection3D host required")
		_detach_and_free(room)
		return
	var enemy: EnemyInfection3D = enemies[0] as EnemyInfection3D
	_prepare_infection_host(enemy)
	var atk: AcidSpitterRangedAttack = enemy.get_node_or_null("AcidSpitterRangedAttack") as AcidSpitterRangedAttack
	if atk == null:
		_fail("PEAR-T-20_attack_missing", "acid attack not wired")
		_detach_and_free(room)
		return
	atk._ready()
	var player := Node3D.new()
	player.name = "TestPlayerPear20"
	player.add_to_group("player")
	room.add_child(player)
	player.position = enemy.position + Vector3(2.0, 0.0, 0.0)
	var iters: int = _pump_acid_attack_integration(room, enemy, atk, 3)
	_assert_true(iters < _PUMP_MAX_ITERS, "PEAR-T-20_three_cycles_within_pump_cap")
	_assert_eq_int(3, _count_acid_projectiles_under(room), "PEAR-T-20_three_cycles_exact_three_projectiles")
	_detach_and_free(room)


func test_pear_t_21_repeat_spawn_calls_do_not_duplicate_attack_nodes() -> void:
	var decl: Array = [{"enemy_family": "acid_spitter", "min_count": 1, "max_count": 1}]
	var tree: SceneTree = _tree()
	var room: Node3D = _instantiate_scene(ROOM_COMBAT_01_PATH) as Node3D
	if room == null:
		_fail("PEAR-T-21_room_setup", "room instantiate failed")
		return
	_set_combat_declarations(room, decl)
	tree.root.add_child(room)
	var assembler: Object = _make_assembler_for_spawn_only()
	_spawn_via_assembler(room, ROOM_COMBAT_01_PATH, assembler)
	_spawn_via_assembler(room, ROOM_COMBAT_01_PATH, assembler)
	_free_assembler_instance(assembler)
	var enemies: Array[Node3D] = _list_procedural_enemy_roots(room)
	_assert_true(not enemies.is_empty(), "PEAR-T-21_spawned_enemy_present")
	if enemies.is_empty():
		_detach_and_free(room)
		return
	_prepare_infection_host(enemies[0])
	var acid_script: GDScript = load("res://scripts/enemy/acid_spitter_ranged_attack.gd") as GDScript
	var count: int = _count_attack_type_under(enemies[0], acid_script)
	_assert_eq_int(1, count, "PEAR-T-21_repeat_spawn_no_duplicate_attack_nodes")
	_detach_and_free(room)


func run_all() -> int:
	print("--- test_procedural_enemy_attack_loop_runtime_contract.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_pear_t_01_acid_spitter_exactly_one_m8_attack_node()
	test_pear_t_02_carapace_exactly_one_m8_attack_node()
	test_pear_t_03_adhesion_exactly_one_m8_attack_node()
	test_pear_t_04_claw_exactly_one_m8_attack_node()
	test_pear_t_05_attack_script_host_reference_non_null()
	test_pear_t_06_assembler_does_not_attach_attack_scripts_directly()
	test_pear_t_07_effective_mutation_drop_meta_matches_family_contract()
	test_pear_t_08_procedural_acid_completes_two_attack_cycles_headless()
	test_pear_t_09_cooldown_separates_active_phases_acid()
	test_pear_t_10_spawn_api_parity_root_vs_wrapper_parent()
	test_pear_t_11_production_path_calls_shared_spawn_routine()
	test_pear_t_12_dead_host_suppresses_further_acid_cycles()
	test_pear_t_13_spawn_failure_logs_room_family_and_reason()
	test_pear_t_14_attack_scripts_use_o1_player_lookup_only()
	test_pear_t_15_no_duplicate_family_attack_siblings()
	test_pear_t_16_suite_traceability_lists_spec_path()
	test_pear_t_17_unknown_family_declaration_fails_closed_without_spawn()
	test_pear_t_18_acid_no_player_no_projectiles_under_stress()
	test_pear_t_19_out_of_range_player_does_not_trigger_acid_attack()
	test_pear_t_20_three_cycles_do_not_burst_fire_same_frame()
	test_pear_t_21_repeat_spawn_calls_do_not_duplicate_attack_nodes()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
