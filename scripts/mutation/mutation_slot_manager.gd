# mutation_slot_manager.gd
#
# Pure logic: coordinator for two independent MutationSlot instances.
# Owns slot A (index 0) and slot B (index 1).
#
# Fill order: first-available (A before B); if both full, slot B is overwritten
# (last-absorb-wins for slot B).
#
# Callers are responsible for index validation before using the return value
# of get_slot() — an out-of-range index returns null.
#
# Ticket: two_mutation_slots.md
# Spec: two_mutation_slots_spec.md (DSM-1, DSM-2, DSM-3)

class_name MutationSlotManager
extends RefCounted

const _MutationSlotScript: GDScript = preload("res://scripts/mutation/mutation_slot.gd")

var _slots: Array = []


func _init() -> void:
	_slots = [_MutationSlotScript.new(), _MutationSlotScript.new()]


func get_slot_count() -> int:
	return 2


func get_slot(index: int) -> RefCounted:
	if index < 0 or index >= _slots.size():
		return null
	return _slots[index]


func any_filled() -> bool:
	for slot in _slots:
		if slot.is_filled():
			return true
	return false


func fill_next_available(id: String) -> void:
	if id == "":
		push_error("MutationSlotManager.fill_next_available: id must not be empty")
		return
	# Slot A first; if A is full, slot B; if both full, overwrite slot B.
	if not _slots[0].is_filled():
		_slots[0].set_active_mutation_id(id)
	elif not _slots[1].is_filled():
		_slots[1].set_active_mutation_id(id)
	else:
		_slots[1].set_active_mutation_id(id)


func clear_all() -> void:
	for slot in _slots:
		slot.clear()


func clear_slot(index: int) -> void:
	if index < 0 or index >= _slots.size():
		return
	_slots[index].clear()
