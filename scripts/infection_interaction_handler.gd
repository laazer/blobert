# infection_interaction_handler.gd
#
# Gameplay wiring: connects input (absorb, infect) and target enemy ESM to
# InfectionAbsorbResolver and MutationInventory. Updates InfectionUI absorb
# prompt visibility. No core simulation logic — delegates to pure modules.
#
# Contract: Engine-Integration or enemy/area nodes call set_target_esm(esm)
# when the player is in range of an enemy; clear_target() when leaving range.
# Chunk contact → infection can be wired separately (chunk or enemy calls
# apply_infection_event on the ESM).
#
# Ticket: infection_interaction.md (Task 7)

class_name InfectionInteractionHandler
extends Node

const _MutationInventoryScript: GDScript = preload("res://scripts/mutation_inventory.gd")
const _ResolverScript: GDScript = preload("res://scripts/infection_absorb_resolver.gd")

var _inventory: RefCounted
var _resolver: RefCounted
var _target_esm: EnemyStateMachine = null
var _infection_ui: CanvasLayer = null


func _ready() -> void:
	_inventory = _MutationInventoryScript.new()
	_resolver = _ResolverScript.new()
	var root: Node = get_parent()
	if root != null:
		_infection_ui = root.get_node_or_null("InfectionUI") as CanvasLayer


func _process(_delta: float) -> void:
	if _infection_ui != null and _infection_ui.has_method("set_absorb_available"):
		var available: bool = _target_esm != null and _resolver.can_absorb(_target_esm)
		_infection_ui.set_absorb_available(available)

	if _target_esm == null:
		return

	if Input.is_action_just_pressed("absorb"):
		if _resolver.can_absorb(_target_esm):
			_resolver.resolve_absorb(_target_esm, _inventory)

	if Input.is_action_just_pressed("infect"):
		if _target_esm.get_state() == "weakened":
			_target_esm.apply_infection_event()


func set_target_esm(esm: EnemyStateMachine) -> void:
	_target_esm = esm


func clear_target() -> void:
	_target_esm = null


func get_mutation_inventory() -> RefCounted:
	return _inventory
