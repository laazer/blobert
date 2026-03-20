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
# Updated: two_mutation_slots.md (Task 6)
#   - Instantiates MutationSlotManager instead of a single MutationSlot.
#   - Exposes get_mutation_slot_manager() returning the full manager.
#   - Keeps get_mutation_slot() as a backward-compat alias returning slot A
#     (index 0) so PlayerController3D and InfectionUI remain unbroken.

class_name InfectionInteractionHandler
extends Node

signal absorb_resolved(esm: EnemyStateMachine)

const _MutationInventoryScript: GDScript = preload("res://scripts/mutation/mutation_inventory.gd")
const _ResolverScript: GDScript = preload("res://scripts/infection/infection_absorb_resolver.gd")
const _MutationSlotManagerScript: GDScript = preload("res://scripts/mutation/mutation_slot_manager.gd")
const _FusionResolverScript: GDScript = preload("res://scripts/fusion/fusion_resolver.gd")

var _inventory: RefCounted
var _resolver: RefCounted
var _slot_manager: RefCounted
var _fusion_resolver: FusionResolver

var _target_esm: EnemyStateMachine = null
var _infection_ui: CanvasLayer = null
var _player_node: Node = null


func _ready() -> void:
	_inventory = _MutationInventoryScript.new()
	_resolver = _ResolverScript.new()
	_slot_manager = _MutationSlotManagerScript.new()
	_fusion_resolver = _FusionResolverScript.new()
	var root: Node = get_parent()
	if root != null:
		_infection_ui = root.get_node_or_null("InfectionUI") as CanvasLayer
	if get_tree() != null:
		_player_node = get_tree().get_first_node_in_group("player")


func _process(_delta: float) -> void:
	if _infection_ui != null and _infection_ui.has_method("set_absorb_available"):
		var available: bool = _target_esm != null and _resolver.can_absorb(_target_esm)
		_infection_ui.set_absorb_available(available)

	if Input.is_action_just_pressed("fuse"):
		if _fusion_resolver != null and _fusion_resolver.can_fuse(_slot_manager):
			_fusion_resolver.resolve_fusion(_slot_manager, _player_node)

	if _target_esm == null:
		return

	if Input.is_action_just_pressed("absorb"):
		if _resolver.can_absorb(_target_esm):
			_resolver.resolve_absorb(_target_esm, _inventory, _slot_manager)
			absorb_resolved.emit(_target_esm)

	if Input.is_action_just_pressed("infect"):
		if _target_esm.get_state() == "weakened":
			_target_esm.apply_infection_event()


func set_target_esm(esm: EnemyStateMachine) -> void:
	_target_esm = esm


func clear_target() -> void:
	_target_esm = null


func get_mutation_inventory() -> RefCounted:
	return _inventory


func get_mutation_slot_manager() -> RefCounted:
	return _slot_manager


# Backward-compat alias: returns slot A from the manager.

func get_mutation_slot() -> RefCounted:
	return _slot_manager.get_slot(0)


## Auto-resolve absorb after chunk DoT (tick 3). Same as pressing absorb when infected.
func resolve_absorb_for_esm(esm: EnemyStateMachine) -> void:
	if _resolver == null or esm == null:
		return
	if not _resolver.can_absorb(esm):
		return
	_resolver.resolve_absorb(esm, _inventory, _slot_manager)
	absorb_resolved.emit(esm)
