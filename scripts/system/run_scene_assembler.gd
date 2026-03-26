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

var _rsm: RunStateManager
var _active_rooms: Array[Node3D] = []


func _ready() -> void:
	_rsm = RunStateManager.new()
	_rsm.run_started.connect(_on_run_started)
	_rsm.apply_event("start_run")


func _on_run_started() -> void:
	_clear_rooms()

	var generator := RoomChainGenerator.new()
	var paths: Array[String] = generator.generate(SEQUENCE, POOL, Time.get_ticks_msec())

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

		level_root.add_child(room)
		_active_rooms.append(room)

		cursor_x += exit_local_x


func _clear_rooms() -> void:
	for node in _active_rooms:
		if is_instance_valid(node):
			node.queue_free()
	_active_rooms.clear()
