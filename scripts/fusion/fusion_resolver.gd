# fusion_resolver.gd
#
# Pure logic: determines if fusion is possible (both mutation slots filled) and
# resolves fusion by applying a timed speed-boost effect to the player and then
# consuming both mutation slots.
#
# No Node, Input, or scene dependencies. Headless-testable.
#
# Analogous structure to InfectionAbsorbResolver.
#
# Ticket: fusion_rules_and_hybrid.md
# Spec:   fusion_rules_and_hybrid_spec.md (FRH-2, FRH-3, FRH-5)

class_name FusionResolver
extends RefCounted


const FUSION_DURATION: float = 5.0
const FUSION_MULTIPLIER: float = 1.5


# Returns true only when both mutation slots are filled.
# Null-safe: returns false for null manager, missing get_slot method, or null
# slot return values. Pure function — no state mutation.
func can_fuse(slot_manager: Object) -> bool:
	if slot_manager == null:
		return false
	if not slot_manager.has_method("get_slot"):
		return false
	var slot_a: Object = slot_manager.get_slot(0)
	if slot_a == null:
		return false
	var slot_b: Object = slot_manager.get_slot(1)
	if slot_b == null:
		return false
	return slot_a.is_filled() and slot_b.is_filled()


# Resolves fusion: applies the timed speed-boost effect to the player then
# consumes both mutation slots.
#
# Guards internally via can_fuse — early-returns if guard fails.
# Order per FRH-3-AC-11: apply_fusion_effect BEFORE consume_fusion_slots.
#
# Null-safety:
#   - null slot_manager or failed guard → early return, no side effects.
#   - null player → slots are still consumed; push_error not emitted for null
#     player (null is an explicitly supported path per FRH-3-AC-8).
#   - player without apply_fusion_effect → push_error + slots still consumed.
#   - slot_manager without consume_fusion_slots → push_error, slots not consumed.
func resolve_fusion(slot_manager: Object, player: Object) -> void:
	if not can_fuse(slot_manager):
		return

	# Apply effect first (FRH-3-AC-11).
	if player != null:
		if player.has_method("apply_fusion_effect"):
			player.apply_fusion_effect(FUSION_DURATION, FUSION_MULTIPLIER)
		else:
			push_error("FusionResolver: player arg does not have apply_fusion_effect — effect not applied; slots will still be consumed")

	# Consume slots after effect (FRH-3-AC-11 / FRH-5).
	if slot_manager.has_method("consume_fusion_slots"):
		slot_manager.consume_fusion_slots()
	else:
		push_error("FusionResolver: slot_manager does not have consume_fusion_slots — slots not consumed")
