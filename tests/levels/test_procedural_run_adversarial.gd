#
# test_procedural_run_adversarial.gd
#
# Adversarial behavioral tests for the procedural_run.tscn canonical M6 entry point.
# Spec:   agent_context/agents/2_spec/procedural_run_scene_spec.md (Adversarial Suite)
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/FEAT-20260326-procedural-run-scene.md
#
# All tests are headless-safe: ResourceLoader.load() + PackedScene.instantiate() +
# node property reads + root.free(). Source-code inspection via FileAccess.
# No await, no physics tick, no SceneTree required.
#
# Red phase:  scene file does not yet exist — scene-dependent tests report FAIL.
#             Script-source tests pass independently as long as the .gd files exist.
# Green phase: all assertions pass after Generalist Agent authors the scene file.
#
# Spec requirement traceability:
#   ADV-PRS-01 → PRS-NODE-3   (RSA is direct child — parent.name == "ProceduralRun")
#   ADV-PRS-02 → PRS-NODE-4   (DRC is direct child — parent.name == "ProceduralRun")
#   ADV-PRS-03 → PRS-NODE-5   (IIH is direct child — parent.name == "ProceduralRun")
#   ADV-PRS-04 → PRS-SPAWN-2  (SpawnPosition.position.y >= 0.9, above floor)
#   ADV-PRS-05 → PRS-PLAYER-1 + PRS-SPAWN-2 (Player Y matches SpawnPosition Y ±0.01)
#   ADV-PRS-06 → PRS-SCENE-6  (no node named "ContainmentHall01" anywhere)
#   ADV-PRS-07 → PRS-NODE constraint (no node named "InfectionUI" in tree)
#   ADV-PRS-08 → PRS-NODE constraint (no node named "RespawnZone" in tree)
#   ADV-PRS-09 → PRS-RUNTIME-4 (RSA source does not contain "reload_current_scene")
#   ADV-PRS-10 → PRS-RUNTIME-4 (DRC source does not contain "reload_current_scene")
#   ADV-PRS-11 → PRS-SCENE-7  (double load/instantiate/free cycle — no crash)
#   ADV-PRS-12 → PRS-SCENE-6 intent (no WorldEnvironment or DirectionalLight3D in tree)
#
# Extended adversarial tests (ADV-PRS-13 through ADV-PRS-24) expose gaps found by
# Test Breaker Agent. Each test is preceded by a comment explaining the vulnerability
# it closes.
#
#   ADV-PRS-13 → PRS-NODE-3   (RSA base class == "Node", not "Node3D")
#   ADV-PRS-14 → PRS-NODE-4   (DRC base class == "Node", not "Node3D")
#   ADV-PRS-15 → PRS-NODE-5   (IIH base class == "Node", not "Node3D")
#   ADV-PRS-16 → PRS-PLAYER-2 (Player3D base class == "CharacterBody3D", not just Node3D)
#   ADV-PRS-17 → PRS-NODE-7   (SpawnPosition parent.name == "ProceduralRun" — depth check)
#   ADV-PRS-18 → PRS-NODE-6   (Player3D parent.name == "ProceduralRun" — depth check)
#   ADV-PRS-19 → PRS-NFR-3    (project.godot run/main_scene does not reference procedural_run)
#   ADV-PRS-20 → PRS-SCENE-6  (no CSGBox3D — geometry gap)
#   ADV-PRS-21 → PRS-SCENE-6  (no CSGCombiner3D — geometry gap)
#   ADV-PRS-22 → PRS-SCENE-6  (no GridMap — geometry gap)
#   ADV-PRS-23 → PRS-PLAYER-3 / PRS-NFR-4 (player_3d.tscn root has no position override)
#   ADV-PRS-24 → PRS-NODE-3/4/5 (RSA/DRC/IIH get_parent() == root object, not name match)
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - Test IDs use ADV-PRS-* prefix; unique across all existing test namespaces.

extends Object

# ---------------------------------------------------------------------------
# Scene and script paths under test
# ---------------------------------------------------------------------------

const SCENE_PATH: String = "res://scenes/levels/procedural_run.tscn"

const RSA_SCRIPT_PATH: String = "res://scripts/system/run_scene_assembler.gd"
const DRC_SCRIPT_PATH: String = "res://scripts/system/death_restart_coordinator.gd"

# Substring that must NOT appear in any coordinator or assembler script source.
const FORBIDDEN_RELOAD: String = "reload_current_scene"

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


# Recursive name search: return true if any node in the subtree has the given name.
func _tree_contains_name(node: Node, target_name: String) -> bool:
	if node == null:
		return false
	if node.name == target_name:
		return true
	for i in range(node.get_child_count()):
		if _tree_contains_name(node.get_child(i), target_name):
			return true
	return false


# Recursive class search: count all nodes whose get_class() matches.
func _count_nodes_of_class(node: Node, class_name_str: String) -> int:
	if node == null:
		return 0
	var count: int = 0
	if node.get_class() == class_name_str:
		count += 1
	for i in range(node.get_child_count()):
		count += _count_nodes_of_class(node.get_child(i), class_name_str)
	return count


# Read a .gd file's source text from disk. Returns "" if file is missing.
func _read_script_source(fs_path: String) -> String:
	var f: FileAccess = FileAccess.open(fs_path, FileAccess.READ)
	if f == null:
		return ""
	var text: String = f.get_as_text()
	f.close()
	return text


# Convert a res:// path to an absolute filesystem path for FileAccess.
# The project root is determined by ProjectSettings.globalize_path.
func _res_to_fs(res_path: String) -> String:
	return ProjectSettings.globalize_path(res_path)


# ---------------------------------------------------------------------------
# ADV-PRS-01: RunSceneAssembler is a direct child (parent.name == "ProceduralRun")
#             — PRS-NODE-3
# ---------------------------------------------------------------------------
func test_adv_prs_01_rsa_is_direct_child() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var rsa: Node = root.get_node_or_null("RunSceneAssembler")
	if rsa == null:
		_fail_test("ADV-PRS-01_rsa_is_direct_child", "RunSceneAssembler not found under root")
		root.free()
		return
	_assert_true(
		rsa.get_parent() != null and rsa.get_parent().name == "ProceduralRun",
		"ADV-PRS-01_rsa_is_direct_child",
		"RunSceneAssembler parent name is \"" + (rsa.get_parent().name if rsa.get_parent() != null else "<null>") + "\"; expected \"ProceduralRun\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-02: DeathRestartCoordinator is a direct child (parent.name == "ProceduralRun")
#             — PRS-NODE-4
# ---------------------------------------------------------------------------
func test_adv_prs_02_drc_is_direct_child() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	if drc == null:
		_fail_test("ADV-PRS-02_drc_is_direct_child", "DeathRestartCoordinator not found under root")
		root.free()
		return
	_assert_true(
		drc.get_parent() != null and drc.get_parent().name == "ProceduralRun",
		"ADV-PRS-02_drc_is_direct_child",
		"DeathRestartCoordinator parent name is \"" + (drc.get_parent().name if drc.get_parent() != null else "<null>") + "\"; expected \"ProceduralRun\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-03: InfectionInteractionHandler is a direct child (parent.name == "ProceduralRun")
#             — PRS-NODE-5
# ---------------------------------------------------------------------------
func test_adv_prs_03_iih_is_direct_child() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var iih: Node = root.get_node_or_null("InfectionInteractionHandler")
	if iih == null:
		_fail_test("ADV-PRS-03_iih_is_direct_child", "InfectionInteractionHandler not found under root")
		root.free()
		return
	_assert_true(
		iih.get_parent() != null and iih.get_parent().name == "ProceduralRun",
		"ADV-PRS-03_iih_is_direct_child",
		"InfectionInteractionHandler parent name is \"" + (iih.get_parent().name if iih.get_parent() != null else "<null>") + "\"; expected \"ProceduralRun\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-04: SpawnPosition.position.y >= 0.9 (above floor top surface)
#             — PRS-SPAWN-2
# ---------------------------------------------------------------------------
func test_adv_prs_04_spawn_position_y_above_floor() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var spawn: Node = root.get_node_or_null("SpawnPosition")
	if spawn == null:
		_fail_test("ADV-PRS-04_spawn_position_y_above_floor", "SpawnPosition not found")
		root.free()
		return
	if not spawn is Node3D:
		_fail_test("ADV-PRS-04_spawn_position_y_above_floor", "SpawnPosition is not Node3D")
		root.free()
		return
	var y: float = (spawn as Node3D).position.y
	_assert_true(
		y >= 0.9,
		"ADV-PRS-04_spawn_position_y_above_floor",
		"SpawnPosition.position.y == " + str(y) + "; expected >= 0.9 (above floor top)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-05: Player3D position Y matches SpawnPosition Y within ±0.01
#             — PRS-PLAYER-1 + PRS-SPAWN-2
# ---------------------------------------------------------------------------
func test_adv_prs_05_player_y_matches_spawn_y() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var player: Node = root.get_node_or_null("Player3D")
	var spawn: Node = root.get_node_or_null("SpawnPosition")
	if player == null or spawn == null:
		_fail_test(
			"ADV-PRS-05_player_y_matches_spawn_y",
			"Player3D or SpawnPosition not found — cannot compare Y positions"
		)
		root.free()
		return
	if not player is Node3D or not spawn is Node3D:
		_fail_test("ADV-PRS-05_player_y_matches_spawn_y", "Player3D or SpawnPosition is not Node3D")
		root.free()
		return
	var player_y: float = (player as Node3D).position.y
	var spawn_y: float = (spawn as Node3D).position.y
	_assert_true(
		absf(player_y - spawn_y) < POS_TOL,
		"ADV-PRS-05_player_y_matches_spawn_y",
		"abs(Player3D.position.y - SpawnPosition.position.y) == " + str(absf(player_y - spawn_y)) + "; expected < " + str(POS_TOL)
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-06: No node named "ContainmentHall01" anywhere in the tree
#             — PRS-SCENE-6 (scene is not a pre-built level)
# ---------------------------------------------------------------------------
func test_adv_prs_06_no_containment_hall_node() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_true(
		not _tree_contains_name(root, "ContainmentHall01"),
		"ADV-PRS-06_no_containment_hall_node",
		"Found a node named \"ContainmentHall01\" in the tree; this is a pre-built geometry scene artefact"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-07: No node named "InfectionUI" in the tree
#             — PRS-NODE constraint (InfectionUI is not part of this scene)
# ---------------------------------------------------------------------------
func test_adv_prs_07_no_infection_ui_node() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_true(
		not _tree_contains_name(root, "InfectionUI"),
		"ADV-PRS-07_no_infection_ui_node",
		"Found a node named \"InfectionUI\" in the tree; it must not be present in procedural_run.tscn"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-08: No node named "RespawnZone" in the tree
#             — PRS-NODE constraint (RespawnZone belongs to containment_hall_01)
# ---------------------------------------------------------------------------
func test_adv_prs_08_no_respawn_zone_node() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_true(
		not _tree_contains_name(root, "RespawnZone"),
		"ADV-PRS-08_no_respawn_zone_node",
		"Found a node named \"RespawnZone\" in the tree; it must not be present in procedural_run.tscn"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-09: RunSceneAssembler source does not contain "reload_current_scene"
#             — PRS-RUNTIME-4
# ---------------------------------------------------------------------------
func test_adv_prs_09_rsa_no_reload_current_scene() -> void:
	var fs_path: String = _res_to_fs(RSA_SCRIPT_PATH)
	var source: String = _read_script_source(fs_path)
	if source == "":
		_fail_test(
			"ADV-PRS-09_rsa_no_reload_current_scene",
			"Could not read script source at " + fs_path + " — file missing or unreadable"
		)
		return
	_assert_true(
		not (FORBIDDEN_RELOAD in source),
		"ADV-PRS-09_rsa_no_reload_current_scene",
		"run_scene_assembler.gd contains \"" + FORBIDDEN_RELOAD + "\"; death-restart must be in-place only"
	)


# ---------------------------------------------------------------------------
# ADV-PRS-10: DeathRestartCoordinator source does not contain "reload_current_scene"
#             — PRS-RUNTIME-4
# ---------------------------------------------------------------------------
func test_adv_prs_10_drc_no_reload_current_scene() -> void:
	var fs_path: String = _res_to_fs(DRC_SCRIPT_PATH)
	var source: String = _read_script_source(fs_path)
	if source == "":
		_fail_test(
			"ADV-PRS-10_drc_no_reload_current_scene",
			"Could not read script source at " + fs_path + " — file missing or unreadable"
		)
		return
	_assert_true(
		not (FORBIDDEN_RELOAD in source),
		"ADV-PRS-10_drc_no_reload_current_scene",
		"death_restart_coordinator.gd contains \"" + FORBIDDEN_RELOAD + "\"; death-restart must be in-place only"
	)


# ---------------------------------------------------------------------------
# ADV-PRS-11: Double load/instantiate/free cycle — no crash (no singleton state)
#             — PRS-SCENE-7
# ---------------------------------------------------------------------------
func test_adv_prs_11_double_load_free_cycle() -> void:
	# First cycle.
	var packed1: PackedScene = ResourceLoader.load(SCENE_PATH) as PackedScene
	if packed1 == null:
		_fail_test(
			"ADV-PRS-11_double_load_free_cycle",
			"First load returned null — scene file absent"
		)
		return
	var inst1: Node = packed1.instantiate()
	if inst1 == null:
		_fail_test("ADV-PRS-11_double_load_free_cycle", "First instantiate() returned null")
		return
	inst1.free()

	# Second cycle — must succeed independently of the first.
	var packed2: PackedScene = ResourceLoader.load(SCENE_PATH) as PackedScene
	if packed2 == null:
		_fail_test("ADV-PRS-11_double_load_free_cycle", "Second load returned null after first free")
		return
	var inst2: Node = packed2.instantiate()
	if inst2 == null:
		_fail_test("ADV-PRS-11_double_load_free_cycle", "Second instantiate() returned null after first free")
		return
	inst2.free()

	_pass_test("ADV-PRS-11_double_load_free_cycle")


# ---------------------------------------------------------------------------
# ADV-PRS-12: No WorldEnvironment or DirectionalLight3D anywhere in the tree
#             — PRS-SCENE-6 intent (rooms provide environment, not the container scene)
# ---------------------------------------------------------------------------
func test_adv_prs_12_no_world_environment_or_directional_light() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var env_count: int = _count_nodes_of_class(root, "WorldEnvironment")
	var light_count: int = _count_nodes_of_class(root, "DirectionalLight3D")
	_assert_true(
		env_count == 0,
		"ADV-PRS-12_no_world_environment",
		"Found " + str(env_count) + " WorldEnvironment node(s); expected 0 (rooms provide environment)"
	)
	_assert_true(
		light_count == 0,
		"ADV-PRS-12_no_directional_light_3d",
		"Found " + str(light_count) + " DirectionalLight3D node(s); expected 0 (rooms provide lighting)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-13: RunSceneAssembler node base class is "Node", not "Node3D"
#
# Vulnerability: implementer could attach run_scene_assembler.gd to a Node3D
# node instead of a plain Node. All existing tests (script path, parent name)
# would still pass. The spec node tree explicitly shows [Node] for RSA.
# get_class() on a scripted Node returns "Node"; on a Node3D it returns "Node3D".
# ---------------------------------------------------------------------------
func test_adv_prs_13_rsa_base_class_is_node() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var rsa: Node = root.get_node_or_null("RunSceneAssembler")
	if rsa == null:
		_fail_test("ADV-PRS-13_rsa_base_class_is_node", "RunSceneAssembler not found")
		root.free()
		return
	_assert_true(
		rsa.get_class() == "Node",
		"ADV-PRS-13_rsa_base_class_is_node",
		"RunSceneAssembler.get_class() == \"" + rsa.get_class() + "\"; expected \"Node\" (spec tree shows [Node])"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-14: DeathRestartCoordinator node base class is "Node", not "Node3D"
#
# Vulnerability: same as ADV-PRS-13. DRC only needs a process loop; attaching
# to Node3D bloats the node with 3D transform state and is architecturally wrong.
# ---------------------------------------------------------------------------
func test_adv_prs_14_drc_base_class_is_node() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	if drc == null:
		_fail_test("ADV-PRS-14_drc_base_class_is_node", "DeathRestartCoordinator not found")
		root.free()
		return
	_assert_true(
		drc.get_class() == "Node",
		"ADV-PRS-14_drc_base_class_is_node",
		"DeathRestartCoordinator.get_class() == \"" + drc.get_class() + "\"; expected \"Node\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-15: InfectionInteractionHandler node base class is "Node", not "Node3D"
#
# Vulnerability: same as ADV-PRS-13/14. IIH is a pure gameplay wiring node;
# there is no reason for it to be a Node3D and the spec says [Node].
# ---------------------------------------------------------------------------
func test_adv_prs_15_iih_base_class_is_node() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var iih: Node = root.get_node_or_null("InfectionInteractionHandler")
	if iih == null:
		_fail_test("ADV-PRS-15_iih_base_class_is_node", "InfectionInteractionHandler not found")
		root.free()
		return
	_assert_true(
		iih.get_class() == "Node",
		"ADV-PRS-15_iih_base_class_is_node",
		"InfectionInteractionHandler.get_class() == \"" + iih.get_class() + "\"; expected \"Node\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-16: Player3D node base class is "CharacterBody3D"
#
# Vulnerability: PRS-PLAYER-2 confirms the "player" group membership but never
# calls get_class(). An implementer who inlines a raw Node3D named "Player3D"
# and manually adds it to the "player" group would pass the existing tests.
# The Player3D must be an instance of player_3d.tscn whose root is CharacterBody3D.
# ---------------------------------------------------------------------------
func test_adv_prs_16_player3d_base_class_is_character_body_3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var player: Node = root.get_node_or_null("Player3D")
	if player == null:
		_fail_test("ADV-PRS-16_player3d_base_class_is_character_body_3d", "Player3D not found")
		root.free()
		return
	_assert_true(
		player.get_class() == "CharacterBody3D",
		"ADV-PRS-16_player3d_base_class_is_character_body_3d",
		"Player3D.get_class() == \"" + player.get_class() + "\"; expected \"CharacterBody3D\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-17: SpawnPosition is a direct child of root (parent object identity)
#
# Vulnerability: ADV-PRS-01/02/03 check parent.name for RSA/DRC/IIH but there
# is no equivalent explicit depth check for SpawnPosition. If an implementer
# nests SpawnPosition under another node (e.g. under Player3D), the node would
# not be found by root.get_node_or_null("SpawnPosition"), so PRS-CHILD-2 would
# fail. However, an explicit parent-name assertion mirrors the pattern of
# ADV-01/02/03 and makes the architectural intent unmistakable.
# ---------------------------------------------------------------------------
func test_adv_prs_17_spawn_position_is_direct_child() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var spawn: Node = root.get_node_or_null("SpawnPosition")
	if spawn == null:
		_fail_test("ADV-PRS-17_spawn_position_is_direct_child", "SpawnPosition not found under root")
		root.free()
		return
	_assert_true(
		spawn.get_parent() != null and spawn.get_parent().name == "ProceduralRun",
		"ADV-PRS-17_spawn_position_is_direct_child",
		"SpawnPosition parent name is \"" + (spawn.get_parent().name if spawn.get_parent() != null else "<null>") + "\"; expected \"ProceduralRun\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-18: Player3D is a direct child of root (parent object identity)
#
# Vulnerability: same gap as ADV-PRS-17 — no explicit parent-name assertion
# exists for Player3D. A Player3D nested under a grouping node named
# "ProceduralRun" (duplicate name) could theoretically fool a shallow name
# check, though Godot's sibling uniqueness prevents that in practice. The
# parent-name assertion is the canonical pattern for this spec.
# ---------------------------------------------------------------------------
func test_adv_prs_18_player3d_is_direct_child() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var player: Node = root.get_node_or_null("Player3D")
	if player == null:
		_fail_test("ADV-PRS-18_player3d_is_direct_child", "Player3D not found under root")
		root.free()
		return
	_assert_true(
		player.get_parent() != null and player.get_parent().name == "ProceduralRun",
		"ADV-PRS-18_player3d_is_direct_child",
		"Player3D parent name is \"" + (player.get_parent().name if player.get_parent() != null else "<null>") + "\"; expected \"ProceduralRun\""
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-19: project.godot run/main_scene does NOT point to procedural_run.tscn
#
# Vulnerability: PRS-NFR-3 says project.godot must not be changed, but there
# is no test for it. An implementer who sets procedural_run.tscn as the main
# scene would break the established sandbox test entry point. This is a
# source-file inspection test (FileAccess) identical in pattern to ADV-09/10.
# ---------------------------------------------------------------------------
func test_adv_prs_19_project_godot_main_scene_unchanged() -> void:
	var fs_path: String = _res_to_fs("res://project.godot")
	var source: String = _read_script_source(fs_path)
	if source == "":
		_fail_test(
			"ADV-PRS-19_project_godot_main_scene_unchanged",
			"Could not read project.godot at " + fs_path
		)
		return
	_assert_true(
		not ("procedural_run" in source.to_lower() and "run/main_scene" in source),
		"ADV-PRS-19_project_godot_main_scene_unchanged",
		"project.godot run/main_scene appears to reference procedural_run; PRS-NFR-3 forbids this"
	)


# ---------------------------------------------------------------------------
# ADV-PRS-20: No CSGBox3D anywhere in the scene tree
#
# Vulnerability: PRS-GEO-1/2 only guard against StaticBody3D and MeshInstance3D.
# PRS-SCENE-6 lists CSGBox3D as a forbidden geometry type. An implementer who
# uses a CSGBox3D floor placeholder would pass PRS-GEO-1 and PRS-GEO-2.
# ---------------------------------------------------------------------------
func test_adv_prs_20_no_csg_box_3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var count: int = _count_nodes_of_class(root, "CSGBox3D")
	_assert_true(
		count == 0,
		"ADV-PRS-20_no_csg_box_3d",
		"Found " + str(count) + " CSGBox3D node(s); no pre-built geometry is permitted (PRS-SCENE-6)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-21: No CSGCombiner3D anywhere in the scene tree
#
# Vulnerability: same gap as ADV-PRS-20. CSGCombiner3D is listed in PRS-SCENE-6
# but has no corresponding test.
# ---------------------------------------------------------------------------
func test_adv_prs_21_no_csg_combiner_3d() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var count: int = _count_nodes_of_class(root, "CSGCombiner3D")
	_assert_true(
		count == 0,
		"ADV-PRS-21_no_csg_combiner_3d",
		"Found " + str(count) + " CSGCombiner3D node(s); no pre-built geometry is permitted (PRS-SCENE-6)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-22: No GridMap anywhere in the scene tree
#
# Vulnerability: same gap as ADV-PRS-20/21. GridMap is listed in PRS-SCENE-6
# but has no test. A GridMap-based floor proxy would pass all existing geometry
# checks.
# ---------------------------------------------------------------------------
func test_adv_prs_22_no_grid_map() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var count: int = _count_nodes_of_class(root, "GridMap")
	_assert_true(
		count == 0,
		"ADV-PRS-22_no_grid_map",
		"Found " + str(count) + " GridMap node(s); no pre-built geometry is permitted (PRS-SCENE-6)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-PRS-23: player_3d.tscn root node has no hard-coded position override
#
# Vulnerability: PRS-PLAYER-3 in the spec says player_3d.tscn must not be
# modified. An implementer who edits player_3d.tscn to set position = Vector3(0,1,0)
# on its root node would satisfy the position test (PRS-PLAYER-1) but violate
# PRS-NFR-4 (no existing files modified). This test reads the .tscn source and
# checks that the Player3D root node declaration does not contain a position
# property override. The root node line in player_3d.tscn is:
#   [node name="Player3D" type="CharacterBody3D" groups=["player", "Player"]]
# A position override would appear as "position = Vector3" on the following
# lines before the next [node] section. The test checks the root node block only.
# ---------------------------------------------------------------------------
func test_adv_prs_23_player3d_tscn_root_has_no_position_override() -> void:
	var fs_path: String = _res_to_fs("res://scenes/player/player_3d.tscn")
	var source: String = _read_script_source(fs_path)
	if source == "":
		_fail_test(
			"ADV-PRS-23_player3d_tscn_root_has_no_position_override",
			"Could not read player_3d.tscn at " + fs_path
		)
		return
	# Extract the root node block: text from the first [node ...] up to (but not
	# including) the second [node ...]. The root node is always first in a .tscn.
	var first_node_idx: int = source.find("[node ")
	if first_node_idx == -1:
		_fail_test(
			"ADV-PRS-23_player3d_tscn_root_has_no_position_override",
			"player_3d.tscn has no [node ...] section — file may be corrupt"
		)
		return
	var second_node_idx: int = source.find("[node ", first_node_idx + 1)
	var root_block: String
	if second_node_idx == -1:
		root_block = source.substr(first_node_idx)
	else:
		root_block = source.substr(first_node_idx, second_node_idx - first_node_idx)
	_assert_true(
		not ("position = Vector3" in root_block),
		"ADV-PRS-23_player3d_tscn_root_has_no_position_override",
		"player_3d.tscn root node block contains \"position = Vector3\"; the source file must not be modified (PRS-PLAYER-3 / PRS-NFR-4)"
	)


# ---------------------------------------------------------------------------
# ADV-PRS-24: RSA, DRC, and IIH get_parent() returns the same object as root
#
# Vulnerability: ADV-PRS-01/02/03/17/18 verify parent.name == "ProceduralRun"
# (string comparison). In theory two distinct nodes could share a name. This
# test verifies object identity: each of the three system nodes' get_parent()
# IS the same object as the instantiated root (reference equality). This closes
# the mutation where a wrapping group node is also named "ProceduralRun".
# ---------------------------------------------------------------------------
func test_adv_prs_24_system_nodes_parent_is_root_object() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var rsa: Node = root.get_node_or_null("RunSceneAssembler")
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	var iih: Node = root.get_node_or_null("InfectionInteractionHandler")
	if rsa == null or drc == null or iih == null:
		_fail_test(
			"ADV-PRS-24_system_nodes_parent_is_root_object",
			"One or more system nodes not found (RSA/DRC/IIH) — cannot compare parent references"
		)
		root.free()
		return
	_assert_true(
		rsa.get_parent() == root,
		"ADV-PRS-24_rsa_parent_is_root_object",
		"RunSceneAssembler.get_parent() is not the same object as root"
	)
	_assert_true(
		drc.get_parent() == root,
		"ADV-PRS-24_drc_parent_is_root_object",
		"DeathRestartCoordinator.get_parent() is not the same object as root"
	)
	_assert_true(
		iih.get_parent() == root,
		"ADV-PRS-24_iih_parent_is_root_object",
		"InfectionInteractionHandler.get_parent() is not the same object as root"
	)
	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_procedural_run_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_prs_01_rsa_is_direct_child()
	test_adv_prs_02_drc_is_direct_child()
	test_adv_prs_03_iih_is_direct_child()
	test_adv_prs_04_spawn_position_y_above_floor()
	test_adv_prs_05_player_y_matches_spawn_y()
	test_adv_prs_06_no_containment_hall_node()
	test_adv_prs_07_no_infection_ui_node()
	test_adv_prs_08_no_respawn_zone_node()
	test_adv_prs_09_rsa_no_reload_current_scene()
	test_adv_prs_10_drc_no_reload_current_scene()
	test_adv_prs_11_double_load_free_cycle()
	test_adv_prs_12_no_world_environment_or_directional_light()
	test_adv_prs_13_rsa_base_class_is_node()
	test_adv_prs_14_drc_base_class_is_node()
	test_adv_prs_15_iih_base_class_is_node()
	test_adv_prs_16_player3d_base_class_is_character_body_3d()
	test_adv_prs_17_spawn_position_is_direct_child()
	test_adv_prs_18_player3d_is_direct_child()
	test_adv_prs_19_project_godot_main_scene_unchanged()
	test_adv_prs_20_no_csg_box_3d()
	test_adv_prs_21_no_csg_combiner_3d()
	test_adv_prs_22_no_grid_map()
	test_adv_prs_23_player3d_tscn_root_has_no_position_override()
	test_adv_prs_24_system_nodes_parent_is_root_object()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
