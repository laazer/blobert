# run_scene_assembler.gd
#
# Assembles the room sequence for a roguelike run on every run_started signal.
# Owns a RunStateManager instance, triggers it on _ready(), and responds by
# clearing previously instantiated rooms, calling RoomChainGenerator.generate(),
# loading and instantiating each PackedScene, positioning rooms end-to-end using
# their Entry/Exit Marker3D nodes, and adding them as siblings under get_parent().
#
# Architectural constraints:
#   - Does NOT share a RunStateManager with DeathRestartCoordinator. Two lightweight
#     instances is intentional — see CHECKPOINTS.md [PRC] Engine Integration.
#   - Does NOT call the scene reload method.
#   - Does NOT connect to any autoload.
#   - Core Simulation (RoomChainGenerator) remains pure RefCounted — called here.
#
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/procedural_room_chaining.md

class_name RunSceneAssembler
extends Node

const SEQUENCE: Array[String] = ["intro", "combat", "combat", "mutation_tease", "boss"]
const POOL: Dictionary = {
	"intro": ["res://scenes/rooms/room_intro_01.tscn"],
	"combat": ["res://scenes/rooms/room_combat_01.tscn", "res://scenes/rooms/room_combat_02.tscn"],
	"mutation_tease": ["res://scenes/rooms/room_mutation_tease_01.tscn"],
	"boss": ["res://scenes/rooms/room_boss_01.tscn"]
}

const _DEFAULT_ROOM_WIDTH: float = 30.0
const _ENTRY_EXIT_MIDPOINT_FACTOR: float = 0.5
const _ENEMY_GENERATED_SCENE_DIR: String = "res://scenes/enemies/generated/"
const _ENEMY_SPAWN_ANCHOR_PREFIX: String = "EnemySpawn_"
const _ENEMY_VISUAL_VARIANT_SELECTOR_PATH: String = "res://scripts/system/enemy_visual_variant_selector.gd"
const _ENEMY_VISUAL_VARIANT_SELECTOR_METHOD: String = "resolve_spawn_visual_variant"
const _ENEMY_DECLARATIONS_META_KEY: String = "enemy_spawn_declarations"
const _ENEMY_DECLARATION_FAMILY_KEY: String = "enemy_family"
const _META_SPAWN_GENERATED_ENEMIES_DONE: String = "spawn_generated_enemies_for_room_done"
const _INFECTION_HOST_SCRIPT_PATH: String = "res://scripts/enemy/enemy_infection_3d.gd"

## M10-01 R4 family keys → mutation_drop for EnemyInfection3D._ensure_*_attack_if_needed.
const _SPAWN_FAMILY_MUTATION_DROP: Dictionary = {
	"acid_spitter": "acid",
	"adhesion_bug": "adhesion",
	"carapace_husk": "carapace",
	"claw_crawler": "claw",
}

var _rsm: RunStateManager
var _active_rooms: Array[Node3D] = []
var _enemy_visual_variant_selector: RefCounted = null


func _ready() -> void:
	_enemy_visual_variant_selector = _build_enemy_visual_variant_selector()
	_rsm = RunStateManager.new()
	_rsm.run_started.connect(_on_run_started)
	_rsm.apply_event("start_run")


func _on_run_started() -> void:
	_clear_rooms()

	var generator := RoomChainGenerator.new()
	var paths: Array[String] = generator.generate(SEQUENCE, POOL, Time.get_ticks_msec())
	preload("res://scripts/system/logging.gd").info("RunSceneAssembler: room layout → %s" % str(paths))

	var cursor_x: float = 0.0
	var level_root: Node = get_parent()

	for path in paths:
		var packed := ResourceLoader.load(path) as PackedScene
		if packed == null:
			push_error("RunSceneAssembler: failed to load PackedScene at path: %s" % path)
			continue

		var room := packed.instantiate() as Node3D
		if room == null:
			push_error("RunSceneAssembler: instantiated node is not Node3D for path: %s" % path)
			continue

		# Entry.x is 0 in local space, so room world origin = cursor_x + 0.
		room.position = Vector3(cursor_x, 0.0, 0.0)

		var exit_node := room.get_node_or_null("Exit") as Node3D
		var exit_local_x: float
		if exit_node != null:
			exit_local_x = exit_node.position.x
		else:
			push_warning(
				"RunSceneAssembler: room at '%s' has no Exit Marker3D — assuming width %.1f" \
				% [path, _DEFAULT_ROOM_WIDTH]
			)
			exit_local_x = _DEFAULT_ROOM_WIDTH

		level_root.add_child.call_deferred(room)
		_spawn_generated_enemies_for_room(room, path)
		_active_rooms.append(room)

		cursor_x += exit_local_x


func _clear_rooms() -> void:
	for node in _active_rooms:
		if is_instance_valid(node):
			node.queue_free()
	_active_rooms.clear()


func _resolve_spawn_visual_variant_for_enemy_family(
	enemy_family: String,
	manifest: Dictionary,
	rng: Variant = null
) -> Dictionary:
	if _enemy_visual_variant_selector == null:
		push_error("RunSceneAssembler: enemy visual variant selector is unavailable")
		return {"ok": false, "error": "selector unavailable", "path": ""}
	if not _enemy_visual_variant_selector.has_method(_ENEMY_VISUAL_VARIANT_SELECTOR_METHOD):
		push_error("RunSceneAssembler: selector missing method %s" % _ENEMY_VISUAL_VARIANT_SELECTOR_METHOD)
		return {"ok": false, "error": "selector method missing", "path": ""}
	var result: Variant = _enemy_visual_variant_selector.call(
		_ENEMY_VISUAL_VARIANT_SELECTOR_METHOD,
		enemy_family,
		manifest,
		rng
	)
	if not (result is Dictionary):
		return {"ok": false, "error": "selector returned non-dictionary", "path": ""}
	return result as Dictionary


func _build_enemy_visual_variant_selector() -> RefCounted:
	if not ResourceLoader.exists(_ENEMY_VISUAL_VARIANT_SELECTOR_PATH):
		push_error("RunSceneAssembler: enemy visual variant selector script missing: %s" % _ENEMY_VISUAL_VARIANT_SELECTOR_PATH)
		return null
	var selector_script: GDScript = load(_ENEMY_VISUAL_VARIANT_SELECTOR_PATH) as GDScript
	if selector_script == null:
		push_error("RunSceneAssembler: failed to load selector script: %s" % _ENEMY_VISUAL_VARIANT_SELECTOR_PATH)
		return null
	if not selector_script.can_instantiate():
		push_error("RunSceneAssembler: selector script is not instantiable: %s" % _ENEMY_VISUAL_VARIANT_SELECTOR_PATH)
		return null
	return selector_script.new() as RefCounted


func _enemy_spawn_fallback_local_relative_to_room(room: Node3D) -> Vector3:
	if room == null:
		return Vector3.ZERO
	var entry := room.get_node_or_null("Entry") as Node3D
	var exit_node := room.get_node_or_null("Exit") as Node3D
	if entry == null or exit_node == null:
		return Vector3.ZERO
	var midpoint_local_x := (entry.position.x + exit_node.position.x) * _ENTRY_EXIT_MIDPOINT_FACTOR
	return Vector3(midpoint_local_x, maxf(entry.position.y, exit_node.position.y), 0.0)


func _compute_room_enemy_spawn_fallback(room: Node3D) -> Vector3:
	if room == null:
		return Vector3.ZERO
	var entry := room.get_node_or_null("Entry") as Node3D
	var exit_node := room.get_node_or_null("Exit") as Node3D
	if entry == null or exit_node == null:
		return room.global_position if room.is_inside_tree() else room.position
	var fallback_local := _enemy_spawn_fallback_local_relative_to_room(room)
	return room.to_global(fallback_local) if room.is_inside_tree() else fallback_local


func _find_room_enemy_spawn_anchors(room: Node3D) -> Array[Marker3D]:
	var anchors: Array[Marker3D] = []
	if room == null:
		return anchors
	for child in room.get_children():
		if not (child is Marker3D):
			continue
		var marker := child as Marker3D
		if marker.name.begins_with(_ENEMY_SPAWN_ANCHOR_PREFIX):
			anchors.append(marker)
	return anchors


func _generated_enemy_scene_path_for_variant(variant_id: String) -> String:
	return _ENEMY_GENERATED_SCENE_DIR + variant_id + ".tscn"


func _generated_enemy_scene_exists(variant_id: String) -> bool:
	var scene_path := _generated_enemy_scene_path_for_variant(variant_id)
	return ResourceLoader.exists(scene_path)


func _mutation_drop_for_spawn_family(enemy_family: String) -> String:
	return str(_SPAWN_FAMILY_MUTATION_DROP.get(enemy_family, "")).strip_edges()


func _effective_mutation_drop_for_declaration(declaration: Dictionary, enemy_family: String) -> String:
	if declaration.has("mutation_drop"):
		return str(declaration.get("mutation_drop")).strip_edges()
	return _mutation_drop_for_spawn_family(enemy_family)


func _apply_m8_infection_host_contract(enemy_instance: Node3D, enemy_family: String, mutation_drop_effective: String) -> bool:
	if enemy_instance is EnemyInfection3D:
		var host: EnemyInfection3D = enemy_instance as EnemyInfection3D
		if not mutation_drop_effective.is_empty():
			host.mutation_drop = mutation_drop_effective
		return true
	if not ResourceLoader.exists(_INFECTION_HOST_SCRIPT_PATH):
		push_warning(
			"RunSceneAssembler: room=<spawn> family=%s error=infection host script missing: %s" \
			% [enemy_family, _INFECTION_HOST_SCRIPT_PATH]
		)
		return false
	var infection_script: GDScript = load(_INFECTION_HOST_SCRIPT_PATH) as GDScript
	if infection_script == null:
		push_warning("RunSceneAssembler: room=<spawn> family=%s error=failed loading infection host script" % enemy_family)
		return false
	enemy_instance.set_script(infection_script)
	enemy_instance.set("mutation_drop", mutation_drop_effective)
	enemy_instance.set("model_scene", null)
	return true


func _spawn_generated_enemies_for_room(room: Node3D, room_path: String) -> void:
	if room == null:
		return
	var declarations_variant: Variant = room.get_meta(_ENEMY_DECLARATIONS_META_KEY, [])
	if not (declarations_variant is Array):
		push_warning(
			"RunSceneAssembler: room=%s family=<none> error=invalid %s metadata shape" \
			% [room_path, _ENEMY_DECLARATIONS_META_KEY]
		)
		return
	var declarations: Array = declarations_variant as Array
	if declarations.is_empty():
		return
	if bool(room.get_meta(_META_SPAWN_GENERATED_ENEMIES_DONE, false)):
		return

	var anchors: Array[Marker3D] = _find_room_enemy_spawn_anchors(room)
	var manifest: Dictionary = _read_model_registry_manifest()
	if manifest.is_empty():
		push_warning("RunSceneAssembler: room=%s family=<none> error=model registry manifest unavailable" % room_path)
		return
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(room_path)
	var spawn_counter: int = 0

	for declaration_variant in declarations:
		if not (declaration_variant is Dictionary):
			push_warning("RunSceneAssembler: room=%s family=<none> error=declaration must be dictionary" % room_path)
			continue
		var declaration: Dictionary = declaration_variant as Dictionary
		var enemy_family: String = str(declaration.get(_ENEMY_DECLARATION_FAMILY_KEY, "")).strip_edges()
		if enemy_family.is_empty():
			push_warning(
				"RunSceneAssembler: room=%s family=<missing> error=declaration missing %s" \
				% [room_path, _ENEMY_DECLARATION_FAMILY_KEY]
			)
			continue
		if _mutation_drop_for_spawn_family(enemy_family).is_empty():
			push_warning(
				"RunSceneAssembler: room=%s family=%s error=unknown enemy_family (not in M10 spawn contract)" \
				% [room_path, enemy_family]
			)
			continue
		var min_count_variant: Variant = declaration.get("min_count", 0)
		var max_count_variant: Variant = declaration.get("max_count", 0)
		if not (min_count_variant is int) or not (max_count_variant is int):
			push_warning(
				"RunSceneAssembler: room=%s family=%s error=declaration min_count/max_count must be integers" \
				% [room_path, enemy_family]
			)
			continue
		var min_count: int = min_count_variant
		var max_count: int = max_count_variant
		if min_count < 0 or min_count > max_count:
			push_warning(
				"RunSceneAssembler: room=%s family=%s error=invalid min/max bounds (%d, %d)" \
				% [room_path, enemy_family, min_count, max_count]
			)
			continue
		var spawn_count: int = min_count if min_count == max_count else rng.randi_range(min_count, max_count)
		for _i in range(spawn_count):
			var variant_result: Dictionary = _resolve_spawn_visual_variant_for_enemy_family(enemy_family, manifest, rng)
			if not bool(variant_result.get("ok", false)):
				push_warning(
					"RunSceneAssembler: room=%s family=%s error=variant resolution failed: %s" \
					% [room_path, enemy_family, str(variant_result.get("error", "unknown"))]
				)
				continue
			var variant_id: String = str(variant_result.get("variant_id", "")).strip_edges()
			if variant_id.is_empty():
				push_warning("RunSceneAssembler: room=%s family=%s error=selector returned empty variant_id" % [room_path, enemy_family])
				continue
			if not _generated_enemy_scene_exists(variant_id):
				push_warning(
					"RunSceneAssembler: room=%s family=%s error=generated scene missing for variant %s" \
					% [room_path, enemy_family, variant_id]
				)
				continue
			var generated_scene_path: String = _generated_enemy_scene_path_for_variant(variant_id)
			var generated_scene := load(generated_scene_path) as PackedScene
			if generated_scene == null:
				push_warning(
					"RunSceneAssembler: room=%s family=%s error=failed loading generated scene %s" \
					% [room_path, enemy_family, generated_scene_path]
				)
				continue
			var enemy_instance := generated_scene.instantiate() as Node3D
			if enemy_instance == null:
				push_warning(
					"RunSceneAssembler: room=%s family=%s error=generated scene root is not Node3D (%s)" \
					% [room_path, enemy_family, generated_scene_path]
				)
				continue
			var mutation_drop_effective: String = _effective_mutation_drop_for_declaration(declaration, enemy_family)
			if not _apply_m8_infection_host_contract(enemy_instance, enemy_family, mutation_drop_effective):
				continue
			enemy_instance.set_meta("enemy_family", enemy_family)
			if mutation_drop_effective.is_empty():
				if declaration.has("mutation_drop"):
					enemy_instance.set_meta("mutation_drop", declaration.get("mutation_drop"))
				elif not enemy_instance.has_meta("mutation_drop"):
					enemy_instance.set_meta("mutation_drop", "")
			else:
				enemy_instance.set_meta("mutation_drop", mutation_drop_effective)
			room.add_child(enemy_instance)
			if spawn_counter < anchors.size():
				enemy_instance.position = anchors[spawn_counter].position
			else:
				enemy_instance.position = _enemy_spawn_fallback_local_relative_to_room(room)
			spawn_counter += 1

	room.set_meta(_META_SPAWN_GENERATED_ENEMIES_DONE, true)


func _read_model_registry_manifest() -> Dictionary:
	var manifest_path: String = "res://asset_generation/python/model_registry.json"
	if not FileAccess.file_exists(manifest_path):
		return {}
	var file := FileAccess.open(manifest_path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		return {}
	return parsed as Dictionary
