# enemy_infection.gd
#
# Engine-integration node for the infection loop: holds an EnemyStateMachine,
# exposes it to InfectionInteractionHandler for target/absorb, and detects
# player (for set_target_esm/clear_target) and chunk (for weaken + infect).
# Uses CharacterBody2D so the enemy is affected by gravity and collides with the floor.
#
# Contract: Parent scene must have "InfectionInteractionHandler" as sibling.
# Chunk contact: apply_weaken_event then apply_infection_event (idempotent per ESM).
#
# Ticket: infection_interaction.md (Task 8)

class_name EnemyInfection
extends CharacterBody2D

var _esm: EnemyStateMachine
var _handler: InfectionInteractionHandler
var _area: Area2D


func _ready() -> void:
	_esm = EnemyStateMachine.new()
	var root: Node = get_parent()
	if root != null:
		_handler = root.get_node_or_null("InfectionInteractionHandler") as InfectionInteractionHandler
	_area = get_node_or_null("InteractionArea") as Area2D
	if _area != null:
		_area.body_entered.connect(_on_body_entered)
		_area.body_exited.connect(_on_body_exited)


func get_esm() -> EnemyStateMachine:
	return _esm


func _on_body_entered(body: Node2D) -> void:
	if body.is_in_group("player"):
		if _handler != null:
			_handler.set_target_esm(_esm)
	if body.is_in_group("chunk"):
		_esm.apply_weaken_event()
		_esm.apply_infection_event()


func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		if _handler != null:
			_handler.clear_target()


func _physics_process(delta: float) -> void:
	# Apply gravity so the enemy stands on the floor and does not float.
	var project_gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity", 980.0) as float
	velocity.y += project_gravity * delta
	velocity.x = 0.0
	move_and_slide()
