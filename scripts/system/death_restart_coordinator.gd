# death_restart_coordinator.gd
#
# Wires the player death / run restart lifecycle without reloading the scene.
# Monitors player HP each frame; on death, tweens SlimeVisual scale to zero,
# then after 1.5s resets HP, chunks, position, and mutation slots in-place.
#
# Spec: agent_context/agents/2_spec/soft_death_and_restart_spec.md
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/soft_death_and_restart.md

class_name DeathRestartCoordinator
extends Node

@export var player: NodePath
@export var spawn_position: NodePath
@export var infection_handler: NodePath

var _rsm: RunStateManager
var _dead: bool = false


func _ready() -> void:
	_rsm = RunStateManager.new()
	_rsm.player_died.connect(_on_player_died)
	_rsm.run_restarted.connect(_on_run_restarted)
	_rsm.apply_event("start_run")


func _process(_delta: float) -> void:
	var player_node := get_node_or_null(player) as PlayerController3D
	if player_node != null \
			and player_node.get_current_hp() <= 0.0 \
			and not _dead \
			and _rsm.get_state() == RunStateManager.State.ACTIVE:
		_rsm.apply_event("player_died")


func _on_player_died() -> void:
	if _dead:
		return
	_dead = true
	var player_node := get_node_or_null(player) as PlayerController3D
	if player_node != null:
		var vis := player_node.get_node_or_null("SlimeVisual") as Node3D
		if vis != null:
			var tween := player_node.create_tween()
			tween.tween_property(vis, "scale", Vector3.ZERO, 0.8)
	get_tree().create_timer(1.5).timeout.connect(_reset_run)


func _reset_run() -> void:
	var player_node := get_node_or_null(player) as PlayerController3D
	var spawn_node := get_node_or_null(spawn_position) as Node3D
	var handler_node := get_node_or_null(infection_handler) as InfectionInteractionHandler
	if player_node != null and spawn_node != null:
		player_node.reset_position(spawn_node.global_position)
	if player_node != null:
		player_node.reset_hp()
		player_node.reset_chunks()
	if handler_node != null:
		handler_node.get_mutation_slot_manager().clear_all()
	else:
		push_warning("DeathRestartCoordinator: infection_handler NodePath not set; mutation slots not cleared")
	_rsm.apply_event("restart")
	_rsm.apply_event("start_run")
	if player_node != null:
		var vis := player_node.get_node_or_null("SlimeVisual") as Node3D
		if vis != null:
			vis.scale = Vector3.ONE
	_dead = false


func _on_run_restarted() -> void:
	pass
