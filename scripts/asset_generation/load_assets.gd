@tool
extends EditorScript

const EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")

const SOURCE_DIR := "res://assets/enemies/generated_glb"
const OUTPUT_DIR := "res://scenes/enemies/generated"

# Shared gameplay script to attach to every generated enemy scene.
# Create this later if you want; the generator will skip attaching it if missing.
const DEFAULT_ENEMY_SCRIPT := "res://scripts/enemies/enemy_base.gd"

# Root node type for generated enemies.
# CharacterBody3D is useful if most enemies move with gameplay logic.
# Change to Node3D if you want a lighter root.
const USE_CHARACTER_BODY := true

# ------------------------------------------------------------
# Mutation mapping by enemy family
# ------------------------------------------------------------

const MUTATION_BY_FAMILY := {
	"adhesion_bug": "adhesion",
	"tar_slug": "adhesion",
	"glue_drone": "adhesion",

	"acid_spitter": "acid",
	"melt_worm": "acid",
	"corrosion_beetle": "acid",

	"claw_crawler": "claw",
	"ripper_bat": "claw",
	"razor_lizard": "claw",

	"carapace_husk": "carapace",
	"shell_roller": "carapace",
	"fortress_bug": "carapace",

	"electric_node": "electric",
	"shock_jelly": "electric",
	"tesla_wasp": "electric",

	"tendril_beast": "tendril",
	"vine_creeper": "tendril",
	"lash_parasite": "tendril",

	"ember_imp": "fire",
	"flame_hopper": "fire",
	"cinder_snake": "fire",

	"frost_jelly": "ice",
	"glacier_crab": "ice",
	"snow_wisp": "ice",

	"stone_burrower": "earth",
	"boulder_golem": "earth",
	"mud_stomper": "earth",

	"gale_sprite": "wind",
	"cyclone_bird": "wind",
	"gust_hopper": "wind",

	"ferro_drone": "metal",
	"iron_beetle": "metal",
	"scrap_slime": "metal",

	"blade_sentinel": "sword",
	"duel_knight": "sword",
	"cutter_wisp": "sword",

	"spear_wisp": "javelin",
	"pike_guard": "javelin",
	"harpoon_eel": "javelin",

	"knuckle_sprite": "punch",
	"slam_golem": "punch",
	"boxer_bot": "punch",

	"ring_drone": "ring",
	"orbit_wisp": "ring",
	"halo_spinner": "ring",

	"powder_bug": "bomb",
	"boom_toad": "bomb",
	"mine_sprite": "bomb",

	"mutation_clown": "random"
}

func _run() -> void:
	print("Enemy scene generation started.")
	_ensure_dir(OUTPUT_DIR)

	var files := _collect_glb_files(SOURCE_DIR)
	if files.is_empty():
		push_warning("No .glb files found in %s" % SOURCE_DIR)
		return

	for file_path in files:
		_generate_scene_for_glb(file_path)

	print("Enemy scene generation complete.")

# ------------------------------------------------------------
# Main generation
# ------------------------------------------------------------

func _generate_scene_for_glb(glb_path: String) -> void:
	var glb_scene: PackedScene = load(glb_path)
	if glb_scene == null:
		push_warning("Failed to load GLB scene: %s" % glb_path)
		return

	var visual_instance := glb_scene.instantiate()
	if visual_instance == null:
		push_warning("Failed to instantiate GLB scene: %s" % glb_path)
		return

	var file_name := glb_path.get_file().get_basename() # e.g. acid_spitter_00
	var family_name := _extract_family_name(file_name)  # e.g. acid_spitter
	var mutation := MUTATION_BY_FAMILY.get(family_name, "unknown")

	var root: Node3D
	if USE_CHARACTER_BODY:
		root = CharacterBody3D.new()
	else:
		root = Node3D.new()

	root.name = file_name

	# Attach common script if present
	if ResourceLoader.exists(DEFAULT_ENEMY_SCRIPT):
		var script_res := load(DEFAULT_ENEMY_SCRIPT)
		if script_res:
			root.set_script(script_res)

	# Store metadata for gameplay lookup
	root.set_meta("enemy_id", file_name)
	root.set_meta("enemy_family", family_name)
	root.set_meta("mutation_drop", mutation)
	root.set_meta("source_glb", glb_path)

	# Optional exported vars on your enemy_base.gd, if they exist
	root.set("enemy_id", file_name)
	root.set("enemy_family", family_name)
	root.set("mutation_drop", mutation)

	# Visual container
	var visual_root := Node3D.new()
	visual_root.name = "Visual"
	root.add_child(visual_root)
	visual_root.owner = root

	visual_instance.name = "Model"
	visual_root.add_child(visual_instance)
	visual_instance.owner = root

	# Generate collision from imported meshes
	var shape := _build_collision_shape_from_node(visual_instance)
	if shape != null:
		var collision := CollisionShape3D.new()
		collision.name = "CollisionShape3D"
		collision.shape = shape
		root.add_child(collision)
		collision.owner = root

	# Common gameplay nodes
	_add_marker(root, "AttackOrigin", Vector3(0.6, 0.0, 0.0))
	_add_marker(root, "ChunkAttachPoint", Vector3(0.0, 0.0, 0.2))
	_add_marker(root, "PickupAnchor", Vector3(0.0, 0.0, 0.0))
	_add_hurtbox(root, shape)
	_add_visible_on_screen_notifier(root, shape)

	# Save scene
	var packed := PackedScene.new()
	var pack_result := packed.pack(root)
	if pack_result != OK:
		push_warning("Failed to pack scene for %s" % glb_path)
		return

	var output_path := "%s/%s.tscn" % [OUTPUT_DIR, file_name]
	var save_result := ResourceSaver.save(packed, output_path)
	if save_result != OK:
		push_warning("Failed to save generated scene: %s" % output_path)
		return

	print("Generated: %s" % output_path)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

func _collect_glb_files(dir_path: String) -> Array[String]:
	var result: Array[String] = []
	var dir := DirAccess.open(dir_path)
	if dir == null:
		push_warning("Could not open source dir: %s" % dir_path)
		return result

	dir.list_dir_begin()
	while true:
		var file_name := dir.get_next()
		if file_name == "":
			break
		if dir.current_is_dir():
			continue
		if file_name.to_lower().ends_with(".glb"):
			result.append("%s/%s" % [dir_path, file_name])
	dir.list_dir_end()

	result.sort()
	return result

func _ensure_dir(path: String) -> void:
	if DirAccess.dir_exists_absolute(path):
		return
	DirAccess.make_dir_recursive_absolute(path)

func _extract_family_name(file_name: String) -> String:
	return EnemyNameUtils.extract_family_name(file_name)

func _add_marker(root: Node3D, marker_name: String, position: Vector3) -> void:
	var marker := Marker3D.new()
	marker.name = marker_name
	marker.position = position
	root.add_child(marker)
	marker.owner = root

func _add_hurtbox(root: Node3D, collision_shape: Shape3D) -> void:
	var area := Area3D.new()
	area.name = "Hurtbox"
	root.add_child(area)
	area.owner = root

	var collision := CollisionShape3D.new()
	collision.name = "CollisionShape3D"
	collision.shape = _duplicate_shape(collision_shape)
	area.add_child(collision)
	collision.owner = root

func _add_visible_on_screen_notifier(root: Node3D, collision_shape: Shape3D) -> void:
	var notifier := VisibleOnScreenNotifier3D.new()
	notifier.name = "VisibleOnScreenNotifier3D"

	var aabb := _aabb_from_shape(collision_shape)
	notifier.aabb = aabb

	root.add_child(notifier)
	notifier.owner = root

func _duplicate_shape(shape: Shape3D) -> Shape3D:
	if shape == null:
		return null
	return shape.duplicate(true)

# ------------------------------------------------------------
# Collision generation
# ------------------------------------------------------------

func _build_collision_shape_from_node(node: Node) -> Shape3D:
	var aabb := _compute_combined_aabb(node)
	if aabb.size == Vector3.ZERO:
		return null

	# Heuristic:
	# - flat/flying enemies get a BoxShape3D
	# - tall/narrow enemies get a CapsuleShape3D
	# - otherwise box is safest
	var size := aabb.size

	if size.y > max(size.x, size.z) * 1.25:
		var capsule := CapsuleShape3D.new()
		capsule.radius = max(size.x, size.z) * 0.35
		capsule.height = max(size.y - capsule.radius * 2.0, 0.1)
		return capsule

	var box := BoxShape3D.new()
	box.size = size
	return box

func _compute_combined_aabb(node: Node) -> AABB:
	var found := false
	var combined := AABB()

	var meshes := []
	_gather_mesh_instances(node, meshes)

	for mesh_instance in meshes:
		if mesh_instance.mesh == null:
			continue

		var local_aabb := mesh_instance.mesh.get_aabb()
		var xform := mesh_instance.global_transform
		var corners := _aabb_corners(local_aabb)

		for corner in corners:
			var world_point := xform * corner
			if not found:
				combined = AABB(world_point, Vector3.ZERO)
				found = true
			else:
				combined = combined.expand(world_point)

	if not found:
		return AABB()

	# Recenter back around local origin of wrapper root
	var center := combined.position + combined.size * 0.5
	combined.position -= center
	return combined

func _gather_mesh_instances(node: Node, out: Array) -> void:
	if node is MeshInstance3D:
		out.append(node)
	for child in node.get_children():
		_gather_mesh_instances(child, out)

func _aabb_corners(aabb: AABB) -> Array[Vector3]:
	var p := aabb.position
	var s := aabb.size
	return [
		p + Vector3(0, 0, 0),
		p + Vector3(s.x, 0, 0),
		p + Vector3(0, s.y, 0),
		p + Vector3(0, 0, s.z),
		p + Vector3(s.x, s.y, 0),
		p + Vector3(s.x, 0, s.z),
		p + Vector3(0, s.y, s.z),
		p + Vector3(s.x, s.y, s.z),
	]

func _aabb_from_shape(shape: Shape3D) -> AABB:
	if shape == null:
		return AABB(Vector3(-0.5, -0.5, -0.5), Vector3.ONE)

	if shape is BoxShape3D:
		var box := shape as BoxShape3D
		return AABB(-box.size * 0.5, box.size)

	if shape is CapsuleShape3D:
		var capsule := shape as CapsuleShape3D
		var size := Vector3(capsule.radius * 2.0, capsule.height + capsule.radius * 2.0, capsule.radius * 2.0)
		return AABB(-size * 0.5, size)

	return AABB(Vector3(-0.5, -0.5, -0.5), Vector3.ONE)