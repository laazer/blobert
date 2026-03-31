# infection_absorb_resolver.gd
#
# Pure logic: determines if an enemy can be absorbed (infected state) and
# resolves absorb by transitioning ESM to dead and granting one mutation.
# No Node or scene dependencies.
#
# Ticket: infection_interaction.md
# API: can_absorb(esm), resolve_absorb(esm, inv)

class_name InfectionAbsorbResolver
extends RefCounted


const DEFAULT_MUTATION_ID: String = "infection_mutation_01"


func can_absorb(esm: EnemyStateMachine) -> bool:
	if esm == null:
		return false
	return esm.get_state() == "infected"


func resolve_absorb(esm: EnemyStateMachine, inv: Object, slot: Object = null, mutation_id: String = "") -> void:
	if esm == null or inv == null:
		return
	if not can_absorb(esm):
		return
	var mid: String = mutation_id if mutation_id != "" else DEFAULT_MUTATION_ID
	esm.apply_death_event()
	inv.grant(mid)

	if slot != null:
		# Dispatch: check fill_next_available first (MutationSlotManager), then
		# set_active_mutation_id (single MutationSlot). If neither is present,
		# log an error but do not crash.
		if slot.has_method("fill_next_available"):
			slot.fill_next_available(mid)
		elif slot.has_method("set_active_mutation_id"):
			slot.set_active_mutation_id(mid)
		else:
			push_error("InfectionAbsorbResolver: slot arg has neither fill_next_available nor set_active_mutation_id")
