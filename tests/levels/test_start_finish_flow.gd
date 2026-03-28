#
# test_start_finish_flow.gd
#
# Start→Finish flow integration checks for Milestone 4 Prototype Level.
#
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/start_finish_flow.md
#
# Headless safety:
# - No physics tick, no await, no input simulation, no signal emission.
# - Scene is instantiated but not added to the SceneTree (unless a test explicitly
#   requires _ready(), which this file intentionally avoids).
#
# What this test suite CAN verify from the available spec:
# - The level scene contains all scope items (mutation tease, fusion opportunity,
#   light skill check, mini-boss) and the start/end markers (SpawnPosition, LevelExit).
# - Cross-zone progression order is consistent along the X axis.
# - `LevelExit` is wired to call `level_complete` (via script source_code or a
#   compiled-method fallback).
#
# What this suite cannot verify (spec gap):
# - Actual human completion time (6–8 minutes) and actual input-driven playthrough.
#   Headless tests in this repo are intentionally structural/deterministic.
#
extends "res://tests/utils/test_utils.gd"

const LEVEL_SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"
const GAME_UI_PATH: String = "res://scenes/ui/game_ui.tscn"

var _pass_count: int = 0
var _fail_count: int = 0

func _load_packed_scene(scene_path: String) -> PackedScene:
	return load(scene_path) as PackedScene

func _load_level_scene() -> Node:
	var packed: PackedScene = _load_packed_scene(LEVEL_SCENE_PATH)
	_assert_true(packed != null, "stf_scene_load_guard", "ResourceLoader.load returned null for " + LEVEL_SCENE_PATH)
	if packed == null:
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("stf_scene_instantiate_guard", "instantiate() returned null for " + LEVEL_SCENE_PATH)
		return null
	return inst

func _load_game_ui() -> Node:
	var packed: PackedScene = _load_packed_scene(GAME_UI_PATH)
	if packed == null:
		_fail("stf_game_ui_load_guard", "ResourceLoader.load returned null for " + GAME_UI_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("stf_game_ui_instantiate_guard", "instantiate() returned null for " + GAME_UI_PATH)
		return null
	return inst

func _read_res_file_as_text(res_path: String) -> String:
	# Reads a res:// file deterministically for inline-script parsing.
	var f: FileAccess = FileAccess.open(res_path, FileAccess.READ)
	if f == null:
		return ""
	var content: String = f.get_as_text()
	f.close()
	return content

func _get_first_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null

func _require_box_shape_collision_shape(node: Node, test_name_prefix: String) -> BoxShape3D:
	var col: CollisionShape3D = _get_first_collision_shape(node)
	if col == null:
		_fail(test_name_prefix + "_has_collision_shape", "Missing CollisionShape3D child on " + str(node))
		return null
	if col.shape == null:
		_fail(test_name_prefix + "_shape_nonnull", "CollisionShape3D.shape is null on " + str(node))
		return null
	if not (col.shape is BoxShape3D):
		_fail(
			test_name_prefix + "_shape_is_box",
			"CollisionShape3D.shape is " + col.shape.get_class() + ", expected BoxShape3D"
		)
		return null
	return col.shape as BoxShape3D

func _world_x_edges_for_box(node: Node, test_name_prefix: String) -> Dictionary:
	# Returns {left: float, right: float}
	var box: BoxShape3D = _require_box_shape_collision_shape(node, test_name_prefix)
	if box == null:
		return {}

	var col: CollisionShape3D = _get_first_collision_shape(node)
	if col == null:
		return {}

	var n3: Node3D = node as Node3D
	if n3 == null:
		_fail(test_name_prefix + "_node_is_node3d", "Node is " + node.get_class() + ", expected Node3D to read transform position")
		return {}
	var center_x: float = n3.position.x + col.position.x
	var half_w: float = box.size.x * 0.5
	return {
		"left": center_x - half_w,
		"right": center_x + half_w,
	}

func _require_node(root: Node, node_name: String, test_name: String, expected_class: String = "") -> Node:
	var node: Node = root.get_node_or_null(node_name)
	_assert_true(node != null, test_name, node_name + " node not found in level scene")
	if node == null:
		return null
	if expected_class != "":
		_assert_true(node.get_class() == expected_class, test_name + "_class", "Expected class " + expected_class + ", got " + node.get_class())
	return node

func test_stf_loads_and_has_core_nodes() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# Start marker + player.
	_require_node(root, "SpawnPosition", "stf_spawn_position_exists", "Marker3D")
	_require_node(root, "Player3D", "stf_player3d_exists", "CharacterBody3D")

	# UI and environment (human-playable editor requirement).
	_assert_true(root.get_node_or_null("InfectionUI") != null, "stf_infection_ui_exists", "InfectionUI node missing (game_ui.tscn expected to be instanced)")
	_assert_true(root.get_node_or_null("WorldEnvironment") != null, "stf_world_environment_exists", "WorldEnvironment node missing")
	_assert_true(root.get_node_or_null("DirectionalLight3D") != null, "stf_directional_light_exists", "DirectionalLight3D node missing")

	# Integration: all scope items and end marker exist.
	var required_nodes: Array[String] = [
		# Mutation tease
		"MutationTeaseFloor",
		"MutationTeasePlatform",
		"EnemyMutationTease",
		# Fusion opportunity
		"FusionFloor",
		"FusionPlatformA",
		"FusionPlatformB",
		"EnemyFusionA",
		"EnemyFusionB",
		"InfectionInteractionHandler",
		# Light skill check
		"SkillCheckFloorBase",
		"SkillCheckPlatform1",
		"SkillCheckPlatform2",
		"SkillCheckPlatform3",
		"RespawnZone",
		# Mini-boss
		"MiniBossFloor",
		"EnemyMiniBoss",
		"ExitFloor",
		# End marker
		"LevelExit",
	]
	for node_name in required_nodes:
		_assert_true(root.get_node_or_null(node_name) != null, "stf_required_" + node_name.to_lower() + "_exists", "Required node '" + node_name + "' missing")

	# Game UI should be loadable (required for visible/signposting).
	var ui: Node = _load_game_ui()
	if ui != null:
		_assert_true(ui.get_class() == "CanvasLayer", "stf_game_ui_is_canvas_layer", "game_ui.tscn root is " + ui.get_class() + ", expected CanvasLayer")
		ui.free()

	root.free()

func test_stf_cross_zone_progression_ordering() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# Ensure adjacency/order along X ensures clear intended traversal:
	# - MutationTeaseFloor precedes FusionFloor.
	# - SkillCheckPlatform1 begins after FusionPlatformB.
	# - MiniBossFloor begins after SkillCheckPlatform3.
	# - ExitFloor begins after MiniBossFloor's right edge.
	#
	# These invariants are the strictest defensible "flow direction/signposting"
	# checks we can do without input-driven playthrough.

	var mutation_tease_floor: Node = root.get_node_or_null("MutationTeaseFloor")
	var fusion_floor: Node = root.get_node_or_null("FusionFloor")
	_assert_true(mutation_tease_floor != null, "stf_order_mutation_tease_floor_exists")
	_assert_true(fusion_floor != null, "stf_order_fusion_floor_exists")
	if mutation_tease_floor == null or fusion_floor == null:
		root.free()
		return

	var edges_m: Dictionary = _world_x_edges_for_box(mutation_tease_floor, "stf_mutation_tease_floor")
	var edges_f: Dictionary = _world_x_edges_for_box(fusion_floor, "stf_fusion_floor")
	_assert_true(edges_m.size() > 0 and edges_f.size() > 0, "stf_order_mutation_fusion_edges_computed", "Failed to compute box edges for MutationTeaseFloor/FusionFloor")
	if edges_m.size() == 0 or edges_f.size() == 0:
		root.free()
		return

	_assert_true(
		edges_m["right"] <= edges_f["left"],
		"stf_order_mutation_tease_precedes_fusion",
		"MutationTeaseFloor right edge (" + str(edges_m["right"]) + ") must be <= FusionFloor left edge (" + str(edges_f["left"]) + ")"
	)

	var fusion_platform_b: Node = root.get_node_or_null("FusionPlatformB")
	var skill_check_p1: Node = root.get_node_or_null("SkillCheckPlatform1")
	_assert_true(fusion_platform_b != null, "stf_order_fusion_platform_b_exists")
	_assert_true(skill_check_p1 != null, "stf_order_skill_check_platform1_exists")
	if fusion_platform_b == null or skill_check_p1 == null:
		root.free()
		return

	_assert_true(
		(skill_check_p1 as Node3D).position.x > (fusion_platform_b as Node3D).position.x,
		"stf_order_skill_check_after_fusion_platform_b",
		"SkillCheckPlatform1.x (" + str((skill_check_p1 as Node3D).position.x) + ") must be > FusionPlatformB.x (" + str((fusion_platform_b as Node3D).position.x) + ")"
	)

	var skill_check_p3: Node = root.get_node_or_null("SkillCheckPlatform3")
	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	_assert_true(skill_check_p3 != null, "stf_order_skill_check_platform3_exists")
	_assert_true(mini_boss_floor != null, "stf_order_mini_boss_floor_exists")
	if skill_check_p3 == null or mini_boss_floor == null:
		root.free()
		return

	_assert_true(
		(skill_check_p3 as Node3D).position.x < (mini_boss_floor as Node3D).position.x,
		"stf_order_mini_boss_after_skill_check_p3",
		"SkillCheckPlatform3.x (" + str((skill_check_p3 as Node3D).position.x) + ") must be < MiniBossFloor.x (" + str((mini_boss_floor as Node3D).position.x) + ")"
	)

	var exit_floor: Node = root.get_node_or_null("ExitFloor")
	_assert_true(exit_floor != null, "stf_order_exit_floor_exists")
	if exit_floor == null:
		root.free()
		return

	var edges_boss: Dictionary = _world_x_edges_for_box(mini_boss_floor, "stf_mini_boss_floor")
	_assert_true(edges_boss.size() > 0, "stf_order_boss_edges_computed", "Failed to compute MiniBossFloor box edges")
	if edges_boss.size() == 0:
		root.free()
		return

	_assert_true(
		(exit_floor as Node3D).position.x > edges_boss["right"],
		"stf_order_exit_floor_after_boss_arena",
		"ExitFloor.x (" + str((exit_floor as Node3D).position.x) + ") must be > MiniBossFloor right edge (" + str(edges_boss["right"]) + ")"
	)

	root.free()

func test_stf_level_exit_triggers_level_complete_wiring() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	_assert_true(level_exit != null, "stf_level_exit_exists")
	if level_exit == null:
		root.free()
		return

	_assert_level_exit_has_level_complete(level_exit)

	root.free()

# Helper to avoid duplication of wiring logic while keeping the test names consistent.
func _assert_level_exit_has_level_complete(level_exit: Node) -> void:
	_assert_true(level_exit is Area3D, "stf_level_exit_is_area3d_assertion", "LevelExit is " + level_exit.get_class() + ", expected Area3D")

	var col: CollisionShape3D = _get_first_collision_shape(level_exit)
	_assert_true(col != null, "stf_level_exit_has_collision_shape_assertion", "LevelExit has no CollisionShape3D child")
	if col == null:
		return
	_assert_true(col.shape != null and col.shape is BoxShape3D, "stf_level_exit_collision_shape_is_box_assertion", "LevelExit CollisionShape3D.shape is not BoxShape3D")

	var script_obj: Script = level_exit.get_script() as Script
	_assert_true(script_obj != null, "stf_level_exit_has_script_assertion", "LevelExit has no script attached")
	if script_obj == null:
		return

	var source: String = script_obj.source_code
	if source != null and source != "":
		_assert_true(
			source.contains("level_complete"),
			"stf_level_exit_source_contains_level_complete_assertion",
			"LevelExit script source_code does not contain 'level_complete'"
		)
	else:
		_assert_true(
			level_exit.has_method("_on_body_entered"),
			"stf_level_exit_has_on_body_entered_fallback_assertion",
			"LevelExit script.source_code is empty and _on_body_entered() is missing"
		)

func test_stf_respawn_zone_retry_wiring_exists() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	_assert_true(zone != null, "stf_respawn_zone_exists")
	if zone == null:
		root.free()
		return

	_assert_true(zone is Area3D, "stf_respawn_zone_is_area3d", "RespawnZone is " + zone.get_class() + ", expected Area3D")

	var script_res: Script = zone.get_script() as Script
	_assert_true(script_res != null, "stf_respawn_zone_has_script", "RespawnZone has no script attached")
	if script_res == null:
		root.free()
		return
	_assert_true(
		script_res.resource_path.contains("respawn_zone.gd"),
		"stf_respawn_zone_script_path_contains_respawn_zone_gd",
		"RespawnZone script resource_path '" + script_res.resource_path + "' does not contain 'respawn_zone.gd'"
	)

	var spawn_point_val = zone.get("spawn_point")
	_assert_true(
		spawn_point_val != null and String(spawn_point_val) != "",
		"stf_respawn_zone_spawn_point_nonempty",
		"RespawnZone.spawn_point is null or empty NodePath"
	)

	if spawn_point_val != null and String(spawn_point_val) != "":
		var resolved: Node = zone.get_node_or_null(spawn_point_val as NodePath)
		_assert_true(
			resolved != null,
			"stf_respawn_zone_spawn_point_resolves",
			"RespawnZone.spawn_point NodePath '" + str(spawn_point_val) + "' did not resolve to a node"
		)

	root.free()

# ---------------------------------------------------------------------------
# ST-5: Integration gap — box-edge ordering across rooms
# Uses collision box edges (not node origins) to catch accidental overlaps
# and/or off-by-half-width boundary regressions between sequential rooms.
# ---------------------------------------------------------------------------
func test_stf_box_edge_adjacency_across_rooms() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var fusion_platform_b: Node = root.get_node_or_null("FusionPlatformB")
	var skill_check_p1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var skill_check_p3: Node = root.get_node_or_null("SkillCheckPlatform3")
	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	var exit_floor: Node = root.get_node_or_null("ExitFloor")

	_assert_true(fusion_platform_b != null, "stf_box_adj_fusion_platform_b_exists")
	_assert_true(skill_check_p1 != null, "stf_box_adj_skill_check_platform1_exists")
	_assert_true(skill_check_p3 != null, "stf_box_adj_skill_check_platform3_exists")
	_assert_true(mini_boss_floor != null, "stf_box_adj_mini_boss_floor_exists")
	_assert_true(exit_floor != null, "stf_box_adj_exit_floor_exists")

	if fusion_platform_b == null or skill_check_p1 == null or skill_check_p3 == null or mini_boss_floor == null or exit_floor == null:
		root.free()
		return

	var edges_fb: Dictionary = _world_x_edges_for_box(fusion_platform_b, "stf_box_adj_fusion_platform_b")
	var edges_p1: Dictionary = _world_x_edges_for_box(skill_check_p1, "stf_box_adj_skill_check_platform1")
	var edges_p3: Dictionary = _world_x_edges_for_box(skill_check_p3, "stf_box_adj_skill_check_platform3")
	var edges_boss: Dictionary = _world_x_edges_for_box(mini_boss_floor, "stf_box_adj_mini_boss_floor")
	var edges_exit: Dictionary = _world_x_edges_for_box(exit_floor, "stf_box_adj_exit_floor")

	_assert_true(edges_fb.size() > 0 and edges_p1.size() > 0, "stf_box_adj_fusion_b_and_p1_edges_computed")
	_assert_true(edges_p3.size() > 0 and edges_boss.size() > 0, "stf_box_adj_p3_and_boss_edges_computed")
	_assert_true(edges_exit.size() > 0 and edges_boss.size() > 0, "stf_box_adj_exit_and_boss_edges_computed")

	# Conservative room adjacency: previous right edge must not be to the right of next left edge.
	_assert_true(
		edges_fb["right"] <= edges_p1["left"],
		"stf_box_adj_fusion_platform_b_right_le_skill_check_platform1_left",
		"FusionPlatformB right edge (" + str(edges_fb["right"]) + ") must be <= SkillCheckPlatform1 left edge (" + str(edges_p1["left"]) + ")"
	)

	_assert_true(
		edges_p3["right"] <= edges_boss["left"],
		"stf_box_adj_skill_check_platform3_right_le_mini_boss_floor_left",
		"SkillCheckPlatform3 right edge (" + str(edges_p3["right"]) + ") must be <= MiniBossFloor left edge (" + str(edges_boss["left"]) + ")"
	)

	_assert_true(
		edges_boss["right"] <= edges_exit["left"],
		"stf_box_adj_mini_boss_floor_right_le_exit_floor_left",
		"MiniBossFloor right edge (" + str(edges_boss["right"]) + ") must be <= ExitFloor left edge (" + str(edges_exit["left"]) + ")"
	)

	root.free()

# ---------------------------------------------------------------------------
# ST-6: Spec-gap checkpoint — LevelExit completion must not be gated on mini-boss state
#
# CHECKPOINT: Conservative assumption used by ticket: normal completion is triggered
# solely when a "player" body enters LevelExit; the LevelExit inline script should
# not reference EnemyMiniBoss / mini-boss defeat state at all.
# ---------------------------------------------------------------------------
func test_stf_checkpoint_level_exit_is_unconditional_completion_trigger() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	_assert_true(level_exit != null, "stf_checkpoint_level_exit_exists")
	if level_exit == null:
		root.free()
		return

	# CHECKPOINT: encode that completion is driven by player-entering LevelExit, not by any mini-boss state variable.
	var tscn_text: String = _read_res_file_as_text(LEVEL_SCENE_PATH)
	_assert_true(
		tscn_text != "",
		"stf_checkpoint_level_exit_tscn_reads",
		"Failed to read level tscn text from " + LEVEL_SCENE_PATH
	)

	var start_idx: int = tscn_text.find("GDScript_level_exit")
	_assert_true(
		start_idx != -1,
		"stf_checkpoint_level_exit_section_start_found",
		"Could not locate GDScript_level_exit sub-resource in " + LEVEL_SCENE_PATH
	)
	if start_idx == -1:
		root.free()
		return

	var end_idx: int = tscn_text.find('[node name="ContainmentHall01"', start_idx)
	if end_idx == -1:
		end_idx = min(start_idx + 5000, tscn_text.length())

	var section: String = tscn_text.substr(start_idx, end_idx - start_idx)
	var section_lower: String = section.to_lower()

	_assert_true(
		section.contains("level_complete"),
		"stf_checkpoint_level_exit_section_contains_level_complete"
	)
	_assert_true(
		section.contains("body_entered.connect(_on_body_entered)") or section.contains("body_entered.connect"),
		"stf_checkpoint_level_exit_section_connects_body_entered"
	)
	_assert_true(
		section_lower.contains("is_in_group") and section_lower.contains("player"),
		"stf_checkpoint_level_exit_section_filters_player_group"
	)

	# Anti-gating assertions: LevelExit should not mention miniboss defeat/state identifiers.
	_assert_true(
		section_lower.find("miniboss") == -1 and section_lower.find("enemymonster") == -1,
		"stf_checkpoint_level_exit_section_has_no_miniboss_references",
		"LevelExit inline script references miniboss identifiers; this violates the ticket's conservative completion trigger assumption."
	)
	_assert_true(
		section_lower.find("enemimini") == -1,
		"stf_checkpoint_level_exit_section_has_no_enemyminiboss_references"
	)

	root.free()

# ---------------------------------------------------------------------------
# ST-7: Edge-case — player initial transform should match SpawnPosition marker
# Prevents scenes where SpawnPosition is correct but Player3D isn't actually placed at it.
# ---------------------------------------------------------------------------
func test_stf_player_spawn_position_matches_player_transform() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var spawn: Node = root.get_node_or_null("SpawnPosition")
	var player: Node = root.get_node_or_null("Player3D")
	_assert_true(spawn != null, "stf_spawn_marker_exists_for_player_alignment")
	_assert_true(player != null, "stf_player_exists_for_player_alignment")
	if spawn == null or player == null:
		root.free()
		return

	_assert_true(
		(spawn is Marker3D),
		"stf_spawn_marker_is_marker3d",
		"SpawnPosition is " + spawn.get_class() + ", expected Marker3D"
	)
	_assert_true(
		(player is Node3D),
		"stf_player_is_node3d_for_alignment",
		"Player3D is " + player.get_class() + ", expected Node3D-based transform"
	)

	var spawn_pos: Vector3 = (spawn as Node3D).position
	var player_pos: Vector3 = (player as Node3D).position

	var tol: float = 0.001
	_assert_true(
		absf(spawn_pos.x - player_pos.x) <= tol and absf(spawn_pos.y - player_pos.y) <= tol and absf(spawn_pos.z - player_pos.z) <= tol,
		"stf_player_position_matches_spawnposition_with_tolerance",
		"Player3D.position (" + str(player_pos) + ") must match SpawnPosition.position (" + str(spawn_pos) + ") within tol=" + str(tol)
	)

	root.free()

# ---------------------------------------------------------------------------
# ST-8: Flow clarity — InfectionUI must include objective prompts + input hints
#
# Structural guard for the human-playable AC: even if prompts are hidden at start,
# they must exist in the level's UI tree and not be removed/replaced.
# ---------------------------------------------------------------------------
func test_stf_infection_ui_has_prompt_labels_and_hints() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var infection_ui: Node = root.get_node_or_null("InfectionUI")
	_assert_true(infection_ui != null, "stf_infection_ui_exists")
	if infection_ui == null:
		root.free()
		return

	var required_labels: Array[String] = [
		"AbsorbPromptLabel",
		"FusePromptLabel",
		"FusionActiveLabel"
	]
	for label_name in required_labels:
		var n: Node = infection_ui.get_node_or_null(label_name)
		_assert_true(n != null, "stf_ui_has_" + label_name.to_lower() + "_exists", "Missing " + label_name + " under InfectionUI")
		if n == null:
			continue
		_assert_true(
			n is Label,
			"stf_ui_has_" + label_name.to_lower() + "_is_label",
			label_name + " is " + n.get_class() + ", expected Label"
		)

	# These contextual prompts start hidden by default in the shipped scene.
	var absorb_prompt: Node = infection_ui.get_node_or_null("AbsorbPromptLabel")
	if absorb_prompt != null:
		_assert_true(!absorb_prompt.visible, "stf_ui_absorb_prompt_hidden_by_default")

	var fuse_prompt: Node = infection_ui.get_node_or_null("FusePromptLabel")
	if fuse_prompt != null:
		_assert_true(!fuse_prompt.visible, "stf_ui_fuse_prompt_hidden_by_default")

	var fusion_active: Node = infection_ui.get_node_or_null("FusionActiveLabel")
	if fusion_active != null:
		_assert_true(!fusion_active.visible, "stf_ui_fusion_active_label_hidden_by_default")

	# Always-visible hints container (signposting/navigation support).
	var hints: Node = infection_ui.get_node_or_null("Hints")
	_assert_true(hints != null, "stf_ui_hints_container_exists")
	if hints == null:
		root.free()
		return
	_assert_true(
		(hints is Control),
		"stf_ui_hints_is_control",
		"Hints is " + hints.get_class() + ", expected Control"
	)

	var required_hint_labels: Array[String] = ["MoveHint", "JumpHint", "DetachRecallHint", "AbsorbHint"]
	for hint_name in required_hint_labels:
		var hint_node: Node = hints.get_node_or_null(hint_name)
		_assert_true(hint_node != null, "stf_ui_hints_has_" + hint_name.to_lower() + "_exists", "Missing hint label " + hint_name)
		if hint_node == null:
			continue
		_assert_true(hint_node is Label, "stf_ui_hints_has_" + hint_name.to_lower() + "_is_label")
		var hint_script: Script = hint_node.get_script() as Script
		_assert_true(
			hint_script != null and hint_script.resource_path.contains("input_hint_label.gd"),
			"stf_ui_hint_script_is_input_hint_label",
			hint_name + " script resource_path '" + (hint_script.resource_path if hint_script != null else "null") + "' does not contain input_hint_label.gd"
		)

	root.free()

# ---------------------------------------------------------------------------
# ST-9: Edge-case — respawn trigger is non-degenerate and spawn_point is the SpawnPosition marker
# ---------------------------------------------------------------------------
func test_stf_respawn_zone_spawn_point_is_spawn_position_and_trigger_non_degenerate() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	_assert_true(zone != null, "stf_adv_respawn_zone_exists")
	if zone == null:
		root.free()
		return

	_assert_true(zone is Area3D, "stf_adv_respawn_zone_is_area3d")

	var box: BoxShape3D = _require_box_shape_collision_shape(zone, "stf_adv_respawn_zone_collision_box")
	if box == null:
		root.free()
		return
	_assert_true(box.size.x > 0.0, "stf_adv_respawn_zone_collision_box_size_x_nonzero")
	_assert_true(box.size.y > 0.0, "stf_adv_respawn_zone_collision_box_size_y_nonzero")
	_assert_true(box.size.z > 0.0, "stf_adv_respawn_zone_collision_box_size_z_nonzero")

	# spawn_point should resolve to SpawnPosition (retry safety for the skill-check pit).
	var spawn_point_val = zone.get("spawn_point")
	_assert_true(spawn_point_val != null and String(spawn_point_val) != "", "stf_adv_respawn_zone_spawn_point_non_empty")
	if spawn_point_val == null or String(spawn_point_val) == "":
		root.free()
		return

	var resolved: Node = zone.get_node_or_null(spawn_point_val as NodePath)
	_assert_true(resolved != null, "stf_adv_respawn_zone_spawn_point_resolves")
	if resolved == null:
		root.free()
		return
	_assert_true(resolved.name == "SpawnPosition", "stf_adv_respawn_zone_spawn_point_is_spawn_position", "spawn_point resolves to '" + resolved.name + "', expected 'SpawnPosition'")
	_assert_true(resolved is Marker3D, "stf_adv_respawn_zone_spawn_point_is_marker3d")

	_assert_true(zone.has_method("_on_body_entered"), "stf_adv_respawn_zone_has_on_body_entered")

	root.free()

# ---------------------------------------------------------------------------
# ST-10: Stress — repeated instantiation stays structurally valid
# Headless suite must be robust to repeated scene instantiation in CI.
# ---------------------------------------------------------------------------
func test_stf_stress_repeated_scene_instantiation() -> void:
	const ITERATIONS: int = 6

	var first_failure: String = ""
	for i in range(ITERATIONS):
		var root: Node = _load_level_scene()
		if root == null:
			first_failure = "instantiate returned null at iteration " + str(i)
			break

		# Keep checks minimal (structural only).
		if root.get_node_or_null("SpawnPosition") == null:
			first_failure = "missing SpawnPosition at iteration " + str(i)
			root.free()
			break
		if root.get_node_or_null("LevelExit") == null:
			first_failure = "missing LevelExit at iteration " + str(i)
			root.free()
			break
		if root.get_node_or_null("MutationTeaseFloor") == null:
			first_failure = "missing MutationTeaseFloor at iteration " + str(i)
			root.free()
			break
		if root.get_node_or_null("SkillCheckFloorBase") == null:
			first_failure = "missing SkillCheckFloorBase at iteration " + str(i)
			root.free()
			break
		if root.get_node_or_null("MiniBossFloor") == null:
			first_failure = "missing MiniBossFloor at iteration " + str(i)
			root.free()
			break

		root.free()

	_assert_true(first_failure == "", "stf_stress_repeated_instantiation_ok", first_failure)

func run_all() -> int:
	print("--- tests/levels/test_start_finish_flow.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ST-1: level loads and contains all required segments + end marker + UI hooks.
	test_stf_loads_and_has_core_nodes()

	# ST-2: cross-zone progression order across mutation → fusion → skill check → mini-boss → exit.
	test_stf_cross_zone_progression_ordering()

	# ST-3: LevelExit wiring includes level_complete path.
	test_stf_level_exit_triggers_level_complete_wiring()

	# ST-4: Respawn zone wiring exists (retry safety around skill check pit).
	test_stf_respawn_zone_retry_wiring_exists()

	# ST-5: Integration gap — box-edge ordering across rooms.
	test_stf_box_edge_adjacency_across_rooms()

	# ST-6: Spec-gap checkpoint — LevelExit completion is unconditional.
	test_stf_checkpoint_level_exit_is_unconditional_completion_trigger()

	# ST-7: Edge-case — Player3D transform matches SpawnPosition.
	test_stf_player_spawn_position_matches_player_transform()

	# ST-8: Flow clarity — InfectionUI includes objective prompts + input hints.
	test_stf_infection_ui_has_prompt_labels_and_hints()

	# ST-9: Edge-case — respawn trigger non-degenerate + spawn_point resolves to SpawnPosition.
	test_stf_respawn_zone_spawn_point_is_spawn_position_and_trigger_non_degenerate()

	# ST-10: Stress — repeated scene instantiation remains structurally valid.
	test_stf_stress_repeated_scene_instantiation()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

