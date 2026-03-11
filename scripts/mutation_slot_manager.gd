# mutation_slot_manager.gd
#
# Pure-logic coordinator for two independent MutationSlot instances.
# Implements the dual-slot fill-order rule (DSM-2):
#   1. Fill slot A (index 0) if empty.
#   2. Else fill slot B (index 1) if empty.
#   3. Else (both full) overwrite slot B — last-absorb-wins.
#
# Slot A is never overwritten by fill_next_available() while it is filled.
# Only clear_slot(0) or clear_all() can empty slot A.
#
# No Node, scene-tree, or engine-API dependencies. Fully headless-testable.
#
# Callers must null-check the result of get_slot() before using it.
# get_slot() with an out-of-range index returns null (caller's responsibility).
#
# Ticket: two_mutation_slots.md
# Spec:   two_mutation_slots_spec.md (DSM-1, DSM-2, DSM-3)

class_name MutationSlotManager
extends RefCounted


const _MutationSlotScript: GDScript = preload("res://scripts/mutation_slot.gd")

# Exactly two slots; capacity is fixed per spec (DSM-1).
var _slots: Array[MutationSlot] = []


func _init() -> void:
	# Create both slot instances at construction time. They are never null
	# during the manager's lifetime.
	_slots.append(_MutationSlotScript.new())
	_slots.append(_MutationSlotScript.new())


# Returns the MutationSlot at the given index, or null if out of range.
# Valid indices: 0 (slot A) and 1 (slot B).
func get_slot(index: int) -> MutationSlot:
	if index < 0 or index >= _slots.size():
		return null
	return _slots[index]


# Fills the next available slot per the DSM-2 fill-order rule:
#   1. Slot A (index 0) if empty.
#   2. Slot B (index 1) if empty.
#   3. Overwrite slot B (last-absorb-wins) when both are full.
# Rejects empty string IDs with push_error and returns without modifying slots.
# Whitespace-only IDs are accepted (not the empty string per spec guard).
func fill_next_available(id: String) -> void:
	if id == "":
		push_error("MutationSlotManager.fill_next_available: id must not be empty string; call ignored.")
		return

	var slot_a: MutationSlot = _slots[0]
	var slot_b: MutationSlot = _slots[1]

	if not slot_a.is_filled():
		slot_a.set_active_mutation_id(id)
	elif not slot_b.is_filled():
		slot_b.set_active_mutation_id(id)
	else:
		# Both slots are filled; overwrite slot B (last-absorb-wins for slot B).
		slot_b.set_active_mutation_id(id)


# Returns 2 always. Capacity is fixed per spec (DSM-1).
func get_slot_count() -> int:
	return 2


# Returns true if at least one slot is_filled(); false if both are empty.
func any_filled() -> bool:
	return _slots[0].is_filled() or _slots[1].is_filled()


# Clears both slots.
func clear_all() -> void:
	_slots[0].clear()
	_slots[1].clear()


# Clears the slot at the given index. No-op if index is out of range (no crash).
func clear_slot(index: int) -> void:
	if index < 0 or index >= _slots.size():
		return
	_slots[index].clear()
