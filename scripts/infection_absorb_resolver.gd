# infection_absorb_resolver.gd
#
# Pure logic: determines if an enemy can be absorbed (infected state) and
# resolves absorb by transitioning ESM to dead and granting one mutation.
# No Node or scene dependencies.
#
# Ticket: infection_interaction.md
# API: can_absorb(esm), resolve_absorb(esm, inv[, slot_or_manager])
#
# Updated: two_mutation_slots.md (Task 5)
# The third argument to resolve_absorb() now accepts three forms:
#   - null                 — no slot operation (backward-compat).
#   - single MutationSlot  — detected via has_method("set_active_mutation_id")
#                            and NOT has_method("fill_next_available").
#                            Calls slot.set_active_mutation_id(DEFAULT_MUTATION_ID).
#   - MutationSlotManager  — detected via has_method("fill_next_available")
#                            (higher-specificity check, evaluated first).
#                            Calls manager.fill_next_available(DEFAULT_MUTATION_ID).
# Dispatch order: fill_next_available checked before set_active_mutation_id to
# avoid routing a manager through the single-slot path (see DSM-6 spec risk note).

class_name InfectionAbsorbResolver
extends RefCounted


const DEFAULT_MUTATION_ID: String = "infection_mutation_01"


func can_absorb(esm: EnemyStateMachine) -> bool:
	if esm == null:
		return false
	return esm.get_state() == "infected"


func resolve_absorb(esm: EnemyStateMachine, inv: Object, slot: Object = null) -> void:
	if esm == null or inv == null:
		return
	if not can_absorb(esm):
		return
	esm.apply_death_event()
	inv.grant(DEFAULT_MUTATION_ID)

	if slot == null:
		return

	# Dispatch: check fill_next_available first (MutationSlotManager path).
	if slot.has_method("fill_next_available"):
		slot.fill_next_available(DEFAULT_MUTATION_ID)
	elif slot.has_method("set_active_mutation_id"):
		# Single-slot backward-compat path.
		slot.set_active_mutation_id(DEFAULT_MUTATION_ID)
	else:
		push_error(
			"InfectionAbsorbResolver.resolve_absorb: slot argument has neither "
			+ "fill_next_available nor set_active_mutation_id; slot update skipped."
		)
