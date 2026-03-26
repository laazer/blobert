#
# test_procedural_run.gd
#
# Primary behavioral tests for the procedural_run.tscn canonical M6 entry point.
# Spec:   agent_context/agents/2_spec/procedural_run_scene_spec.md
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/FEAT-20260326-procedural-run-scene.md
#
# All tests are headless-safe: ResourceLoader.load() + PackedScene.instantiate() +
# node property reads + root.free(). No await, no physics tick, no SceneTree required.
#
# Red phase:  scene file does not yet exist — tests relying on it report FAIL with a
#             clear message. Tests that inspect source files on disk (PRS-RSA-1 etc.)
#             will pass as long as the script files exist.
# Green phase: all assertions pass after Generalist Agent authors the scene file.
#
# Spec requirement traceability:
#   PRS-LOAD-1   → PRS-SCENE-2  (ResourceLoader.load non-null)
#   PRS-LOAD-2   → PRS-SCENE-3  (instantiate non-null)
#   PRS-LOAD-3   → PRS-SCENE-7  (free without error)
#   PRS-ROOT-1   → PRS-SCENE-4  (root class == Node3D)
#   PRS-ROOT-2   → PRS-SCENE-5  (root name == "ProceduralRun")
#   PRS-ROOT-3   → PRS-NODE-1   (root has no script)
#   PRS-ROOT-4   → PRS-NODE-2   (root has exactly 5 direct children)
#   PRS-CHILD-1  → PRS-NODE-6   (Player3D exists as direct child)
#   PRS-CHILD-2  → PRS-NODE-7   (SpawnPosition exists as direct child)
#   PRS-CHILD-3  → PRS-NODE-3   (RunSceneAssembler exists as direct child)
#   PRS-CHILD-4  → PRS-NODE-4   (DeathRestartCoordinator exists as direct child)
#   PRS-CHILD-5  → PRS-NODE-5   (InfectionInteractionHandler exists as direct child)
#   PRS-PLAYER-1 → PRS-PLAYER-1 (Player3D position == (0,1,0) ±0.01)
#   PRS-PLAYER-2 → PRS-PLAYER-2 (Player3D is in "player" group)
#   PRS-SPAWN-1  → PRS-SPAWN-1  (SpawnPosition.get_class() == "Marker3D")
#   PRS-SPAWN-2  → PRS-SPAWN-2  (SpawnPosition.position == (0,1,0) ±0.01)
#   PRS-SPAWN-3  → PRS-SPAWN-3  (SpawnPosition has no script)
#   PRS-WIRE-1   → PRS-WIRE-1   (DRC.player == NodePath("Player3D"))
#   PRS-WIRE-2   → PRS-WIRE-2   (DRC.spawn_position == NodePath("SpawnPosition"))
#   PRS-WIRE-3   → PRS-WIRE-3   (DRC.infection_handler == NodePath("InfectionInteractionHandler"))
#   PRS-GEO-1    → PRS-SCENE-6  (no StaticBody3D in tree)
#   PRS-GEO-2    → PRS-SCENE-6  (no MeshInstance3D in tree)
#   PRS-RSA-1    → PRS-NODE-3   (RunSceneAssembler script path correct)
#   PRS-DRC-1    → PRS-NODE-4   (DeathRestartCoordinator script path correct)
#   PRS-IIH-1    → PRS-NODE-5   (InfectionInteractionHandler script path correct)
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - Test IDs use PRS-* prefix; unique across all existing test namespaces.

extends Object

# ---------------------------------------------------------------------------
# Scene path under test
# ---------------------------------------------------------------------------

const SCENE_PATH: String = "res://scenes/levels/procedural_run.tscn"

# Position tolerance per spec (±0.01 m).
const POS_TOL: float = 0.01

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

func _pass_test(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail_test(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
	if condition:
		_pass_test(test_name)
	else:
		_fail_test(test_name, fail_msg)


func _assert_eq(actual: Variant, expected: Variant, test_name: String) -> void:
	if actual == expected:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected " + str(expected) + ", got " + str(actual))


func _assert_eq_str(actual: String, expected: String, test_name: String) -> void:
	if actual == expected:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected \"" + expected + "\", got \"" + actual + "\"")


func _near(a: float, b: float, tol: float) -> bool:
	return absf(a - b) <= tol


func _assert_vec3_near(actual: Vector3, expected: Vector3, tol: float, test_name: String) -> void:
	var ok: bool = _near(actual.x, expected.x, tol) \
		and _near(actual.y, expected.y, tol) \
		and _near(actual.z, expected.z, tol)
	if ok:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected ~" + str(expected) + " (tol " + str(tol) + "), got " + str(actual))


# Load and instantiate. Returns null and records the failure when scene is absent (red phase).
func _load_scene() -> Node:
	var packed: PackedScene = ResourceLoader.load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("scene_file_exists", "ResourceLoader.load returned null: " + SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("scene_instantiates", "instantiate() returned null")
	return inst


# Recursive search: count all nodes in the subtree whose class matches class_name_str.
func _count_nodes_of_class(node: Node, class_name_str: String) -> int:
	if node == null:
		return 0
	var count: int = 0
	if node.get_class() == class_name_str:
		count += 1
	for i in range(node.get_child_count()):
		count += _count_nodes_of_class(node.get_child(i), class_name_str)
	return count


# ---------------------------------------------------------------------------
# PRS-LOAD-1: Scene file loads as non-null PackedScene — PRS-SCENE-2
# ---------------------------------------------------------------------------
func test_prs_load_1_scene_loads_as_packed_scene() -> void:
	var packed: PackedScene = ResourceLoader.load(SCENE_PATH) as PackedScene
	_assert_true(
		packed != null,
		"PRS-LOAD-1_scene_loads_as_packed_scene",
		"ResourceLoader.load returned null — scene file absent (expected in red phase)"
	)
	if packed != null:
		var inst: Node = packed.instantiate()
		if inst != null:
			inst.free()


# ---------------------------------------------------------------------------
# PRS-LOAD-2: Scene instantiates without error (non-null node returned) — PRS-SCENE-3
# ---------------------------------------------------------------------------
func test_prs_load_2_scene_instantiates() -> void:
	var packed: PackedScene = ResourceLoader.load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("PRS-LOAD-2_scene_instantiates", "PackedScene is null — cannot instantiate")
		return
	var inst: Node = packed.instantiate()
	_assert_true(
		inst != null,
		"PRS-LOAD-2_scene_instantiates",
		"instantiate() returned null"
	)
	if inst != null:
		inst.free()


# ---------------------------------------------------------------------------
# PRS-LOAD-3: Scene frees without error — PRS-SCENE-7
# ---------------------------------------------------------------------------
func test_prs_load_3_scene_frees_without_error() -> void:
	var root: Node = _load_scene()
	if root == null:
		_fail_test("PRS-LOAD-3_scene_frees_without_error", "scene not loaded — skip free test")
		return
	# free() must not crash; if it does the test runner itself will catch the error.
	root.free()
	_pass_test("PRS-LOAD-3_scene_frees_without_error")


# ---------------------------------------------------------------------------
# PRS-ROOT-1: Root node type is Node3D — PRS-SCENE-4
# ---------------------------------------------------------------------------
func test_prs_root_1_root_class_is_node3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_eq_str(root.get_class(), "Node3D", "PRS-ROOT-1_root_class_is_node3d")
	root.free()


# ---------------------------------------------------------------------------
# PRS-ROOT-2: Root node name is "ProceduralRun" — PRS-SCENE-5
# ---------------------------------------------------------------------------
func test_prs_root_2_root_name_is_procedural_run() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_eq_str(root.name, "ProceduralRun", "PRS-ROOT-2_root_name_is_procedural_run")
	root.free()


# ---------------------------------------------------------------------------
# PRS-ROOT-3: Root has no script — PRS-NODE-1
# ---------------------------------------------------------------------------
func test_prs_root_3_root_has_no_script() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_true(
		root.get_script() == null,
		"PRS-ROOT-3_root_has_no_script",
		"Root node has a script attached; expected none"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-ROOT-4: Root has exactly 5 direct children — PRS-NODE-2
# ---------------------------------------------------------------------------
func test_prs_root_4_root_has_exactly_5_children() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var count: int = root.get_child_count()
	_assert_eq(count, 5, "PRS-ROOT-4_root_has_exactly_5_children")
	root.free()


# ---------------------------------------------------------------------------
# PRS-CHILD-1: Player3D exists as direct child of root — PRS-NODE-6
# ---------------------------------------------------------------------------
func test_prs_child_1_player3d_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("Player3D")
	_assert_true(
		node != null,
		"PRS-CHILD-1_player3d_exists",
		"No direct child named Player3D found under root"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-CHILD-2: SpawnPosition exists as direct child of root — PRS-NODE-7
# ---------------------------------------------------------------------------
func test_prs_child_2_spawn_position_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("SpawnPosition")
	_assert_true(
		node != null,
		"PRS-CHILD-2_spawn_position_exists",
		"No direct child named SpawnPosition found under root"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-CHILD-3: RunSceneAssembler exists as direct child of root — PRS-NODE-3
# ---------------------------------------------------------------------------
func test_prs_child_3_run_scene_assembler_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("RunSceneAssembler")
	_assert_true(
		node != null,
		"PRS-CHILD-3_run_scene_assembler_exists",
		"No direct child named RunSceneAssembler found under root"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-CHILD-4: DeathRestartCoordinator exists as direct child of root — PRS-NODE-4
# ---------------------------------------------------------------------------
func test_prs_child_4_death_restart_coordinator_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("DeathRestartCoordinator")
	_assert_true(
		node != null,
		"PRS-CHILD-4_death_restart_coordinator_exists",
		"No direct child named DeathRestartCoordinator found under root"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-CHILD-5: InfectionInteractionHandler exists as direct child of root — PRS-NODE-5
# ---------------------------------------------------------------------------
func test_prs_child_5_infection_interaction_handler_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("InfectionInteractionHandler")
	_assert_true(
		node != null,
		"PRS-CHILD-5_infection_interaction_handler_exists",
		"No direct child named InfectionInteractionHandler found under root"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-PLAYER-1: Player3D position is Vector3(0, 1, 0) ±0.01 — PRS-PLAYER-1
# ---------------------------------------------------------------------------
func test_prs_player_1_player3d_position() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var player: Node = root.get_node_or_null("Player3D")
	if player == null:
		_fail_test("PRS-PLAYER-1_player3d_position", "Player3D not found — skip position check")
		root.free()
		return
	if not player is Node3D:
		_fail_test("PRS-PLAYER-1_player3d_position", "Player3D is not a Node3D — cannot check position")
		root.free()
		return
	_assert_vec3_near(
		(player as Node3D).position,
		Vector3(0.0, 1.0, 0.0),
		POS_TOL,
		"PRS-PLAYER-1_player3d_position"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-PLAYER-2: Player3D is in the "player" group — PRS-PLAYER-2
# ---------------------------------------------------------------------------
func test_prs_player_2_player3d_in_player_group() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var player: Node = root.get_node_or_null("Player3D")
	if player == null:
		_fail_test("PRS-PLAYER-2_player3d_in_player_group", "Player3D not found — skip group check")
		root.free()
		return
	_assert_true(
		player.is_in_group("player"),
		"PRS-PLAYER-2_player3d_in_player_group",
		"Player3D is not in group \"player\""
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-SPAWN-1: SpawnPosition is Marker3D — PRS-SPAWN-1
# ---------------------------------------------------------------------------
func test_prs_spawn_1_spawn_position_is_marker3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("SpawnPosition")
	if node == null:
		_fail_test("PRS-SPAWN-1_spawn_position_is_marker3d", "SpawnPosition not found")
		root.free()
		return
	_assert_eq_str(
		node.get_class(),
		"Marker3D",
		"PRS-SPAWN-1_spawn_position_is_marker3d"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-SPAWN-2: SpawnPosition position is Vector3(0, 1, 0) ±0.01 — PRS-SPAWN-2
# ---------------------------------------------------------------------------
func test_prs_spawn_2_spawn_position_coordinates() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("SpawnPosition")
	if node == null:
		_fail_test("PRS-SPAWN-2_spawn_position_coordinates", "SpawnPosition not found")
		root.free()
		return
	if not node is Node3D:
		_fail_test("PRS-SPAWN-2_spawn_position_coordinates", "SpawnPosition is not Node3D — cannot check position")
		root.free()
		return
	_assert_vec3_near(
		(node as Node3D).position,
		Vector3(0.0, 1.0, 0.0),
		POS_TOL,
		"PRS-SPAWN-2_spawn_position_coordinates"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-SPAWN-3: SpawnPosition has no script — PRS-SPAWN-3
# ---------------------------------------------------------------------------
func test_prs_spawn_3_spawn_position_has_no_script() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("SpawnPosition")
	if node == null:
		_fail_test("PRS-SPAWN-3_spawn_position_has_no_script", "SpawnPosition not found")
		root.free()
		return
	_assert_true(
		node.get_script() == null,
		"PRS-SPAWN-3_spawn_position_has_no_script",
		"SpawnPosition has a script attached; expected none"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-WIRE-1: DeathRestartCoordinator.player == NodePath("Player3D") — PRS-WIRE-1
# ---------------------------------------------------------------------------
func test_prs_wire_1_drc_player_nodepath() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	if drc == null:
		_fail_test("PRS-WIRE-1_drc_player_nodepath", "DeathRestartCoordinator not found")
		root.free()
		return
	var val: Variant = drc.get("player")
	_assert_eq(val, NodePath("Player3D"), "PRS-WIRE-1_drc_player_nodepath")
	root.free()


# ---------------------------------------------------------------------------
# PRS-WIRE-2: DeathRestartCoordinator.spawn_position == NodePath("SpawnPosition") — PRS-WIRE-2
# ---------------------------------------------------------------------------
func test_prs_wire_2_drc_spawn_position_nodepath() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	if drc == null:
		_fail_test("PRS-WIRE-2_drc_spawn_position_nodepath", "DeathRestartCoordinator not found")
		root.free()
		return
	var val: Variant = drc.get("spawn_position")
	_assert_eq(val, NodePath("SpawnPosition"), "PRS-WIRE-2_drc_spawn_position_nodepath")
	root.free()


# ---------------------------------------------------------------------------
# PRS-WIRE-3: DeathRestartCoordinator.infection_handler == NodePath("InfectionInteractionHandler")
#             — PRS-WIRE-3
# ---------------------------------------------------------------------------
func test_prs_wire_3_drc_infection_handler_nodepath() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	if drc == null:
		_fail_test("PRS-WIRE-3_drc_infection_handler_nodepath", "DeathRestartCoordinator not found")
		root.free()
		return
	var val: Variant = drc.get("infection_handler")
	_assert_eq(val, NodePath("InfectionInteractionHandler"), "PRS-WIRE-3_drc_infection_handler_nodepath")
	root.free()


# ---------------------------------------------------------------------------
# PRS-GEO-1: No StaticBody3D anywhere in the scene tree — PRS-SCENE-6
# ---------------------------------------------------------------------------
func test_prs_geo_1_no_static_body_3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var count: int = _count_nodes_of_class(root, "StaticBody3D")
	_assert_true(
		count == 0,
		"PRS-GEO-1_no_static_body_3d",
		"Found " + str(count) + " StaticBody3D node(s); expected 0 (no pre-built geometry)"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-GEO-2: No MeshInstance3D anywhere in the scene tree — PRS-SCENE-6
# ---------------------------------------------------------------------------
func test_prs_geo_2_no_mesh_instance_3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var count: int = _count_nodes_of_class(root, "MeshInstance3D")
	_assert_true(
		count == 0,
		"PRS-GEO-2_no_mesh_instance_3d",
		"Found " + str(count) + " MeshInstance3D node(s); expected 0 (no pre-built geometry)"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-RSA-1: RunSceneAssembler script path is
#            res://scripts/system/run_scene_assembler.gd — PRS-NODE-3
# ---------------------------------------------------------------------------
func test_prs_rsa_1_run_scene_assembler_script_path() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var rsa: Node = root.get_node_or_null("RunSceneAssembler")
	if rsa == null:
		_fail_test("PRS-RSA-1_run_scene_assembler_script_path", "RunSceneAssembler not found")
		root.free()
		return
	var script_res: Resource = rsa.get_script()
	if script_res == null:
		_fail_test("PRS-RSA-1_run_scene_assembler_script_path", "RunSceneAssembler has no script attached")
		root.free()
		return
	_assert_eq_str(
		script_res.resource_path,
		"res://scripts/system/run_scene_assembler.gd",
		"PRS-RSA-1_run_scene_assembler_script_path"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-DRC-1: DeathRestartCoordinator script path is
#            res://scripts/system/death_restart_coordinator.gd — PRS-NODE-4
# ---------------------------------------------------------------------------
func test_prs_drc_1_death_restart_coordinator_script_path() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	if drc == null:
		_fail_test("PRS-DRC-1_death_restart_coordinator_script_path", "DeathRestartCoordinator not found")
		root.free()
		return
	var script_res: Resource = drc.get_script()
	if script_res == null:
		_fail_test("PRS-DRC-1_death_restart_coordinator_script_path", "DeathRestartCoordinator has no script attached")
		root.free()
		return
	_assert_eq_str(
		script_res.resource_path,
		"res://scripts/system/death_restart_coordinator.gd",
		"PRS-DRC-1_death_restart_coordinator_script_path"
	)
	root.free()


# ---------------------------------------------------------------------------
# PRS-IIH-1: InfectionInteractionHandler script path is
#            res://scripts/infection/infection_interaction_handler.gd — PRS-NODE-5
# ---------------------------------------------------------------------------
func test_prs_iih_1_infection_interaction_handler_script_path() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var iih: Node = root.get_node_or_null("InfectionInteractionHandler")
	if iih == null:
		_fail_test("PRS-IIH-1_infection_interaction_handler_script_path", "InfectionInteractionHandler not found")
		root.free()
		return
	var script_res: Resource = iih.get_script()
	if script_res == null:
		_fail_test("PRS-IIH-1_infection_interaction_handler_script_path", "InfectionInteractionHandler has no script attached")
		root.free()
		return
	_assert_eq_str(
		script_res.resource_path,
		"res://scripts/infection/infection_interaction_handler.gd",
		"PRS-IIH-1_infection_interaction_handler_script_path"
	)
	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_procedural_run.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_prs_load_1_scene_loads_as_packed_scene()
	test_prs_load_2_scene_instantiates()
	test_prs_load_3_scene_frees_without_error()
	test_prs_root_1_root_class_is_node3d()
	test_prs_root_2_root_name_is_procedural_run()
	test_prs_root_3_root_has_no_script()
	test_prs_root_4_root_has_exactly_5_children()
	test_prs_child_1_player3d_exists()
	test_prs_child_2_spawn_position_exists()
	test_prs_child_3_run_scene_assembler_exists()
	test_prs_child_4_death_restart_coordinator_exists()
	test_prs_child_5_infection_interaction_handler_exists()
	test_prs_player_1_player3d_position()
	test_prs_player_2_player3d_in_player_group()
	test_prs_spawn_1_spawn_position_is_marker3d()
	test_prs_spawn_2_spawn_position_coordinates()
	test_prs_spawn_3_spawn_position_has_no_script()
	test_prs_wire_1_drc_player_nodepath()
	test_prs_wire_2_drc_spawn_position_nodepath()
	test_prs_wire_3_drc_infection_handler_nodepath()
	test_prs_geo_1_no_static_body_3d()
	test_prs_geo_2_no_mesh_instance_3d()
	test_prs_rsa_1_run_scene_assembler_script_path()
	test_prs_drc_1_death_restart_coordinator_script_path()
	test_prs_iih_1_infection_interaction_handler_script_path()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
