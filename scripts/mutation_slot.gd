class_name MutationSlot
extends RefCounted


var _active_mutation_id: String = ""


func is_filled() -> bool:
	return _active_mutation_id != ""


func get_active_mutation_id() -> String:
	return _active_mutation_id


func set_active_mutation_id(id: String) -> void:
	if id == "":
		clear()
		return

	_active_mutation_id = id


func clear() -> void:
	_active_mutation_id = ""

