# mutation_inventory.gd
#
# Pure logic: tracks which mutation IDs have been granted (e.g. via absorb).
# No Node or scene dependencies. Deterministic and testable in isolation.
#
# Ticket: infection_interaction.md
# API: grant(id), has(id), get_granted_count()

class_name MutationInventory
extends RefCounted


var _granted_ids: Array[String] = []


func grant(id: String) -> void:
	_granted_ids.append(id)


func has(id: String) -> bool:
	return id in _granted_ids


func get_granted_count() -> int:
	return _granted_ids.size()
