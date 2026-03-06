# enemy_infection_3d.gd
#
# 3D engine-integration node for the infection loop: holds an EnemyStateMachine,
# exposes it to InfectionInteractionHandler for target/absorb, and detects
# player (for set_target_esm/clear_target) and chunk (for weaken + infect).
# Same contract as enemy_infection.gd but with Area3D and Node3D.

extends Node3D

var _esm: EnemyStateMachine
var _handler: InfectionInteractionHandler
var _area: Area3D


func _ready() -> void:
	_esm = EnemyStateMachine.new()
	var root: Node = get_parent()
	if root != null:
		_handler = root.get_node_or_null("InfectionInteractionHandler") as InfectionInteractionHandler
	_area = get_node_or_null("InteractionArea") as Area3D
	if _area != null:
		_area.body_entered.connect(_on_body_entered)
		_area.body_exited.connect(_on_body_exited)


func get_esm() -> EnemyStateMachine:
	return _esm


func _on_body_entered(body: Node3D) -> void:
	if body.is_in_group("player"):
		if _handler != null:
			_handler.set_target_esm(_esm)
	if body.is_in_group("chunk"):
		_esm.apply_weaken_event()
		_esm.apply_infection_event()


func _on_body_exited(body: Node3D) -> void:
	if body.is_in_group("player"):
		if _handler != null:
			_handler.clear_target()
