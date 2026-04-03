# enemy_generated_esm_stub.gd
#
# Minimal stand-in for EnemyStateMachine on procedurally generated enemies until
# M15 wires a real RefCounted ESM. Serialized as a child of EnemyAnimationController.
extends Node


func get_state() -> String:
	return "idle"
