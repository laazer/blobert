# enemy_base.gd
#
# Shared base script for procedurally generated enemies. Attached to
# CharacterBody3D roots created by scripts/asset_generation/load_assets.gd.
# Exposes identity exports and a three-state enum for external coordination.
#
# Ticket: enemy_base_script
# Spec: agent_context/agents/2_spec/enemy_base_spec.md

class_name EnemyBase
extends CharacterBody3D

@export var enemy_id: String = ""
@export var enemy_family: String = ""
@export var mutation_drop: String = ""

enum State { NORMAL = 0, WEAKENED = 1, INFECTED = 2 }

var current_state: State = State.NORMAL


func set_base_state(state: State) -> void:
	current_state = state


func get_base_state() -> State:
	return current_state
