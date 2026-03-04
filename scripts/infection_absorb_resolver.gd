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


func resolve_absorb(esm: EnemyStateMachine, inv: Object) -> void:
	if esm == null or inv == null:
		return
	if not can_absorb(esm):
		return
	esm.apply_death_event()
	inv.grant(DEFAULT_MUTATION_ID)
