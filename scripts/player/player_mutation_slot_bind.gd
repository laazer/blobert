## Late-binds mutation slot manager from InfectionInteractionHandler for PlayerController3D.

class_name PlayerMutationSlotBind
extends RefCounted


static func try_bind_from_handler(handler: Node) -> Variant:
	if handler == null:
		return null
	if handler.has_method("get_mutation_slot_manager"):
		var mgr: Variant = handler.call("get_mutation_slot_manager")
		if mgr != null:
			return mgr
	if handler.has_method("get_mutation_slot"):
		var legacy_slot: Variant = handler.call("get_mutation_slot")
		if legacy_slot != null:
			return legacy_slot
	return null


static func ensure_binding(player: PlayerController3D) -> void:
	if player._mutation_slot != null:
		return
	var root: Node = player.get_parent()
	if root == null:
		return
	var handler: Node = root.get_node_or_null("InfectionInteractionHandler")
	if handler == null:
		return
	player._infection_handler = handler
	player._mutation_slot = try_bind_from_handler(handler)
